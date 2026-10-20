"""Actual Godot Web story UI, trusted clicks/touches, persistent failure evidence."""
import argparse
import functools
import http.server
import json
from pathlib import Path
import shutil
import threading
from playwright.sync_api import sync_playwright
from test_v2_browser import POINT


def exercise(browser, url, output, width, height, touch, full):
    context = browser.new_context(viewport={"width":width,"height":height},has_touch=touch)
    context.tracing.start(screenshots=False,snapshots=True,sources=False)
    page = context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
    page.on('console',lambda m: print('STORY_CONSOLE',m.type,m.text,flush=True))
    def wait(expr,arg=None,timeout=120000):
        page.wait_for_function(expr,arg=arg,timeout=timeout,polling=250)
    def story(): return page.evaluate('window.__TELANICO_STORY')
    def click(key):
        print('STORY_ACTION',width,key,flush=True)
        point=page.evaluate("""async key=>{
          const deadline=performance.now()+120000;let frame=-1,signature='',stable=0;
          while(performance.now()<deadline){
            const s=window.__TELANICO_STORY;
            const b=s?.controls?.find(b=>!b.disabled&&(b.action===key||b.text===key||b.art===key));
            if(b&&s.frame!==frame){const next=JSON.stringify(b.rect);stable=next===signature?stable+1:0;signature=next;frame=s.frame;
              if(stable>=1){const r=document.querySelector('#canvas').getBoundingClientRect();return {x:r.x+(b.rect[0]+b.rect[2]/2)/s.viewport[0]*r.width,y:r.y+(b.rect[1]+b.rect[3]/2)/s.viewport[1]*r.height};}}
            await new Promise(r=>setTimeout(r,150));
          }throw Error('Missing or unstable story control '+key);
        }""",key)
        before=story()['frame']
        (page.touchscreen.tap if touch else page.mouse.click)(point['x'],point['y'])
        wait('(before)=>window.__TELANICO_STORY.frame>before',before)
    def nav(key,group='ui'):
        point=page.evaluate(POINT,[group,key])
        before=story()['frame']
        (page.touchscreen.tap if touch else page.mouse.click)(point['x'],point['y'])
        wait('(before)=>window.__TELANICO_STORY.frame>before',before)
    def shot(name): page.screenshot(path=str(output/f'{name}-{width}.png'),timeout=120000)
    def finish_reply():
        while story()['line_index']<story()['lines']-1:click('CONTINUE →')
        # A new verified fact is reviewed after the NPC's last line, before choices.
        if any(c['text']=='CONTINUE →' for c in story()['controls']):
            click('CONTINUE →')
            wait("window.__TELANICO_STORY.modal==='invoice'")
            shot('verified-invoice')
            click('button_close_invoice.png')
            wait("window.__TELANICO_STORY.modal==='assistant'")
            shot('assistant')
            click('CONTINUE')
            wait("window.__TELANICO_STORY.modal===''")
    def walk(target):
        before=story()['time']
        nav(target,'sites')
        wait('(id)=>window.__TELANICO_STATE.selected===id&&window.__TELANICO_STATE.ui.Walk',target)
        nav('Walk')
        wait('(id)=>window.__TELANICO_STATE.current===id&&window.__TELANICO_STATE.state==="IDLE"',target)
        assert story()['time']>before
    def transfer():
        nav('Tube')
        wait("window.__TELANICO_STATE.state==='TUBE'")
        wait("window.__TELANICO_STATE.state==='IDLE'")
    def visit(target,actions):
        walk(target)
        assert story()['office']==''
        nav('Enter')
        wait('(id)=>window.__TELANICO_STORY.office===id',target)
        assert story()['locked']
        shot('office-'+target)
        finish_reply()
        if any(c['action']=='__wait_lunch__' for c in story()['controls']):click('__wait_lunch__');finish_reply()
        elif any(c['action']=='greet_polite' for c in story()['controls']):click('greet_polite');finish_reply()
        for action in actions:
            click(action)
            if not story()['won']:finish_reply()
        if not story()['won']:
            click('LEAVE OFFICE')
            wait("window.__TELANICO_STORY.office===''")
    try:
        page.goto(url+'?test=1&story_test=1',wait_until='domcontentloaded',timeout=120000)
        wait('window.__TELANICO_STORY?.screen==="intro"',timeout=180000)
        shot('intro')
        click('CHOOSE YOUR ROLE')
        wait("window.__TELANICO_STORY.screen==='characters'")
        assert sum(c['disabled'] for c in story()['controls'] if c['text']=='LOCKED')==3
        shot('characters')
        click('SELECT COOPER')
        wait("window.__TELANICO_STORY.modal==='invoice'")
        assert story()['time']==0 and story()['invoice']['cargo']=='High Quality Energy (Physical Oil)'
        assert story()['invoice']['quantity']=='' and story()['invoice']['total']==''
        shot('initial-invoice')
        click('button_close_invoice.png')
        wait("window.__TELANICO_STORY.modal==='assistant'")
        click('CONTINUE')
        wait("!window.__TELANICO_STORY.locked")
        page.evaluate('window.__TELANICO_COMMAND={rate:12}')
        shot('story-world')
        await_menu=False
        # The exact existing gesture handler is also exercised by the V2.1 suite.
        if touch:
            cdp=context.new_cdp_session(page)
            for kind,points in [('touchStart',[(width*.47,height*.6),(width*.57,height*.6)]),('touchMove',[(width*.4,height*.6),(width*.64,height*.6)]),('touchEnd',[])]:
                cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'x':x,'y':y,'id':i} for i,(x,y) in enumerate(points)]})
            wait('window.__TELANICO_STATE.camera_size<124')
            nav('Reset')
        visit('operations',['ops_qty','ops_report','ops_full_documents'] if full else ['ops_estimate','ops_qty'])
        assert story()['invoice']['quantity']=='8,470 MT'
        if full:
            walk('tube_w');transfer()
            visit('contracts',['contract_entity','contract_terms','contract_fixing','contract_verified_precision'])
            visit('trader',['trader_price'])
            visit('vat',['vat_treatment'])
            visit('fx',['fx_rate'])
            walk('tube_e');transfer()
            visit('lc',['lc_terms','lc_docs','lc_match','lc_original'])
            visit('settlements',['settlements_check','settlements_release'])
            wait('window.__TELANICO_STORY.won&&window.__TELANICO_STORY.modal==="result"')
            assert story()['time']==114
            shot('victory')
            click('PLAY AGAIN')
            wait('window.__TELANICO_STORY.screen==="intro"&&window.__TELANICO_STORY.time===0')
            shot('restarted')
        else:
            # Check menu/music ownership after office and modal transitions.
            click('button_menu.png')
            wait("window.__TELANICO_STORY.modal==='menu'")
            shot('menu')
            click('RETURN TO GAME')
        audio=page.evaluate('window.VorGunAudio.diagnostic()')
        assert audio['musicStarts']==1, audio
        assert not errors,errors
        (output/f'story-result-{width}.json').write_text(json.dumps({'state':story(),'audio':audio,'errors':errors},indent=2))
        print('STORY_BROWSER_PASS',width,'full' if full else 'opening-office-wrong-answer',flush=True)
    except Exception:
        (output/f'story-failure-{width}.json').write_text(json.dumps({'state':story(),'errors':errors},indent=2))
        shot('story-failure')
        raise
    finally:
        context.tracing.stop(path=str(output/f'story-trace-{width}.zip'))
        context.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',nargs='?',default='build/web')
    parser.add_argument('--url')
    parser.add_argument('--case',type=int,choices=[1280,844])
    args=parser.parse_args()
    output=Path('build/screenshots/story');output.mkdir(parents=True,exist_ok=True)
    server=None
    if args.url:url=args.url
    else:
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=args.directory))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url=f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--use-angle=swiftshader','--enable-webgl','--enable-unsafe-swiftshader'])
            for width,height,touch,full in [(1280,720,False,False),(844,390,True,True)]:
                if args.case is None or args.case==width:exercise(browser,url,output,width,height,touch,full)
            browser.close()
    finally:
        if server:server.shutdown();server.server_close()
if __name__=='__main__':main()
