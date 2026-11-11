from pathlib import Path
from hashlib import sha256
from html import escape
import json
import math

import pypdfium2 as pdfium
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import toColor as HexColor


ROOT = Path(r'C:\Users\wangjianing\Desktop\SRDP')
OUT = ROOT / '申报书与材料/示意图'
WORK = ROOT / 'work/figure_previews'
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT / '申报书与材料/申报书beta1.3.2.docx'
SOURCE_HASH = sha256(SOURCE.read_bytes()).hexdigest()
pdfmetrics.registerFont(TTFont('DiagramChinese', r'C:\Windows\Fonts\simhei.ttf'))
INK = '#222222'
BLUE = '#315f80'
GRAY = '#727b83'
LIGHT = '#f1f4f6'
SCALE = 72 / 254


class Drawing:
    def __init__(self, name, width, height):
        self.name, self.width, self.height = name, width, height
        self.pdf_path = WORK / f'{name}.pdf'
        self.pdf = canvas.Canvas(str(self.pdf_path), pagesize=(width*SCALE, height*SCALE))
        self.pdf.setTitle(name)
        self.pdf.scale(SCALE, SCALE)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width/100:g}cm" height="{height/100:g}cm" viewBox="0 0 {width} {height}">',
                    '<rect width="100%" height="100%" fill="white"/>']

    def line(self, x1, y1, x2, y2, color=INK, width=2.5, dash=None):
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setLineWidth(width)
        self.pdf.setDash(dash or [])
        self.pdf.line(x1, self.height-y1, x2, self.height-y2)
        self.pdf.setDash([])
        style = f' stroke-dasharray="{" ".join(map(str,dash))}"' if dash else ''
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{style}/>')

    def polyline(self, points, color=INK, width=2.5, dash=None):
        for a, b in zip(points, points[1:]):
            self.line(*a, *b, color=color, width=width, dash=dash)

    def polygon(self, points, fill='white', color=INK, width=2.5):
        path = self.pdf.beginPath()
        path.moveTo(points[0][0], self.height-points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, self.height-y)
        path.close()
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setFillColor(HexColor(fill))
        self.pdf.setLineWidth(width)
        self.pdf.drawPath(path, stroke=1, fill=1)
        coords = ' '.join(f'{x},{y}' for x,y in points)
        self.svg.append(f'<polygon points="{coords}" fill="{fill}" stroke="{color}" stroke-width="{width}"/>')

    def rect(self, x, y, width, height, fill='white', color=INK, radius=0, stroke=2.5):
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setFillColor(HexColor(fill))
        self.pdf.setLineWidth(stroke)
        self.pdf.roundRect(x, self.height-y-height, width, height, radius, stroke=1, fill=1)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{color}" stroke-width="{stroke}"/>')

    def circle(self, x, y, radius, fill='white', color=INK, width=2.5):
        self.pdf.setStrokeColor(HexColor(color))
        self.pdf.setFillColor(HexColor(fill))
        self.pdf.setLineWidth(width)
        self.pdf.circle(x, self.height-y, radius, stroke=1, fill=1)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{color}" stroke-width="{width}"/>')

    def text(self, x, y, value, size=28, color=INK, anchor='middle', angle=0):
        self.pdf.saveState()
        self.pdf.translate(x, self.height-y)
        self.pdf.rotate(-angle)
        self.pdf.setFont('DiagramChinese', size)
        self.pdf.setFillColor(HexColor(color))
        offset = {'middle': -pdfmetrics.stringWidth(value,'DiagramChinese',size)/2,
                  'start': 0, 'end': -pdfmetrics.stringWidth(value,'DiagramChinese',size)}[anchor]
        self.pdf.drawString(offset, -size*0.34, value)
        self.pdf.restoreState()
        transform = f' transform="rotate({angle} {x} {y})"' if angle else ''
        self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="SimHei, Microsoft YaHei, sans-serif" font-size="{size}" text-anchor="{anchor}" dominant-baseline="central"{transform}>{escape(value)}</text>')

    def arrow(self, x1, y1, x2, y2, color=INK, width=2.5, both=False, head=11):
        self.line(x1,y1,x2,y2,color,width)
        self.arrowhead(x1,y1,x2,y2,color,head)
        if both:
            self.arrowhead(x2,y2,x1,y1,color,head)

    def arrowhead(self,x1,y1,x2,y2,color=INK,head=11):
        angle = math.atan2(y2-y1,x2-x1)
        points = [(x2,y2),
                  (x2-head*math.cos(angle)+head*.4*math.sin(angle), y2-head*math.sin(angle)-head*.4*math.cos(angle)),
                  (x2-head*math.cos(angle)-head*.4*math.sin(angle), y2-head*math.sin(angle)+head*.4*math.cos(angle))]
        self.polygon(points,fill=color,color=color,width=1)

    def leader(self, points):
        self.polyline(points,color=GRAY,width=1.8)

    def dimension(self, x1,y1,x2,y2,label,tx,ty):
        self.arrow(x1,y1,x2,y2,color=BLUE,width=2,both=True,head=9)
        self.text(tx,ty,label,size=30,color=BLUE)

    def finish(self):
        self.svg.append('</svg>')
        (OUT / f'{self.name}.svg').write_text('\n'.join(self.svg),encoding='utf-8')
        self.pdf.showPage()
        self.pdf.save()
        pdf = pdfium.PdfDocument(str(self.pdf_path))
        image = pdf[0].render(scale=300/72).to_pil().convert('RGB')
        image.save(OUT / f'{self.name}.png',dpi=(300,300))
        return str(OUT / f'{self.name}.svg')


def figure_one():
    d=Drawing('图1_交互笔结构示意图',1500,700)
    d.line(55,355,1455,355,color=GRAY,width=1.6,dash=[20,7,3,7])
    # Upper shell section and open lower outline.
    d.polygon([(80,265),(1040,265),(1120,325),(1110,340),(1030,290),(80,290)],fill='#f4f4f4')
    for x in range(100,1020,25):
        d.line(x,290,x+25,265,color=GRAY,width=1)
    d.polyline([(80,290),(80,430),(1040,430),(1120,385),(1120,370)])
    d.line(80,265,80,290)
    d.rect(110,315,185,62,fill=LIGHT,radius=7)
    d.text(202,346,'ESP32-S3',size=28)
    d.rect(130,391,140,26,radius=3)
    d.text(200,402,'电池',size=23)
    d.rect(365,245,85,21,fill=LIGHT,radius=5)
    d.text(407,190,'模式键',size=29)
    d.leader([(407,213),(407,243)])
    d.text(205,480,'笔尾',size=28)
    d.leader([(205,458),(205,430)])
    # Switch body and plunger. The left-moving rod compresses the spring.
    d.rect(445,328,80,55,fill=LIGHT,radius=4)
    d.rect(525,347,20,16,fill='#dddddd')
    d.rect(560,344,818,22,fill='#fafafa')
    d.line(573,315,573,344)
    d.line(573,366,573,399)
    d.line(716,318,716,394,width=5)
    coil=[(578,355)]
    for i in range(17):
        coil.append((585+i*7.3,334 if i%2==0 else 376))
    coil.append((710,355))
    d.polyline(coil,width=2)
    d.text(660,190,'复位弹簧',size=29)
    d.leader([(660,212),(660,315)])
    d.text(920,190,'笔尖杆',size=29)
    d.leader([(920,212),(920,335)])
    d.text(465,480,'微动开关，受压触发',size=27)
    d.leader([(490,456),(490,388)])
    d.arrow(543,310,573,310,both=True,head=7,width=1.8,color=BLUE)
    d.text(485,110,'压动行程约 1 mm',size=27,color=BLUE)
    d.leader([(500,132),(540,220),(553,300)])
    # Detection sleeve is outside the shell, on the moving rod.
    d.rect(1170,315,70,80,fill='#e4edf3',color=BLUE,stroke=3)
    d.line(1181,315,1181,395,color=BLUE,width=1)
    d.line(1229,315,1229,395,color=BLUE,width=1)
    d.circle(1385,355,15,fill=LIGHT,width=3)
    d.text(1160,75,'可拆卸套环',size=29)
    d.text(1160,116,'外径 D 可替换',size=27)
    d.leader([(1195,140),(1205,195),(1205,308)])
    d.text(1360,190,'可更换圆头笔尖',size=27)
    d.leader([(1360,214),(1385,330)])
    d.line(1205,175,1205,648,color=BLUE,width=2,dash=[18,7,3,7])
    d.line(1400,250,1400,650,width=4)
    d.text(1440,280,'板面',size=27,angle=90)
    d.text(1070,475,'雷达扫描面',size=27,color=BLUE)
    d.text(1070,511,'与板面平行',size=25,color=BLUE)
    d.leader([(1170,475),(1205,445)])
    d.line(1245,315,1303,315,color=GRAY,width=1)
    d.line(1245,395,1303,395,color=GRAY,width=1)
    d.dimension(1290,315,1290,395,'D',1322,355)
    d.dimension(1205,564,1400,564,'L',1302,541)
    d.dimension(1205,626,1400,626,'h',1302,603)
    return d.finish()


def figure_two():
    d=Drawing('图2_系统连接与数据处理流程图',1550,800)
    d.rect(55,65,280,105,fill=LIGHT,radius=8)
    d.text(195,117,'二维激光雷达',size=32)
    d.rect(425,55,310,125,fill=LIGHT,radius=8)
    d.text(580,91,'交互笔',size=31)
    d.text(580,139,'笔尖开关 / 按键 / IMU',size=24)
    d.rect(855,80,230,80,fill=LIGHT,radius=8)
    d.text(970,119,'ESP32-S3',size=31)
    d.arrow(735,120,855,120)
    d.text(795,91,'采集',size=24)
    d.rect(25,270,1300,215,color=BLUE,radius=8)
    d.text(500,301,'电脑处理程序',size=29,color=BLUE)
    labels=['扫描数据接入','有效区域筛选','笔端检测','目标跟踪','笔尖位置估计','投影坐标映射','接触事件融合','界面响应']
    xs=[44+i*160 for i in range(8)]
    for i,(x,label) in enumerate(zip(xs,labels)):
        d.rect(x,355,144,72,fill='white',stroke=2)
        d.text(x+72,391,label,size=22)
        if i<7:
            d.arrow(x+144,391,x+160,391,head=7,width=2)
    d.arrow(195,170,195,241)
    d.polyline([(195,241),(116,241),(116,355)])
    d.arrowhead(116,300,116,355)
    d.text(210,211,'以太网 / 厂家 SDK',size=26,anchor='start')
    d.polyline([(970,160),(970,241),(1076,241),(1076,355)])
    d.arrowhead(1076,310,1076,355)
    d.text(1115,211,'USB 串口',size=26)
    # Display output stays a forward chain to the right of the processing path.
    d.rect(1365,355,150,72,fill=LIGHT,radius=6)
    d.text(1440,391,'投影仪',size=29)
    d.arrow(1308,391,1365,391,head=9)
    d.rect(1330,75,190,115,fill='white',stroke=3)
    d.text(1425,132,'投影画面',size=29)
    d.arrow(1440,355,1440,190)
    d.text(1468,270,'显示',size=24,angle=90)
    # Logged events share a host timeline. Video measures the physical-to-display interval.
    d.arrow(70,612,1320,612,color=GRAY,width=2,head=9)
    for x in [116,1076,1236]:
        d.line(x,427,x,612,color=GRAY,width=1.6,dash=[7,7])
        d.circle(x,612,5,fill=BLUE,color=BLUE,width=1)
    d.rect(106,507,148,38,color='white',stroke=0)
    d.rect(925,507,171,38,color='white',stroke=0)
    d.rect(1162,547,176,38,color='white',stroke=0)
    d.text(180,526,'扫描时间戳',size=25)
    d.text(1010,526,'串口接收时间',size=24)
    d.text(1250,566,'画面刷新时间',size=24)
    d.text(670,652,'电脑统一时间轴（设备时间经对齐）',size=25,color=GRAY)
    d.polyline([(116,680),(116,696),(1236,696),(1236,680)],color=BLUE,width=2)
    d.text(676,741,'端到端延迟（接触或运动至画面变化，录像测量）',size=28,color=BLUE)
    return d.finish()


def figure_three():
    d=Drawing('图3_扫描面与笔尖偏移几何关系',900,750)
    sx,bx,ay,by=290,680,150,540
    d.line(sx,105,sx,620,color=BLUE,width=3,dash=[18,7,3,7])
    d.line(bx,105,bx,620,width=5)
    d.text(245,34,'雷达扫描面',size=30,color=BLUE)
    d.text(680,34,'书写面（板面）',size=30)
    d.dimension(sx,88,bx,88,'h',485,63)
    d.line(150,by,820,by,color=GRAY,width=2,dash=[10,7])
    d.text(205,581,'法线方向',size=27,color=GRAY)
    d.line(sx,ay,bx,ay,color=GRAY,width=1.8,dash=[8,7])
    d.line(230,90,bx,by,width=5)
    d.circle(sx,ay,7,fill=BLUE,color=BLUE)
    d.circle(bx,by,7,fill=INK)
    d.text(137,205,'A  检测位置',size=29)
    d.leader([(223,205),(272,164)])
    d.text(633,593,'B  笔尖落点',size=29)
    d.leader([(641,570),(674,546)])
    d.dimension(775,ay,775,by,'d',810,345)
    d.line(bx+10,ay,788,ay,color=GRAY,width=1.5)
    d.line(bx+10,by,788,by,color=GRAY,width=1.5)
    arc=[]
    for i in range(31):
        angle=math.radians(180+i*45/30)
        arc.append((bx+105*math.cos(angle),by+105*math.sin(angle)))
    d.polyline(arc,color=BLUE,width=2)
    d.text(548,484,'θ',size=34,color=BLUE)
    d.arrow(522,382,425,285,color=BLUE,width=3,head=13)
    d.text(455,430,'u（笔尖指向笔尾）',size=26,color=BLUE)
    d.text(510,650,'d = h·tan θ',size=36,color=BLUE)
    d.text(450,711,'h = 10 mm，θ = 45° 时 d ≈ 10 mm',size=28)
    return d.finish()


def figure_four():
    d=Drawing('图4_软件界面与模式切换流程',1550,800)
    d.text(380,45,'界面',size=34)
    d.text(1150,45,'状态切换',size=34)
    d.line(760,30,760,765,color=GRAY,width=2,dash=[10,8])
    d.rect(35,100,690,630,fill='white',radius=10)
    d.line(35,205,725,205)
    buttons=[(55,110,'操作工具'),(175,110,'书写工具'),(295,80,'清屏'),(385,80,'保存'),(475,230,'模式  近程')]
    for x,width,label in buttons:
        d.rect(x,130,width,50,fill=LIGHT,radius=5,stroke=1.8)
        d.text(x+width/2,155,label,size=25)
    d.rect(60,235,445,465,stroke=2)
    d.text(282,271,'画布',size=29,color=GRAY)
    d.polyline([(105,430),(160,375),(225,455),(280,360),(340,426),(413,340)],color=BLUE,width=5)
    d.circle(194,570,55,color=BLUE,width=4)
    d.rect(530,235,170,465,fill='#fafafa',stroke=2)
    d.text(615,272,'对象 / 按钮',size=25)
    for y,label in [(320,'对象 1'),(388,'对象 2'),(456,'测试按钮')]:
        d.rect(547,y,136,48,fill='white',radius=4,stroke=1.5)
        d.text(615,y+24,label,size=25)
    d.rect(1010,90,260,64,fill=LIGHT,radius=16)
    d.text(1140,122,'待机',size=30)
    d.arrow(1140,154,1140,200)
    d.rect(820,200,680,220,fill='white',radius=16,color=BLUE)
    d.text(1160,236,'近程（主要任务）',size=31,color=BLUE)
    for y,label in [(284,'位置有效未接触 → 更新光标'),(332,'接触 → 书写 / 按下'),(380,'抬笔 → 结束笔画')]:
        d.text(852,y,label,size=28,anchor='start')
    d.rect(820,525,680,225,fill=LIGHT,radius=16)
    d.text(1160,559,'远程（后期拓展）',size=31)
    for y,label in [(603,'偏转笔杆 → 移动光标'),(644,'固定键 → 按一次锁定 / 再按恢复'),(685,'复位键 → 归中 / 松开定零'),(726,'点击键 → 点击 / 拖动')]:
        d.text(852,y,label,size=26,anchor='start')
    d.arrow(1170,420,1170,525,color=BLUE,width=2.5)
    d.text(1330,455,'切换至远程',size=25,color=BLUE)
    d.text(1330,492,'结束当前操作，释放按下状态',size=21,color=GRAY)
    d.polyline([(820,636),(795,636),(795,310),(820,310)],color=BLUE,width=2.5)
    d.arrowhead(795,310,820,310,color=BLUE,head=9)
    d.text(980,455,'回到近程',size=25,color=BLUE)
    d.text(980,492,'结束当前操作，释放按下状态',size=21,color=GRAY)
    return d.finish()


files=[figure_one(),figure_two(),figure_three(),figure_four()]
assert sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
(WORK/'manifest.json').write_text(json.dumps({'source':str(SOURCE),'source_sha256':SOURCE_HASH,'svg_files':files},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':files,'document_unchanged':True},ensure_ascii=False))
