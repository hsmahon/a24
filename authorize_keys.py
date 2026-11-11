"""Obtain ordinary A24 playback authorizations and save returned HLS keys.
Tokens are short-lived; run each prepare/download/keys/download batch in order.
"""
import json,re,sys
from pathlib import Path
from harvest import ROOT,D,dump
from streams import H,identity
size=20
tracks=json.loads((H/'tracks.json').read_text());videos={v['id']:v for v in json.loads((D/'videos.json').read_text())}
stage=sys.argv[1];batch=int(sys.argv[2]);items=tracks[batch*size:(batch+1)*size]
if stage=='prepare':
 lines=['rate = "1/s"'];count=0
 for v in items:
  paths=[]
  for t in v['tracks']:
   s=(H/v['id']/(t['kind']+'.remote.m3u8')).read_text()
   for u in re.findall(r'#EXT-X-KEY:.*?URI="([^"]+)"',s):
    path=H/v['id']/(identity(u)+'.bin')
    if not path.exists() or path.stat().st_size!=16:paths.append(u)
  if not paths:continue
  out=D/'tokens'/(v['id']+'.json');out.parent.mkdir(exist_ok=True)
  if count:lines+=['next']
  lines+=['silent','show-error','location','max-time = 30','header = "Content-Type: application/json"','data = '+json.dumps(json.dumps({'supplemental_video_content_slug':videos[v['id']]['slug']})),'url = "https://api.a24films.com/api/web/v1/playback-token/"','output = '+json.dumps(str(out))];count+=1
 (D/'tokens.curl').write_text('\n'.join(lines)+'\n');print('batch',batch,'token requests',count,'batches',(len(tracks)+size-1)//size)
elif stage=='keys':
 lines=['parallel','parallel-max = 4'];count=0;errors=[]
 for v in items:
  tokenfile=D/'tokens'/(v['id']+'.json')
  if not tokenfile.exists():continue
  tok=json.loads(tokenfile.read_text()).get('jwt')
  if not tok:errors.append({'id':v['id'],'response':json.loads(tokenfile.read_text())});continue
  urls=set()
  for t in v['tracks']:
   s=(H/v['id']/(t['kind']+'.remote.m3u8')).read_text();urls.update(re.findall(r'#EXT-X-KEY:.*?URI="([^"]+)"',s))
  for u in urls:
   out=H/v['id']/(identity(u)+'.bin')
   if out.exists() and out.stat().st_size==16:continue
   if count:lines+=['next']
   lines+=['silent','show-error','fail','location','max-time = 30','header = '+json.dumps('BCOV-Auth: '+tok),'url = '+json.dumps(u),'output = '+json.dumps(str(out))];count+=1
 (D/'keys.curl').write_text('\n'.join(lines)+'\n');dump(D/'tokens'/('errors-'+str(batch)+'.json'),errors);print('batch',batch,'key requests',count,'token errors',len(errors))
