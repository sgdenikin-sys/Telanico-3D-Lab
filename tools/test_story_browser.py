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

# Ignore animation/layout-only changes when acknowledging an actual story choice.
DIALOGUE_PROGRESS = "JSON.stringify([s.time,s.modal,s.office,s.line_index,s.lines,s.invoice,s.controls.map(c=>[c.text,c.action,c.art,c.disabled])])"


def exercise(browser, url, output, width, height, touch, full, landmarks_only=False, restart_only=False):
    context = browser.new_context(viewport={"width":width,"height":height},has_touch=touch,
        **({'user_agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'} if touch else {}))
    context.tracing.start(screenshots=False,snapshots=True,sources=False)
    page = context.new_page()
    page.add_init_script("""window.__RABBIT_EVENTS=[];
      setInterval(()=>{const h=document.querySelector('#vorgun-rabbit-animation');
        if(!h)return;const i=h.querySelector('img');const visible=h.style.display==='block'&&!!i?.naturalWidth;
        const previous=window.__RABBIT_EVENTS.at(-1);
        if(!previous||previous.visible!==visible){const r=h.getBoundingClientRect();
          window.__RABBIT_EVENTS.push({visible,time:performance.now(),rect:[r.x,r.y,r.width,r.height]});}
      },50);""")
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
    def compact_modal():
        state=story()
        rect=state['modal_rect'];vp=state['viewport']
        assert rect[2]<vp[0]*0.90 and rect[3]<vp[1]*0.90, (state['modal'],rect,vp)
        assert rect[0]>=0 and rect[1]>=0 and rect[0]+rect[2]<=vp[0] and rect[1]+rect[3]<=vp[1],rect
        if not state['office']:
            assert state['world_visible'] and state['courier_visible'],state
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
              if(stable>=1){const r=document.querySelector('#canvas').getBoundingClientRect();return {action:b.action,x:r.x+(b.rect[0]+b.rect[2]/2)/s.viewport[0]*r.width,y:r.y+(b.rect[1]+b.rect[3]/2)/s.viewport[1]*r.height,clip:b.clip.map((n,i)=>n/(i%2?s.viewport[1]:s.viewport[0])*(i%2?r.height:r.width))};}}
            await new Promise(r=>setTimeout(r,150));
          }throw Error('Missing or unstable story control '+key);
        }""",key)
        clip=point.get('clip')
        if clip and not (clip[1]+8 <= point['y'] <= clip[1]+clip[3]-8):
            # Press the actual in-game office scroll arrow. This tests a
            # player-facing fallback that works even if iOS touch scrolling
            # is unavailable on slow WebGL frames.
            arrow = 'v' if point['y'] > clip[1]+clip[3]-8 else '^'
            available = any(c.get('text') == arrow and not c.get('disabled')
                            for c in story().get('controls', []))
            if available and key not in ('v', '^'):
                button_before = next(c for c in story()['controls'] if c.get('action') == key)
                previous_y = button_before['rect'][1]
                click(arrow)
                # Compare Godot-space coordinates on both sides of the check.
                # CSS-space click positions and Godot viewport coordinates differ
                # on retina / scaled landscape devices.
                wait("""([name, old]) => window.__TELANICO_STORY?.controls?.some(
                    c => c.action===name && Math.abs(c.rect[1]-old)>8)""",
                    [key, previous_y], timeout=15000)
                return click(key, scroll_attempts+1)
            # Fall back to an actual touch swipe on other scrollable screens.
            x=clip[0]+clip[2]*0.6
            y=clip[1]+clip[3]*0.6
            direction=1 if point['y']>clip[1]+clip[3] else -1
            before=story()['frame']
            if touch:
                cdp=context.new_cdp_session(page)
                # SwiftShader/WebGL frames may be slower than CDP dispatches.
                # Without spacing, Godot sees touchStart and touchEnd in one
                # frame and the ScrollContainer never receives a drag.
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':0}]})
                page.wait_for_timeout(130)
                for step in range(1,7):
                    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-direction*clip[3]*0.70*step/6,'id':0}]})
                    page.wait_for_timeout(130)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
                cdp.detach()
            else:
                page.mouse.move(x,y)
                page.mouse.wheel(0,direction*max(100,clip[3]*0.6))
            wait('(before)=>window.__TELANICO_STORY.frame>before',before)
            return click(key, scroll_attempts+1)
        before=story()['frame']
        acknowledge=bool(point.get('action')) or key=='CONTINUE >'
        previous=page.evaluate('()=>{const s=window.__TELANICO_STORY;return '+DIALOGUE_PROGRESS+';}') if acknowledge else None
        print('STORY_TAP',width,key,point['x'],point['y'],flush=True)
        (page.touchscreen.tap if touch else page.mouse.click)(point['x'],point['y'])
        if acknowledge:
            # A newer telemetry frame can precede delivery of the touch event.
            # Wait for meaningful dialogue/session state before paging its reply.
            wait('([before,previous])=>{const s=window.__TELANICO_STORY;return s.frame>before&&'+DIALOGUE_PROGRESS+'!==previous;}',[before,previous])
            print('STORY_DIALOGUE_ACK',width,key,story()['time'],flush=True)
        else:
            wait('(before)=>window.__TELANICO_STORY.frame>before',before)
    def nav(key,group='ui'):
        print('STORY_NAV',width,group,key,flush=True)
        point=page.evaluate(POINT,[group,key])
        before=story()['frame']
        print('STORY_TAP',width,key,point['x'],point['y'],flush=True)
        (page.touchscreen.tap if touch else page.mouse.click)(point['x'],point['y'])
        wait('(before)=>window.__TELANICO_STORY.frame>before',before)
    def uncover_landmark(ident):
        # The approved left HUD overlaps part of the overview on short phones.
        # Reframe using real existing gestures; never click through a HUD button.
        def geometry():
            return page.evaluate("""id=>{
                const w=window.__TELANICO_STATE,s=window.__TELANICO_STORY,p=w.sites[id];
                return {x:p[0],outside:p[0]<12||p[0]>w.viewport[0]-12,
                  covered:s.controls.some(c=>!c.disabled&&c.rect[0]<=p[0]&&p[0]<=c.rect[0]+c.rect[2]&&c.rect[1]<=p[1]&&p[1]<=c.rect[1]+c.rect[3])};
            }""",ident)
        if geometry()['outside']:
            nav('Reset')
            page.evaluate(POINT,['sites',ident])
        current=geometry()
        if current['covered']:
            assert touch, 'Desktop landmark unexpectedly covered by HUD'
            print('STORY_PAN_TO_UNCOVER',width,ident,flush=True)
            cdp=context.new_cdp_session(page)
            x,y=width*.5,height*.8
            cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':0}]})
            page.wait_for_timeout(250)
            for step in range(1,7):
                cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+width*.18*step/6,'y':y,'id':0}]})
                page.wait_for_timeout(250)
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            cdp.detach()
            wait('([id,old])=>window.__TELANICO_STATE.sites[id][0]>old+30',[ident,current['x']])
            page.evaluate(POINT,['sites',ident])
        assert not geometry()['outside'] and not geometry()['covered'], (ident,geometry())

    def shot(name): page.screenshot(path=str(output/f'{name}-{width}.png'),timeout=120000)
    def finish_reply():
        while story()['line_index']<story()['lines']-1:click('CONTINUE >')
        # A new verified fact is reviewed after the NPC's last line, before choices.
        if any(c['text']=='CONTINUE >' for c in story()['controls']):
            click('CONTINUE >')
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
        # Match the existing V2.1 player flow: dismiss the arrival card before
        # picking a nearby department behind it. This never changes geography.
        nav('Outside')
        wait("!window.__TELANICO_STATE.ui.Outside")
        assert story()['time']-before==3, 'Dismissing arrival must not charge time'
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
        compact_modal()
        assert 'Diorama' not in story()['hud']
        assert story()['walk_speed']==9.375 and story()['courier_scale']==3
        assert story()['clock_art'].endswith('clock_analog_blue.png')
        assert story()['time']==0 and story()['invoice']['cargo']=='High Quality Energy (Physical Oil)'
        assert story()['invoice']['quantity']=='' and story()['invoice']['total']==''
        for control in story()['controls']:
            if not control['disabled']:
                assert control['rect'][3]/story()['viewport'][1]*height >= 43.5, control
        shot('initial-invoice')
        click('button_close_invoice.png')
        wait("window.__TELANICO_STORY.modal==='assistant'")
        compact_modal()
        wait('window.__RABBIT_EVENTS.some(e=>e.visible)',timeout=30000)
        wait('window.__RABBIT_EVENTS.some((e,i,a)=>!e.visible&&a.slice(0,i).some(x=>x.visible))',timeout=15000)
        assert story()['assistant_png'].endswith('.png')
        assert story()['assistant_framed']
        state=story();anchor=state['hud']['Assistant'];card=state['modal_rect']
        assert abs(card[0]-anchor[0])<1 and abs(card[1]-anchor[1]-anchor[3]-8)<1, (anchor,card)
        assert all(r[2]>=200 and r[3]>=54 for r in state['hud'].values())
        shot('framed-assistant')
        print('CANONICAL_GIF_TO_PNG_PASS',width,page.evaluate('window.__RABBIT_EVENTS'),flush=True)
        click('CONTINUE')
        wait("!window.__TELANICO_STORY.locked")
        page.evaluate('window.__TELANICO_COMMAND={rate:12}')
        shot('story-world')
        if restart_only:
            click('button_menu.png')
            wait("window.__TELANICO_STORY.modal==='menu'")
            click('RESTART GAME')
            wait("window.__TELANICO_STORY.screen==='intro'&&window.__TELANICO_STORY.time===0")
            shot('menu-restarted')
            audio=page.evaluate('window.VorGunAudio.diagnostic()')
            assert audio['musicStarts']==1,audio
            assert not errors,errors
            print('STORY_RESTART_BROWSER_PASS',width,'real menu touch/mouse callback; no runtime errors',flush=True)
            return
        # The exact existing gesture handler is also exercised by the V2.1 suite.
        if touch:
            cdp=context.new_cdp_session(page)
            for kind,points in [('touchStart',[(width*.47,height*.6),(width*.57,height*.6)]),('touchMove',[(width*.4,height*.6),(width*.64,height*.6)]),('touchEnd',[])]:
                cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'x':x,'y':y,'id':i} for i,(x,y) in enumerate(points)]})
            wait('window.__TELANICO_STATE.camera_size<124')
            nav('Reset')
        if landmarks_only:
            for ident in page.evaluate('Object.keys(window.__TELANICO_STATE.sites)'):
                uncover_landmark(ident)
                nav(ident,'sites')
                wait('(id)=>window.__TELANICO_STATE.selected===id&&window.__TELANICO_STATE.ui.Walk',ident)
                assert story()['time']==0, 'Selection must never spend story time'
                nav('Cancel')
                wait("!window.__TELANICO_STATE.ui.Walk")
            shot('all-15-landmarks')
            assert not errors,errors
            print('STORY_LANDMARK_SELECTION_PASS',width,'all 15 through real touch/mouse with approved HUD',flush=True)
            return
        visit('operations',['ops_qty','ops_report','ops_full_documents'] if full else ['ops_estimate','ops_qty'])
        assert story()['invoice']['quantity']=='8,470 MT'
        assert story()['time_titles']['history'], 'Actual travel/dialogue must publish time-loss feedback'
        assert all(event['minutes']>0 for event in story()['time_titles']['history'])
        print('TIME_LOSS_EVENTS_PASS',width,story()['time_titles']['history'],flush=True)
        if full:
            walk('tube_w');transfer()
            visit('contracts',['contract_entity','contract_terms','contract_fixing','contract_verified_precision'])
            visit('trader',['trader_price'])
            visit('vat',['vat_treatment'])
            visit('fx',['fx_rate'])
            # The player can always use the actual Reset control to reframe the
            # two-island map before selecting a distant tube terminal. A
            # follow-camera close-up can place tube_e outside the viewport.
            nav('Reset')
            wait('window.__TELANICO_STATE.state==="IDLE" && !window.__TELANICO_STATE.follow')
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
        (output/f'story-failure-{width}.json').write_text(json.dumps({'state':story(),'world':page.evaluate('window.__TELANICO_STATE'),'errors':errors},indent=2))
        shot('story-failure')
        raise
    finally:
        context.tracing.stop(path=str(output/f'story-trace-{width}.zip'))
        context.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',nargs='?',default='build/web')
    parser.add_argument('--url')
    parser.add_argument('--case',type=int,choices=[1280,844,667])
    parser.add_argument('--landmarks-only',action='store_true')
    parser.add_argument('--restart-only',action='store_true')
    args=parser.parse_args()
    if args.landmarks_only and args.restart_only:
        parser.error('choose only one focused browser test')
    if args.case==667 and not args.landmarks_only:
        parser.error('--case 667 requires --landmarks-only; the full story phone case is 844')
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
            cases=[(1280,720,False,False),(844,390,True,True)]
            if args.landmarks_only:cases.append((667,375,True,False))
            for width,height,touch,full in cases:
                if args.case is None or args.case==width:exercise(browser,url,output,width,height,touch,full,args.landmarks_only,args.restart_only)
            browser.close()
    finally:
        if server:server.shutdown();server.server_close()
if __name__=='__main__':main()
