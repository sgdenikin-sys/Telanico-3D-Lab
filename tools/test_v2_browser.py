"""Exercise the shipped runtime through desktop and real synthesized touch input."""
import argparse
import functools
import http.server
import json
import shutil
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

# Read coordinates and the CSS rectangle atomically. After orientation changes,
# await matching aspect ratios and stable UI coordinates across several probes.
# A fixed sleep can combine the old portrait probe with the new landscape canvas.
POINT = """async ([group, key]) => {
  let previous = '', stable = 0;
  const until = performance.now() + 30000;
  while (performance.now() < until) {
    const s = window.__TELANICO_STATE, r = document.querySelector('#canvas').getBoundingClientRect();
    const point = s?.[group]?.[key];
    const aspectReady = s && Math.abs(s.viewport[0]/s.viewport[1] - r.width/r.height) < .01;
    const signature = JSON.stringify([s?.viewport, s?.ui?.Reset, point, r.x, r.y, r.width, r.height]);
    stable = signature === previous ? stable + 1 : 0;
    previous = signature;
    if (point && aspectReady && stable >= 3) return {
      x:r.x + point[0]/s.viewport[0]*r.width,
      y:r.y + point[1]/s.viewport[1]*r.height, inspect:s.inspect
    };
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  throw new Error('Viewport/UI did not settle for ' + group + '/' + key);
}"""


def exercise(browser, url, width, height, touch, output):
    context = browser.new_context(viewport={'width': width, 'height': height},
                                  has_touch=touch, device_scale_factor=2 if width == 667 else 1)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)
    page.on('console', lambda m: print('BROWSER', m.type, m.text, flush=True))
    cdp = context.new_cdp_session(page) if touch else None

    def state():
        return page.evaluate('window.__TELANICO_STATE')

    def wait(expression, *, arg=None, timeout=30000):
        page.wait_for_function(expression, arg=arg, polling=250, timeout=timeout)

    def click(group, key):
        print('ACTION', width, group, key, flush=True)
        point = page.evaluate(POINT, [group, key])
        (page.touchscreen.tap if touch else page.mouse.click)(point['x'], point['y'])
        if group == 'sites':
            wait('(id)=>window.__TELANICO_STATE.selected===id && window.__TELANICO_STATE.ui.Walk!==undefined', arg=key)
        if key == 'Enter':
            wait('window.__TELANICO_STATE.ui.Return!==undefined')
        if key in ('Cancel', 'Outside', 'Return'):
            wait("Object.keys(window.__TELANICO_STATE.ui).every(k=>['Explore','Follow','Names','Reset'].includes(k))")
        if key == 'Follow':
            wait('window.__TELANICO_STATE.follow')
        if key == 'Explore':
            wait('(old)=>window.__TELANICO_STATE.inspect!==old', arg=point['inspect'])
        if key == 'Reset':
            wait('window.__TELANICO_STATE.camera_size===124 && window.__TELANICO_STATE.yaw===0 && window.__TELANICO_STATE.elevation===40 && !window.__TELANICO_STATE.follow')

    def fingers(kind, points):
        cdp.send('Input.dispatchTouchEvent', {'type': kind,
                 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(points)]})

    def drag_camera(inspect=False):
        if touch:
            fingers('touchStart', [(width*.5, height*.6)])
            for step in range(1, 4):
                fingers('touchMove', [(width*(.5+.1*step/3), height*(.6+.05*step/3))])
            fingers('touchEnd', [])
        else:
            button = 'right' if inspect else 'left'
            page.mouse.move(width*.5, height*.6)
            page.mouse.down(button=button)
            page.mouse.move(width*.6, height*.65, steps=3)
            page.mouse.up(button=button)

    def shot(name):
        page.screenshot(path=str(output/f'{name}-{width}.png'), timeout=120000)

    try:
        page.goto(url+'?test=1', wait_until='domcontentloaded', timeout=120000)
        wait('window.__TELANICO_STATE?.ready', timeout=120000)
        print('GAME_READY', width, flush=True)
        assert len(state()['sites']) == 15
        assert state()['elevation'] == 40 and state()['projection'] == 1
        page.evaluate(POINT, ['ui', 'Reset'])
        shot('world')
        click('sites', 'finance')
        click('ui', 'Cancel')
        assert state()['story_minutes'] == 0
        # Complete travel on desktop and phone. The smaller HiDPI phone adds
        # selection, camera and rotation coverage without duplicating all trips.
        if width in (1440,844):
            # CPU-only WebGL may render at 1 FPS. Keep a visible walking
            # interval while allowing enough physics steps within the deadline.
            page.evaluate('window.__TELANICO_COMMAND={rate:3}')
            click('sites', 'finance')
            click('ui', 'Walk')
            wait("window.__TELANICO_STATE.state==='WALKING'")
            assert 'Walking' in state()['animation']
            shot('walking')
            wait("window.__TELANICO_STATE.current==='finance' && window.__TELANICO_STATE.state==='IDLE'", timeout=90000)
            assert state()['story_minutes'] > 0 and 'Idle' in state()['animation']
            page.evaluate('window.__TELANICO_COMMAND={rate:12}')
            click('ui', 'Enter')
            click('ui', 'Return')
            click('sites', 'dock_e')
            click('ui', 'Walk')
            wait("window.__TELANICO_STATE.current==='dock_e' && window.__TELANICO_STATE.state==='IDLE'", timeout=120000)
            before = state()['story_minutes']
            click('ui', 'Boat')
            wait("window.__TELANICO_STATE.current==='dock_w' && window.__TELANICO_STATE.state==='IDLE'", timeout=120000)
            assert state()['story_minutes']-before == 5 and state()['last_trip']['kind'] == 'boat'
            click('ui', 'Outside')
            click('sites', 'tube_w')
            click('ui', 'Tube')
            wait("window.__TELANICO_STATE.current==='tube_e' && window.__TELANICO_STATE.state==='IDLE'", timeout=120000)
            assert state()['last_trip']['kind'] == 'tube' and state()['last_trip']['minutes'] == 3
            click('ui', 'Outside')
        click('ui', 'Reset')
        if not touch:
            page.mouse.move(width*.5,height*.6)
            page.mouse.wheel(0,-120)
            wait('window.__TELANICO_STATE.camera_size<124')
            page.evaluate('window.__TELANICO_COMMAND={size:999}')
            wait('window.__TELANICO_STATE.camera_size===190')
            page.evaluate('window.__TELANICO_COMMAND={size:1}')
            wait('window.__TELANICO_STATE.camera_size===12')
            click('ui','Reset')
        click('ui', 'Follow')
        wait('window.__TELANICO_STATE.follow && window.__TELANICO_STATE.camera_size===30')
        shot('follow')
        click('ui', 'Reset')
        wait('!window.__TELANICO_STATE.follow && window.__TELANICO_STATE.elevation===40')
        click('ui', 'Explore')
        drag_camera(True)
        wait('Math.abs(window.__TELANICO_STATE.yaw)>.01')
        click('ui', 'Explore')
        old = state()['camera_target']
        drag_camera()
        wait('(old)=>JSON.stringify(window.__TELANICO_STATE.camera_target)!==JSON.stringify(old)', arg=old)
        click('ui', 'Reset')
        if touch:
            fingers('touchStart', [(width*.45, height*.55), (width*.55, height*.55)])
            fingers('touchMove', [(width*.35, height*.55), (width*.65, height*.55)])
            fingers('touchEnd', [])
            wait('window.__TELANICO_STATE.camera_size<124')
            page.set_viewport_size({'width': height, 'height': width})
            page.evaluate(POINT, ['ui', 'Reset'])
            shot('portrait')
            page.set_viewport_size({'width': width, 'height': height})
            click('ui', 'Reset')
            shot('landscape-recovered')
        assert not errors, errors
        print('CASE_OK', width, flush=True)
    except Exception:
        print('FAILURE_STATE', json.dumps(state(), sort_keys=True), flush=True)
        shot('failure')
        raise
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', default='build/web')
    parser.add_argument('--url')
    args = parser.parse_args()
    output = Path('build/screenshots')
    output.mkdir(parents=True, exist_ok=True)
    server = None
    if args.url:
        url = args.url
    else:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=args.directory))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True,
                args=['--no-sandbox', '--use-angle=swiftshader', '--enable-webgl', '--enable-unsafe-swiftshader'])
            for width, height, touch in [(1920, 1080, False), (1440, 900, False), (844, 390, True), (667, 375, True)]:
                exercise(browser, url, width, height, touch, output)
            browser.close()
    finally:
        if server:
            server.shutdown()
            server.server_close()
    print('V2_BROWSER_OK desktop/mobile: walking, bridge, ferry, tube, animated rig, touch pan/pinch/Inspect, rotation recovery')


if __name__ == '__main__':
    main()
