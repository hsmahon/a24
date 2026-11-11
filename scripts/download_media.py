#!/usr/bin/env python3
"""Resume catalog-linked media downloads through A24's ordinary playback flow."""
import argparse,concurrent.futures,json,re,threading,time,urllib.request,urllib.parse,subprocess,os
from pathlib import Path
from harvest import D,MEDIA,dump

lock=threading.Lock();rate_lock=threading.Lock();last_token=0
STATUS=D/'download-status.json'

def fetch(url,body=None,headers=None):
 data=json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(url,data=data,headers=headers or {})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read()
def api_token(slug):
 global last_token
 with rate_lock:
  time.sleep(max(0,1.1-(time.monotonic()-last_token)));last_token=time.monotonic()
  return json.loads(fetch('https://api.a24films.com/api/web/v1/playback-token/',{'supplemental_video_content_slug':slug},{'Content-Type':'application/json'}))['jwt']
def save(results):
 with lock:
  tmp=STATUS.with_suffix('.tmp');tmp.write_text(json.dumps(results,indent=2)+'\n');tmp.replace(STATUS)
def name(v):return re.sub('[^a-zA-Z0-9._-]+','-',v.get('slug') or v['name']).strip('-')+'--'+v['id']
def verify(out,expected):
 r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-show_entries','stream=codec_type','-of','json',str(out)],capture_output=True,text=True,check=True)
 p=json.loads(r.stdout);duration=float(p['format']['duration'])
 if expected and abs(duration-expected)>max(3,expected*.01):raise ValueError('duration does not match metadata')
 if not any(s['codec_type']=='video' for s in p['streams']):raise ValueError('no video stream')
 return duration

def download(v):
 out=MEDIA/(name(v)+'.mp4');out.parent.mkdir(parents=True,exist_ok=True)
 folder=D/'staging'/'downloads'/v['id']
 policy=re.search(r'policyKey:"(BCpk[^"]+)"',(D/'player.js').read_text())[1]
 metadata=json.loads(fetch('https://edge.api.brightcove.com/playback/v1/accounts/6276845754001/videos/'+v['id'],headers={'Accept':'application/json;pk='+policy}))
 # Brightcove describes the actual current asset. Catalog durations may be stale.
 expected=(metadata.get('duration') or 0)/1000 or v['video'].get('duration_in_seconds')
 if out.exists():
  duration=verify(out,expected);return {'status':'complete','path':str(out),'bytes':out.stat().st_size,'duration':duration}
 tmp=folder/(out.stem+'.partial.mp4')
 if tmp.exists():
  try:duration=verify(tmp,expected)
  except (ValueError,subprocess.CalledProcessError,KeyError):pass
  else:
   # Verify every audio/video packet decodes before recovering an earlier transfer.
   with (folder/'recovery-decode.log').open('w') as log:
    decoded=subprocess.run(['ffmpeg','-nostdin','-v','error','-xerror','-i',str(tmp),'-map','0:v:0','-map','0:a:0?','-f','null','-'],stdout=log,stderr=log,timeout=1800)
   if decoded.returncode:raise ValueError('Recovered file failed full decode; see recovery-decode.log')
   tmp.rename(out)
   return {'status':'complete','path':str(out),'bytes':out.stat().st_size,'duration':duration}
 candidates=[x for x in metadata.get('sources',[]) if x.get('type')=='application/x-mpegURL' and x.get('src','').startswith('https:') and not x.get('key_systems')]
 if not candidates:raise ValueError('Only DRM-protected sources are returned by the playback API; a downloadable non-DRM rendition or source export is required.')
 master=next((x['src'] for x in candidates if '/v1/' in x['src']),candidates[0]['src'])
 token=api_token(v['slug'])
 from streams import attrs
 body=fetch(master).decode();lines=body.splitlines();variants=[];audios=[]
 for i,line in enumerate(lines):
  if line.startswith('#EXT-X-STREAM-INF:'):
   a=attrs(line);a['url']=urllib.parse.urljoin(master,lines[i+1]);variants.append(a)
  elif line.startswith('#EXT-X-MEDIA:'):audios.append(attrs(line))
 best=max(variants,key=lambda a:int(a.get('BANDWIDTH',0)));urls=[best['url']]
 matching=[a for a in audios if a.get('TYPE')=='AUDIO' and a.get('GROUP-ID')==best.get('AUDIO') and a.get('URI')]
 if matching:urls.append(urllib.parse.urljoin(master,next((a for a in matching if a.get('DEFAULT')=='YES'),matching[0])['URI']))
 folder=D/'staging'/'downloads'/v['id'];folder.mkdir(parents=True,exist_ok=True);args=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y'];keycache={}
 for index,url in enumerate(urls):
  playlist=fetch(url).decode();rewritten=[];frag=0
  for line in playlist.splitlines():
   if line.startswith('#EXT-X-KEY:') and 'URI="' in line:
    if 'METHOD=AES-128' not in line:raise ValueError('Unsupported protected rendition; expected ordinary AES-128 HLS')
    keyurl=urllib.parse.urljoin(url,re.search('URI="([^"]+)"',line)[1])
    if keyurl not in keycache:
     key=fetch(keyurl,headers={'BCOV-Auth':token})
     if len(key)!=16:raise ValueError('invalid returned HLS key')
     kp=folder/('key-'+str(len(keycache))+'.bin');kp.write_bytes(key);keycache[keyurl]=kp
    line=re.sub('URI="[^"]+"','URI="'+str(keycache[keyurl])+'"',line)
   elif line and not line.startswith('#'):
    frag+=1;line=urllib.parse.urljoin(url,line)
    # Reuse complete fragments from the initial native-downloader attempt.
    cached=list((D/'staging'/'native').glob(out.stem+'.f*.mp4.part-Frag'+str(frag))) if index==0 else []
    if cached:
     link=folder/('fragment-'+str(frag)+'.ts')
     if not link.exists():os.link(cached[0],link)
     line=str(link)
   rewritten.append(line)
  local=folder/(str(index)+'.m3u8');local.write_text('\n'.join(rewritten)+'\n')
  args+=['-protocol_whitelist','file,http,https,tcp,tls,crypto,data','-allowed_extensions','ALL','-i',str(local)]
 if len(urls)>1:args+=['-map','0:v:0','-map','1:a:0']
 tmp=folder/(out.stem+'.partial.mp4');args+=['-c','copy','-movflags','+faststart',str(tmp)]
 with (folder/'ffmpeg.log').open('w') as log:
  r=subprocess.run(args,stdout=log,stderr=log,timeout=14400)
 if r.returncode:raise RuntimeError('ffmpeg failed; see '+str(folder/'ffmpeg.log'))
 verify(tmp,expected);tmp.rename(out)

 duration=verify(out,expected)
 return {'status':'complete','path':str(out),'bytes':out.stat().st_size,'duration':duration}

def main():
 p=argparse.ArgumentParser();p.add_argument('--limit',type=int);p.add_argument('--id');p.add_argument('--workers',type=int,default=2);p.add_argument('--failed-only',action='store_true');args=p.parse_args()
 videos=[v for v in json.loads((D/'videos.json').read_text()) if v['video'].get('brightcove_id')];videos.sort(key=lambda v:v['video'].get('duration_in_seconds') or 0)
 if args.failed_only:
  prior=json.loads(STATUS.read_text()) if STATUS.exists() else {}
  videos=[v for v in videos if prior.get(v['id'],{}).get('status')=='failed']
 if args.id:videos=[v for v in videos if v['id']==args.id]
 if args.limit:videos=videos[:args.limit]
 MEDIA.mkdir(parents=True,exist_ok=True)
 results=json.loads(STATUS.read_text()) if STATUS.exists() else {}
 def work(v):
  with lock:results[v['id']]={'status':'downloading','name':v['name']}
  save(results)
  try:r=download(v)
  except Exception as e:
   # Do not put tokens or signed request URLs in the status report.
   msg=str(e);msg=re.sub(r'https?://\S+','[request URL]',msg)
   r={'status':'failed','error':msg[:600]}
  with lock:results[v['id']]={**r,'name':v['name']}
  save(results);print(v['id'],r['status'],v['name'],flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:list(pool.map(work,videos))
 print('Finished; status:',STATUS,flush=True)
if __name__=='__main__':main()
