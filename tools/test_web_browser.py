"""Test the actual WebGL build across landscape sizes, safe insets and gestures."""
import argparse
import faulthandler
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def run(directory, executable=None):
    # Bound driver/browser shutdown too, so a hung WASM page leaves diagnostics.
    faulthandler.dump_traceback_later(300, exit=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    screenshots = directory.parent / 'screenshots'
    screenshots.mkdir(exist_ok=True)
    results = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=executable,
                args=['--no-sandbox', '--enable-webgl', '--use-angle=swiftshader',
                      '--enable-unsafe-swiftshader'],
            )
            context = browser.new_context(viewport={'width': 844, 'height': 390},
                                          device_scale_factor=1, is_mobile=True, has_touch=True)
            page = context.new_page()
            page.set_default_timeout(15000)
            print('BROWSER: loading WebGL build', flush=True)
            errors, messages, failed_requests = [], [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: (
                errors.append(message.text) if message.type == 'error' else messages.append(message.text)))
            page.on('response', lambda response: (
                failed_requests.append(f'{response.status}: {response.url}') if response.status >= 400 else None))
            page.on('requestfailed', lambda request: failed_requests.append(request.url))
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            page.wait_for_selector('#status', state='detached', timeout=120000)
            for _ in range(120):
                if any('TELANICO_VIEWER_READY' in message for message in messages):
                    break
                page.wait_for_timeout(500)
            assert any('TELANICO_VIEWER_READY' in message for message in messages), messages
            assert not page.evaluate('crossOriginIsolated'), 'Must run without COOP/COEP'
            assert page.evaluate('GODOT_THREADS_ENABLED') is False
            assert 'viewport-fit=cover' in page.locator('meta[name=viewport]').get_attribute('content')
            session = context.new_cdp_session(page)

            def touch(kind, points):
                session.send('Input.dispatchTouchEvent', {
                    'type': kind,
                    'touchPoints': [{'x': x, 'y': y, 'id': i} for i, x, y in points],
                })
                page.wait_for_timeout(80)

            def check_layout(width, height, safe):
                page.wait_for_timeout(1000)
                evidence = page.evaluate("""() => {
                    const c = document.getElementById('canvas'), r = c.getBoundingClientRect();
                    return {x:r.x, y:r.y, width:r.width, height:r.height,
                        bufferWidth:c.width, bufferHeight:c.height, hud:window.telanicoHUD,
                        scrollWidth:document.documentElement.scrollWidth,
                        background:getComputedStyle(document.body).backgroundColor};
                }""")
                assert abs(evidence['x']) < 1 and abs(evidence['y']) < 1, evidence
                assert abs(evidence['width'] - width) < 1, evidence
                assert abs(evidence['height'] - height) < 1, evidence
                assert evidence['scrollWidth'] == width, evidence
                assert abs(evidence['bufferWidth'] / evidence['bufferHeight'] - width / height) < 0.01, evidence
                assert evidence['background'] == 'rgb(31, 43, 56)', evidence
                hud = evidence['hud']
                assert 111 <= hud['width'] <= 114 and 47 <= hud['height'] <= 50, evidence
                assert hud['x'] >= safe and hud['y'] >= 11, evidence
                assert width - hud['x'] - hud['width'] >= safe + 11, evidence
                results.append(evidence)
                return hud

            # Small iPhone, notch-era, modern sizes and Safari with expanded chrome.
            for width, height in [(667, 375), (812, 375), (844, 390), (852, 393),
                                  (932, 430), (844, 320)]:
                page.set_viewport_size({'width': width, 'height': height})
                print(f'BROWSER: checking {width}x{height}', flush=True)
                hud = check_layout(width, height, 0)
                prefix = f'{width}x{height}'
                # Ignore GUI focus/hover highlights when comparing the scene.
                clip = {'x': 0, 'y': 100, 'width': width, 'height': height - 100}

                def shot(suffix):
                    return page.screenshot(path=str(screenshots / f'{prefix}-{suffix}.png'), clip=clip)

                before = shot('initial')
                y = height * 0.65
                touch('touchStart', [(1, width * 0.35, y)])
                for fraction in [0.4, 0.45, 0.5, 0.55, 0.6]:
                    touch('touchMove', [(1, width * fraction, y)])
                touch('touchEnd', [])
                page.wait_for_timeout(500)
                rotated = shot('rotated')
                assert rotated != before, (prefix, 'One-finger rotation failed')
                touch('touchStart', [(1, width * 0.4, y), (2, width * 0.6, y)])
                for delta in [0.02, 0.04, 0.06, 0.08]:
                    touch('touchMove', [(1, width * (0.4-delta), y), (2, width * (0.6+delta), y)])
                touch('touchEnd', [])
                page.wait_for_timeout(500)
                print('BROWSER: after pinch', page.evaluate('window.telanicoViewport()'), flush=True)
                assert shot('pinched') != rotated, (prefix, 'Pinch failed')
                page.touchscreen.tap(hud['x'] + hud['width']/2, hud['y'] + hud['height']/2)
                page.wait_for_timeout(500)
                assert shot('reset') == before, (prefix, 'Reset failed')
                page.screenshot(path=str(screenshots / f'{prefix}-full.png'))

            # Chromium does not emulate a notch. Inject resolved CSS insets to
            # exercise the same bridge/layout code; real env() values need iPhone.
            page.set_viewport_size({'width': 844, 'height': 390})
            page.evaluate("""() => {
                const s = document.documentElement.style;
                s.setProperty('--safe-left', '48px'); s.setProperty('--safe-right', '48px');
                s.setProperty('--safe-bottom', '21px'); s.setProperty('--safe-top', '8px');
            }""")
            hud = check_layout(844, 390, 48)
            assert hud['y'] >= 19
            before = page.screenshot(clip={'x': 0, 'y': 100, 'width': 844, 'height': 290})
            touch('touchStart', [(1, 300, 230)])
            touch('touchMove', [(1, 500, 230)])
            touch('touchEnd', [])
            page.touchscreen.tap(hud['x'] + hud['width']/2, hud['y'] + hud['height']/2)
            page.wait_for_timeout(500)
            assert page.screenshot(clip={'x': 0, 'y': 100, 'width': 844, 'height': 290}) == before
            page.screenshot(path=str(screenshots / 'simulated-safe-area.png'))

            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(1000)
            portrait_clip = {'x': 0, 'y': 100, 'width': 390, 'height': 744}
            portrait = page.screenshot(path=str(screenshots / 'portrait.png'), clip=portrait_clip)
            touch('touchStart', [(1, 150, 350)])
            touch('touchMove', [(1, 250, 350)])
            touch('touchEnd', [])
            assert page.screenshot(clip=portrait_clip) == portrait, 'Portrait must block gestures'
            page.set_viewport_size({'width': 844, 'height': 390})
            check_layout(844, 390, 48)
            assert page.screenshot(clip={'x': 0, 'y': 100, 'width': 844, 'height': 290}) == before
            assert not errors, errors
            assert not failed_requests, failed_requests
            (screenshots / 'layout-evidence.json').write_text(json.dumps(results, indent=2))
            context.close()
            # Check the actual WebGL layout at high DPI as well, without making
            # the full screenshot/gesture matrix depend on software-GPU throughput.
            retina = browser.new_context(viewport={'width': 844, 'height': 390},
                                         device_scale_factor=2, is_mobile=True, has_touch=True)
            retina_page = retina.new_page()
            retina_page.on('pageerror', lambda error: errors.append(str(error)))
            retina_page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            retina_page.wait_for_selector('#status', state='detached', timeout=120000)
            retina_page.wait_for_timeout(1000)
            retina_size = retina_page.evaluate("""() => {
                const c = document.getElementById('canvas');
                return {width:c.width, height:c.height, hud:window.telanicoHUD};
            }""")
            assert retina_size['width'] == 1688 and retina_size['height'] == 780, retina_size
            assert 47 <= retina_size['hud']['height'] <= 50, retina_size
            assert not errors, errors
            retina.close()
            browser.close()
            print('BROWSER_OK: WebGL; six landscape sizes at DPR 1 plus DPR 2 startup/layout; canvas aspect; drag/pinch/reset; simulated safe areas; portrait recovery')
    finally:
        faulthandler.cancel_dump_traceback_later()
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--chromium', help='Optional system Chromium executable')
    args = parser.parse_args()
    run(args.directory.resolve(), args.chromium)
