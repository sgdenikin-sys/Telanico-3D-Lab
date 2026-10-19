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


def png_pixel(data, x, y):
    """Read one RGB/RGBA screenshot pixel using only the Python standard library."""
    import struct
    import zlib
    offset, payload = 8, bytearray()
    while offset < len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset+4:offset+8]
        chunk = data[offset+8:offset+8+length]
        if kind == b'IHDR':
            width, height, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', chunk)
        elif kind == b'IDAT':
            payload.extend(chunk)
        offset += length + 12
    assert depth == 8 and color in (2, 6) and interlace == 0
    bpp = 3 if color == 2 else 4
    stride = width * bpp
    raw = zlib.decompress(payload)
    previous = bytearray(stride)
    for row_index in range(y+1):
        start = row_index * (stride+1)
        mode, row = raw[start], bytearray(raw[start+1:start+1+stride])
        for i in range(stride):
            a = row[i-bpp] if i >= bpp else 0
            b = previous[i]
            c = previous[i-bpp] if i >= bpp else 0
            if mode == 1:
                predictor = a
            elif mode == 2:
                predictor = b
            elif mode == 3:
                predictor = (a+b)//2
            elif mode == 4:
                p = a+b-c
                distances = [abs(p-a), abs(p-b), abs(p-c)]
                predictor = [a, b, c][distances.index(min(distances))]
            else:
                assert mode == 0
                predictor = 0
            row[i] = (row[i]+predictor) & 255
        previous = row
    return list(previous[x*bpp:x*bpp+3])


def run(directory, executable=None):
    # Bound driver/browser shutdown too, so a hung WASM page leaves diagnostics.
    faulthandler.dump_traceback_later(480, exit=True)
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
                        background:getComputedStyle(document.body).backgroundColor,
                        layers:['html','body','#game','#canvas'].map(s =>
                            getComputedStyle(document.querySelector(s)).backgroundColor)};
                }""")
                assert abs(evidence['x']) < 1 and abs(evidence['y']) < 1, evidence
                assert abs(evidence['width'] - width) < 1, evidence
                assert abs(evidence['height'] - height) < 1, evidence
                assert evidence['scrollWidth'] == width, evidence
                assert abs(evidence['bufferWidth'] / evidence['bufferHeight'] - width / height) < 0.01, evidence
                assert evidence['background'] == 'rgb(31, 43, 56)', evidence
                hud = evidence['hud']
                assert 91 <= hud['width'] <= 94 and 33 <= hud['height'] <= 36, evidence
                assert hud['x'] >= safe and hud['y'] >= 9, evidence
                assert width - hud['x'] - hud['width'] >= safe + 9, evidence
                assert len(set(evidence['layers'])) == 1, evidence
                assert 10 <= hud['instruction_font'] <= 12, evidence
                assert hud['instruction_x'] >= safe + 9, evidence
                assert hud['instruction_x'] + hud['instruction_width'] + 12 < hud['x'], evidence
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
                full = page.screenshot(path=str(screenshots / f'{prefix}-full.png'))
                edge = png_pixel(full, 3, height-4)
                assert all(abs(a-b) <= 1 for a, b in zip(edge, [31,43,56])), (prefix, 'Rendered edge/background mismatch', edge)
                results[-1]['rendered_edge_rgb'] = edge

            # Chromium does not emulate a notch. Inject resolved CSS insets to
            # exercise the same bridge/layout code; real env() values need iPhone.
            page.set_viewport_size({'width': 844, 'height': 390})
            page.evaluate("""() => {
                const s = document.documentElement.style;
                s.setProperty('--safe-left', '48px'); s.setProperty('--safe-right', '48px');
                s.setProperty('--safe-bottom', '21px'); s.setProperty('--safe-top', '8px');
            }""")
            hud = check_layout(844, 390, 48)
            assert hud['y'] >= 17
            before = page.screenshot(clip={'x': 0, 'y': 100, 'width': 844, 'height': 290})
            touch('touchStart', [(1, 300, 230)])
            touch('touchMove', [(1, 500, 230)])
            touch('touchEnd', [])
            page.touchscreen.tap(hud['x'] + hud['width']/2, hud['y'] + hud['height']/2)
            page.wait_for_timeout(500)
            assert page.screenshot(clip={'x': 0, 'y': 100, 'width': 844, 'height': 290}) == before
            page.screenshot(path=str(screenshots / 'simulated-safe-area.png'))

            # Conservative resolved notch insets for both landscape orientations.
            # Chromium does not supply iOS env() values: exercise the same bridge
            # with 47/59-pixel profiles at real iPhone CSS viewport dimensions.
            for width, height, inset in [(812,375,47), (844,390,47), (852,393,59), (932,430,59)]:
                page.set_viewport_size({'width': width, 'height': height})
                page.evaluate("""value => {
                    const s = document.documentElement.style;
                    s.setProperty('--safe-left', value+'px');
                    s.setProperty('--safe-right', value+'px');
                }""", inset)
                check_layout(width, height, inset)
                page.screenshot(path=str(screenshots / f'notch-{width}x{height}.png'))
            page.set_viewport_size({'width': 844, 'height': 390})
            page.evaluate("""() => {
                const s = document.documentElement.style;
                s.setProperty('--safe-left','48px'); s.setProperty('--safe-right','48px');
                // Regression: a visual-viewport offset must not be added twice
                // to a container that is already fixed to the page.
                Object.defineProperty(window.visualViewport, 'offsetLeft', {configurable:true, value:48});
                window.visualViewport.dispatchEvent(new Event('scroll'));
            }""")
            check_layout(844, 390, 48)
            page.evaluate("""() => {
                delete window.visualViewport.offsetLeft;
                window.visualViewport.dispatchEvent(new Event('scroll'));
            }""")

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
            assert 33 <= retina_size['hud']['height'] <= 36, retina_size
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
