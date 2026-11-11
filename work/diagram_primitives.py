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
        if fill is not None:
            self.pdf.setFillColor(HexColor(fill))
        self.pdf.setLineWidth(width)
        self.pdf.circle(x, self.height-y, radius, stroke=1, fill=int(fill is not None))
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill or "none"}" stroke="{color}" stroke-width="{width}"/>')

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

