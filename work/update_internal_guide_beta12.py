from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json

from lxml import etree as ET


ROOT=Path(r'C:\Users\wangjianing\Desktop\SRDP')
SOURCE=ROOT/'申报书与材料/交互笔项目_内部实现步骤beta1.1.docx'
PROPOSAL=ROOT/'申报书与材料/申报书beta1.3.3.1.docx'
OUTPUT=ROOT/'申报书与材料/交互笔项目_内部实现步骤beta1.2.docx'
README=ROOT/'README.md'
hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in (SOURCE,PROPOSAL,README)}
with ZipFile(SOURCE) as archive:
    entries=archive.infolist()
    parts={entry.filename:archive.read(entry.filename) for entry in entries}
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W}


def q(name):
    return f'{{{W}}}{name}'


document=ET.fromstring(parts['word/document.xml'])
paragraphs=document.xpath('//w:body//w:p',namespaces=NS)
updates={int(k):v for k,v in json.loads((ROOT/'work/guide_beta12_updates.json').read_text(encoding='utf-8')).items()}
struck={i for i,p in enumerate(paragraphs) if p.xpath('.//w:strike',namespaces=NS)}
assert struck.issubset(updates), struck-set(updates)


def replace_text(paragraph,value):
    sample=paragraph.find(q('r'))
    properties=deepcopy(sample.find(q('rPr'))) if sample is not None and sample.find(q('rPr')) is not None else ET.Element(q('rPr'))
    for child in list(paragraph):
        if child.tag!=q('pPr'):
            paragraph.remove(child)
    for i,line in enumerate(value.split('\n')):
        run=ET.SubElement(paragraph,q('r'))
        run.append(deepcopy(properties))
        if i:
            ET.SubElement(run,q('br'))
        text=ET.SubElement(run,q('t'))
        text.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
        text.text=line


for index,value in updates.items():
    replace_text(paragraphs[index],value)


def insert_after(index,items):
    anchor=paragraphs[index]
    parent=anchor.getparent()
    position=parent.index(anchor)+1
    for kind,value in items:
        template=paragraphs[45] if kind=='heading' else paragraphs[46]
        paragraph=deepcopy(template)
        replace_text(paragraph,value)
        parent.insert(position,paragraph)
        position+=1


insert_after(52,[
    ('heading','5 制作笔身前端和可压动笔尖'),
    ('body','笔身前端与笔壳一体，先采用与笔轴同轴的规则圆柱截面。用不同直径和材料的前壳样件比较回波。初样可参考图中的约 20 mm 笔身宽度，实际尺寸结合握持与检测实验确定。'),
    ('body','圆头笔尖短距离伸出，笔尖杆通过导向结构相对固定笔壳轴向滑动，压动时触发内部微动开关。D2F-01FL 为当前候选，开关形式、约 1 mm 的行程及复位结构通过装配试验调整，记录触发力和回程表现。'),
    ('body','握持区与笔杆按键放在检测段后方，用轻微台阶或凹槽引导手指，保证雷达能看到前端表面。比较塑料圆头及软质包覆圆头的滑动、压动和板面接触表现。'),
])
insert_after(120,[
    ('heading','5 扩展为桌面批注和独立白板'),
    ('body','做一个可拖动、可收起的浮动工具条，先放操作、画笔、橡皮、撤销、清屏、保存和白板按钮，再提供颜色与粗细设置。工具条独立于覆盖层，操作模式下也能点击。'),
    ('body','透明批注层覆盖投影对应的桌面区域。操作工具让下层软件接收点击和拖动，画笔工具把笔迹绘制在覆盖层上。工具条区域优先响应按钮，切换工具时结束笔画并释放按下状态。'),
    ('body','白板按钮打开独立画布，继续使用同一套绘图和工具逻辑。白板与桌面分别保留笔迹，回到桌面后恢复批注。保存先支持画面与笔迹的合成图片，同时保留轨迹数据用于回放。'),
    ('body','先用鼠标检查透明层、工具切换与下层应用操作，再接入真实笔端。用同一套位置和接触事件控制绘图或桌面操作，并保留调试入口。'),
])
insert_after(174,[
    ('body','有效跟踪帧按目标被识别且位置有效来统计，分母采用雷达记录的原始扫描帧数。额外记录最长连续丢失时间。悬停以每次 2 秒试验为单位，期间出现误落笔就记该次失败。'),
    ('body','接触触发策略对照中，两种策略各统计 40 次悬停，并比较 40 次接触的识别表现。保存同一组动作的位置与开关记录，可在回放时分别计算两种策略。'),
])
insert_after(184,[
    ('heading','远程拓展的按键与零位'),
    ('body','模式开关切换近远程。点击键按下时产生鼠标按下，松开时释放，支持点击和拖动。'),
    ('body','复位键按住时释放鼠标按下状态、暂停姿态驱动并把光标置于屏幕中心，松开时以当前姿态更新零位。'),
    ('body','固定键按一次锁定光标当前位置，点击键继续可用；再按一次，以当前姿态更新零位并恢复移动。'),
    ('body','远程以相对零位的水平、竖直偏转角控制光标速度，设置零位死区。图中 A/B/C/L/R 与具体功能的对应关系，在笔壳装配时确定。'),
    ('heading','结题演示的近程主线'),
    ('body','近程点击桌面快捷方式，打开批注工具，在当前应用上圈画和书写，再演示按钮操作、拖动、清屏、保存及独立白板。结合六项考核指标整理数据，另附模拟输入切换记录和远程拓展进展。'),
])
insert_after(178,[
    ('heading','四人分工建议'),
    ('body','成员 A 负责笔端结构和固件，完成接触开关、IMU 采集、笔壳初样及接线记录，与 B 比较前端回波，与 C 对齐串口字段。'),
    ('body','成员 B 负责雷达接入、检测跟踪和笔轴估计，交付原始扫描记录与有效位置输出，配合 A 确定检测段尺寸，配合 D 完成标定记录。'),
    ('body','成员 C 负责电脑端界面与集成，完成鼠标画布、浮动工具条、透明批注层及独立白板，统一接收 A/B 的输入，并与 D 检查完整流程。'),
    ('body','成员 D 负责测试与数据管理，前期准备测试表和模拟回放数据，后期汇总误差、有效跟踪及延迟结果，组织各成员补齐实验记录和报告。'),
    ('body','首轮并行推进按键采集、雷达样例、鼠标画布和测试准备，集成前共同确定输入字段和时间记录方式。A/B/C/D 为职责认领标记，后续按实际进度平衡工作量。'),
])
insert_after(191,[
    ('body','桌面批注可参考 gInk 的简洁工具条、ppInk 的鼠标穿透与工具组织、OpenBoard 的桌面和白板切换。开发继续采用 Python/PySide6，按当前阶段完成所需功能。'),
])

# Remove the previous manual editing marks for a clean working guide.
for element in list(document.xpath('//w:strike|//w:dstrike|//w:highlight|//w:vanish',namespaces=NS)):
    element.getparent().remove(element)
for properties in document.xpath('//w:rPr',namespaces=NS):
    color=properties.find(q('color'))
    if color is None:
        color=ET.SubElement(properties,q('color'))
    color.attrib.clear()
    color.set(q('val'),'000000')
styles=ET.fromstring(parts['word/styles.xml'])
for color in styles.xpath('//w:color',namespaces=NS):
    color.attrib.clear()
    color.set(q('val'),'000000')

# Let the expanded sections flow naturally, keeping headings with their text.
for element in document.xpath('//w:pageBreakBefore',namespaces=NS)+styles.xpath('//w:pageBreakBefore',namespaces=NS):
    element.set(q('val'),'0')
for element in list(document.xpath('//w:br[@w:type="page"]',namespaces=NS)):
    element.getparent().remove(element)
for paragraph in document.xpath('//w:body//w:p',namespaces=NS):
    if paragraph.xpath('./w:pPr/w:pStyle',namespaces=NS) or paragraph.xpath('./w:r/w:rPr/w:b',namespaces=NS):
        props=paragraph.find(q('pPr'))
        if props is None:
            props=ET.Element(q('pPr'))
            paragraph.insert(0,props)
        keep=props.find(q('keepNext'))
        if keep is None:
            keep=ET.SubElement(props,q('keepNext'))
        keep.set(q('val'),'1')
first_step_props=paragraphs[25].find(q('pPr'))
page_break=first_step_props.find(q('pageBreakBefore'))
if page_break is None:
    page_break=ET.SubElement(first_step_props,q('pageBreakBefore'))
page_break.set(q('val'),'1')
parts['word/styles.xml']=ET.tostring(styles,xml_declaration=True,encoding='UTF-8',standalone=True)
parts['word/document.xml']=ET.tostring(document,xml_declaration=True,encoding='UTF-8',standalone=True)
if OUTPUT.exists():
    assert (ROOT/'work/final_review/update_audit.json').exists(), 'Review existing output before replacing it.'
with ZipFile(OUTPUT,'w') as archive:
    for entry in entries:
        archive.writestr(entry,parts[entry.filename])

all_text=''.join(document.xpath('//w:t/text()',namespaces=NS))
for outdated in ['套环','2350','5000','卖家','beta1.1','100次','95%','15mm']:
    assert outdated not in all_text, outdated
assert not document.xpath('//w:strike|//w:commentRangeStart|//w:ins|//w:del',namespaces=NS)
assert not document.xpath('//w:color[@w:val="0000FF"]',namespaces=NS)
for path,digest in hashes.items():
    assert sha256(Path(path).read_bytes()).hexdigest()==digest,path
with ZipFile(OUTPUT) as archive:
    for name in archive.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            ET.fromstring(archive.read(name))
(ROOT/'work/final_review/update_audit.json').write_text(json.dumps({'source_hashes':hashes,'updated_paragraphs':len(updates),'output':str(OUTPUT)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'output':str(OUTPUT),'updated_paragraphs':len(updates),'clean_version':True,'sources_preserved':True},ensure_ascii=False))
