"""Comparable real WebGL views; commands change camera only, never the world."""
import argparse,functools,http.server,threading,shutil,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_v2_browser import POINT

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--url');args=parser.parse_args()
 out=Path('docs/v2-1');out.mkdir(exist_ok=True)
 server=None
 if not args.url:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory='build/web'))
  threading.Thread(target=server.serve_forever,daemon=True).start()
 url=args.url or f'http://127.0.0.1:{server.server_port}/'
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=b.new_page(viewport={'width':1440,'height':900})
  page.goto(url+'?test=1');page.wait_for_function('window.__TELANICO_STATE?.ready',timeout=120000)
  def shot(name,command):
   page.evaluate('(c)=>window.__TELANICO_COMMAND=c',dict(rate=1,**command))
   page.wait_for_function('window.__TELANICO_COMMAND===null',timeout=30000)
   page.wait_for_timeout(1800)
   page.screenshot(path=str(out/(name+'.png')),timeout=120000)
   print('REVIEW',name,flush=True)
  for angle in (40,30,38,45,55):
   shot(f'final-web-{angle}',dict(target=[0,5,0],size=124,elevation=angle,projection='orthographic'))
  shot('final-perspective-40',dict(target=[0,5,0],size=124,elevation=40,projection='perspective'))
  shot('final-east',dict(focus='trader',size=65,elevation=40,projection='orthographic'))
  shot('final-waterfront',dict(target=[0,5,-24],size=83,elevation=35,projection='orthographic'))
  shot('final-terraces',dict(target=[-55,6,-13],size=68,elevation=35,projection='orthographic'))
  point=page.evaluate(POINT,['ui','Follow']);page.mouse.click(point['x'],point['y'])
  page.wait_for_function('window.__TELANICO_STATE.follow && window.__TELANICO_STATE.camera_size===30',timeout=30000)
  page.wait_for_timeout(3000)
  page.screenshot(path=str(out/'final-follow-settlements.png'),timeout=120000)
  print('REVIEW Follow',flush=True)
  point=page.evaluate(POINT,['ui','Reset']);page.mouse.click(point['x'],point['y'])
  page.wait_for_function('!window.__TELANICO_STATE.follow',timeout=30000)
  page.set_viewport_size({'width':844,'height':390});page.evaluate(POINT,['ui','Reset'])
  page.screenshot(path=str(out/'final-phone-844.png'),timeout=120000)
  (out/'review-state.json').write_text(json.dumps(page.evaluate('window.__TELANICO_STATE'),indent=2))
  b.close()
 if server:server.shutdown()
if __name__=='__main__':main()
