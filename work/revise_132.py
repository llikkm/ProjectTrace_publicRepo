from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json

from lxml import etree as ET


ROOT = Path(r'C:\Users\wangjianing\Desktop\SRDP')
SOURCE = ROOT / '申报书与材料/申报书beta1.3.1.docx'
OUTPUT = ROOT / '申报书与材料/申报书beta1.3.2.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
BLUE = '0000FF'
source_hash = sha256(SOURCE.read_bytes()).hexdigest()
with ZipFile(SOURCE) as archive:
    entries = archive.infolist()
    parts = {entry.filename: archive.read(entry.filename) for entry in entries}
document = ET.fromstring(parts['word/document.xml'])
comments = ET.fromstring(parts['word/comments.xml'])
paragraphs = document.xpath('//w:body//w:p', namespaces=NS)
next_comment_id = max(int(c.get(f'{{{W}}}id')) for c in comments) + 1
changes = []


def q(name):
    return f'{{{W}}}{name}'


def text(paragraph):
    return ''.join(paragraph.xpath('.//w:t/text()', namespaces=NS))


baseline = [text(p) for p in paragraphs]


def run(text_value, properties, blue=False):
    node = ET.Element(q('r'))
    properties = deepcopy(properties) if properties is not None else ET.Element(q('rPr'))
    if blue:
        color = properties.find(q('color'))
        if color is None:
            color = ET.SubElement(properties, q('color'))
        color.attrib.clear()
        color.set(q('val'), BLUE)
    if len(properties):
        node.append(properties)
    value = ET.SubElement(node, q('t'))
    value.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    value.text = text_value
    return node


def replace_comment(paragraph, message):
    global next_comment_id
    old_ids = set(paragraph.xpath('./w:commentRangeStart/@w:id|./w:commentRangeEnd/@w:id|./w:r/w:commentReference/@w:id', namespaces=NS))
    for node in list(paragraph.xpath('./w:commentRangeStart|./w:commentRangeEnd|./w:r[w:commentReference]', namespaces=NS)):
        paragraph.remove(node)
    for comment in list(comments):
        if comment.get(q('id')) in old_ids:
            comments.remove(comment)
    comment_id = str(next_comment_id)
    next_comment_id += 1
    start = ET.Element(q('commentRangeStart'), {q('id'): comment_id})
    paragraph.insert(1 if paragraph.find(q('pPr')) is not None else 0, start)
    paragraph.append(ET.Element(q('commentRangeEnd'), {q('id'): comment_id}))
    reference = ET.SubElement(paragraph, q('r'))
    properties = ET.SubElement(reference, q('rPr'))
    ET.SubElement(properties, q('rStyle'), {q('val'): 'CommentReference'})
    ET.SubElement(properties, q('color'), {q('val'): BLUE})
    ET.SubElement(reference, q('commentReference'), {q('id'): comment_id})
    comment = ET.SubElement(comments, q('comment'), {
        q('id'): comment_id, q('author'): 'Codex', q('initials'): 'CX',
        q('date'): datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    })
    body = ET.SubElement(comment, q('p'))
    properties = ET.Element(q('rPr'))
    ET.SubElement(properties, q('rFonts'), {q('eastAsia'): '宋体', q('ascii'): 'Calibri', q('hAnsi'): 'Calibri'})
    ET.SubElement(properties, q('sz'), {q('val'): '20'})
    body.append(run('1.3.2 修订。' + message, properties, blue=True))


def edit(index, replacements, message):
    paragraph = paragraphs[index]
    old = text(paragraph)
    new = old
    for before, after in replacements:
        assert new.count(before) == 1, (index, before)
        new = new.replace(before, after, 1)
    assert old != new
    spans = []
    position = 0
    for old_run in paragraph.xpath('.//w:r', namespaces=NS):
        value = ''.join(old_run.xpath('.//w:t/text()', namespaces=NS))
        if value:
            spans.append((position, position + len(value), old_run.find(q('rPr'))))
            position += len(value)
    default = spans[0][2] if spans else None
    # Retain old anchors until replace_comment removes their corresponding entries.
    for child in list(paragraph):
        if child.tag == q('r') and child.find(q('commentReference')) is None:
            paragraph.remove(child)
    for opcode, i1, i2, j1, j2 in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if opcode == 'equal':
            for start, end, properties in spans:
                a, b = max(i1, start), min(i2, end)
                if a < b:
                    paragraph.append(run(old[a:b], properties))
        elif opcode in ('replace', 'insert'):
            properties = next((properties for start, end, properties in spans if start <= i1 < end), default)
            paragraph.append(run(new[j1:j2], properties, blue=True))
    replace_comment(paragraph, message)
    changes.append({'paragraph': index, 'before': old, 'after': new, 'comment': message})


edit(112, [('项目先完成近程点击、拖动和大字书写，再探索同一支笔在远程光标控制与近程批注之间的切换方法。六轴惯性传感器（IMU）实现的远程光标控制排在近程功能之后，在近程功能完成后接入并验证。',
            '项目以近程点击、拖动和大字书写为主要任务，预留近远程共用接口。近程功能及性能测试完成后，根据项目进展开展六轴惯性传感器（IMU）远程光标控制与模式切换的拓展实验。')],
     '明确近程为主要任务，IMU 远程空鼠作为后期拓展。远程接口验证、进度和结题成果作对应调整。')
edit(129, [('研究从坐标标定、接触检测、误差与稳定性分析、近远程联动四个方面依次展开',
            '研究围绕坐标标定、接触检测及误差与稳定性分析展开，并设计近远程共用接口')],
     '将近远程共用接口列为系统扩展设计，使研究内容与近程主线一致。')
edit(143, [('（四）近远程联动方法与远程操控', '（四）近远程接口与远程操控拓展')],
     '在小节标题中标明远程操控的拓展性质。')
edit(144, [('采用笔杆按键切换近程书写与远程控制模式。近程与远程共用一套事件接口，两种输入都输出光标位置与按下状态。',
            '设计近程书写与远程控制共用的事件接口，两种输入都输出光标位置与按下状态，先以鼠标模拟远程输入验证模式切换。IMU 远程拓展采用模式开关切换输入源。'),
           ('按住复位键暂停光标，松开时以当前姿态更新零位。',
            '按住复位键时释放鼠标按下状态、暂停姿态驱动，并将光标置于屏幕中心，松开时以当前姿态更新零位。')],
     '先以模拟输入验证接口与切换，再按进展接入真实 IMU。统一复位键的动作，使其与用户更新的屏幕中心归位功能一致。')
edit(188, [('阶段四 完整应用流程验证', '阶段四 近程应用验证与远程拓展')],
     '阶段名称与近程结题主线、后期远程拓展的安排对齐。')
edit(189, [(baseline[189],
            '结题演示以近程点击桌面快捷方式、打开自研软件、完成规定书写和拖动为主，记录各环节的完成情况、耗时和异常，并结合（五）中的六项指标评估近程系统。近远程共用接口采用鼠标模拟远程输入验证，检查切换时按下状态的释放与输入源交接。后期开展 IMU 远程拓展时，补充空鼠打开应用、返回近程继续操作的演示，并单独记录实现进展和测试结果。')],
     '将结题依据落实到近程演示及六项既有指标。模拟输入验证接口，真实 IMU 空鼠按后期拓展进展单独报告。')
edit(208, [('笔杆按键分为模式切换开关、点击键、复位键、固定键及其他功能键。',
            '远程拓展的笔杆控制件设为模式切换开关、点击键、复位键和固定键。'),
           ('支持点击与拖动 ；复位键按住时释放按下状态，光标强制归位于屏幕中心，松开时更新姿态零位。固定键固定光标位于当前位置，防止光标乱移。视情况与开发需要，可以后续添加其他功能。',
            '支持点击与拖动；复位键按住时释放鼠标按下状态、暂停姿态驱动，并将光标置于屏幕中心，松开时更新姿态零位。固定键按住时暂停姿态驱动，使光标保持当前位置，点击键仍可操作；松开固定键时以当前姿态更新零位，恢复光标运动。其他功能键根据开发需要增设。')],
     '沿用用户新增的模式开关、点击键、复位键和固定键。复位键归中并暂停姿态驱动。固定键本轮细化为按住锁定、松开恢复，释放时更新姿态零位，供审阅。点击键在锁定期间保持可用。')
edit(214, [(baseline[214],
            '完成一套大屏幕显示交互系统原型、一个带接触检测的交互笔样机，以及源程序、标定配置和测试报告。结题成果以近程点击、按住拖动、接触书写、抬笔断笔、清屏和笔迹保存为核心，按以下六项指标考核，并提交近远程共用接口及模拟输入切换的验证记录。IMU 远程空鼠列为后期拓展，按实际进展单独报告。')],
     '在预期成果处明确结题考核范围。近程六项指标构成考核主体，共用接口以模拟输入验证，真实 IMU 空鼠按拓展进展报告。近程倾斜补偿中的 IMU 研究沿用现稿。')
edit(227, [(baseline[227],
            '2027.8-2027.10：完善近程演示和共用事件接口，采用模拟输入验证模式切换，整理测试数据；根据近程完成情况开展 IMU 空鼠拓展，记录远程点击、光标归中与位置锁定的实现进展。')],
     '调整后期进度，把近程完善和接口验证放在前面，IMU 空鼠根据近程完成情况开展。')
edit(238, [(baseline[238],
            '面向近远程联动的共用事件接口。近程由雷达位置和接触信号生成光标与按下状态，接口预留 IMU 姿态及点击按键输入。采用鼠标模拟远程输入，验证模式切换时的状态释放与输入源交接；后期接入 IMU 后，进一步探索同一支笔的近远程操作。')],
     '将特色由已完成同笔近远程操作调整为共用接口及联动探索，与拓展任务范围一致。')
edit(241, [('并以连续书写和近远程切换任务评估交互效果。',
            '以近程连续书写评估交互效果，并以模拟输入验证模式切换。')],
     '统一比较段落中的评价口径，近程效果与接口切换分别验证。')
edit(258, [('近程直接书写，远程姿态控光标', '近程直接书写，后期拓展远程光标')],
     '表格中的使用流程同步标明远程光标为后期拓展。')
replace_comment(paragraphs[209], '图 4 先绘制近程画布、工具选择和接口切换流程，远程拓展区标出模式开关、点击键、复位键与固定键。图片按用户要求留待后续绘制。')

# Remove the template's off-page duplicate header/footer table, which adds a blank page.
body = document.find(q('body'))
last_table = body.findall(q('tbl'))[-1]
indent = last_table.find('w:tblPr/w:tblInd', NS)
instructions = ''.join(last_table.xpath('.//w:instrText/text()', namespaces=NS))
assert indent is not None and indent.get(q('w')) == '21600'
assert 'PAGE' in instructions and 'NUMPAGES' in instructions
assert not last_table.xpath('.//w:commentRangeStart', namespaces=NS)
body.remove(last_table)

parts['word/document.xml'] = ET.tostring(document, xml_declaration=True, encoding='UTF-8', standalone=True)
parts['word/comments.xml'] = ET.tostring(comments, xml_declaration=True, encoding='UTF-8', standalone=True)
if OUTPUT.exists():
    assert (ROOT / 'work/revision_132_audit.json').exists(), 'Review existing output before replacing it.'
with ZipFile(OUTPUT, 'w') as archive:
    for entry in entries:
        archive.writestr(entry, parts[entry.filename])

assert sha256(SOURCE.read_bytes()).hexdigest() == source_hash
for index, paragraph in enumerate(paragraphs):
    changed = next((change for change in changes if change['paragraph'] == index), None)
    assert text(paragraph) == (changed['after'] if changed else baseline[index])
ids = sorted(comments.xpath('w:comment/@w:id', namespaces=NS))
for element in ('commentRangeStart', 'commentRangeEnd', 'commentReference'):
    assert ids == sorted(document.xpath(f'//w:{element}/@w:id', namespaces=NS))
for index in range(215, 221):
    assert text(paragraphs[index]) == baseline[index]
assert text(paragraphs[185]) == baseline[185]
assert len(document.xpath('//w:drawing', namespaces=NS)) == 0
with ZipFile(OUTPUT) as archive:
    for name in archive.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            ET.fromstring(archive.read(name))
(ROOT / 'work/revision_132_audit.json').write_text(json.dumps({
    'source_sha256': source_hash, 'changes': changes, 'new_comment_count': len(changes) + 1,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(OUTPUT), 'changed_paragraphs': len(changes),
                  'new_comments': len(changes) + 1, 'total_comments': len(comments),
                  'near_field_metrics_verified': True, 'source_preserved': True}, ensure_ascii=False))
