#!/usr/bin/env python3
"""Additional original topographic teaching map for mock 1, question 2."""
from pathlib import Path
import runpy,math
g=runpy.run_path(str(Path(__file__).with_name('build_geo_visuals.py')))
text,line,rect,path,circle,symbol,north,save=[g[k] for k in ['text','line','rect','path','circle','symbol','north','save']]
b=text(25,30,'資料2　地形図（学習用の模式図）',22)+rect(25,55,750,490,'#fbfcf8')+north(725,85)
# A river crosses a flat valley. Rice fields occur along both banks.
b+=path('M 30 200 Q 165 170 305 205 Q 415 240 545 195 Q 665 160 765 185','#2882a5',7)
for x,y in [(78,147),(112,143),(380,130),(420,130),(75,250),(111,250),(175,265),(220,267)]:b+=symbol('rice',x,y,.7)
b+=text(100,325,'地区X',19)
# City hall lies northwest of station: dx=240, dy=180 => 300 SVG units = 1 km.
b+=symbol('city',160,110)+text(183,115,'市役所',18)
# The station is shown as a station building on a railway, not a town symbol.
b+=line(35,285,755,320,'#333',3)
for i in range(24):
    x=45+i*30;y=285+(x-35)*35/720
    b+=line(x-1,y-6,x+1,y+6,'#333',1.4)
b+=rect(379,281,42,18,'white','#172b3a',2)+text(400,271,'駅',19,'middle')
b+=line(160,110,400,290,'#687983',1.4,'5 4')+text(244,163,'原寸で4 cm',17)
# Southern hill: contours have short horizontal separation => steep slope.
for i in range(6):
    rx=168-12*i;ry=100-12*i;cx=575;cy=430
    b+=f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#9b6840" stroke-width="{3 if i in (0,5) else 1.8}"/>'
    angle=math.radians(-140 if i%2==0 else -40)
    xx=cx+rx*math.cos(angle);yy=cy+ry*math.sin(angle)
    b+=rect(xx-18,yy-12,36,22,'#fbfcf8','none')+text(xx,yy+5,50+i*10,16,'middle',fill='#734520')
for x,y in [(535,426),(606,443),(570,450)]:b+=symbol('orchard',x,y,.75)
b+=text(578,416,'地区Y',19)
# Scale matches all map coordinates. Four original cm correspond to 300 svg units.
b+=line(45,580,195,580)+line(45,574,45,586)+line(120,574,120,586)+line(195,574,195,586)
b+=text(45,607,'0',16,'middle')+text(120,607,'250',16,'middle')+text(195,607,'500 m',16,'middle')
b+=text(275,574,'原寸の縮尺 1：25,000／等高線は10 mごと',17)
b+=text(275,601,'地区Xは川沿いの平地、地区Yは南の丘。',17)
b+=text(25,640,'画面では縮尺バーを使う。点線は駅と市役所の直線を示す。',16)
assert math.hypot(400-160,290-110)==300
assert 300/150*500==1000
save('geo_mock1_map.svg',b,'模擬テスト1の地形図資料',800,665)
print('PASS: station–city hall distance = 1,000 m, city hall northwest of station')
