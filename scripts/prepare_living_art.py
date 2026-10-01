"""Offline crop/resize/export only; generation uses the built-in image tool."""
import json
from io import BytesIO
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'generated_images'
OUT=ROOT/'assets/living'
SOURCES={
 'hero':'exec-94044eed-bcbc-4400-ac51-ba333832d237.png',
 'entry':'exec-582a887b-b7b5-4a8a-bdff-67eb7184c889.png',
 'category':'exec-d6d07e7d-efd3-4b4e-b331-acfcfb482686.png',
 'ages':'exec-82d961be-203d-418e-9760-bcdf3b0d614a.png',
 'sizes':'exec-9b7c7e70-b9a4-4295-b3fc-226dadf02240.png',
 'play':'exec-89be205f-43d7-41f6-a101-fe145a276e8a.png',
}
def main():
 OUT.mkdir(parents=True,exist_ok=True);records=[]
 def export(key,name,box=None,size=(320,240),crop=False):
  original=Image.open(SOURCE/SOURCES[key]);im=original.crop(box) if box else original.copy()
  if crop:
   # Natural alternate header framing, not a duplicate of the category tile.
   im=im.crop((int(im.width*.07),int(im.height*.14),int(im.width*.96),int(im.height*.96)))
  if key!='hero':
   canvas=Image.new('RGBA',(max(im.width,round(im.height*4/3)),max(im.height,round(im.width*3/4))),(0,0,0,0))
   canvas.paste(im,((canvas.width-im.width)//2,(canvas.height-im.height)//2));im=canvas
  im=im.resize(size,Image.Resampling.LANCZOS)
  buffer=BytesIO();im.save(buffer,'WEBP',quality=86,method=4,exact=True)
  dest=OUT/(name+'.webp');temp=dest.with_suffix('.webp.tmp');temp.write_bytes(buffer.getvalue());temp.replace(dest)
  with Image.open(dest) as verified:verified.load();assert verified.size==size
  records.append({'file':dest.name,'width':size[0],'height':size[1],'bytes':dest.stat().st_size,'master':SOURCES[key],'crop':box,'header_crop':crop})
 export('hero','home',size=(1200,800))
 for i,name in enumerate(['entry-dog','entry-cat']):export('entry',name,(i*887,0,(i+1)*887,887))
 boxes=[(0,0,460,450),(460,0,888,450),(888,0,1335,450),(1335,0,1774,450),(0,450,462,887),(462,450,888,887),(888,450,1335,887)]
 names=['dog-food','cat-food','sheets','litter','system','dog-toys','cat-toys']
 for name,box in zip(names,boxes):
  export('category',name,box)
  if name in ['sheets','litter','system']:export('category','header-'+name,box,crop=True)
 for i,name in enumerate(['dog-young','dog-adult','dog-senior','cat-young','cat-adult','cat-senior']):
  x=i%3*512;y=0 if i<3 else 490;bottom=490 if i<3 else 1024;export('ages',name,(x,y,x+512,bottom))
 for name,box in zip(['size-small','size-medium','size-large'],[(0,0,530,887),(530,0,1070,887),(1070,0,1774,887)]):export('sizes',name,box)
 for name,box in zip(['chew','chase','together','puzzle','teaser','hide'],[(0,0,500,500),(505,0,955,450),(960,0,1536,485),(0,505,503,965),(505,505,950,1024),(955,490,1536,1024)]):
  export('play','play-'+name,box)
 (OUT/'manifest.json').write_text(json.dumps({'version':'pet-living-2','mode':'built-in-imagegen','assets':records},ensure_ascii=False,indent=2))
 print(f'{len(records)} assets, {sum(r["bytes"] for r in records):,} bytes')
if __name__=='__main__':main()
