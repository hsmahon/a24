#!/usr/bin/env python3
"""Download publicly returned HLS sources using curl, then remux local files."""
import json,re,hashlib,subprocess,argparse,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin
from harvest import ROOT,D,MEDIA,dump,config
H=D/'staging'/'hls'
def identity(url):return hashlib.sha256(url.encode()).hexdigest()
def attrs(line):return dict((k,v.strip('"')) for k,v in re.findall(r'([\w-]+)=("[^"]*"|[^,]*)',line.partition(':')[2]))
def masters():
 jobs=[];selected=[]
 for p in sorted((D/'playback').glob('*.json')):
  s=json.loads(p.read_text());sources=s.get('sources',[])
  src=next((x['src'] for x in sources if x.get('type')=='application/x-mpegURL' and x.get('src','').startswith('https:') and '/v1/' in x['src']),None)
  if src:
   selected.append({'id':p.stem,'url':src,'name':s.get('name'),'duration':s.get('duration')});jobs.append((src,H/p.stem/'master.m3u8'))
 dump(H/'selected.json',selected);config('masters',jobs)
def variants():
 jobs=[];selected=[];errors=[]
 for v in json.loads((H/'selected.json').read_text()):
  p=H/v['id']/'master.m3u8'
  try:
   lines=p.read_text().splitlines();candidates=[];audio=[]
   for i,line in enumerate(lines):
    if line.startswith('#EXT-X-STREAM-INF:'):
     a=attrs(line);a['url']=urljoin(v['url'],lines[i+1]);candidates.append(a)
    if line.startswith('#EXT-X-MEDIA:'):audio.append(attrs(line))
   best=max(candidates,key=lambda x:int(x.get('BANDWIDTH',0)))
   tracks=[{'kind':'video','url':best['url']}]
   audios=[a for a in audio if a.get('TYPE')=='AUDIO' and a.get('GROUP-ID')==best.get('AUDIO') and a.get('URI')]
   if audios:
    a=next((a for a in audios if a.get('DEFAULT')=='YES'),audios[0]);tracks.append({'kind':'audio','url':urljoin(v['url'],a['URI'])})
   v.update({'resolution':best.get('RESOLUTION'),'bandwidth':best.get('BANDWIDTH'),'tracks':tracks});selected.append(v)
   for t in tracks:jobs.append((t['url'],H/v['id']/(t['kind']+'.remote.m3u8')))
  except Exception as e:errors.append({'id':v['id'],'error':str(e)})
 dump(H/'tracks.json',selected);dump(H/'master-errors.json',errors);config('variants',jobs)
def segments():
 jobs={};errors=[];total=0
 for v in json.loads((H/'tracks.json').read_text()):
  folder=H/v['id']
  for t in v['tracks']:
   try:
    src=folder/(t['kind']+'.remote.m3u8');lines=src.read_text().splitlines();out=[]
    if '#EXT-X-ENDLIST' not in lines:raise ValueError('not a complete VOD playlist')
    def local(uri):
     url=urljoin(t['url'],uri);name=identity(url)+'.bin';dest=folder/name
     if not dest.exists() or not dest.stat().st_size:jobs[url]=dest
     return name
    for line in lines:
     if line and not line.startswith('#'):line=local(line);total+=1
     elif 'URI="' in line:line=re.sub(r'URI="([^"]+)"',lambda m:'URI="'+local(m[1])+'"',line)
     out.append(line)
    (folder/(t['kind']+'.m3u8')).write_text('\n'.join(out)+'\n')
   except Exception as e:errors.append({'id':v['id'],'track':t['kind'],'error':str(e)})
 config('segments',list(jobs.items()));dump(H/'segment-errors.json',errors);print('segments',total,'errors',len(errors))
def remux():
 vids={v['id']:v for v in json.loads((D/'videos.json').read_text())};dest=MEDIA;dest.mkdir(exist_ok=True)
 def run(v):
  folder=H/v['id'];out=dest/(re.sub('[^a-zA-Z0-9._-]+','-',vids.get(v['id'],{}).get('slug') or v['name']).strip('-')+'--'+v['id']+'.mp4')
  if out.exists() and out.stat().st_size:return {'id':v['id'],'status':'exists','path':str(out.relative_to(MEDIA))}
  args=['ffmpeg','-v','error','-nostdin','-y']
  for t in v['tracks']:args+=['-protocol_whitelist','file,crypto,data','-allowed_extensions','ALL','-i',str(folder/(t['kind']+'.m3u8'))]
  if len(v['tracks'])>1:args+=['-map','0:v:0','-map','1:a:0']
  tmp=H/v['id']/(out.stem+'.partial.mp4');args+=['-c','copy','-movflags','+faststart',str(tmp)]
  try:
   r=subprocess.run(args,capture_output=True,text=True,timeout=600)
   if r.returncode:raise RuntimeError(r.stderr[-1500:])
   probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(tmp)],capture_output=True,text=True,check=True)
   duration=float(json.loads(probe.stdout)['format']['duration']);expected=(v.get('duration') or 0)/1000
   if expected and abs(duration-expected)>max(3,expected*.01):raise ValueError(f'duration {duration} != expected {expected}')
   tmp.rename(out);return {'id':v['id'],'status':'downloaded','path':str(out.relative_to(MEDIA)),'duration':duration,'bytes':out.stat().st_size}
  except Exception as e:return {'id':v['id'],'status':'failed','error':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,json.loads((H/'tracks.json').read_text())))
 dump(D/'download-results.json',results);print('remux',len(results),'failed',sum(r['status']=='failed' for r in results))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['masters','variants','segments','remux']);a=p.parse_args();globals()[a.stage]()
