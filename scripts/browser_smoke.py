#!/usr/bin/env python3
"""Optional real-browser smoke test for the bundled synthetic dashboard.

Requires Playwright and its Chromium browser in the caller's QA environment.
This helper is not a runtime dependency. It never submits or sends anything.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dashboard', nargs='?', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'examples' / 'Dashboard.html')
    args = parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        parser.exit(2, 'Optional QA dependency missing: install playwright, then run python -m playwright install chromium.\n')
    path = args.dashboard.resolve(strict=True)
    errors, requests = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            page.on('request', lambda request: requests.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
            page.route('http://**/*', lambda route: route.abort())
            page.route('https://**/*', lambda route: route.abort())
            page.goto(path.as_uri())
            assert 'SYNTHETIC / DEMO DATA' in page.locator('body').inner_text()
            total = int(page.locator('#main').get_attribute('data-count-total'))
            current = int(page.locator('#main').get_attribute('data-count-current'))
            assert total == 8, 'This smoke test expects the bundled eight-record synthetic example'
            assert page.locator('article[data-role-id]:visible').count() == total
            page.locator('#lane-filter').select_option('current')
            assert page.locator('article[data-role-id]:visible').count() == current
            page.locator('article[data-role-id]:visible .feedback-button').first.click()
            page.locator('#feedback-action').select_option('hide')
            assert page.locator('#copy-prompt').is_disabled()
            page.locator('#feedback-reason').fill('Synthetic review: prefer a different work pattern.')
            assert not page.locator('#copy-prompt').is_disabled()
            assert '"action": "hide"' in page.locator('#feedback-prompt').input_value()
            # Exercise the documented manual-copy branch without changing a clipboard.
            page.evaluate("Object.defineProperty(navigator, 'clipboard', {value: undefined, configurable: true})")
            page.locator('#copy-prompt').click()
            assert 'NOT SAVED' in page.locator('#feedback-status').inner_text()
            assert page.locator('article[data-role-id]:visible').count() == current
            page.locator('#close-feedback').click()
            assert page.locator('#feedback-panel').is_hidden()
            page.locator('#lane-filter').select_option('')
            page.locator('#role-search').fill('facilities administrator')
            assert page.locator('article[data-role-id]:visible').count() == 1
            page.locator('#role-search').fill('')
            assert page.locator('article[data-role-id]:visible').count() == total
            for width, height in [(1280, 900), (390, 844)]:
                page.set_viewport_size({'width': width, 'height': height})
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1'), f'Horizontal overflow at {width}px'
                assert page.locator('#role-search').is_visible()
            assert not errors, errors
            assert not requests, 'Dashboard attempted a network request'
            print(json.dumps({'status': 'passed', 'browser': browser.version, 'records': total,
                              'current': current, 'viewports': [1280, 390], 'console_errors': len(errors),
                              'network_requests': len(requests), 'feedback': 'copy only; not saved'}, sort_keys=True))
        finally:
            browser.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
