from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json

from lxml import etree as ET


ROOT = Path(r'C:\Users\wangjianing\Desktop\SRDP')
SOURCE = ROOT / '申报书与材料/申报书beta1.3.docx'
DESTINATION = ROOT / '申报书与材料/申报书beta1.3.1.docx'
WORK = ROOT / 'work'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
BLUE = '0000FF'


def q(name):
    return f'{{{W}}}{name}'


def visible_text(paragraph):
    return ''.join(paragraph.xpath('.//w:t/text()', namespaces=NS))


with ZipFile(SOURCE) as archive:
    parts = {entry.filename: archive.read(entry.filename) for entry in archive.infolist()}
    entries = archive.infolist()

document = ET.fromstring(parts['word/document.xml'])
original_paragraphs = document.xpath('//w:body//w:p', namespaces=NS)
source_text = {i: visible_text(p) for i, p in enumerate(original_paragraphs)}
source_hash = sha256(SOURCE.read_bytes()).hexdigest()

# The source's current text is the baseline for this review round.
deleted_empty_paragraphs = [
    p for p in original_paragraphs
    if p.xpath('./w:pPr/w:rPr/w:del', namespaces=NS) and not visible_text(p)
]
for element in list(document.xpath('//w:del|//w:moveFrom', namespaces=NS)):
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)
for element in list(document.xpath('//w:ins|//w:moveTo', namespaces=NS)):
    parent = element.getparent()
    if parent is not None:
        position = parent.index(element)
        children = list(element)
        parent.remove(element)
        for offset, child in enumerate(children):
            parent.insert(position + offset, child)
for element in list(document.xpath('//w:rPrChange|//w:pPrChange|//w:tblPrChange|//w:tcPrChange|//w:trPrChange', namespaces=NS)):
    element.getparent().remove(element)
for paragraph in deleted_empty_paragraphs:
    paragraph.getparent().remove(paragraph)

comments = ET.Element(q('comments'), nsmap={'w': W})
changes = []


def make_run(text, properties, blue=False):
    run = ET.Element(q('r'))
    properties = deepcopy(properties) if properties is not None else ET.Element(q('rPr'))
    if blue:
        color = properties.find(q('color'))
        if color is None:
            color = ET.SubElement(properties, q('color'))
        color.attrib.clear()
        color.set(q('val'), BLUE)
    if len(properties):
        run.append(properties)
    node = ET.SubElement(run, q('t'))
    node.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    node.text = text
    return run


def add_comment(paragraph, message):
    comment_id = str(len(comments))
    start = ET.Element(q('commentRangeStart'), {q('id'): comment_id})
    end = ET.Element(q('commentRangeEnd'), {q('id'): comment_id})
    paragraph.insert(1 if paragraph.find(q('pPr')) is not None else 0, start)
    paragraph.append(end)
    reference = ET.SubElement(paragraph, q('r'))
    properties = ET.SubElement(reference, q('rPr'))
    ET.SubElement(properties, q('rStyle'), {q('val'): 'CommentReference'})
    ET.SubElement(properties, q('color'), {q('val'): BLUE})
    ET.SubElement(reference, q('commentReference'), {q('id'): comment_id})
    comment = ET.SubElement(comments, q('comment'), {
        q('id'): comment_id,
        q('author'): 'Codex',
        q('initials'): 'CX',
        q('date'): datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    })
    body = ET.SubElement(comment, q('p'))
    properties = ET.Element(q('rPr'))
    ET.SubElement(properties, q('rFonts'), {q('eastAsia'): '宋体', q('ascii'): 'Calibri', q('hAnsi'): 'Calibri'})
    ET.SubElement(properties, q('sz'), {q('val'): '20'})
    body.append(make_run(message, properties, blue=True))


def edit(index, replacements, message):
    paragraph = original_paragraphs[index]
    old = visible_text(paragraph)
    new = old
    for before, after in replacements:
        if new.count(before) != 1:
            raise ValueError(f'Paragraph {index}: expected one match for {before!r}, got {new.count(before)}')
        new = new.replace(before, after, 1)
    if old == new:
        raise ValueError(f'Paragraph {index}: no change')
    runs = []
    cursor = 0
    for run in paragraph.xpath('.//w:r', namespaces=NS):
        text = ''.join(run.xpath('.//w:t/text()', namespaces=NS))
        if text:
            runs.append((cursor, cursor + len(text), run.find(q('rPr'))))
            cursor += len(text)
    default_properties = runs[0][2] if runs else None
    for child in list(paragraph):
        if child.tag != q('pPr'):
            paragraph.remove(child)
    for opcode, i1, i2, j1, j2 in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if opcode == 'equal':
            for start, end, properties in runs:
                a, b = max(i1, start), min(i2, end)
                if a < b:
                    paragraph.append(make_run(old[a:b], properties))
        elif opcode in ('replace', 'insert'):
            properties = next((properties for start, end, properties in runs if start <= i1 < end), default_properties)
            paragraph.append(make_run(new[j1:j2], properties, blue=True))
    add_comment(paragraph, message)
    changes.append({'paragraph': index, 'before': old, 'after': new, 'comment': message})


edit(112, [('视项目进度启动', '在近程功能完成后接入并验证')],
     '统一远程任务范围，将真实 IMU 空鼠与后文的完整流程演示和预期成果对齐。')
edit(131, [('角度零点与正方向按实测结果确定后写入配置文件；不合并点云，保留每帧全部扫描点，因为合并点数增大会把笔杆或套环上的点并掉。',
            '角度约定依据接口文档核对后写入配置文件。点云合并设为 1 点，筛除零距离等无效点，保留细笔检测所需的采样密度。')],
     '采用设备支持的 1 点合并设置，并明确无效点筛选。角度约定先查接口文档，再用实物检查方向。')
edit(133, [('对于笔端的组，其宽度接近笔杆或套环的直径，而手掌和袖口形成的组宽度明显更大，按宽度和点数即可分开。',
            '以笔杆或套环尺寸为参考设置候选组的宽度和点数范围，并通过手掌、袖口进入扫描区的实验调整筛选阈值。'),
           ('连续 3 帧没有匹配到候选组即判定目标丢失，回到全区域重新搜索。',
            '缺少有效位置时停止绘制；超过设定时间仍未匹配到候选组，则判定目标丢失并回到全区域搜索，超时阈值结合帧周期和遮挡实验确定。')],
     '将目标尺寸作为筛选依据，通过干扰实验确定阈值。绘制停止与目标身份超时分别处理，超时采用时间量，便于比较不同帧率。')
edit(136, [('塑料圆头滑动省力，软质包覆对板面更友好，两者的取舍按 40 次接触试验的结果确定。',
            '结合划线表现和 40 次接触试验结果选择笔尖材料。')],
     '材料选择依据滑动和接触试验，删除试验前对两种材料效果的判断。')
edit(137, [('进入雷达扫描面的检测段设在靠近笔尖的位置，采用可拆卸套环，套环与笔轴同轴安装，外径和表面材料做成可替换的几组。扫描面穿过套环时回波点数比裸笔杆多：2 m 处相邻扫描点间隔约 2.8 mm，直径 12 mm 的套环约有 4 点落入，8 mm 的裸笔杆约 3 点；帧率升到 20–30 Hz 时角分辨率变粗，套环仍有 1–2 点，裸笔杆常在一帧内没有回波而断笔。跟踪因此更容易保持连续，检测位置也从笔杆落到靠近笔尖的高度。',
            '进入雷达扫描面的检测段设在靠近笔尖的位置，采用可拆卸套环，即套在笔杆外侧、局部增加直径的短圆筒。套环与笔轴同轴固定，轴向长度结合扫描高度、笔尖行程和握笔倾角确定，并避开握持区及笔尖活动结构。首版采用浅色、哑光、不透明塑料，外径和表面材料做成可替换的几组。以直径 8 mm 的笔杆和外径 12 mm 的套环作为初始对照，实际回波点数随帧率、扫描位置和表面反射变化。')],
     '补充套环的具体形态、固定方式和长度设计依据。浅色哑光塑料作为首轮样件，按实测回波比较材料及表面处理。删除固定回波点数和检测改善的预判，保留 8 mm 与 12 mm 作为初始对照尺寸。')
edit(142, [('结构上先把扫描面与书写面的间距压到 10 mm 量级；剩余偏差依靠笔轴姿态估计补偿',
            '先在交互区各处检查光斑与板面的接触情况及检测段回波，据此确定安装间距；再结合笔轴姿态估计开展补偿')],
     '安装间距先由实际出光方向、光斑和目标回波确定，再开展姿态补偿。几何示例中的 h=10 mm 继续作为计算示例。')
edit(144, [('近程与远程共用一套事件接口，两种输入都输出光标位置与按下状态：近程由雷达位置和笔尖接触信号产生，远程由笔端 IMU 的姿态变化产生。进入远程模式时以当前姿态为零位，笔杆转动量换算为光标速度，按键用于暂停光标；需要重新对准时先暂停光标，摆正笔的指向后再继续。',
            '近程与远程共用一套事件接口，两种输入都输出光标位置与按下状态。近程由雷达位置和笔尖接触信号产生，远程由 IMU 姿态和点击按键产生。进入远程模式时以当前姿态为零位，将相对零位的水平、竖直偏转角分别映射为光标速度；按住复位键暂停光标，松开时以当前姿态更新零位。')],
     '将远程算法明确为相对零位的偏转角控制速度，并补全重新对准时更新零位的规则。远程按下状态来自点击按键，具体分配见交互事件小节。')
edit(147, [('扫描面与板面平行', '调整扫描面使其与板面近似平行')],
     '将两平面关系表述为安装调整目标，与后文各处间距检查相衔接。')
edit(168, [('0.21 A（12 V）', '典型电流 0.21 A（12 V）')],
     '表 1 按厂家当前 PAVO 产品页列示。V2.4 手册与当前网页在电流及防护等级上有版本差异，接机时以设备铭牌和对应资料核对。产品页 https://www.siminics.com/laser_radar/208.html')
edit(173, [(source_text[173],
            '定位误差通过静态重复测量和独立检核点试验评估。10 Hz、点云合并为 1 点时，2 m 处相邻采样方向的间隔约为 2.8 mm。分别统计目标中心的帧间波动和相对物理标记的平均偏差，并记录材料、距离及参与平均的帧数。结合光斑覆盖和套环表面回波分析中心估计偏差，采用九点检核、支架调整和姿态补偿控制误差。书写时比较短窗口滤波下的笔迹抖动和延迟，以实测结果评估平均误差不超过 20 mm 的目标。')],
     '删除将 ±30 mm 直接按独立随机误差进行平方根降噪的计算。静态波动、固定偏差和目标表面几何分别测量，20 mm 保留为待实验评估的考核目标。')
edit(174, [('雷达数据到界面响应经过八个环节：', '雷达数据到界面响应依次经过'),
           ('实际字段与角度约定以到货设备的接口文档为准', '实际字段与角度约定按该设备的接口文档核对'),
           ('笔尖位置估计先给出扫描面内的笔轴位置，再按两平面的间距修正到板面笔尖',
            '笔尖位置估计结合套环尺寸和可见表面回波，通过结构标定估计扫描面内的笔轴位置，再结合两平面间距与姿态修正到板面笔尖'),
           ('接触事件融合按时间戳把接触状态与位置对齐，生成落笔、移动和抬笔事件',
            '接触事件融合先记录两路数据的电脑接收时间，再估计设备时间与电脑时间的对应关系，将接触状态与位置对齐并生成落笔、移动和抬笔事件'),
           ('各环节记录处理耗时，端到端延迟由扫描时间戳、串口接收时间和画面刷新时间逐段相加，作为⑥中延迟测量的依据。',
            '各环节在电脑统一时钟下记录处理耗时，设备时间用于分析采样及传输过程。端到端延迟采用⑥中的慢动作录像测量，程序日志用于定位主要耗时环节。')],
     '补上套环可见表面到笔轴的结构标定，并明确多设备时间对齐和延迟测量方法。录像测端到端延迟，统一时钟日志分析处理耗时。')
edit(181, [('帧率提高会缩短帧周期（10 Hz 的帧周期已占满 100 ms 的延迟预算），但角分辨率随之变粗、套环上的点变少，取舍按这两组数据确定。',
            '10 Hz 的扫描周期为 100 ms，实际响应受扫描时刻、SDK 缓存和显示刷新共同影响。提高帧率会缩短扫描周期，同时增大相邻采样方向的间隔，配置取舍按目标回波、有效跟踪帧占比及端到端延迟确定。')],
     '区分扫描周期与端到端延迟，保留 10、20、30 Hz 的原定对照安排。')
edit(186, [('研究分两步。第一步控制结构误差：调整安装支架使两平面保持平行，检查交互区各处的间距是否一致，把 h 压到 10 mm 量级；',
            '研究分两步。第一步控制结构误差。调整安装支架，检查各处扫描高度及光斑与板面的关系，依据笔端回波确定 h，并记录区域内的间距变化；'),
           ('第二步研究补偿方法：用笔端 IMU 估计笔轴姿态', '第二步研究补偿方法。用笔端 IMU 估计笔轴姿态'),
           ('u 为从笔尖指向笔尾的笔轴单位向量，已换算到板面坐标系；',
            '板面向右、向上及向使用者分别定义为 x、y、z 方向，u 为从笔尖指向笔尾的笔轴单位向量，并换算到板面坐标系。x_detect、y_detect 取经结构标定得到的笔轴交点坐标，在 u_z 大于预设正阈值的握姿范围内应用补偿；')],
     '将固定 10 mm 安装要求改为实测确定间距，补全坐标系、笔轴交点和公式适用的握姿范围。出光方向及光斑资料见 PAVO 用户手册第 11–12 页。')
edit(206, [('目标丢失或通信超时', '近程目标丢失或笔端通信超时')],
     '将雷达目标丢失限定于近程，笔端通信超时在两种模式下均释放按下状态。')
edit(210, [('自研软件接收同一通道的输入，按当前工具解释输入：操作工具用于选择和拖动，书写工具用于绘制。工具由界面按钮或笔杆第二按键切换，接触后移动的动作随工具确定。',
            '自研软件接收鼠标事件，按当前工具解释输入。操作工具用于选择和拖动，书写工具用于绘制。工具由界面按钮切换，接触后移动的动作随工具确定。')],
     '明确桌面鼠标事件作为共同入口，避免同一输入在软件中重复触发。工具通过界面切换，为远程点击和复位保留清楚的按键分工。')
edit(211, [(source_text[211],
            '笔杆按键分为模式键、点击键和复位键。模式键切换近远程模式；点击键在远程按下时产生鼠标按下，松开时产生释放，支持点击与拖动；复位键按住时暂停光标并释放按下状态，松开时更新姿态零位。远程光标速度按相对零位的偏转角计算，设置零位死区抑制静止抖动。模式切换、近程目标丢失或笔端通信超时均结束当前操作并释放按下状态。软件界面与模式切换的流程见图 4。')],
     '本轮提出三键分工供审阅，分别承担模式、远程点击和姿态复位。补齐空鼠点击、拖动和零位死区，复位时释放按下状态。')
edit(242, [('申请经费5000元', '申请经费4500元')],
     '申请金额按现有预算分项合计 4500 元统一，分项金额沿用当前预算表。')
edit(50, [('5000元', '4500元')],
     '基本情况中的申请金额与预算表合计 4500 元对齐。')
edit(245, [('雷达位置只负责笔尖坐标', '雷达回波经目标检测、结构标定及坐标映射得到笔尖位置'),
           ('验证方法是对比两种触发策略：一种只按笔尖进入扫描区域触发，另一种在接触信号确认后才触发；',
            '验证时对比两种触发策略，一种按检测到的笔端进入交互区域触发，另一种在接触信号确认后触发；')],
     '区分原始回波与估计笔尖位置，基线触发对象明确为雷达检测到的笔端。')
edit(247, [('近程由雷达和接触信号产生，远程由笔端 IMU 产生。',
            '近程由雷达和接触信号产生，远程由笔端 IMU 与点击按键产生。')],
     '统一远程位置和按下状态的来源，姿态用于光标运动，点击按键用于按下及释放。')
edit(249, [(source_text[249],
            '共用事件接口将输入采集与桌面操作分离，便于分阶段接入雷达、笔端开关及 IMU，并复用画布和对象拖动逻辑。')],
     '压缩与前文重复的接口说明，明确接口复用的用途。')
edit(250, [(source_text[250],
            '表 3 按输入方式比较普通空鼠、深度相机投影交互和本项目。比较内容包括位置获取、接触判定和操作流程。本项目研究二维雷达定位与笔尖开关的配合，并以连续书写和近远程切换任务评估交互效果。')],
     '将过宽的产品概括改为输入方式比较，效果由本项目实验评价。具体产品对比待选定型号后补充。')
edit(251, [('与现有输入方式的比较', '不同输入方式的比较')],
     '表题与按输入方式展开的比较口径一致。')
edit(261, [('深度相机，逐面标定', '深度相机及表面标定')],
     '调整为方法描述，具体系统的标定流程依其资料核实。')
edit(263, [('手指操作，需专用设备', '手指操作，配合深度相机与投影')],
     '写出所用感知及显示设备，便于与雷达方案比较。')
edit(268, [('表中前两类的参数按最终选定的产品核实。', '后续选定代表产品，依据其公开资料补充型号及功能对照。')],
     '明确后续产品比较所需的资料和内容。')

# Give retained figure placeholders self-contained labels and review notes.
figure_notes = {
    139: ('1', '图 1 绘制笔尖、D2F-01FL 开关及复位结构，标出套环的直径和轴向长度，并画出扫描面穿过套环的位置。'),
    175: ('2', '图 2 绘制雷达与笔端至电脑的连接，标出定位处理、时间对齐和交互事件输出。'),
    187: ('3', '图 3 标出板面、扫描面、间距 h、笔轴交点和真实笔尖，并注明板面坐标方向。'),
    212: ('4', '图 4 展示画布工具、近远程状态提示，以及模式键、点击键和复位键的操作流程。'),
}
for index, (number, note) in figure_notes.items():
    edit(index, [(source_text[index], f'〔待绘制图 {number}〕')], note)

# Keep a stage heading with the following explanation.
for index in (177, 178):
    paragraph_properties = original_paragraphs[index].find(q('pPr'))
    if paragraph_properties is None:
        paragraph_properties = ET.Element(q('pPr'))
        original_paragraphs[index].insert(0, paragraph_properties)
    if paragraph_properties.find(q('keepNext')) is None:
        paragraph_properties.insert(0, ET.Element(q('keepNext')))

settings = ET.fromstring(parts['word/settings.xml'])
for element in list(settings.xpath('//w:trackRevisions', namespaces=NS)):
    element.getparent().remove(element)
parts['word/settings.xml'] = ET.tostring(settings, xml_declaration=True, encoding='UTF-8', standalone=True)

rels_ns = 'http://schemas.openxmlformats.org/package/2006/relationships'
relationships = ET.fromstring(parts['word/_rels/document.xml.rels'])
used_ids = {node.get('Id') for node in relationships}
number = 1
while f'rId{number}' in used_ids:
    number += 1
ET.SubElement(relationships, f'{{{rels_ns}}}Relationship', {
    'Id': f'rId{number}',
    'Type': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments',
    'Target': 'comments.xml',
})
parts['word/_rels/document.xml.rels'] = ET.tostring(relationships, xml_declaration=True, encoding='UTF-8', standalone=True)
content_types = ET.fromstring(parts['[Content_Types].xml'])
ET.SubElement(content_types, '{http://schemas.openxmlformats.org/package/2006/content-types}Override', {
    'PartName': '/word/comments.xml',
    'ContentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml',
})
parts['[Content_Types].xml'] = ET.tostring(content_types, xml_declaration=True, encoding='UTF-8', standalone=True)
parts['word/document.xml'] = ET.tostring(document, xml_declaration=True, encoding='UTF-8', standalone=True)
parts['word/comments.xml'] = ET.tostring(comments, xml_declaration=True, encoding='UTF-8', standalone=True)

if DESTINATION.exists():
    assert (WORK / 'revision_131_audit.json').exists(), 'Review existing destination before replacing it.'
with ZipFile(DESTINATION, 'w') as archive:
    for entry in entries:
        archive.writestr(entry, parts.pop(entry.filename))
    for name, data in parts.items():
        archive.writestr(name, data)

# Verify source preservation, exact edited text, color coverage and comment anchors.
assert sha256(SOURCE.read_bytes()).hexdigest() == source_hash
assert not document.xpath('//w:ins|//w:del', namespaces=NS)
assert len(comments) == len(changes)
for change in changes:
    paragraph = original_paragraphs[change['paragraph']]
    assert visible_text(paragraph) == change['after']
    assert paragraph.xpath('./w:commentRangeStart', namespaces=NS)
    assert paragraph.xpath('./w:r/w:rPr/w:color[@w:val="0000FF"]', namespaces=NS)
for index, paragraph in enumerate(original_paragraphs):
    if index not in {change['paragraph'] for change in changes}:
        assert visible_text(paragraph) == source_text[index]
with ZipFile(DESTINATION) as archive:
    for name in archive.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            ET.fromstring(archive.read(name))
WORK.mkdir(exist_ok=True)
(WORK / 'revision_131_audit.json').write_text(json.dumps({'source_sha256': source_hash, 'changes': changes}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(DESTINATION), 'changed_paragraphs': len(changes), 'comments': len(comments), 'source_preserved': True}, ensure_ascii=False))
