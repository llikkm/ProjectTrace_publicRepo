import json
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pypdfium2 as pdfium
from lxml import etree as ET
from pypdf import PdfReader

root = Path(r'C:\Users\wangjianing\Desktop\SRDP')
folder = root / 'work/render_131'
pdf = pdfium.PdfDocument(str(folder / 'review.pdf'))
for i in range(len(pdf)):
    pdf[i].render(scale=1.4).to_pil().save(folder / f'page-{i+1}.png')
reader = PdfReader(folder / 'review.pdf')
print('P9_END', reader.pages[8].extract_text()[-200:])
print('P10_START', reader.pages[9].extract_text()[:200])
audit = json.loads((root / 'work/revision_131_audit.json').read_text(encoding='utf-8'))
assert sha256((root / '申报书与材料/申报书beta1.3.docx').read_bytes()).hexdigest() == audit['source_sha256']
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(root / '申报书与材料/申报书beta1.3.1.docx') as archive:
    document = ET.fromstring(archive.read('word/document.xml'))
    comments = ET.fromstring(archive.read('word/comments.xml'))
ids = sorted(comments.xpath('w:comment/@w:id', namespaces=ns))
for element in ('commentRangeStart', 'commentRangeEnd', 'commentReference'):
    assert ids == sorted(document.xpath(f'//w:{element}/@w:id', namespaces=ns))
assert len(ids) == 30
for comment in comments:
    assert comment.xpath('.//w:color[@w:val="0000FF"]', namespaces=ns)
print('Verified source preservation, 30 blue comments and anchors, and', len(pdf), 'rendered pages')
