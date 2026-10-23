"""Verify the actual published V2.2 at desktop and phone landscape sizes."""
import argparse
import json
from pathlib import Path
import urllib.request

from playwright.sync_api import sync_playwright
from test_story_browser import exercise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://sgdenikin-sys.github.io/Telanico-3D-Lab/')
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    url = args.url.rstrip('/') + '/'
    with urllib.request.urlopen(url + 'build.json?verify=' + args.commit, timeout=60) as response:
        meta = json.load(response)
    assert meta['version'] == 'telanico-v2.2' and meta['commit'] == args.commit, meta
    output = Path('build/screenshots/hosted-v22')
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--use-angle=swiftshader', '--enable-webgl', '--enable-unsafe-swiftshader'])
        for width, height, touch in [(1280, 720, False), (844, 390, True)]:
            exercise(browser, url, output, width, height, touch, False)
        browser.close()
    (output / 'live-build.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print('LIVE_V22_DESKTOP_PHONE_PASS', args.commit, url, flush=True)


if __name__ == '__main__':
    main()
