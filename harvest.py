#!/usr/bin/env python3
"""Reproducible A24 public-catalog inventory and curl batch preparation."""
import argparse, json, re, hashlib, shutil, os
from pathlib import Path
from urllib.parse import urlsplit, urljoin
ROOT=Path(__file__).resolve().parent
D=ROOT/'data'
MEDIA=Path(os.environ.get('A24_OUTPUT_DIR', Path.home() / 'Media' / 'a24')).expanduser().resolve()
def dump(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2)+'\n')
def config(name,jobs,headers=None):
 jobs=[(url,out) for url,out in jobs if os.environ.get('A24_REFRESH')=='1' or not out.exists() or out.stat().st_size==0]
 p=D/(name+'.curl');lines=['parallel','parallel-max = 4','location','fail','silent','show-error','retry = 2','max-time = 120','connect-timeout = 20']
 for h in headers or []:lines.append('header = '+json.dumps(h))
 for url,out in jobs:
  out.parent.mkdir(parents=True,exist_ok=True)
  lines.extend(['url = '+json.dumps(url),'output = '+json.dumps(str(out))])
 p.write_text('\n'.join(lines)+'\n');print(name,len(jobs),str(p))
def catalog():
 titles=[]
 for p in sorted((D/'catalog').glob('*.json')):titles.extend(json.loads(p.read_text())['results'])
 unique={(t['title_type'],t['slug']):t for t in titles};titles=list(unique.values());dump(D/'titles.json',titles)
 jobs=[]
 for t in titles:
  slug=t['slug'];typ='films' if t['title_type']=='film' else 'television'
  jobs.extend([('https://a24films.com/'+typ+'/'+slug,D/'pages'/(slug+'.html')),('https://api.a24films.com/api/web/v1/titles/'+slug+'/associated/',D/'associated'/(slug+'.json'))])
 config('catalog-details',jobs)
def objects(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from objects(v)
 elif isinstance(x,list):
  for v in x:yield from objects(v)
def inventory():
 videos={};assets={};errors=[]
 for t in json.loads((D/'titles.json').read_text()):
  slug=t['slug'];objs=[t]
  try:objs.append(json.loads((D/'associated'/(slug+'.json')).read_text()))
  except Exception as e:errors.append({'slug':slug,'stage':'associated','error':str(e)})
  try:
   html=(D/'pages'/(slug+'.html')).read_text()
   rsc=''.join(json.loads(m) for m in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)',html))
   # RSC rows contain JSON payloads after a hexadecimal reference and colon.
   decoder=json.JSONDecoder()
   for m in re.finditer(r'(?:^|\n)[\w,:]+:',rsc):
    try:obj,_=decoder.raw_decode(rsc,m.end());objs.append(obj)
    except (ValueError,TypeError):pass
  except Exception as e:errors.append({'slug':slug,'stage':'page','error':str(e)})
  for o in objects(objs):
   v=o.get('video')
   if isinstance(v,dict) and v.get('brightcove_id'):
    key=str(v.get('brightcove_id') or 'youtube-'+v['youtube_id'])
    entry=videos.setdefault(key,{'id':key,'name':o.get('display_name') or o.get('name'),'slug':o.get('slug'),'content_type':o.get('content_type'),'is_member_content':o.get('is_member_content'),'video':v,'titles':[]})
    if slug not in entry['titles']:entry['titles'].append(slug)
   for val in o.values():
    if isinstance(val,str) and val.startswith('https://api-asset-production.s3.amazonaws.com/'):
     assets.setdefault(val,set()).add(slug)
 dump(D/'videos.json',list(videos.values()));dump(D/'assets.json',[{'url':u,'titles':sorted(t)} for u,t in sorted(assets.items())]);dump(D/'inventory-errors.json',errors)
 key=re.search(r'policyKey:"(BCpk[^"]+)"',(D/'player.js').read_text())[1]
 config('playback',[('https://edge.api.brightcove.com/playback/v1/accounts/6276845754001/videos/'+v,D/'playback'/(v+'.json')) for v in videos if not v.startswith('youtube-')],['Accept: application/json;pk='+key])
 # Artwork references are retained as evidence; image downloads are excluded by user request.
 print('videos',len(videos),'assets',len(assets),'errors',len(errors))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['catalog','inventory']);a=p.parse_args();globals()[a.stage]()
