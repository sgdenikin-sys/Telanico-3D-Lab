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
    context = browser.new_context(viewport={"width":width,"height":height},has_touch=touch,
        **({'user_agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'} if touch else {}))
    context.tracing.start(screenshots=False,snapshots=True,sources=False)
    page = context.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
    def console(message):
        print('STORY_CONSOLE',message.type,message.text,flush=True)
        if 'SCRIPT ERROR' in message.text or 'Parse Error' in message.text or 'ERROR:' in message.text:
            errors.append(message.text)
    page.on('console',console)
    def wait(expr,arg=None,timeout=120000):
        page.wait_for_function(expr,arg=arg,timeout=timeout,polling=250)
    def story(): return page.evaluate('window.__TELANICO_STORY')
    def click(key, scroll_attempts=0):
        print('STORY_ACTION',width,key,'scroll_attempt',scroll_attempts,flush=True)
        if scroll_attempts >= 10:
            controls=story().get('controls',[])
            selected=[c for c in controls if c.get('action')==key or c.get('text')==key or c.get('art')==key]
            raise AssertionError(f'Control {key} remains outside viewport after {scroll_attempts} scrolls: {selected}')
        point=page.evaluate("""async key=>{
          const deadline=performance.now()+120000;let frame=-1,signature='',stable=0;
          while(performance.now()<deadline){
            const s=window.__TELANICO_STORY;
            const b=s?.controls?.find(b=>!b.disabled&&(b.action===key||b.text===key||b.art===key));
            if(b&&s.frame!==frame){const next=JSON.stringify(b.rect);stable=next===signature?stable+1:0;signature=next;frame=s.frame;
              if(stable>=1){const r=document.querySelector('#canvas').getBoundingClientRect();return {x:r.x+(b.rect[0]+b.rect[2]/2)/s.viewport[0]*r.width,y:r.y+(b.rect[1]+b.rect[3]/2)/s.viewport[1]*r.height,clip:b.clip.map((n,i)=>n/(i%2?s.viewport[1]:s.viewport[0])*(i%2?r.height:r.width))};}}
            await new Promise(r=>setTimeout(r,150));
          }throw Error('Missing or unstable story control '+key);
        }""",key)
        clip=point.get('clip')
        if clip and not (clip[1]+8 <= point['y'] <= clip[1]+clip[3]-8):
            # Scroll the real Godot ScrollContainer; never invoke an offscreen button.
            x=clip[0]+clip[2]*0.6
            y=clip[1]+clip[3]*0.6
            direction=1 if point['y']>clip[1]+clip[3] else -1
            before=story()['frame']
            if touch:
                cdp=context.new_cdp_session(page)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':0}]})
                for step in range(1,5):
                    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-direction*clip[3]*0.45*step/4,'id':0}]})
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                cdp.detach()
            else:
                page.mouse.move(x,y)
                page.mouse.wheel(0,direction*max(100,clip[3]*0.6))
            wait('(before)=>window.__TELANICO_STORY.frame>before',before)
            return click(key, scroll_attempts+1)
        before=story()['frame']
        (page.touchscreen.tap if touch else page.mouse.click)(point['x'],point['y'])
        wait('(before)=>window.__TELANICO_STORY.frame>before',before)
    def nav(key,group='ui'):
        print('STORY_NAV',width,group,key,flush=True)
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
        # Tube state may last less than Playwright's polling interval on WebGL.
        # Assert the observable completed journey rather than requiring a sampled
        # intermediate animation frame. Keep the travel-cost assertion.
        before=story()['time']
        origin=page.evaluate('window.__TELANICO_STATE.current')
        nav('Tube')
        wait("""([origin,before]) => {
            const world=window.__TELANICO_STATE;
            const session=window.__TELANICO_STORY;
            return world && session && world.state==='IDLE'
                && world.current!==origin && session.time>before;
        }""",[origin,before])
        assert story()['time']-before==3, 'Tube must charge exactly three minutes'
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
        for control in story()['controls']:
            if not control['disabled']:
                assert control['rect'][3]/story()['viewport'][1]*height >= 43.5, control
        shot('initial-invoice')
        click('button_close_invoice.png')
        wait("window.__TELANICO_STORY.modal==='assistant'")
        click('CONTINUE')
        wait("!window.__TELANICO_STORY.locked")
        page.evaluate('window.__TELANICO_COMMAND={rate:12}')
        shot('story-world')
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
            click('SOUND EFFECTS')
            wait('!window.VorGunAudio.diagnostic().sfxEnabled')
            click('SOUND EFFECTS')
            wait('window.VorGunAudio.diagnostic().sfxEnabled')
            click('RESUME GAME')
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
