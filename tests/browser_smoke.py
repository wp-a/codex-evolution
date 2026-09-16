"""Optional browser integration smoke test against a real temporary backend.

Default: real browser-to-localhost navigation.
--bridge: for managed environments that block browser navigation to localhost;
          renders shipped assets and forwards fetch to the real server in Python.
          This does NOT validate browser network/origin enforcement. HTTP tests do.
Runtime users do not need Playwright. Install it only to run this developer test.
"""
from __future__ import annotations
import argparse
import base64
import json
import re
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codex_evolution.server import EvolutionServer
from codex_evolution.storage import Store


def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bridge',action='store_true')
    parser.add_argument('--browser',help='Optional Chromium executable path')
    parser.add_argument('--screenshots',default=str(ROOT/'docs/screenshots'))
    args=parser.parse_args()
    try:
        from playwright.sync_api import expect, sync_playwright
    except ImportError:
        parser.error('Optional test requires: python -m pip install playwright; python -m playwright install chromium')
    out=Path(args.screenshots);out.mkdir(parents=True,exist_ok=True)
    errors=[];checks={}
    with tempfile.TemporaryDirectory() as folder:
        server=EvolutionServer(('127.0.0.1',0),Store(Path(folder)/'browser.sqlite'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(headless=True,**({'executable_path':args.browser} if args.browser else {}))
                page=browser.new_page(viewport={'width':1512,'height':1120},device_scale_factor=1)
                page.on('pageerror',lambda error:errors.append(str(error)))
                if args.bridge:
                    assets=ROOT/'codex_evolution/web'
                    with urllib.request.urlopen(base+'/') as response: html=response.read().decode()
                    html=re.sub(r'<link[^>]*>','',html)
                    html=re.sub(r'<script.*?</script>','',html,flags=re.S)
                    html=html.replace('</head>','<style>'+(assets/'styles.css').read_text(encoding='utf-8')+'</style></head>')
                    def bridge(url,options):
                        if not str(url).startswith('/api/'): raise ValueError('Test bridge only accepts local API paths')
                        request=urllib.request.Request(base+url,method=options.get('method','GET'),
                            headers=options.get('headers',{}),
                            data=options['body'].encode() if options.get('body') else None)
                        try: response=urllib.request.urlopen(request,timeout=30)
                        except urllib.error.HTTPError as error: response=error
                        with response:
                            return {'status':response.status,'headers':dict(response.headers),'body':base64.b64encode(response.read()).decode()}
                    page.expose_function('localBackendFetch',bridge)
                    page.set_content(html)
                    page.evaluate("""() => {window.fetch=async(url,options={})=>{
                        const r=await window.localBackendFetch(String(url),options);
                        return new Response(Uint8Array.from(atob(r.body),c=>c.charCodeAt(0)),{status:r.status,headers:r.headers});
                    };}""")
                    script=(assets/'app.js').read_text(encoding='utf-8').replace('src="/logo.svg"','src="data:image/svg+xml;base64,'+base64.b64encode((assets/'logo.svg').read_bytes()).decode()+'"')
                    page.add_script_tag(content=script)
                else:
                    page.goto(base,wait_until='networkidle')
                def nav(name): page.locator(f'.sidebar .nav-item[data-page="{name}"]').click()
                def shot(name):
                    page.evaluate('() => window.scrollTo(0,0)')
                    expect(page.locator('#toast')).not_to_have_class(re.compile(r'\bshow\b'),timeout=6000)
                    page.screenshot(path=str(out/name),full_page=True,animations='disabled')
                def close(): page.locator('[data-action="close-modal"]').click()
                def open_report_exports():
                    disclosure=page.locator('.report-export')
                    if not disclosure.evaluate('(element)=>element.open'):
                        disclosure.locator(':scope > summary').click()
                expect(page.locator('.start-page')).to_be_visible()
                expect(page.locator('.start-page')).to_contain_text('Codex')
                expect(page.locator('html')).to_have_attribute('data-theme','light')
                expect(page.locator('.sidebar-nav')).to_be_visible()
                assert set(page.locator('.sidebar-nav .nav-item').evaluate_all(
                    '(items)=>items.map(item=>item.dataset.page)'))=={
                    'start','overview','explorer','timeline','audit','skills','prompts','reports','data'}
                expect(page.locator('.start-actions [data-page="data"]')).to_be_visible()
                expect(page.locator('.start-actions [data-action="try-demo"]')).to_be_visible()
                shot('start-light.png');checks['first_use_introduction_and_navigation']=True
                for width in [320,360,736,1024,1512]:
                    page.set_viewport_size({'width':width,'height':1000})
                    assert not page.evaluate('() => document.documentElement.scrollWidth>window.innerWidth'),f'Start page overflow at {width}'
                    if width==360: shot('start-mobile.png')
                page.set_viewport_size({'width':1512,'height':1120})
                checks['start_responsive_widths']=[320,360,736,1024,1512]
                page.locator('[data-action="theme"]').click()
                expect(page.locator('html')).to_have_attribute('data-theme','dark')
                if args.bridge:
                    checks['saved_theme_reload']='not tested: bridge uses an opaque document origin'
                else:
                    assert page.evaluate("() => localStorage.getItem('evolution-theme')")=='dark'
                    page.reload(wait_until='networkidle')
                    expect(page.locator('.start-page')).to_be_visible()
                    expect(page.locator('html')).to_have_attribute('data-theme','dark')
                    checks['saved_theme_reload']=True
                shot('start-dark.png');checks['light_default_and_theme_toggle']=True
                page.locator('.start-actions [data-page="data"]').click()
                expect(page.locator('#historyUpload')).to_be_attached()
                assert page.evaluate('() => location.hash')=='#data'
                page.select_option('#dataset','live')
                expect(page.locator('#dataset')).to_have_value('live')
                nav('start');page.locator('.start-actions [data-action="try-demo"]').click()
                page.wait_for_selector('.heat-cell')
                assert page.evaluate('() => location.hash')=='#overview'
                expect(page.locator('#dataset')).to_have_value('demo')
                assert page.locator('.kpi-value').first.text_content()=='3,086'
                shot('overview-dark.png')
                checks['introduction_import_and_demo_actions']=True;checks['demo_metrics']=True
                page.locator('.heat-cell').first.click();page.wait_for_selector('dialog .evidence-item')
                assert page.locator('dialog .evidence-item').count()>0
                checks['heatmap_evidence']=True;close()
                nav('audit');page.locator('[data-action="run-audit"]').click();page.wait_for_selector('.finding')
                assert page.locator('.finding').count()==6
                assert page.locator('.protected-item').count()==2
                shot('instruction-audit.png');checks['audit_quotes_and_protections']=True
                page.locator('[data-action="audit-kind"][data-kind="plan"]').click()
                page.locator('[data-action="run-audit"]').click();page.wait_for_selector('.finding')
                assert page.locator('.finding').count()==4
                checks['plan_audit']=True
                nav('skills');page.wait_for_selector('.skill-card');assert page.locator('.skill-card').count()==8
                shot('skill-lab.png');page.locator('[data-action="skill-preview"]').first.click()
                assert 'not an installed skill' in page.locator('#skillEditor').input_value()
                checks['skill_draft']=True;close()
                nav('prompts');page.locator('[data-prompt="instruction-audit"]').click()
                assert '保留明确' in page.locator('#promptEditor').input_value()
                checks['complete_prompt']=True;close()
                nav('reports');expect(page.locator('#reportText')).to_contain_text('## 数据范围')
                assert not page.locator('.report-export').evaluate('(element)=>element.open')
                assert page.locator('.report-details').count()>0
                assert page.locator('.report-details').evaluate_all('(elements)=>elements.every(element=>!element.open)')
                checks['report_progressive_disclosure']=True
                dossier=page.locator('#growthDossier')
                assert '合成演示数据' in dossier.inner_text()
                assert '3,086' in dossier.inner_text()
                assert page.locator('.growth-ledger tbody th').all_text_contents()==[
                    '请/请你','帮我','继续','自然消息中位长度','≤20字短提示','验证/证据','确认']
                assert page.locator('.growth-phase tbody th').all_text_contents()==[
                    '发起/目标','规划/拆解','执行/交付','验证/证据','反馈/迭代','反思/收尾']
                growth=page.evaluate("""async () => (await (await fetch('/api/analysis?mode=demo',{
                    headers:{'X-Evolution-Token':document.querySelector('meta[name=evolution-token]').content}
                })).json()).growth""")
                for signal in growth['comparison']['signals']:
                    row=page.locator(f'[data-growth-signal="{signal["id"]}"]')
                    if signal['kind']=='monthly_endpoint':
                        unit='%' if signal['unit']=='%' else ' Unicode 字符'
                        value=f'{signal["start_value"]:.1f}%' if unit=='%' else f'{signal["start_value"]:,.1f}'.rstrip('0').rstrip('.')+unit
                        assert value in row.inner_text()
                        assert f'{signal["start_denom"]:,}' in row.inner_text()
                        assert signal['start_month'] in row.inner_text() and signal['end_month'] in row.inner_text()
                        assert (' pp' if unit=='%' else ' Unicode 字符') in row.locator('.growth-change').inner_text()
                    else:
                        for period in growth['comparison']['periods']:
                            metric=period['phase_rates' if signal['kind']=='phase' else 'term_rates'][signal['label']]
                            assert f'{metric["rate_pct"]:.1f}%' in row.inner_text()
                            assert f'{metric["hits"]:,} / {metric["denom"]:,}' in row.inner_text()
                        assert ' pp' in row.locator('.growth-change').inner_text()
                assert 1<=page.locator('.growth-evolution li').count()<=6
                assert 'HEURISTIC' in page.locator('.growth-evolution').inner_text()
                page.locator('.growth-evolution [data-action="month"]').first.click()
                page.wait_for_selector('dialog .evidence-item');close()
                assert not page.locator('.growth-protocol').evaluate('(e)=>e.open')
                page.locator('.growth-protocol summary').click()
                assert page.locator('.growth-protocol li').count()==4
                assert '短任务不强制' in page.locator('.growth-protocol').inner_text()
                assert page.locator('.growth-audit [data-audit="keep"] li').count()>0
                assert page.locator('.growth-audit [data-audit="avoid"] li').count()>0
                shot('growth-report-dark.png');checks['growth_dossier_and_evidence']=True
                page.locator('[data-action="theme"]').click();shot('growth-report-light.png')
                page.locator('[data-action="theme"]').click()
                for width in [320,360,736,1024,1512]:
                    page.set_viewport_size({'width':width,'height':1000})
                    assert not page.evaluate('() => document.documentElement.scrollWidth>window.innerWidth'),f'Growth report overflow at {width}'
                    if width==360: shot('growth-report-mobile.png')
                page.set_viewport_size({'width':1512,'height':1120})
                checks['growth_responsive_widths']=[320,360,736,1024,1512]
                open_report_exports()
                with page.expect_download() as download: page.locator('[data-export="html"]').click()
                assert download.value.suggested_filename.endswith('.html')
                with page.expect_download() as download: page.locator('[data-action="share-card"]').click()
                assert download.value.suggested_filename.endswith('.png')
                checks['html_and_png_exports']=True
                page.locator('.report-details:has([data-action="prepare-retro-model"]) > summary').click()
                page.locator('[data-action="prepare-retro-model"]').click();page.wait_for_selector('#packetEditor')
                assert json.loads(page.locator('#packetEditor').input_value())['coverage']['reference_count']==36
                checks['previewed_handoff']=True;close()
                page.select_option('#fromMonth','2026-08')
                page.wait_for_selector('.growth-empty')
                assert '至少需要三个有自然消息的月份' in page.locator('.growth-empty').inner_text()
                assert page.locator('.growth-ledger').count()==0
                assert page.locator('.growth-phase').count()==0
                assert page.locator('.growth-evolution').count()==0
                assert page.locator('.growth-protocol').count()==0
                open_report_exports()
                with page.expect_download() as download: page.locator('[data-export="json"]').click()
                short_report=json.loads(Path(download.value.path()).read_text(encoding='utf-8'))
                assert not short_report['growth']['comparison']['available']
                assert short_report['summary']['natural_messages']<3086
                checks['growth_short_window_and_filtered_export']=True
                page.locator('[data-action="reset-filters"]').click();page.wait_for_selector('.growth-ledger')
                nav('explorer');page.wait_for_selector('.evidence-item')
                page.locator('#evidenceSearch').fill('继续');page.locator('[data-action="search-evidence"]').click()
                expect(page.locator('.evidence-item p').first).to_be_visible()
                expect(page.locator('.evidence-item p').filter(has_not_text='继续')).to_have_count(0)
                checks['message_search']=True
                nav('overview');page.select_option('#fromMonth','2026-06');page.wait_for_timeout(350)
                page.select_option('#toMonth','2026-08');expect(page.locator('.kpi-value').first).to_have_text('1,660')
                checks['month_filter']=True
                page.locator('[data-action="reset-filters"]').click();page.wait_for_timeout(400)
                page.locator('[data-action="theme"]').click();shot('overview-light.png')
                page.locator('[data-action="theme"]').click()
                checks['responsive_widths']=[]
                for width in [360,768,1024,1512]:
                    page.set_viewport_size({'width':width,'height':1000});page.wait_for_timeout(150)
                    assert not page.evaluate('() => document.documentElement.scrollWidth>window.innerWidth'),f'Page overflow at {width}'
                    checks['responsive_widths'].append(width)
                    if width==360: shot('mobile.png')
                page.set_viewport_size({'width':1512,'height':1120})
                page.keyboard.press('Control+k');page.locator('#commandSearch').fill('Skill')
                assert page.locator('.command-row:visible').count()==1
                checks['keyboard_palette']=True;close()
                nav('data');page.locator('#historyUpload').set_input_files(str(ROOT/'examples/normalized.jsonl'))
                expect(page.locator('#dataset')).to_have_value('live')
                nav('overview');expect(page.locator('.kpi-value').first).to_have_text('9')
                assert page.locator('.heat-cell.empty').count()>0
                assert not page.evaluate('() => document.documentElement.scrollWidth>window.innerWidth')
                checks['real_upload_and_empty_months']=True
                nav('reports');page.wait_for_selector('.growth-phase')
                assert '本机导入数据' in page.locator('#growthDossier').inner_text()
                assert page.locator('.growth-phase td.growth-no-data').count()>0
                assert all('无数据' in text for text in page.locator('.growth-phase td.growth-no-data').all_text_contents())
                assert '合成演示数据' not in page.locator('#growthDossier').inner_text()
                checks['growth_imported_empty_months']=True
                nav('data');page.locator('[data-action="clear-confirm"]').click()
                page.locator('#clearText').fill('DELETE LOCAL IMPORTS');page.locator('[data-action="clear-data"]').click()
                expect(page.locator('#modal')).to_be_hidden()
                nav('overview');expect(page.locator('.kpi-value').first).to_have_text('0')
                checks['delete_app_copy']=True
                assert errors==[],errors
                checks['javascript_errors']=errors
                browser.close()
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)
    result={'mode':'actual-backend-fetch-bridge' if args.bridge else 'direct-localhost','checks':checks}
    (out/'browser-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': run()
