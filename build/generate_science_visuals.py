#!/usr/bin/env python3
"""Create original, exact SVG learning diagrams; no external images or data.

Run with an optional repository root. Default output is the staging directory.
All quantitative figures use the explicitly supplied teaching data.
"""
from pathlib import Path
from html import escape
import math
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else (SCRIPT_DIR.parent if SCRIPT_DIR.name == 'build' else SCRIPT_DIR)
OUT = ROOT / 'src/h5/science/figs'
OUT.mkdir(parents=True, exist_ok=True)

class SVG:
    def __init__(self, w=720, h=400, title='学習用の模式図'):
        self.w,self.h=w,h
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title,quote=True)}"><title>{escape(title)}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#263548"/></marker><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse"><path d="M-1,1 L1,-1 M0,7 L7,0 M6,8 L8,6" stroke="#66788d" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="white"/><g font-family="Noto Sans CJK JP, Noto Sans JP, Yu Gothic, sans-serif" font-size="17" fill="#182b40" stroke-linecap="round" stroke-linejoin="round">']
    def raw(self,s): self.parts.append(s)
    def text(self,x,y,s,size=17,anchor='middle',weight=None,fill='#182b40'):
        self.raw(f'<text x="{x:g}" y="{y:g}" font-size="{size}" text-anchor="{anchor}"'+(f' font-weight="{weight}"' if weight else '')+f' fill="{fill}">{escape(str(s))}</text>')
    def line(self,x1,y1,x2,y2,color='#263548',width=2,dash=None,arrow=False):
        self.raw(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
    def rect(self,x,y,w,h,fill='white',stroke='#263548',rx=0,width=2):
        self.raw(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def circle(self,x,y,r,fill='white',stroke='#263548',width=2):
        self.raw(f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def ellipse(self,x,y,rx,ry,fill='white',stroke='#263548',width=2):
        self.raw(f'<ellipse cx="{x:g}" cy="{y:g}" rx="{rx:g}" ry="{ry:g}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def path(self,d,fill='none',stroke='#263548',width=2,dash=None):
        self.raw(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def poly(self,pts,fill='none',stroke='#263548',width=2):
        self.raw('<polygon points="'+' '.join(f'{x:g},{y:g}' for x,y in pts)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    def save(self,name):
        self.text(self.w/2,self.h-12,'自作の学習用模式図・数値は設問用',14,fill='#526277')
        svg=''.join(self.parts)+'</g></svg>'
        # Inline diagrams share an HTML document: keep all paint servers and
        # marker/clip references local to the asset rather than using common IDs.
        prefix='sci-'+re.sub(r'[^a-zA-Z0-9_-]','-',name)+'-'
        svg=re.sub(r'\bid="([^"]+)"',lambda m:'id="'+prefix+m.group(1)+'"',svg)
        svg=re.sub(r'url\(#([^)]+)\)',lambda m:'url(#'+prefix+m.group(1)+')',svg)
        (OUT/(name+'.svg')).write_text(svg,encoding='utf-8')

def chart(s,x,y,w,h,xmax,ymax,xticks,yticks,xlabel,ylabel):
    # y is top; labels deliberately outside the plotting rectangle.
    for v in xticks:
        px=x+w*v/xmax
        s.line(px,y,px,y+h,color='#d6dce4',width=1)
        s.text(px,y+h+24,f'{v:g}',16)
    for v in yticks:
        py=y+h-h*v/ymax
        s.line(x,py,x+w,py,color='#d6dce4',width=1)
        s.text(x-12,py+5,f'{v:g}',16,anchor='end')
    s.line(x,y,x,y+h);s.line(x,y+h,x+w,y+h)
    s.text(x+w/2,y+h+52,xlabel,17)
    s.text(x,y-18,ylabel,17,anchor='start')
    return lambda a,b:(x+w*a/xmax,y+h-h*b/ymax)

def series(s,xy,data,label=None,label_dx=10,label_dy=0,color='#126b8d',dash=None):
    pts=[xy(a,b) for a,b in data]
    s.path('M'+' L'.join(f'{x:g},{y:g}' for x,y in pts),stroke=color,width=3,dash=dash)
    for x,y in pts:s.circle(x,y,3.8,fill=color,stroke=color,width=1)
    if label:
        x,y=pts[-1];s.text(x+label_dx,y+label_dy,label,17,anchor='start',weight='bold',fill=color)

def cell(s,x,y,stage,label):
    s.text(x+85,y+20,label,20,weight='bold')
    s.rect(x+15,y+36,140,126,fill='#f8fbff',rx=10)
    if stage=='rest':s.ellipse(x+85,y+99,35,30,fill='#e6edf5')
    elif stage=='condense':
        for dx,dy in [(-22,-17),(17,-20),(-20,20),(20,17)]:
            s.path(f'M{x+85+dx-7},{y+99+dy-9} l14,18 m0,-18 l-14,18',width=3)
    elif stage=='middle':
        for yy in [61,86,111,136]:s.path(f'M{x+76},{y+yy-8} l18,16 m0,-16 l-18,16',width=3)
    elif stage=='separate':
        for yy in [62,86,110,134]:
            s.path(f'M{x+58},{y+yy-7} l-10,7 l10,7 M{x+112},{y+yy-7} l10,7 l-10,7',width=3)
    elif stage in ('plate','two'):
        s.ellipse(x+52,y+99,20,30,fill='#e6edf5');s.ellipse(x+118,y+99,20,30,fill='#e6edf5')
        s.line(x+85,y+(66 if stage=='plate' else 36),x+85,y+(132 if stage=='plate' else 162),width=3)

s=SVG(600,430,'タマネギの体細胞分裂 A〜F。順不同。染色体は模式化。')
for i,(lab,stage) in enumerate([('A','separate'),('B','rest'),('C','middle'),('D','plate'),('E','condense'),('F','two')]):
    cell(s,30+(i%3)*185,18+(i//3)*182,stage,lab)
s.text(300,394,'染色体は模式化。図の本数はタマネギの実際の本数ではない。',15)
s.save('visual_mitosis')

s=SVG(700,310,'カエルの初期発生 A〜E。受精卵から胚までは同じ外径。')
for i,lab in enumerate('ABCDE'):
    x=76+i*136;s.text(x,42,lab,20,weight='bold')
    if lab!='E':
        s.circle(x,140,50,fill='#eff6fc')
        if lab in ('B','C'):s.line(x,90,x,190)
        if lab=='B':s.line(x-50,140,x+50,140)
        if lab=='D':
            # Many small cells represented within the same circular outline.
            for dy in [-30,-10,10,30]:
                for dx in [-30,-10,10,30]:
                    if dx*dx+dy*dy<1900:s.circle(x+dx,140+dy,10,fill='#e1ecf7',width=1)
    else:
        s.path(f'M{x-38},145 C{x-52},99 {x-2},97 {x+3},130 C{x+22},129 {x+40},111 {x+49},119 C{x+39},144 {x+25},161 {x-3},162 C{x-25},177 {x-37},161 {x-38},145 Z',fill='#dcebf5')
        s.circle(x-30,127,3,fill='#182b40')
s.text(350,238,'A〜D：同じ倍率で見た模式図。 E：倍率は異なる。',17)
s.text(350,267,'卵割の溝を見分ける。D の細かい円は細胞を表す。',16)
s.save('visual_frog')

s=SVG(680,430,'根の成長の観察。等間隔の印の変化と根の部位。')
for xx,label,marks in [(140,'観察前',[75,100,125,150,175]),(400,'1日後',[75,100,140,205,230])]:
    s.text(xx,35,label,20,weight='bold')
    last=marks[-1]
    s.path(f'M{xx-28},55 L{xx-28},{last+18} Q{xx},{last+62} {xx+28},{last+18} L{xx+28},55',fill='#eff6fc')
    for i,yy in enumerate(marks):s.line(xx-28,yy,xx+28,yy,width=2.5);s.text(xx-43,yy+5,str(i+1),17)
    s.text(xx,last+76,'根の先端',16)
for i,(a,b) in enumerate(zip([75,100,140,205],[100,140,205,230])):
    s.text(487,(a+b)/2+5,['A','B','C','D'][i],19,weight='bold')
s.text(350,350,'1〜5 は根につけた印。A〜D は1日後の印の間。',17)
s.text(350,381,'模式図の縦の長さは観察結果に比例する。',16)
s.save('visual_root')

s=SVG(640,470,'被子植物のめしべと受精までの道すじ。①〜④は部位。')
s.path('M230,65 Q320,25 410,65 Q390,92 342,92 L342,225 Q450,260 435,355 Q424,403 320,410 Q217,403 205,355 Q190,260 298,225 L298,92 Q250,92 230,65 Z',fill='#edf5fc')
s.circle(290,58,12,fill='#d4e5f0');s.circle(332,51,12,fill='#d4e5f0')
s.path('M290,62 Q320,85 321,122 L321,250 Q302,267 300,300',stroke='#126b8d',width=5)
s.ellipse(310,331,54,55,fill='white');s.circle(300,345,17,fill='#d4e5f0')
s.path('M300,283 L300,326',stroke='#126b8d',width=5)
s.circle(301,313,5,fill='#263548');s.line(311,192,311,230,arrow=True)
for xx,yy,targetx,targety,num in [(125,72,267,78,'①'),(480,165,323,165,'②'),(505,330,361,330,'③'),(128,355,280,345,'④')]:
    s.text(xx,yy,num,22,weight='bold');s.line(xx+(20 if xx<300 else -20),yy-6,targetx,targety,width=1.5)
s.text(320,440,'黒い小円は、管の中を移動する精細胞を表す。',16)
s.save('visual_flower')

s=SVG(650,330,'エンドウの検定交雑。かけ合わせの表は空欄。')
s.text(325,35,'丸い種子の個体 X × しわの純系 aa',20,weight='bold')
s.text(325,69,'X の生殖細胞の遺伝子は、まだ決めない。',16)
for row in range(3):
    for col in range(3):s.rect(175+col*100,92+row*60,100,60,fill='#edf5fc' if row==0 or col==0 else 'white')
for x,lab in [(325,'?'),(425,'?')]:s.text(x,130,lab,23)
for y in [190,250]:s.text(225,y,'a',23)
s.text(126,214,'aa の',16);s.text(126,241,'生殖細胞',16)
for xx,yy,lab in [(325,190,'①'),(425,190,'②'),(325,250,'③'),(425,250,'④')]:s.text(xx,yy,lab,22)
s.save('visual_cross')

s=SVG(680,365,'ふ入りの葉の模式図。緑色部分とふ、遮光部分の組合せ。')
# Deliberately schematic quadrants: chlorophyll condition independent of light.
leaf_outline='M150,65 L510,65 Q570,65 570,125 L570,223 Q570,283 510,283 L150,283 Q90,283 90,223 L90,125 Q90,65 150,65 Z'
s.raw(f'<defs><clipPath id="leaf-outline"><path d="{leaf_outline}"/></clipPath></defs><g clip-path="url(#leaf-outline)">')
s.rect(90,65,480,218,fill='#e0eddb',stroke='none')
s.rect(330,65,240,218,fill='white',stroke='none')
s.rect(90,172,480,111,fill='url(#hatch)',stroke='none')
s.raw('</g>');s.path(leaf_outline)
s.line(330,65,330,283,width=1.5);s.line(90,172,570,172,width=1.5)
for xx,yy,lab in [(210,130,'A'),(450,130,'C'),(210,241,'B'),(450,241,'D')]:s.text(xx,yy,lab,24,weight='bold')
s.text(210,42,'緑色の部分',18);s.text(450,42,'白いふの部分',18)
s.text(600,124,'光あり',17);s.text(608,231,'光なし',17)
s.text(330,318,'下半分は両面をアルミニウムはくでおおった。',17)
s.save('visual_leaf')

s=SVG(680,400,'葉にワセリンをぬる条件と水の減少量。')
xy=chart(s,82,62,490,236,4,6,[.5,1.5,2.5,3.5],[0,1,2,3,4,5,6],'','水の減少量 [g]')
# Cover categorical numeric tick labels and replace them.
s.rect(70,301,520,40,fill='white',stroke='none')
for i,(v,lab) in enumerate([(6,'A なし'),(5,'B 表'),(2,'C 裏'),(1,'D 両面')]):
    x,y=xy(i+.5,v);s.rect(x-36,y,72,298-y,fill='#cfdfed');s.text(x,y-10,str(v),18,weight='bold');s.text(x,327,lab,17)
s.text(330,359,'ワセリンをぬった面（表＝おもて、裏＝うら）',17)
s.save('visual_transpiration')

s=SVG(690,310,'だ液実験。試験管から二つの試料を分けて検査。')
s.rect(34,85,156,84,fill='#edf5fc',rx=12);s.text(112,118,'デンプン液',19);s.text(112,147,'＋だ液または水',16)
s.line(195,128,270,128,arrow=True);s.text(231,94,'保温',17)
s.rect(282,80,118,98,fill='white',rx=12);s.text(341,119,'別々の',18);s.text(341,147,'試験管へ',18)
s.line(404,105,460,74,arrow=True);s.line(404,154,460,216,arrow=True)
s.rect(470,38,184, 72,fill='#edf5fc',rx=10);s.text(562,66,'ヨウ素液',18);s.text(562,94,'デンプンを調べる',16)
s.rect(470,180,184,82,fill='#edf5fc',rx=10);s.text(562,207,'ベネジクト液',18);s.text(562,232,'加熱して糖を調べる',16)
s.text(223,263,'同じ試料に2種類の薬品を順番に加えない。',16)
s.save('visual_saliva')

s=SVG(690,290,'BTB液の実験。水草の有無と明暗を組み合わせる。')
for i,(lab,plant,dark) in enumerate([('A',True,False),('B',False,False),('C',True,True),('D',False,True)]):
    x=89+170*i;s.text(x,34,lab,20,weight='bold')
    s.rect(x-46,58,92,147,fill='#f7efc5' if not dark else 'url(#hatch)',rx=14)
    s.line(x-46,76,x+46,76,color='#a89c52')
    if plant:
        s.line(x,188,x,101,color='#263548',width=3)
        for y in [118,144,168]:s.path(f'M{x},{y} q-28,-22 -29,-6 q14,15 29,6 M{x},{y} q28,-22 29,-6 q-14,15 -29,6',fill='#c1dbca')
    s.text(x,233,'暗い' if dark else '明るい',17)
s.save('visual_btb')

s=SVG(730,680,'電圧と電流。同じ2本の電熱線を縦横の軸を入れかえて表した。')
p=chart(s,85,58,500,210,6,.6,[0,2,4,6],[0,.2,.4,.6],'電圧 [V]','図1 電流 [A]')
series(s,p,[(0,0),(2,.2),(4,.4),(6,.6)],'P');series(s,p,[(0,0),(2,.1),(4,.2),(6,.3)],'Q',color='#874c18',dash='9 5')
p=chart(s,85,388,500,210,.6,6,[0,.2,.4,.6],[0,2,4,6],'電流 [A]','図2 電圧 [V]')
series(s,p,[(0,0),(.2,2),(.4,4),(.6,6)],'P');series(s,p,[(0,0),(.1,2),(.2,4),(.3,6)],'Q',label_dy=-4,color='#874c18',dash='9 5')
s.save('visual_iv')

def battery(s,cx,y,label):
    s.line(cx-7,y-22,cx-7,y+22,width=3);s.line(cx+7,y-11,cx+7,y+11,width=4)
    s.text(cx-19,y-31,'＋',17);s.text(cx+22,y-23,'−',17);s.text(cx,y+48,label,17)

def circuit_panel(s,x,y,parallel,a,b,volts,meter):
    s.text(x+154,y+22,'図2（並列）' if parallel else '図1（直列）',20,weight='bold')
    L,R,top,bottom=x+25,x+289,y+75,y+255
    s.line(L,top,L,bottom);s.line(R,top,R,bottom)
    if parallel:
        for yy,lab in [(top,a),(top+82,b)]:
            s.line(L,yy,x+116,yy);s.rect(x+116,yy-12,75,24);s.line(x+191,yy,R,yy);s.text(x+153,yy+39,lab,18)
        s.circle(L,top+82,4,fill='#263548');s.circle(R,top+82,4,fill='#263548')
    else:
        s.line(L,top,x+64,top);s.rect(x+64,top-12, 60,24);s.line(x+124,top,x+181,top);s.rect(x+181,top-12,60,24);s.line(x+241,top,R,top)
        s.text(x+94,top+40,a,18);s.text(x+211,top+40,b,18)
    cx=x+117
    s.line(L,bottom,cx-7,bottom);battery(s,cx,bottom,volts)
    s.line(cx+7,bottom,x+224,bottom);s.circle(x+242,bottom,18);s.text(x+242,bottom+6,'A',18);s.line(x+260,bottom,R,bottom)
    s.text(x+242,bottom+48,meter,17)

for name,a,b,v1,v2,amps in [('circuit_sp','a','b','12 V','12 V',('A₁','A₂')),('mock1_circuit','P','Q','10 V','6 V',('A','A')),('visual_circuit','P 10 Ω','Q 20 Ω','6 V','6 V',('A₁','A₂'))]:
    s=SVG(680,380,'直列と並列の閉じた回路。電源の長い線がプラス極。')
    circuit_panel(s,16,10,False,a,b,v1,amps[0]);circuit_panel(s,352,10,True,a,b,v2,amps[1]);s.save(name)

s=SVG(730,690,'電流計の接続と目盛り。500 mA端子を使用。')
s.line(76,84,76,276);s.line(76,84,257,84);s.rect(257,71,124,26);s.text(319,60,'電熱線',18);s.line(381,84,623,84);s.line(623,84,623,276)
s.line(76,276,247,276);battery(s,254,276,'電源');s.line(261,276,469,276);s.circle(490,276,21);s.text(490,283,'A',20);s.line(511,276,623,276)
s.text(444,244,'500 mA',17);s.text(523,244,'＋',18)
s.line(215,84,215,174);s.line(425,84,425,174);s.line(215,174,299,174);s.circle(319,174,20);s.text(319,181,'V',20);s.line(339,174,425,174)
s.text(292,145,'＋',18);s.text(351,145,'−',18);s.text(320,219,'電圧計：4.8 V',18)
s.text(365,380,'電流計の目盛り（0〜50）',20,weight='bold')
cx,cy,r=365,620,195
for i in range(51):
    ang=math.pi-math.pi*i/50
    rr=r-17 if i%10==0 else r-11 if i%5==0 else r-6
    s.line(cx+rr*math.cos(ang),cy-rr*math.sin(ang),cx+r*math.cos(ang),cy-r*math.sin(ang),width=1.5)
    if i%10==0:s.text(cx+(r+27)*math.cos(ang),cy-(r+27)*math.sin(ang)+6,str(i),17)
ang=math.pi-math.pi*32/50
s.line(cx,cy,cx+(r-10)*math.cos(ang),cy-(r-10)*math.sin(ang),color='#126b8d',width=3,arrow=True);s.circle(cx,cy,6,fill='#263548')
s.text(365,651,'接続：＋端子と500 mA端子。最小目盛りは1。',16)
s.save('visual_meter')

s=SVG(700,430,'電熱線で水を加熱した記録。縦軸は上昇温度。')
p=chart(s,85,65,480,260,5,8,[0,1,2,3,4,5],[0,2,4,6,8],'加熱時間 [分]','上昇温度 [℃]')
series(s,p,[(0,0),(1,1.6),(2,3.2),(3,4.8),(4,6.4),(5,8)],'Q');series(s,p,[(0,0),(1,.8),(2,1.6),(3,2.4),(4,3.2),(5,4)],'P',color='#874c18',dash='9 5')
s.save('visual_heat')

s=SVG(700,430,'銅をくり返し加熱したあとの固体の質量。')
p=chart(s,85,65,480,260,5,1.2,[0,1,2,3,4,5],[0,.2,.4,.6,.8,1,1.2],'加熱回数 [回]','固体の質量 [g]')
series(s,p,[(0,.8),(1,.88),(2,.96),(3,1),(4,1),(5,1)],label=None)
s.text(350,393,'加熱・冷却後に毎回はかる。固体は失われない。',16)
s.save('visual_copper')

s=SVG(700,435,'石灰石の質量と発生した二酸化炭素の質量。塩酸は同量。')
p=chart(s,85,70,480,250,4,1.32,[0,1,2,3,4],[0,.22,.44,.66,.88,1.1,1.32],'加えた石灰石 [g]','発生した二酸化炭素 [g]')
series(s,p,[(0,0),(1,.44),(2,.88),(2.5,1.1),(3,1.1),(4,1.1)])
s.text(350,394,'純粋な石灰石。同じ濃さ・同じ量の塩酸で比較。',16)
s.save('visual_gas_mass')

s=SVG(740,440,'炭酸水素ナトリウムの熱分解装置。試験管の口は底より低い。')
# Heated closed end upper-left; mouth lower-right; delivery above trough then submerged.
s.path('M87,85 Q54,94 70,122 L275,191 L287,153 Z',fill='#f0f6fb')
s.poly([(79,107),(130,117),(127,141),(78,122)],fill='#d4dfe9')
s.line( 88,131,133,146,width=4);s.text(150,56,'炭酸水素ナトリウム',17)
s.line(154,64,111,111,width=1)
s.poly([(272,151),(287,157),(278,195),(264,188)],fill='#b1bdc9')
s.path('M277,170 L349,193 L349,101 L519,101 L519,306 L569,306',width=5)
s.rect(438,238,253,139,fill='#ecf6fb');s.line(438,279,691,279,color='#126b8d',width=2)
s.path('M555,325 L555,174 Q555,162 568,162 L616,162 Q629,162 629,174 L629,325',fill='white')
s.line(556,254,628,254,color='#126b8d');s.rect(557,255,70,69,fill='#d9eef7',stroke='none')
s.path('M277,170 L349,193 L349,101 L519,101 L519,306 L569,306',width=4)
s.circle(585,284,4,stroke='#126b8d');s.circle(589,271,3,stroke='#126b8d')
s.text(592,143,'気体',18);s.text(474,400,'水そう',18);s.text(220,220,'口',18);s.line(236,213,265,183,width=1)
s.rect(86,222,56,92,fill='#edf5fc');s.rect(77,314,75,12,fill='#d4dfe9')
s.path('M100,208 Q84,173 114,143 Q134,174 124,208 Z',fill='#f6d7a3',stroke='#874c18')
s.text(171,278,'加熱',17);s.text(386,53,'ガラス管の先は水中',17)
s.save('visual_decomposition')

s=SVG(720,460,'硝酸カリウムと食塩の溶解度。水100gあたり。')
p=chart(s,88, 70,460,278,60,120,[0,20,40,60],[0,20,40,60,80,100,120],'温度 [℃]','水100 gにとける質量 [g]')
series(s,p,[(0,13),(20,32),(40,64),(60,110)],'硝酸カリウム',label_dx=10,label_dy=0)
series(s,p,[(0,35.7),(20,36),(40,36.5),(60,37)],'食塩',color='#874c18',dash='9 5')
s.text(350,419,'この問題では図の値を使う。水の蒸発はない。',16)
s.save('visual_solubility')

s=SVG(720,460,'地震波の到着時間と震源からの距離。P波6km/s、S波3km/sのモデル。')
p=chart(s,88,70,480,280,40,120,[0,10,20,30,40],[0,30,60,90,120],'地震発生からの時間 [秒]','震源からの距離 [km]')
series(s,p,[(0,0),(5,30),(10,60),(15,90),(20,120)],'P波',label_dy=-8)
series(s,p,[(0,0),(10,30),(20,60),(30,90),(40,120)],'S波',color='#874c18',dash='9 5')
s.text(352,421,'地震波が一定の速さで伝わるモデル。',16)
s.save('visual_seismic')

s=SVG(740,470,'3地点の柱状図。火山灰は同じ噴火でできた層。深さは各地点の地表から。')
for xx,lab,alt,depth in [(125,'A',100,10),(370,'B',90,5),(615,'C',110,30)]:
    s.text(xx,34,f'{lab} 地点',20,weight='bold');s.text(xx,62,f'地表の標高 {alt} m',17)
    s.rect(xx-40,100,80,280,fill='#f1e7d6')
    ash=100+depth*7
    s.rect(xx-40,100,80,max(0,ash-100),fill='url(#hatch)')
    s.rect(xx-40,ash,80,14,fill='#4b5b6d')
    for d in range(0,41,5):
        yy=100+d*7;s.line(xx+40,yy,xx+48,yy,width=1);s.text(xx+52,yy+5,str(d),16,anchor='start')
    s.text(xx,410,'深さ [m]',17)
s.text(370,441,'西 A ─ B ─ C 東 ／ 濃い帯＝同じ噴火の火山灰層。',16)
s.save('visual_strata')

s=SVG(710,410,'寒冷前線の模式地図。北が上、前線は東へ進む。')
s.rect(35,55,640,266,fill='#f7f9fc');s.line(605,115,605,72,arrow=True);s.text(605,51,'北',18)
s.path('M335,75 L285,145 L250,220 L222,300',stroke='#126b8d',width=4)
for x,y in [(310,110),(274,169),(240,247)]:s.poly([(x-5,y-10),(x-15,y+10),(x+15,y+9)],fill='#126b8d',stroke='#126b8d')
s.text(130,183,'冷たい空気',20);s.text(466,182,'暖かい空気',20)
s.circle(379,248,5,fill='#263548');s.text(397,253,'観測地点 X',18,anchor='start')
s.line(368, 92,480,92,arrow=True);s.text(431,74,'移動の向き',16)
s.text(355,361,'三角形は前線の進む側についている。',17)
s.save('visual_front')

s=SVG(720,445,'飽和水蒸気量と温度。この問題の計算用数値。')
p=chart(s,90,65,480,270,25,25,[0,5,10,15,20,25],[0,5,10,15,20,25],'気温 [℃]','飽和水蒸気量 [g/m³]')
series(s,p,[(0,4.8),(5,6.8),(10,9.4),(15,12.8),(20,17.3),(25,23.1)])
for a,b in [(5,6.8),(10,9.4),(20,17.3)]:
    x,y=p(a,b);s.text(x+12,y-14,str(b),17,anchor='start')
s.text(350,410,'空気1 m³あたり。曲線は資料の点を結んだ近似。',16)
s.save('visual_humidity')

s=SVG(730,440,'凸レンズの作図。焦点距離10cm。物体はレンズの左30cm。')
L,axis=385,205
s.line(35,axis,690,axis,color='#738297',width=1)
s.path('M385,94 Q351,205 385,316 Q419,205 385,94 Z',fill='#e9f4fa')
for x,label in [(185,'2F'),(285,'F'),(485,'F'),(585,'2F')]:s.line(x,axis-5,x,axis+5);s.text(x,axis+28,label,17)
s.line(85,205,85,145,width=3,arrow=True);s.text(85,127,'物体',18)
# Parallel ray refracts through the far focal point, central ray remains straight.
s.line(85,145,385,145,color='#126b8d',width=2.5);s.line(385,145,635,295,color='#126b8d',width=2.5,arrow=True)
s.line(85,145,635,255,color='#874c18',width=2.5,arrow=True)
s.line(535,205,535,235,width=3,arrow=True);s.text(550,270,'像',18)
s.line(85,344,385,344);s.line(85,338,85,350);s.line(385,338,385,350);s.text(235,372,'30 cm',18)
s.line(385,344,485,344);s.line(485,338,485,350);s.text(435,372,'10 cm',18)
s.text(385,66,'凸レンズ',20,weight='bold');s.text(610,365,'図は長さの比も表す',15)
s.save('visual_lens')

s=SVG(730,700,'音の波形3種類。縦軸は振幅比較用、横軸の時間幅に注意。')
for j,(lab,cycles,amp,span) in enumerate([('A',2,1,.02),('B',4,2,.02),('C',2,2,.04)]):
    x,y,w,h=90,55+j*211,510,128
    p=chart(s,x,y,w,h,span,4,[0,span/2,span],[0,2,4],'時間 [秒]','')
    s.rect(x-57,y-7,46,h+20,fill='white',stroke='none')
    s.text(30,y+65,lab,22,weight='bold')
    for yy,lab2 in [(0,'−2'),(2,'0'),(4,'2')]:
        _,py=p(0,yy);s.text(x-14,py+5,lab2,16,anchor='end')
    s.line(x,y+h/2,x+w,y+h/2,color='#738297',width=1)
    pts=[p(span*i/200,2+amp*math.sin(cycles*2*math.pi*i/200)) for i in range(201)]
    s.path('M'+' L'.join(f'{xx:.2f},{yy:.2f}' for xx,yy in pts),stroke='#126b8d',width=2.5)
s.text(650, 77,'縦の1目盛り',15);s.text(650,99,'は全図共通',15)
s.save('visual_sound')

s=SVG(710,440,'顕微鏡の視野と観察条件。像は左下にある。')
s.circle(208,211,133,fill='#f6faff');s.line(75,211,341,211,color='#c0ccda',width=1,dash='5 5');s.line(208,78,208,344,color='#c0ccda',width=1,dash='5 5')
s.ellipse(155,266,27,16,fill='#c8dcec');s.circle(155,266,6,fill='#667f97')
s.text(208,49,'今の視野',20,weight='bold');s.text(208,385,'像を中央へ移したい',17)
s.rect(397,91,261,208,fill='#edf5fc',rx=12)
for i,line in enumerate(['接眼：10倍','対物：10倍 → 40倍','100倍の視野直径：1.8 mm','400倍では直径に細胞3個']):s.text(527,132+i*43,line,16)
s.save('visual_microscope')

s=SVG(730,430,'植物の茎の横断面。Aは輪状の維管束、Bは散在する維管束。拡大図はA。')
for cx,lab in [(170,'A'),(535,'B')]:
    s.circle(cx,158,109,fill='#f5f9ed');s.text(cx, 32,lab,22,weight='bold')
    positions=[(80*math.cos(2*math.pi*i/10),80*math.sin(2*math.pi*i/10)) for i in range(10)] if lab=='A' else [(-55,-50),(5,-70),(60,-39),(-70,5),(-18,-19),(35,8),(69,49),(-47,62),(4,64)]
    for dx,dy in positions:
        s.ellipse(cx+dx,158+dy,8,12,fill='#cfdeeb',width=1.5)
        r=math.hypot(dx,dy) or 1;s.circle(cx+dx-dx/r*4,158+dy-dy/r*4,3,fill='#263548',width=1)
s.rect(227,306,272,71,fill='#edf5fc',rx=12);s.text(363,330,'A の維管束の拡大',17)
s.circle(336,354,11,fill='#263548');s.circle(391,354,11,fill='white');s.text(285,360,'内側',17);s.text(445,360,'外側',17)
s.text(350,404,'黒くぬった部分は、色水を吸わせると染まった部分。',16)
s.save('visual_stem')

print(f'Generated {len(list(OUT.glob("*.svg")))} science SVG files in {OUT}')
