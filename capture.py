from playwright.sync_api import sync_playwright
from pathlib import Path
import os
Path('screenshots').mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
    page.goto('http://127.0.0.1:8504'); page.click('#demo'); page.wait_for_function("document.querySelector('#status').textContent.includes('Dataset ready')")
    page.screenshot(path='screenshots/01-dashboard.png',full_page=True)
    page.fill('#question','Total Sales by Region'); page.click('#ask button'); page.wait_for_selector('#chart .bar'); page.locator('#chat').scroll_into_view_if_needed(); page.screenshot(path='screenshots/02-analysis.png')
    page.click('[data-clean=fill]'); page.wait_for_function("document.querySelector('#status').textContent.includes('9 rows')"); page.locator('#quality').scroll_into_view_if_needed(); page.screenshot(path='screenshots/03-cleaning.png')
    browser.close()
readme=Path('README.md'); text=readme.read_text().split('<!-- captures -->')[0]; readme.write_text(text+'\n<!-- captures -->\n'+''.join(f'\n![{p.stem}]({p.as_posix()})\n' for p in sorted(Path('screenshots').glob('*.png')) if 'preview' not in p.name))
