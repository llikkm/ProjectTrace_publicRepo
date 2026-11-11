from pathlib import Path
from hashlib import sha256
from lxml import etree as ET

from diagram_primitives import Drawing, BLUE, GRAY, LIGHT


ROOT=Path(r'C:\Users\wangjianing\Desktop\SRDP')
DOCUMENT=ROOT/'申报书与材料/申报书beta1.3.3.docx'
document_hash=sha256(DOCUMENT.read_bytes()).hexdigest()
d=Drawing('图4_桌面浮动批注界面与模式切换流程',1550,800)
d.text(380,45,'桌面批注界面',size=34)
d.text(1150,45,'状态切换',size=34)
d.line(760,30,760,765,color=GRAY,width=2,dash=[10,8])

# Desktop and an underlying application remain visible through the annotation layer.
d.rect(35,100,690,445,fill='#fafbfc',radius=10)
d.line(35,146,725,146,color=GRAY,width=1.6)
d.text(68,123,'桌面 / 当前应用',size=26,anchor='start')
for x in [657,680,703]:
    d.circle(x,123,5,fill=GRAY,color=GRAY,width=1)
d.rect(90,172,580,290,fill='white',radius=5,stroke=1.8)
d.line(90,216,670,216,color=GRAY,width=1.4)
d.text(115,194,'正在运行的软件',size=25,anchor='start',color=GRAY)
d.text(358,256,'示例内容',size=31)
for y,end in [(300,592),(338,540),(376,585)]:
    d.line(145,y,end,y,color='#c6cdd3',width=4)
d.circle(357,257,78,fill=None,color=BLUE,width=4)
d.polyline([(142,348),(195,315),(250,352),(285,329)],color=BLUE,width=5)
d.arrow(565,368,486,303,color=BLUE,width=4,head=15)

# A movable palette is shown over the application, with a selected pen tool.
d.rect(60,418,650,105,fill='#dce2e7',color='#dce2e7',radius=10,stroke=1)
d.rect(55,412,650,105,fill='white',color=BLUE,radius=10,stroke=2.8)
for i in range(3):
    d.line(64,435+i*9,70,435+i*9,color=GRAY,width=2)
tools=['操作','画笔','橡皮','撤销','清屏','保存','白板']
for i,label in enumerate(tools):
    x=79+i*88
    selected=label=='画笔'
    d.rect(x,427,78,43,fill='#e4edf3' if selected else LIGHT,
           color=BLUE if selected else GRAY,radius=5,stroke=1.5)
    d.text(x+39,448,label,size=26,color=BLUE if selected else '#222222')
d.text(87,494,'颜色',size=23,anchor='start',color=GRAY)
for x,color in [(169,BLUE),(207,'#b75149'),(245,'#222222')]:
    d.circle(x,494,9,fill=color,color=color,width=1)
d.text(288,494,'粗细',size=23,anchor='start',color=GRAY)
d.line(350,494,395,494,color=BLUE,width=3)
d.line(415,494,460,494,color=BLUE,width=6)
d.text(660,494,'收起',size=23,color=GRAY)

d.text(177,575,'浮动工具条',size=28,color=BLUE)
d.leader([(177,553),(177,522)])
d.text(528,575,'透明批注层',size=28,color=BLUE)
d.leader([(650,555),(735,555),(735,350),(625,320)])

# Separate whiteboard view opened from the same palette.
d.rect(65,627,455,132,fill='white',radius=7,stroke=2)
d.text(89,650,'独立白板',size=25,anchor='start',color=GRAY)
d.polyline([(107,716),(160,688),(214,724),(268,685),(312,712)],color=BLUE,width=4)
d.circle(423,699,32,color=BLUE,width=3)
d.polyline([(646,470),(718,470),(718,696),(520,696)],color=BLUE,width=2)
d.arrowhead(572,696,520,696,color=BLUE,head=10)
d.text(614,735,'打开白板',size=25,color=BLUE)

# Retain the existing hardware-mode flow and its labels.
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

svg=Path(d.finish())
ET.parse(str(svg))
assert sha256(DOCUMENT.read_bytes()).hexdigest()==document_hash
print(svg)
print(svg.with_suffix('.png'))
