"""Annotate the exact Blender UV0 export; never move/rescale/repack islands."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

out=Path(sys.argv[1]); data=json.loads((out/'surface_mapping.json').read_text()); size=2048
colors=['#d8b58d','#82acc9','#a8c295','#c5a0bb','#cabd79','#94c5c4','#c89b87','#9ca3d4','#b9c58c','#9fc4da','#d1b4ca','#d1c1a8']
groups=list(data['regions']); palette={g:colors[i%len(colors)] for i,g in enumerate(groups)}
native=Image.new('RGBA',(size,size),(0,0,0,0));nd=ImageDraw.Draw(native)
for node in ET.parse(out/'uv_layout.svg').getroot().iter():
    if node.tag.endswith('polygon'):
        coords=[tuple(map(float,p.split(','))) for p in node.attrib['points'].strip().split()]
        nd.line(coords+[coords[0]],fill=(12,18,24,255),width=1)
native.save(out/'uv_layout.png')
im=Image.new('RGBA',(size,size),(30,38,48,255));d=ImageDraw.Draw(im)
def portable_font(size):
    for name in ('DejaVuSans.ttf','arial.ttf'):
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default()
font=portable_font(20);small=portable_font(11)
for f in data['surfaces']:
    pts=[(u*size,(1-v)*size) for u,v in f['uv']]
    d.polygon(pts,fill=palette[f['region']])
    xs=[p[0] for p in pts];ys=[p[1] for p in pts]
    if max(xs)-min(xs)>40 and max(ys)-min(ys)>20:
        x=sum(xs)/len(xs);y=sum(ys)/len(ys)
        d.text((x,y),f['id'],font=small,fill=(18,27,34),anchor='mm')
# Native Blender linework is the final overlay, pixel-for-pixel with clean PNG.
native=Image.open(out/'uv_layout.png').convert('RGBA');im=Image.alpha_composite(im,native)
d=ImageDraw.Draw(im)
for group,r in data['regions'].items():
    x=r['x']*size;y=(1-r['y']-r['h'])*size
    label=group
    bounds=d.textbbox((x,y),label,font=font)
    d.rectangle((bounds[0]-2,bounds[1]-2,bounds[2]+2,bounds[3]+2),fill=(20,28,36,245))
    d.text((x,y),label,font=font,fill=(255,255,255))
im.save(out/'uv_guide.png')
