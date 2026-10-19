"""Optional close-up evidence from the actual exported game, not a mock render."""
import functools,http.server,threading,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
out=Path('docs/v2');out.mkdir(exist_ok=True)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory='build/web'))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1280,'height':800})
 page.goto(f'http://127.0.0.1:{server.server_port}/?test=1')
 page.wait_for_function('window.__TELANICO_STATE?.ready',polling=500,timeout=120000)
 for name,focus,size in [('west','settlements',85),('east','trader',85),('tube-west','tube_w',25),('tube-east','tube_e',25),('cooper-temporary','settlements',25),('channel','dock_w',85)]:
  print('CAPTURE',name,flush=True)
  page.evaluate('(c)=>window.__TELANICO_COMMAND=c',{'focus':focus,'size':size,'rate':1})
  page.wait_for_timeout(1000)
  page.screenshot(path=str(out/(name+'.png')),timeout=120000)
 b.close()
