from pathlib import Path
from hashlib import sha256
from lxml import etree as ET

from diagram_primitives import Drawing, BLUE, GRAY, LIGHT, INK


ROOT = Path(r'C:\Users\wangjianing\Desktop\SRDP')
DOCUMENT = ROOT / '申报书与材料/申报书beta1.3.3.docx'
REFERENCE = ROOT / '申报书与材料/示意图/示意图1.png'
before = {p: sha256(p.read_bytes()).hexdigest() for p in (DOCUMENT, REFERENCE)}

d = Drawing('图1_交互笔结构示意图_笔身检测版',1600,1030)
d.text(80,65,'内部结构',size=34,anchor='start')

# Fixed casing with a uniform front sensing section and a short protected tip.
d.polygon([(80,230),(1260,230),(1300,274),(1300,292),
           (1248,254),(80,254)],fill='#f4f4f4')
for x in range(100,1220,26):
    d.line(x,254,x+24,230,color=GRAY,width=1)
d.polyline([(80,230),(60,250),(60,370),(80,390),(1260,390),
            (1300,346),(1300,328)],width=3)
d.line(80,254,80,368,color=GRAY,width=1)
d.line(55,310,1420,310,color=GRAY,width=1.4,dash=[18,7,3,7])

for x,w,label in [(115,265,'电池与电源'),(420,220,'ESP32-S3'),(680,135,'IMU')]:
    d.rect(x,278,w,62,fill=LIGHT,radius=5,stroke=2)
    d.text(x+w/2,309,label,size=29)

# Grip and button placement are behind the exposed sensing section.
d.rect(900,208,80,22,fill=LIGHT,radius=5,stroke=2)
d.text(900,150,'笔杆按键',size=29)
d.leader([(900,174),(940,206)])
d.text(1165,80,'笔身前端检测段',size=31,color=BLUE)
d.text(1165,121,'与笔壳一体',size=27,color=BLUE)
d.leader([(1165,144),(1180,202),(1180,226)])
d.text(1410,95,'可压动',size=28)
d.text(1410,133,'圆头笔尖',size=28)
d.leader([(1405,157),(1384,282)])

# The switch is fixed; the axial tip rod moves inside the casing.
d.rect(1000,278,90,58,fill=LIGHT,radius=4)
d.rect(1090,302,22,16,fill='#dddddd',stroke=1.8)
d.rect(1127,301,241,18,fill='#fafafa',stroke=2.5)
d.circle(1384,310,16,fill=LIGHT,width=3)
d.line(1140,277,1140,301,width=3)
d.line(1140,319,1140,343,width=3)
d.line(1240,278,1240,342,width=4)
spring=[(1144,310)]
for i in range(12):
    spring.append((1151+i*7.4,291 if i%2==0 else 329))
spring.append((1236,310))
d.polyline(spring,width=2)
d.text(1010,452,'微动开关',size=29)
d.leader([(1010,427),(1045,340)])
d.text(1250,452,'复位弹簧',size=29)
d.leader([(1250,427),(1200,336)])
d.arrow(1112,267,1127,267,color=BLUE,width=1.6,both=True,head=5)
d.text(995,535,'压动行程约 1 mm',size=27,color=BLUE)
d.leader([(1070,518),(1118,390),(1118,278)])

# The radar ray terminates on the lower surface of the body, not on the tip rod.
d.rect(1400,210,75,540,fill='#f4f4f4',stroke=2)
d.line(1400,210,1400,750,width=4)
d.text(1440,460,'墙面',size=31,angle=90)
d.line(1180,175,1180,650,color=BLUE,width=1.8,dash=[18,7,3,7])
d.arrow(1180,650,1180,390,color=BLUE,width=3,head=13)
d.circle(1180,390,6,fill=BLUE,color=BLUE,width=1)
d.text(905,617,'雷达扫描面',size=28,color=BLUE)
d.text(905,657,'与墙面平行',size=26,color=BLUE)
d.leader([(1068,618),(1180,596)])
d.dimension(1180,563,1400,563,'h',1290,539)
d.rect(1110,650,150,100,fill=LIGHT,stroke=2.5)
d.rect(1260,650,140,100,fill='#fafafa',stroke=2.5)
d.text(1185,697,'激光雷达',size=27)
d.text(1330,697,'安装支架',size=25)

# Exterior view mirrors the user's C/B/A and L/R button arrangement.
d.text(80,805,'外观与按键布置',size=34,anchor='start')
d.polygon([(80,850),(1255,850),(1300,878),(1300,922),
           (1255,950),(80,950),(60,935),(60,865)],fill='white',width=3)
d.rect(1300,892,68,16,fill='#fafafa',stroke=2)
d.circle(1384,900,16,fill=LIGHT,width=3)
for x,label in [(720,'C'),(810,'B'),(900,'A')]:
    d.circle(x,900,30,fill=LIGHT,width=2.5)
    d.text(x,900,label,size=28)
for y,label in [(876,'L'),(925,'R')]:
    d.circle(990,y,20,fill=LIGHT,width=2)
    d.text(990,y,label,size=24)
d.text(830,990,'握持及按键区',size=27,color=GRAY)
d.leader([(830,968),(830,950)])
d.text(1175,805,'前端检测区',size=28,color=BLUE)
d.leader([(1175,827),(1175,847)])
d.line(1180,850,1180,950,color=BLUE,width=1.8,dash=[15,6,3,6])
d.line(1330,850,1448,850,color=GRAY,width=1.2)
d.line(1330,950,1448,950,color=GRAY,width=1.2)
d.dimension(1435,850,1435,950,'',1435,900)
d.text(1500,898,'宽约 20 mm',size=26,angle=90)

svg_path = Path(d.finish())
ET.parse(str(svg_path))
assert '套环' not in svg_path.read_text(encoding='utf-8')
for path, digest in before.items():
    assert sha256(path.read_bytes()).hexdigest()==digest
print(svg_path)
print(svg_path.with_suffix('.png'))
