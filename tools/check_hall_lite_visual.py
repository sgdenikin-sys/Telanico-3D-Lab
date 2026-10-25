"""Check the isolated Godot 4.6.3 Web QA pack with the existing Chromium.

No game files are changed. The scratch pack uses copies of the existing Web
engine and a separate asset-only project. Browser emulation is not iPhone Safari.
"""
import functools
import hashlib
import http.server
import json
from pathlib import Path
import shutil
import threading
import time

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'blender/generated/settlements_hall_lite'
WEB = ROOT/'work/hall-v3-web'


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(WEB))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    errors = []
    report = {'viewport': [844, 390], 'device_pixel_ratio': 1,
              'physical_device': False,
              'method': 'Godot 4.6.3 Compatibility in Chromium with SwiftShader; cached engine, isolated PCK',
              'glb_sha256': hashlib.sha256((OUT/'settlements_hall.glb').read_bytes()).hexdigest(),
              'engine_js_sha256': hashlib.sha256((WEB/'index.js').read_bytes()).hexdigest(),
              'variants': {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium'),
            args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 844, 'height': 390}, device_scale_factor=1)
        page.on('console', lambda msg: print('WEB_CONSOLE', msg.type, msg.text[:600], flush=True))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
        page.wait_for_function('window.__HALL_STATE?.ready || window.__HALL_ERROR', timeout=120000)
        assert not page.evaluate('window.__HALL_ERROR || null')
        state = page.evaluate('window.__HALL_STATE')
        assert state['engine'].startswith('4.6.3') and state['renderer'] == 'gl_compatibility', state
        report['engine'] = state['engine']
        report['browser_startup_ms'] = page.evaluate('window.__HALL_STARTUP_MS')
        report['gl_vendor'] = page.evaluate('''() => {
            const gl=document.querySelector('canvas').getContext('webgl2');
            const ext=gl.getExtension('WEBGL_debug_renderer_info');
            return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
        }''')

        serial = 0
        def command(data, mode=None, variant=None):
            nonlocal serial
            serial += 1
            page.evaluate('(v)=>window.__HALL_COMMAND=v', dict(data, id=serial))
            page.wait_for_function('(i)=>window.__HALL_STATE?.command_id===i', arg=serial, timeout=60000)
            if mode:
                page.wait_for_function('(s)=>window.__HALL_STATE?.mode===s', arg=mode)
            if variant:
                page.wait_for_function('(s)=>window.__HALL_STATE?.variant===s', arg=variant)
            page.wait_for_timeout(700)

        for name in ['v2', 'lite']:
            command({'mode': name}, mode='model', variant=name)
            page.wait_for_timeout(4000)
            state = page.evaluate('window.__HALL_STATE')
            state['js_heap_bytes'] = page.evaluate('performance.memory?.usedJSHeapSize || null')
            report['variants'][name] = state
            page.screenshot(path=str(OUT/f'godot_{name}_844x390.png'))
        command({'mode': 'pose', 'seconds': 0.5})
        state = page.evaluate('window.__HALL_STATE')
        print('WEB_ANIMATION_POSE', json.dumps(state), flush=True)
        assert len(state['hinge_degrees']) == 2 and all(abs(v) > 40 for v in state['hinge_degrees'].values())
        assert len(state['fabric_weights']) == 4 and all(v[2] > .9 for v in state['fabric_weights'].values())
        report['web_animation_pose'] = state
        page.screenshot(path=str(OUT/'godot_lite_animation_pose.png'))

        pixels = {}
        for kind in ['hidden', 'transparent', 'opaque']:
            command({'mode': 'glass', 'kind': kind}, mode=kind)
            path = OUT/f'godot_glass_{kind}.png'
            page.screenshot(path=str(path))
            image = np.asarray(Image.open(path).convert('RGB'), dtype=float)
            pixels[kind] = np.array([image[y-2:y+3, x-2:x+3].mean(axis=(0, 1))
                                    for x, y in [(344, 148), (500, 148), (344, 242), (500, 242)]])
        delta_opaque = np.linalg.norm(pixels['opaque']-pixels['hidden'], axis=1)
        delta_alpha = np.linalg.norm(pixels['transparent']-pixels['hidden'], axis=1)
        ratios = delta_alpha / np.maximum(delta_opaque, 1)
        assert all(delta_opaque > 20), 'Glass control fixture not visible'
        assert all((ratios > .1) & (ratios < .95)), f'Glass failed actual alpha-composition check: {ratios}'
        report['glass_pixels'] = {k: v.round(2).tolist() for k, v in pixels.items()}
        report['glass_transparent_to_opaque_distance_ratios'] = ratios.tolist()
        report['glass_render_verified'] = True
        report['page_errors'] = errors
        assert not errors, errors
        browser.close()
    server.shutdown()
    report['limitations'] = 'Software rendering, one emulated landscape viewport, both resource choices in one PCK. Decode timings share a warm cache. JS heap is not total WASM/device RAM; the native memory counter returns unsupported zero. Not physical Safari, a mobile-ready certification, or an isolated per-model performance/memory benchmark.'
    (OUT/'godot_visual_validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print('GODOT_LITE_VISUAL_QA_OK', json.dumps({'engine': report['engine'], 'renderer': report['gl_vendor'],
          'glass_distance_ratios': ratios.tolist(), 'variants': report['variants']}))


if __name__ == '__main__':
    main()
