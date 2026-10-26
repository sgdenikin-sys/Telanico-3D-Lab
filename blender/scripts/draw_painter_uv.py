"""Rasterize saved Blender UV coordinates; clean/guide/checker never repack."""
from pathlib import Path
import colorsys,csv,json,math,sys,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont

out=Path(sys.argv[1]);data=json.loads((out/'surface_mapping.json').read_text())
def font(n):
    for name in ('DejaVuSans.ttf','arial.ttf'):
        try:return ImageFont.truetype(name,n)
        except OSError:pass
    return ImageFont.load_default()
def area(p):return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1])))/2
rows=[]
for sheet,size in data['sheets'].items():
    name=sheet.lower();charts=[c for c in data['charts'] if c['sheet']==sheet]
    wire=Image.new('RGBA',(size,size),(0,0,0,0));wd=ImageDraw.Draw(wire)
    for node in ET.parse(out/(name+'_native.svg')).getroot().iter():
        if node.tag.endswith('polygon'):
            p=[tuple(map(float,v.split(','))) for v in node.attrib['points'].strip().split()]
            wd.line(p+[p[0]],fill=(30,35,40,255),width=1)
    wire.save(out/(name+'_wire.png'))
    clean=Image.new('RGBA',(size,size),(0,0,0,0));cd=ImageDraw.Draw(clean)
    guide=Image.new('RGBA',(size,size),(244,244,240,255));gd=ImageDraw.Draw(guide)
    checker=guide.copy();xd=ImageDraw.Draw(checker)
    grid=Image.new('RGBA',(size,size));gg=ImageDraw.Draw(grid);cell=32 if size==2048 else 16
    for y in range(0,size,cell):
        for x in range(0,size,cell):gg.rectangle((x,y,x+cell-1,y+cell-1),fill=(255,255,255,255) if (x//cell+y//cell)%2 else (135,135,135,255))
    for k,c in enumerate(charts):
        rgb=tuple(round(x*255) for x in colorsys.hsv_to_rgb((k*.61803398875)%1,.30,.91))
        mask=Image.new('L',(size,size));md=ImageDraw.Draw(mask);edges={};pixel_faces=[]
        for f in c['faces']:
            p=[(u*size,(1-v)*size) for u,v in f['uv']];pixel_faces.append(p)
            gd.polygon(p,fill=(*rgb,255));md.polygon(p,fill=255)
            for a,b in zip(f['uv'],f['uv'][1:]+f['uv'][:1]):
                ka,kb=(tuple(round(x,6) for x in p) for p in (a,b));key=tuple(sorted((ka,kb)))
                count,_,_=edges.get(key,(0,a,b));edges[key]=(count+1,a,b)
            rows.append([sheet,c['id'],c['label'],f['object'],f['face'],f.get('facing','')])
        tint=Image.new('RGBA',(size,size),(*rgb,255))
        from PIL import ImageChops
        pattern=ImageChops.multiply(tint,grid);checker.paste(pattern,(0,0),mask)
        for count,a,b in edges.values():
            if count==1:
                p=[(u*size,(1-v)*size) for u,v in (a,b)]
                cd.line(p,fill=(28,35,42,255),width=1)
        p=max(pixel_faces,key=area);xs=[v[0] for v in p];ys=[v[1] for v in p]
        cx,cy=sum(xs)/len(xs),sum(ys)/len(ys)
        text=c['id'];fs=18 if size==2048 else 12
        if max(xs)-min(xs)>fs*3 and max(ys)-min(ys)>fs:
            xd.text((cx,cy),text,font=font(fs),anchor='mm',fill=(10,15,20),stroke_width=1,stroke_fill=(255,255,255))
        # Label whole charts, not individual polygons: a hull strip or canopy
        # may be large even though every constituent quad is narrow. Chart
        # bounds are disjoint, so labels in an annulus' hole remain unambiguous.
        allpts=[p for face in pixel_faces for p in face]
        xx=[p[0] for p in allpts];yy=[p[1] for p in allpts]
        x=(min(xx)+max(xx))/2;y=(min(yy)+max(yy))/2
        if max(xx)-min(xx)>fs*2 and max(yy)-min(yy)>fs:
            gd.text((x,y),c['id'],font=font(fs),anchor='mm',fill=(10,15,20),stroke_width=1,stroke_fill=(255,255,255))
            if sheet=='MAIN' and max(xx)-min(xx)>150 and max(yy)-min(yy)>60:
                label=c['label'].replace('_',' ').upper()
                if 'ROOF GORE' in label:label='ROOF GORE '+label.split('ROOF GORE')[-1].split()[0]
                elif 'HULL ' in label:label=label.split(' / ')[-1]
                else:label=label.replace('FOUNDATION OCTAGONAL STONE','FOUNDATION').replace('HALL WALKABLE FLOOR','HALL FLOOR').replace(' / NET','')
                gd.text((x,y+23),label[:31],font=font(15),anchor='mm',fill=(10,15,20),stroke_width=1,stroke_fill=(255,255,255))
    # The exact same boundary PNG is overlaid last on both diagnostic variants.
    Image.alpha_composite(guide,clean).save(out/(name+'_guide.png'))
    Image.alpha_composite(checker,clean).save(out/(name+'_checker.png'))
    clean.save(out/(name+'_layout.png'))
    Image.new('RGBA',(size,size),(255,255,255,255)).save(out/(name+'_paint.png'))
    line=30;columns=2;count=math.ceil(len(charts)/columns)
    key=Image.new('RGB',(2048,max(2048,count*line+120)),(248,248,245));kd=ImageDraw.Draw(key)
    kd.text((30,20),data['asset']+' / '+sheet+' / CHART KEY',font=font(28),fill=(25,30,35))
    for i,c in enumerate(charts):
        col=i//count;row=i%count
        label=c['id']+'  '+c['label']
        kd.text((30+col*1024,90+row*line),label[:85],font=font(18),fill=(25,30,35))
    key.save(out/(name+'_key.png'))
with (out/'surface_mapping.csv').open('w',newline='',encoding='utf-8-sig') as file:
    w=csv.writer(file);w.writerow(['atlas','chart_id','surface_label','blender_object','polygon_index','face_direction']);w.writerows(rows)
