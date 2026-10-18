"""Serve the artifact without isolation headers and exercise it in Chromium."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def run(directory, executable=None):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    screenshots = directory.parent / 'screenshots'
    screenshots.mkdir(exist_ok=True)
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
            errors, messages, failed_requests = [], [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: (
                errors.append(message.text) if message.type == 'error' else messages.append(message.text)))
            page.on('response', lambda response: (
                failed_requests.append(f'{response.status}: {response.url}') if response.status >= 400 else None))
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
            page.wait_for_selector('#status', state='detached', timeout=120000)
            for _ in range(120):
                if any('TELANICO_VIEWER_READY' in message for message in messages):
                    break
                page.wait_for_timeout(500)
            assert any('TELANICO_VIEWER_READY' in message for message in messages), messages
            assert not page.evaluate('crossOriginIsolated'), 'Must run without COOP/COEP'
            assert page.evaluate('GODOT_THREADS_ENABLED') is False
            page.wait_for_timeout(1000)
            def landscape_shot(name):
                # Compare the model area, excluding the GUI button's focus highlight.
                return page.screenshot(path=str(screenshots / name),
                                       clip={'x': 0, 'y': 60, 'width': 844, 'height': 330})

            before = landscape_shot('landscape.png')
            session = context.new_cdp_session(page)

            def touch(kind, points):
                session.send('Input.dispatchTouchEvent', {
                    'type': kind,
                    'touchPoints': [{'x': x, 'y': y, 'id': i} for i, x, y in points],
                })
                page.wait_for_timeout(80)

            touch('touchStart', [(1, 310, 230)])
            for x in range(330, 511, 30):
                touch('touchMove', [(1, x, 230)])
            touch('touchEnd', [])
            page.wait_for_timeout(500)
            rotated = landscape_shot('rotated.png')
            assert rotated != before, 'Touch drag did not change the rendered island'
            touch('touchStart', [(1, 340, 230), (2, 490, 230)])
            for delta in range(10, 91, 20):
                touch('touchMove', [(1, 340-delta, 230), (2, 490+delta, 230)])
            touch('touchEnd', [])
            page.wait_for_timeout(500)
            zoomed = landscape_shot('zoomed.png')
            assert zoomed != rotated, 'Pinch did not change the rendered island'
            # Reset is a Godot GUI button, including on touch devices.
            page.touchscreen.tap(790, 26)
            page.wait_for_timeout(500)
            reset = landscape_shot('reset.png')
            assert reset == before, 'Reset did not restore the initial view'
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(1000)
            portrait_clip = {'x': 0, 'y': 100, 'width': 390, 'height': 744}
            portrait = page.screenshot(path=str(screenshots / 'portrait.png'), clip=portrait_clip)
            # The orientation hint blocks the diorama while portrait.
            touch('touchStart', [(1, 150, 350)])
            touch('touchMove', [(1, 250, 350)])
            touch('touchEnd', [])
            assert page.screenshot(path=str(screenshots / 'portrait-after-touch.png'),
                                   clip=portrait_clip) == portrait, 'Portrait hint must block gestures'
            page.set_viewport_size({'width': 844, 'height': 390})
            page.wait_for_timeout(1000)
            assert landscape_shot('landscape-recovered.png') == before, 'Landscape must recover after rotation'
            assert not errors, errors
            assert not failed_requests, failed_requests
            browser.close()
            print('BROWSER_OK: WebGL startup; no isolation headers; touch drag/pinch/reset; portrait recovery')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--chromium', help='Optional system Chromium executable')
    args = parser.parse_args()
    run(args.directory.resolve(), args.chromium)
