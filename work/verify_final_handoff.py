from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile
import json

import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from pypdf import PdfReader
from lxml import etree as ET


ROOT=Path(r'C:\Users\wangjianing\Desktop\SRDP')
WORK=ROOT/'work/final_review'
for name in ('proposal','guide'):
    folder=WORK/name
    folder.mkdir(exist_ok=True)
    document=pdfium.PdfDocument(str(WORK/f'{name}.pdf'))
    reader=PdfReader(WORK/f'{name}.pdf')
    for index in range(len(document)):
        document[index].render(scale=1.4).to_pil().save(folder/f'page-{index+1}.png')
    for start in range(0,len(document),4):
        sheet=Image.new('RGB',(1200,1760),'#dddddd')
        draw=ImageDraw.Draw(sheet)
        for offset in range(4):
            if start+offset>=len(document):
                break
            image=Image.open(folder/f'page-{start+offset+1}.png')
            image.thumbnail((580,840))
            x=(offset%2)*600+10
            y=(offset//2)*880+30
            sheet.paste(image,(x,y))
            draw.text((x,y-20),str(start+offset+1),fill='black')
        sheet.save(folder/f'sheet-{start//4+1}.png')
    print(name,'pages',len(document))
    print('Page characters',[len(page.extract_text()) for page in reader.pages])
    if name=='proposal':
        print('Figure pages',[(i+1,[f'图 {n}' for n in range(1,5) if f'图 {n}' in page.extract_text()]) for i,page in enumerate(reader.pages) if any(f'图 {n}' in page.extract_text() for n in range(1,5))])

audit=json.loads((WORK/'update_audit.json').read_text(encoding='utf-8'))
for path,digest in audit['source_hashes'].items():
    assert sha256(Path(path).read_bytes()).hexdigest()==digest,path
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(ROOT/'申报书与材料/交互笔项目_内部实现步骤beta1.2.docx') as archive:
    doc=ET.fromstring(archive.read('word/document.xml'))
    guide=''.join(doc.xpath('//w:t/text()',namespaces=ns))
    assert 'word/comments.xml' not in archive.namelist()
    assert not doc.xpath('//w:ins|//w:del|//w:strike',namespaces=ns)
    assert not doc.xpath('//w:color[@w:val="0000FF"]',namespaces=ns)
readme=(ROOT/'READMEbeta1.1.md').read_text(encoding='utf-8')
for word in ('SIMO-LS-20H','4500','120','50','20','40','90','100','固定键','透明','后期'):
    assert word in guide and word in readme,word
for rule in ('防御性写作','蓝字正文','内部实现步骤采用干净版本','避免重复询问','三项并列'):
    assert rule in readme,rule
print('Verified source preservation, clean Word guide, synchronized key facts, and handoff preferences')
