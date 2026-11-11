from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json

from lxml import etree as ET


ROOT = Path(r'C:\Users\wangjianing\Desktop\SRDP')
SOURCE = ROOT / '申报书与材料/申报书beta1.3.2.docx'
OUTPUT = ROOT / '申报书与材料/申报书beta1.3.3.docx'
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
    body.append(run('1.3.3 修订。' + message, properties, blue=True))


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


edit(133, [('以笔杆或套环尺寸为参考', '以笔身前端检测段的尺寸为参考')],
     '候选目标的尺寸筛选改以笔身前端检测段为基准。')
edit(135, [('笔尖与检测套环做成可更换件。', '笔尖与前端笔壳做成可更换件，便于调整接触手感及检测段尺寸。')],
     '采用可更换笔尖及前端笔壳样件，便于在整笔结构内比较检测段尺寸和接触手感。')
edit(137, [(baseline[137],
            '以笔身前端作为雷达检测段，检测段与笔壳一体设计，保持与笔轴同轴的规则圆柱外形。笔尖在前端短距离伸出，受压时相对笔壳轴向滑动并触发内部微动开关。握持区及按键布置在检测段后方，通过握持凹槽或轻微台阶引导手指位置，保持检测段可见。根据扫描高度和握笔姿势确定检测段长度及其距笔尖的位置。首版尝试采用浅色、哑光、不透明塑料，制作不同直径和表面材料的前端笔壳样件。比较各样件的回波点数、有效跟踪帧占比及跟踪中断次数，并测量检测位置与笔尖标记之间的偏差。笔身前端检测段、复位结构、开关与扫描面的位置关系见图 1。')],
     '采用用户确定的笔身前端检测方案。检测段融入笔壳，笔尖保留短距离外露及压动触发结构，握持区后移。规则圆柱作为首版检测截面，便于从表面回波估计笔轴位置。')
edit(142, [('同时试验可拆卸检测套环，测量套环检测位置与笔尖之间的偏差。',
            '同时比较笔身前端检测段的尺寸与握持位置，测量检测位置与真实笔尖之间的偏差。')],
     '稳定性实验同步改为检测段尺寸和握持位置对照，继续评估检测位置到笔尖的偏差。')
edit(173, [('结合光斑覆盖和套环表面回波分析中心估计偏差',
            '结合光斑覆盖和笔身前端表面回波分析笔轴中心估计偏差')],
     '将误差分析对象改为笔身前端表面回波，明确估计目标为笔轴中心。')
edit(174, [('笔尖位置估计结合套环尺寸和可见表面回波',
            '笔尖位置估计结合笔身前端检测段的截面尺寸和可见表面回波')],
     '笔尖估计依据笔身前端的已知截面与表面回波开展结构标定，继续估计笔轴位置并进行姿态修正。')
edit(181, [('每帧落在套环上的点数', '每帧落在笔身前端检测段上的点数')],
     '不同帧率下的回波统计对象统一为笔身前端检测段。')
edit(237, [(baseline[237],
            '笔身前端的检测结构与笔尖定位。将雷达检测段融入笔身前端，通过规则截面和后移的握持区组织笔端结构，比较不同直径、表面材料及握持位置下的有效跟踪帧占比、跟踪中断次数与定位偏差；再用固定笔尖、改变倾角的实验测量倾斜造成的偏差量级，把结构控制与姿态补偿分开评估。')],
     '创新点与整笔结构统一，重点比较检测截面和握持位置对跟踪及定位的影响。')
replace_comment(paragraphs[139], '图 1 按笔身前端检测方案绘制，标出固定笔壳、短外露笔尖、微动开关及复位结构。扫描面穿过笔身前端检测段，握持区与按键位于其后方。图片留待用户后续调整和插入。')

parts['word/document.xml'] = ET.tostring(document, xml_declaration=True, encoding='UTF-8', standalone=True)
parts['word/comments.xml'] = ET.tostring(comments, xml_declaration=True, encoding='UTF-8', standalone=True)
assert not OUTPUT.exists(), 'Destination already exists.'
with ZipFile(OUTPUT, 'w') as archive:
    for entry in entries:
        archive.writestr(entry, parts[entry.filename])

assert sha256(SOURCE.read_bytes()).hexdigest() == source_hash
assert '套环' not in ''.join(document.xpath('//w:t/text()', namespaces=NS))
assert '套环' not in ''.join(comments.xpath('//w:t/text()', namespaces=NS))
assert len(changes) == 8
for index, paragraph in enumerate(paragraphs):
    changed = next((change for change in changes if change['paragraph'] == index), None)
    assert text(paragraph) == (changed['after'] if changed else baseline[index])
    if changed:
        assert paragraph.xpath('./w:r/w:rPr/w:color[@w:val="0000FF"]', namespaces=NS)
ids = sorted(comments.xpath('w:comment/@w:id', namespaces=NS))
for element in ('commentRangeStart', 'commentRangeEnd', 'commentReference'):
    assert ids == sorted(document.xpath(f'//w:{element}/@w:id', namespaces=NS))
with ZipFile(OUTPUT) as archive:
    for name in archive.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            ET.fromstring(archive.read(name))
(ROOT / 'work/revision_133_audit.json').write_text(json.dumps({
    'source_sha256': source_hash, 'changes': changes, 'new_comments': 9,
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(OUTPUT), 'changed_paragraphs': len(changes),
                  'new_comments': 9, 'total_comments': len(comments),
                  'source_preserved': True}, ensure_ascii=False))
