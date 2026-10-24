"""Retina touch UI regression with Safari toolbar-height and safe-area constraints.
Chromium simulation, not a physical Safari claim. No test mutates game session.
"""
import functools, http.server, json, shutil, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('build/screenshots/mobile-ui');out.mkdir(parents=True,exist_ok=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory='build/web'))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader'])
  context=browser.new_context(viewport={'width':844,'height':306},device_scale_factor=3,has_touch=True,is_mobile=True,
      user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1')
  page=context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
  page.on('console',lambda m:errors.append(m.text) if any(t in m.text for t in ['SCRIPT ERROR','Parse Error','ERROR:']) else None)
  def wait(expr):page.wait_for_function(expr,timeout=180000,polling=300)
  def state():return page.evaluate('window.__TELANICO_STORY')
  def click(key,edge=False):
   wait("Math.abs(window.__TELANICO_STORY.viewport[0]/window.__TELANICO_STORY.viewport[1]-innerWidth/visualViewport.height)<0.01")
   frame=state()['frame'];wait(f"window.__TELANICO_STORY.frame>{frame}")
   xy=page.evaluate('''([key,edge])=>{const s=window.__TELANICO_STORY,c=s.controls.find(c=>!c.disabled&&[c.text,c.art].includes(key));
    if(!c)throw Error('Missing '+key);const r=document.querySelector('canvas').getBoundingClientRect();
    return [r.x+(c.rect[0]+c.rect[2]*(edge?.16:.5))*r.width/s.viewport[0],r.y+(c.rect[1]+c.rect[3]*.5)*r.height/s.viewport[1]]}''',[key,edge])
   print('MOBILE_TOUCH',key,xy,'frame',state()['frame'],flush=True)
   page.touchscreen.tap(*xy)
  def validate(name):
   s=state();w,h=s['viewport'];css=page.evaluate('({w:innerWidth,h:visualViewport.height})');ratio=css['w']/w
   for b in s['controls']:
    if b['art_rect']:
     assert all(abs(x-y)<1 for x,y in zip(b['rect'],b['art_rect'])),b
   if s['modal']=='assistant':
    a=s['assistant_frame'];media=s['assistant_media'];card=s['modal_rect']
    assert abs(a[2]-a[3])<1 and a[2]*ratio>=70,(a,css)
    assert all(abs(x-y)<1 for x,y in zip(a,media)),(a,media)
    assert a[0]>=card[0] and a[1]>=card[1] and a[1]+a[3]<=card[1]+card[3]+1,(a,card)
    c=next(c for c in s['controls'] if c['text']=='CONTINUE')
    assert a[0]+a[2] <= c['rect'][0],(a,c)
    assert c['rect'][3]*ratio<=54,("Footer must not crush message",c) # portrait cannot be covered by footer
   rect=s['modal_rect']
   if rect[2]:assert rect[0]>=0 and rect[1]>=0 and rect[0]+rect[2]<=w+1 and rect[1]+rect[3]<=h+1,rect
   plate=s['clock_plate'];assert plate[0]>=0 and plate[0]+plate[2]<=w+1,plate
   page.screenshot(path=str(out/(name+'.png')),timeout=120000)
   (out/(name+'.json')).write_text(json.dumps(s,indent=2))
   print('MOBILE_UI_LAYOUT_PASS',name,css,'retina',3,flush=True)
  page.goto(f'http://127.0.0.1:{server.server_port}/?test=1&story_test=1',wait_until='domcontentloaded')
  wait('window.__TELANICO_STORY?.screen==="intro"')
  # Simulate the cutout/home-indicator insets independently of Chromium's zero iOS env().
  page.evaluate("document.documentElement.style.setProperty('--safe-left','47px');document.documentElement.style.setProperty('--safe-right','47px');document.documentElement.style.setProperty('--safe-bottom','21px')")
  page.wait_for_timeout(2000)
  validate('intro-844x306')
  click('CHOOSE YOUR ROLE');wait('window.__TELANICO_STORY.screen==="characters"')
  validate('characters-844x306')
  click('SELECT COOPER');wait('window.__TELANICO_STORY.modal==="invoice"')
  validate('invoice-844x306')
  click('button_close_invoice.png');wait('window.__TELANICO_STORY.modal==="assistant"')
  validate('assistant-844x306')
  # Real Safari toolbar opening/closing and short screen: no reload or state loss.
  for width,height in [(667,280),(844,390)]:
   page.set_viewport_size({'width':width,'height':height})
   wait(f"Math.abs(window.__TELANICO_STORY.viewport[0]/window.__TELANICO_STORY.viewport[1]-{width}/{height})<0.01")
   frame=state()['frame'];wait(f"window.__TELANICO_STORY.frame>{frame}")
   validate(f'assistant-{width}x{height}')
  click('CONTINUE',True);wait('window.__TELANICO_STORY.modal===""')
  click('button_menu.png',True);wait('window.__TELANICO_STORY.modal==="menu"')
  validate('menu-844x390')
  click('RESUME GAME');wait('window.__TELANICO_STORY.modal===""')
  click('button_assistant.png',True);wait('window.__TELANICO_STORY.modal==="assistant"')
  validate('assistant-reopened')
  click('CONTINUE');wait('window.__TELANICO_STORY.modal===""')
  validate('world-clock-controls')
  assert not errors,errors
  print('MOBILE_UI_RETINA_PASS no resource/runtime errors, visual rectangles match hitboxes, real touch at artwork edge, safe areas and toolbar resize',flush=True)
  context.close();browser.close()
finally:server.shutdown();server.server_close()
