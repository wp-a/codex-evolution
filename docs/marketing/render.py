"""Render the editable marketing artboards. Optional development tool only.

python -m pip install playwright
python -m playwright install chromium
python docs/marketing/render.py [--browser /path/to/chrome]
"""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', help='Optional installed Chrome/Chromium binary')
    args = parser.parse_args()
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parent
    with sync_playwright() as playwright:
        options = {'executable_path': args.browser} if args.browser else {}
        browser = playwright.chromium.launch(headless=True, **options)
        page = browser.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto((root / 'source.html').as_uri(), wait_until='load')
        boards = page.locator('[data-artboard]').evaluate_all('(items) => items.map(item => item.id)')
        for name in boards:
            page.goto((root / 'source.html').as_uri() + '?render=' + name, wait_until='load')
            page.evaluate('document.fonts.ready')
            assert page.locator('img').evaluate_all('(items) => items.every(item => item.complete && item.naturalWidth > 0)'), 'Missing image'
            board = page.locator('#' + name)
            size = board.bounding_box()
            page.set_viewport_size({'width': int(size['width']), 'height': int(size['height'])})
            board.screenshot(path=str(root / (name + '.png')), animations='disabled')
            print(name + '.png', int(size['width']), int(size['height']))
        browser.close()
        assert not errors, errors


if __name__ == '__main__':
    main()
