"""Exercise shipped WebGL runtime through actual desktop and touch input."""
import argparse, functools, http.server, json, os, shutil, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('directory',nargs='?',default='build/web');p.add_argument('--url');args=p.parse_args()
out=Path('build/screenshots');out.mkdir(parents=True,exist_ok=True)
if not args.url:
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=args.directory))
 threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
else:url=args.url
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader'])
 for width,height,touch in [(1440,900,False),(844,390,True),(667,375,True)]:
  context=browser.new_context(viewport={'width':width,'height':height},has_touch=touch,device_scale_factor=2 if touch else 1)
  page=context.new_page();page.on('response',lambda r:errors.append(f'HTTP {r.status} {r.url}') if r.status>=400 else None);page.on('console',lambda m:print('BROWSER',m.type,m.text,flush=True));errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'?test=1',wait_until='domcontentloaded',timeout=120000)
  print('HTML_READY',width,flush=True)
  page.wait_for_function('window.__TELANICO_STATE?.ready',polling=500,timeout=120000)
  print('GAME_READY',width,flush=True)
  def state():return page.evaluate('window.__TELANICO_STATE')
  def click(group,key):
   print('ACTION',width,group,key,flush=True);s=state();x,y=s[group][key];v=s['viewport'];r=page.locator('#canvas').bounding_box();x=r['x']+x/v[0]*r['width'];y=r['y']+y/v[1]*r['height']
   (page.touchscreen.tap if touch else page.mouse.click)(x,y);page.wait_for_timeout(1000)
   if group=='sites':page.wait_for_function('(id)=>window.__TELANICO_STATE.selected===id',arg=key,timeout=20000)
  assert len(state()['sites'])==15
  page.screenshot(timeout=120000,path=str(out/f'world-{width}.png'))
  click('sites','finance');assert state()['selected']=='finance',state()
  assert 'Walk' in state()['ui'];click('ui','Cancel');assert state()['story_minutes']==0
  click('sites','finance');click('ui','Walk')
  page.wait_for_function("window.__TELANICO_STATE.state==='WALKING'",polling=250)
  assert 'Walking' in state()['animation']
  page.screenshot(timeout=120000,path=str(out/f'walking-{width}.png'))
  page.wait_for_function("window.__TELANICO_STATE.current==='finance' && window.__TELANICO_STATE.state==='IDLE'",polling=250,timeout=90000)
  assert state()['story_minutes']>0 and 'Idle' in state()['animation']
  assert 'Enter' in state()['ui'];click('ui','Enter');click('ui','Return')
  # The same browser input path exercises slow and fast crossings.
  click('sites','dock_e');click('ui','Walk')
  page.wait_for_function("window.__TELANICO_STATE.current==='dock_e' && window.__TELANICO_STATE.state==='IDLE'",timeout=120000)
  before=state()['story_minutes'];click('ui','Boat')
  page.wait_for_function("window.__TELANICO_STATE.current==='dock_w' && window.__TELANICO_STATE.state==='IDLE'",polling=250,timeout=120000)
  assert state()['story_minutes']-before==5 and state()['last_trip']['kind']=='boat'
  click('ui','Outside');click('sites','tube_w');click('ui','Tube')
  page.wait_for_function("window.__TELANICO_STATE.current==='tube_e' && window.__TELANICO_STATE.state==='IDLE'",polling=250,timeout=120000)
  assert state()['last_trip']['kind']=='tube' and state()['last_trip']['minutes']==3
  click('ui','Outside')
  click('ui','Explore');assert state()['inspect'];click('ui','Explore');assert not state()['inspect']
  old=state()['camera_target'];page.mouse.move(width*.5,height*.6);page.mouse.down();page.mouse.move(width*.6,height*.65,steps=8);page.mouse.up();page.wait_for_timeout(400)
  assert state()['camera_target']!=old
  click('ui','Reset');assert state()['camera_size']==124
  if touch:
   cdp=context.new_cdp_session(page)
   def fingers(kind,points):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'x':x,'y':y,'id':i} for i,(x,y) in enumerate(points)]})
   fingers('touchStart',[(width*.45,height*.55),(width*.55,height*.55)])
   fingers('touchMove',[(width*.35,height*.55),(width*.65,height*.55)])
   fingers('touchEnd',[]);page.wait_for_timeout(500)
   assert state()['camera_size']<124
  assert not errors,errors
  context.close()
 browser.close()
print('V2_BROWSER_OK desktop, mobile landscape, actual selection/walk/entry, pan, reset, pinch, animated rig')
