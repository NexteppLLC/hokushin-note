#!/usr/bin/env python3
"""Rebuild original teaching diagrams (all statistical data are synthetic)."""
from pathlib import Path
from html import escape
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src/h5/social/figs'
OUT.mkdir(parents=True, exist_ok=True)

def text(x,y,t,size=17,anchor='start',fill='#172b3a'):
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}">{escape(str(t))}</text>'
def line(x1,y1,x2,y2,c='#172b3a',w=2,dash=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'
def rect(x,y,w,h,fill='#fff',stroke='#94a3b8',sw=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def circle(x,y,r,fill='white',stroke='#172b3a',sw=2):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def path(d,c='#172b3a',w=2,fill='none'):
    return f'<path d="{d}" stroke="{c}" stroke-width="{w}" fill="{fill}"/>'
def save(name,body,title='資料',w=800,h=500):
    key=Path(name).stem
    s=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="{key}_title {key}_desc"><title id="{key}_title">{escape(title)}</title><desc id="{key}_desc">自作の学習用模式図・統計。実在地点の測量図や実測統計ではありません。</desc><rect width="{w}" height="{h}" fill="white"/><g font-family="Noto Sans CJK JP, Yu Gothic, IPAexGothic, sans-serif">{body}</g></svg>'
    (OUT/name).write_text(s)
def labelbox(x,y,w,h,lines,fill='#f0f7fc'):
    return rect(x,y,w,h,fill)+''.join(text(x+12,y+26+i*25,t) for i,t in enumerate(lines))
def arrow(x1,y1,x2,y2,c='#2c677f'):
    angle=math.atan2(y2-y1,x2-x1); a=11
    p1=(x2-a*math.cos(angle-.4),y2-a*math.sin(angle-.4));p2=(x2-a*math.cos(angle+.4),y2-a*math.sin(angle+.4))
    return line(x1,y1,x2,y2,c,3)+path(f'M {p1[0]} {p1[1]} L {x2} {y2} L {p2[0]} {p2[1]}',c,3)
def north(x,y):
    return arrow(x,y+50,x,y+10,'#172b3a')+text(x,y,'北',18,'middle')
def scale(x,y):
    return line(x,y,x+160,y)+line(x,y-6,x,y+6)+line(x+80,y-6,x+80,y+6)+line(x+160,y-6,x+160,y+6)+text(x,y+26,'0',16,'middle')+text(x+80,y+26,'250',16,'middle')+text(x+160,y+26,'500 m',16,'middle')

# Symbols redrawn with paths from GSI's public map-sign reference.
def symbol(kind,x,y,s=1):
    b=''
    if kind=='city': b=circle(0,0,12)+circle(0,0,6)
    elif kind=='police': b=circle(0,0,12)+line(-8,-8,8,8)+line(-8,8,8,-8)
    elif kind=='fire': b=path('M -11 -11 Q -10 0 0 0 Q 10 0 11 -11 M 0 0 L 0 14')
    elif kind=='temple': b=path('M 12 -12 L 12 0 L -12 0 L -12 12 M -12 -12 L 0 -12 L 0 12 L 12 12')
    elif kind=='rice': b=path('M -9 -10 L -9 8 M -14 8 L -4 8 M 9 -10 L 9 8 M 4 8 L 14 8')
    elif kind=='field': b=path('M -12 -10 Q -10 4 0 10 Q 10 4 12 -10')
    elif kind=='orchard': b=circle(0,2,10)+line(0,-8,0,-16)
    elif kind=='triangulation': b=path('M 0 -13 L -13 10 L 13 10 Z')+circle(0,2,1.8,'#172b3a')
    elif kind=='school': b=path('M -2 -16 L 3 -12 M -15 -7 L 15 -7 M -8 -7 Q -4 6 14 14 M 8 -7 Q 4 6 -14 14')
    elif kind=='post': b=line(-12,-10,12,-10)+line(-12,-3,12,-3)+line(0,-3,0,13)
    elif kind=='hospital': b=circle(0,0,12)+line(-9,0,9,0)+line(0,-9,0,9)
    return f'<g transform="translate({x} {y}) scale({s})">{b}</g>'

names=['市役所','警察署','消防署','寺院','田','畑','果樹園','三角点','小・中学校','郵便局','病院']
kinds=['city','police','fire','temple','rice','field','orchard','triangulation','school','post','hospital']
for answered in (False,True):
    b=text(25,30,'地図記号の資料',22)
    for i,(n,k) in enumerate(zip(names,kinds)):
        x=85+(i%4)*190;y=85+(i//4)*120
        b+=symbol(k,x,y,1.25)+text(x,y+45,(f'{i+1}　{n}' if answered else f'{i+1}'),17,'middle')
    b+=text(25,435,'国土地理院の地図記号を参照して作図。形を拡大して表示。',16)
    save('geo_symbols'+('_key' if answered else '')+'.svg',b,'地図記号の資料',800,465)

# Two slope-asymmetric contour diagrams; each contour is 10 m apart.
b=text(25,30,'地図A（自作の地形図）',22)+rect(25,55,750,365,'#fcfcf5')+north(725,80)
for i in range(6):
    # west contours 14 px apart, east contours 42 px apart => west steeper
    left=135+14*i;right=635-42*i;top=90+21*i;bottom=395-21*i
    cx=(left+right)/2;cy=(top+bottom)/2
    b+=f'<ellipse cx="{cx}" cy="{cy}" rx="{(right-left)/2}" ry="{(bottom-top)/2}" fill="none" stroke="#9b6840" stroke-width="{3 if i==0 or i==5 else 1.8}"/>'
    b+=text(cx+15,top+5,100+10*i,16,fill='#734520')
b+=circle(205,242.5,4,'#172b3a')+text(191,229,'B',19)+circle(135,242.5,4,'#172b3a')+text(113,237,'A',19)
b+=text(94,300,'西側',17)+text(620,300,'東側',17)+symbol('school',270,363)+text(293,369,'S',19)+symbol('post',430,363)+text(453,369,'T',19)
b+=scale(40,456)+text(300,470,'等高線の数値：標高（m）／主曲線は10 mごと',16)
save('geo_contours.svg',b,'地図Aと等高線・縮尺バー',800,510)

b=text(25,30,'地図B（自作の地形図）',22)+rect(25,55,750,365,'#fbfcf8')+north(725,80)
# river and alluvial plain in west; increasing elevations east
b+=path('M 125 65 Q 210 180 135 295 Q 95 355 155 410','#2882a5',7)
for i in range(5):
    x=365+i*48
    b+=path(f'M {x+15} 65 Q {x-45} 215 {x+5} 410','#9b6840',3 if i==0 else 1.8)+text(x+5,94,50+i*10,16,fill='#734520')
for x,y in [(220,135),(270,135),(240,195),(290,250),(210,315)]:b+=symbol('rice',x,y,.72)
for x,y in [(412,170),(452,235),(510,290)]:b+=symbol('orchard',x,y,.9)
b+=text(220,90,'地区X',20)+text(425,130,'地区Y',20)
b+=symbol('school',285,345)+text(306,352,'S',19)+symbol('post',525,345)+text(546,352,'T',19)
b+=line(285,375,525,375,'#666',1,'4 4')+text(405,400,'原寸印刷で3 cm',16,'middle')
b+=scale(40,456)+text(310,458,'原寸の縮尺 1：25,000',17)+text(310,484,'画面では縮尺バーを使う。道路距離ではなく直線距離。',16)
save('geo_landuse.svg',b,'地図Bと土地利用・縮尺',800,520)

climates={
'A':([8,9,11,15,19,24,27,27,23,18,13,9],[90,75,65,45,25,10,5,10,35,80,110,100]),
'B':([26,26,26,27,27,27,27,27,27,27,26,26],[200,160,190,210,220,200,180,170,180,210,240,240]),
'C':([23,23,21,18,15,12,11,12,14,17,19,22],[100,90,100,110,120,130,120,100,90,90,100,110]),
'D':([-2,-1,3,9,15,19,23,24,20,13,7,1],[180,140,110,90,90,110,150,140,150,170,200,220]),
}
def climate_panel(x,y,name):
    temp,rain=climates[name];left=x+55;top=y+45;pw=270;ph=240;bottom=top+ph
    z=text(left+pw/2,y+18,f'地点{name}',21,'middle')+text(left-5,top-16,'℃',16)+text(left+pw+7,top-16,'mm',16)
    for v in range(0,301,50):
        yy=bottom-v/300*ph
        z+=line(left,yy,left+pw,yy,'#d6e0e7',1)+text(left+pw+8,yy+5,v,15)
    for v in range(-10,31,10):z+=text(left-10,bottom-(v+10)/40*ph+5,v,15,'end')
    points=[]
    for i,(t,r) in enumerate(zip(temp,rain)):
        xx=left+(i+.5)*pw/12
        z+=rect(xx-7,bottom-r/300*ph,14,r/300*ph,'#8bc1dd','none')+text(xx,bottom+23,i+1,16,'middle')
        points.append((xx,bottom-(t+10)/40*ph))
    z+=path('M '+' L '.join(f'{a} {b}' for a,b in points),'#a43636',3)+line(left,top,left,bottom)+line(left,bottom,left+pw,bottom)
    z+=text(left+pw+7,bottom+23,'月',15)+text(left,bottom+52,f'年降水量 {sum(rain):,} mm',17)
    return z
for pair,file in [('AB','geo_climate_ab.svg'),('CD','geo_climate_cd.svg')]:
    b=text(25,30,'月平均気温と月降水量（学習用データ・単年の12か月）',20)
    b+=climate_panel(10,55,pair[0])+climate_panel(405,55,pair[1])
    b+=line(95,440,135,440,'#a43636',3)+text(145,446,'気温：左軸',17)+rect(320,428,25,17,'#8bc1dd','none')+text(357,446,'降水量：右軸',17)
    save(file,b,'2地点の雨温図',820,475)

# Population pyramid; equal-width 5-year age classes; percentages of total population.
ages=['0–4','5–9','10–14','15–19','20–24','25–29','30–34','35–39','40–44','45–49','50–54','55–59','60–64','65–69','70–74','75–79','80–84','85以上']
pop={'A':[5,5,5,5,4,4,3.5,3.5,3.5,2.5,2.5,2,1.5,1,1,.5,.3,.2],'B':[2,2,2,2,2,2,3,3,3.5,3.5,3.5,3.5,3.5,3.5,3.5,3,2,2.5]}
assert sum(pop['A'])==sum(pop['B'])==50
b=text(25,30,'年齢別人口の割合（学習用・2025年を想定）',22)
for j,k in enumerate(['A','B']):
    cx=200+j*410;top=98;scalev=24
    b+=text(cx,65,f'地域{k}：総人口 '+('200万人' if k=='A' else '100万人'),20,'middle')+text(cx-110,89,'男性',17,'middle')+text(cx+110,89,'女性',17,'middle')
    for i,age in enumerate(ages):
        y=top+(17-i)*19;v=pop[k][i]
        b+=rect(cx-30-v*scalev,y,v*scalev,16,'#79add0','none')+rect(cx+30,y,v*scalev,16,'#d99680','none')+text(cx,y+13,age,15,'middle')
    for v in [0,2,4,6]:
        b+=text(cx-30-v*scalev,460,v,15,'middle')+text(cx+30+v*scalev,460,v,15,'middle')
    b+=text(cx,488,'横軸：総人口に占める割合（％）',16,'middle')
b+=text(25,520,'縦軸：年齢（歳）。最上段は85歳以上。各地域は男女合計100％。',16)
save('geo_population.svg',b,'2地域の人口ピラミッド',820,550)

def stacked(x,y,width,vals,labels,colors,show=True):
    z='';cur=x
    for v,lab,c in zip(vals,labels,colors):
        ww=width*v/100;z+=rect(cur,y,ww,50,c,'white')
        if show:z+=text(cur+ww/2,y+31,f'{lab} {v}%',16,'middle')
        cur+=ww
    return z
b=text(25,30,'工業製品出荷額の構成（学習用データ）',22)
b+=text(30,90,'2015年　総額200億円',20)+stacked(40,110,720,[40,30,30],['機械','食品','その他'],['#8dbcd2','#f3cf95','#d1dcda'])
b+=text(30,230,'2025年　総額300億円',20)+stacked(40,250,720,[30,40,30],['機械','食品','その他'],['#8dbcd2','#f3cf95','#d1dcda'])
b+=text(40,355,'帯全体の長さは各年の100％を表す。総額は年ごとに異なる。',18)
save('geo_share_total.svg',b,'工業出荷額の割合と総額',800,400)

# Schematic Japanese outline, oriented north up. Points are broad regions, not prefecture boundaries.
def japan(x=25,y=60):
    d='M 310 10 L 348 28 L 343 54 L 372 80 L 340 100 L 310 76 L 295 40 Z M 302 102 L 317 132 L 299 178 L 274 218 L 250 251 L 210 260 L 184 280 L 156 278 L 125 295 L 84 297 L 92 275 L 151 255 L 170 234 L 226 228 L 248 203 L 273 165 Z M 119 304 L 166 292 L 191 302 L 171 318 L 129 323 Z M 64 303 L 99 313 L 87 348 L 60 371 L 42 337 Z'
    return f'<g transform="translate({x} {y})">'+path(d,'#456477',2,'#f2f3df')+north(36,20)+text(25,404,'位置の模式図（県境は省略）',16)+'</g>'
b=text(25,30,'日本の4地域の位置と農業資料',22)+japan()
for x,y,l in [(353,117,'A'),(293,248,'B'),(231,306,'C'),(91,394,'D')]:b+=circle(x,y,15,'white')+text(x,y+6,l,18,'middle')
b+=labelbox(440,70,335,160,['資料1　位置の手がかり','A：北海道　B：東北地方','C：中部の内陸高地','D：九州南部'], '#f5f8fa')
b+=labelbox(440,255,335,185,['資料2　地域の特徴（模式）','① 冷涼・広い耕地・畑作と酪農','② 水田率が高い・米の生産','③ 標高が高い・夏の葉物野菜','④ 冬に温暖・冬春の野菜'], '#fff7e9')
save('geo_japan_farming.svg',b,'日本の位置図と農業資料',800,510)

b=text(25,30,'日本の3地域の位置と工業統計',22)+japan()
for x,y,l in [(299,293,'P'),(249,315,'Q'),(176,333,'R')]:b+=circle(x,y,15,'white')+text(x,y+6,l,18,'middle')
b+=labelbox(435,65,340,115,['資料1　位置の手がかり','P：東京湾岸　Q：愛知県周辺','R：瀬戸内海沿岸'])
b+=text(440,220,'資料2　出荷額の構成（％）',18)+text(440,247,'学習用データ・2025年を想定',16)
for i,(k,vals) in enumerate([('ア',[35,10,30,25]),('イ',[65,10,10,15]),('ウ',[20,40,25,15])]):
    yy=280+i*60;b+=text(433,yy+29,k,18)+stacked(463,yy,295,vals,['','','',''],['#8dbcd2','#f3cf95','#a9cda2','#d1dcda'],False)
b+=text(435,481,'凡例：青＝機械　黄＝金属',16)+text(435,507,'緑＝化学　灰＝その他',16)
save('geo_japan_industry.svg',b,'日本の位置図と工業統計',800,540)

b=text(25,30,'各地域が使う標準時子午線',22)+text(25,65,'サマータイムは考えない。都市そのものの経度ではない。',18)
positions=[(90+((lon+120)/255)*600,label,key) for lon,label,key in [(-120,'西経120°','L'),(-75,'西経75°','N'),(0,'0°','G'),(135,'東経135°','J')]]
b+=arrow(50,155,755,155)+text(675,137,'東へ',18)
for x,lon,k in positions:b+=line(x,110,x,235,'#477990',2)+text(x,100,lon,18,'middle')+text(x,270,k,23,'middle')
b+=labelbox(30,310,740,110,['日本J：1月1日 午前9時','飛行機：Jを1月1日 午前10時に出発し、12時間後にLへ到着。','地球は24時間で360°回転する。1時間に相当する経度差を考える。'])
save('geo_timezones.svg',b,'標準時子午線の位置図',800,450)

b=text(25,30,'2つの産地の気温と出荷時期（学習用データ）',22)
b+=labelbox(30,65,350,125,['産地A：太平洋側の沿岸平野','標高20m／温室で栽培','産地B：内陸の高原','標高1,200m'])
tempA=[8,9,12,16,20,24,28,28,25,20,15,10];tempB=[-5,-4,0,6,11,15,19,19,14,8,3,-2]
left=80;top=215;bottom=410;pw=650;ph=195
for v in range(-10,31,10):
    yy=bottom-(v+10)/40*ph;b+=line(left,yy,left+pw,yy,'#ddd',1)+text(left-12,yy+5,v,16,'end')
for vals,c in [(tempA,'#b54430'),(tempB,'#287998')]:
    pts=[(left+(i+.5)*pw/12,bottom-(v+10)/40*ph) for i,v in enumerate(vals)]
    b+=path('M '+' L '.join(f'{x} {y}' for x,y in pts),c,3)
for i in range(12):b+=text(left+(i+.5)*pw/12,bottom+25,i+1,16,'middle')
b+=text(33,207,'気温（℃）',16)+text(746,435,'月',16)
b+=line(450,86,485,86,'#b54430',3)+text(495,92,'Aの月平均気温',17)+line(450,124,485,124,'#287998',3)+text(495,130,'Bの月平均気温',17)
b+=text(40,488,'出荷：Aのピーマンは1〜4月、Bのレタスは7〜9月に多い。',18)
save('geo_climate_farming.svg',b,'2産地の気温と出荷資料',800,525)

b=text(25,30,'体育館の利用希望と3つの案',22)
b+=labelbox(30,60,740,80,['同じ放課後の体育館を、バスケ部30人・バレー部20人が希望。','体育館は半面ずつ同時利用できる。毎週の利用枠は計10枠。'])
for i,rows in enumerate([
['案A','バスケ部が10枠すべて使用','バレー部の意見を聞かず決定'],
['案B','希望を聞き、半面ずつ10枠共有','待ち時間と使わない面を減らす'],
['案C','部長2人だけでくじを引く','当選した部だけが10枠を独占']]):
    b+=labelbox(30,165+i*95,740,80,rows,'#f4f7fa' if i!=1 else '#fdf4e6')
b+=text(30,480,'合意に向けて、設備の安全性・競技ごとの必要面積も確認する。',17)
save('geo_consensus.svg',b,'利用希望と配分案の比較',800,510)

b=text(25,30,'ある市の人口と情報利用（学習用統計）',22)
b+=text(30,70,'資料A　年齢3区分の構成（％）',19)
b+=text(30,110,'2005年：人口10万人',18)+stacked(40,125,720,[20,65,15],['','',''],['#99c7dc','#e5c083','#b3cba9'])
b+=text(30,210,'2025年：人口8万人',18)+stacked(40,225,720,[10,55,35],['','',''],['#99c7dc','#e5c083','#b3cba9'])
b+=text(40,305,'凡例：青＝0〜14歳　黄＝15〜64歳　緑＝65歳以上',17)
b+=labelbox(30,325,740,125,['資料B　市の広報の受け取り方（2025年）','インターネットを使う：70％／使わない：30％','市は印刷費を減らすため、広報をウェブ配信だけにする案を検討。','ある住民は「端末がない人にも必要な情報を届けてほしい」と発言。'])
save('geo_social_change.svg',b,'年齢構成と情報利用の資料',800,480)

assert sum(climates['A'][1])==650
assert sum(climates['B'][1])==2400
assert 200*.4==80 and 300*.3==90 and 300*.4-200*.3==60
assert (135+75)/15==14 and (135+120)/15==17
assert 10*.15==1.5 and 8*.35==2.8
print(f'Generated {len(list(OUT.glob("geo_*.svg")))} SVG diagrams in {OUT}')
