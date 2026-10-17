import asyncio, json, os, re, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from pydub import AudioSegment
import edge_tts

DIR=Path("demo-output-v2"); DIR.mkdir(exist_ok=True)
(DIR/"voice").mkdir(exist_ok=True)
URL=os.getenv("DEMO_URL","https://madhav-order-desk.opalsage3.chatgpt.site")
BEATS=[
("intro","Meet MADHAV Order Desk: a simple way for small bakeries to turn customer messages into checked orders, with the owner in control.","MADHAV  /  REAL APP DEMO"),
("aanya","Aanya asks in Hinglish for one chocolate cake tomorrow. Let's prepare the reply.","AANYA  /  HINGLISH REQUEST"),
("aanya_parse","This is a real AMD TokenFactory inference request. The model identifies her product, quantity and pickup date for owner review.","AMD LIVE  /  REQUEST UNDERSTANDING"),
("aanya_price","The catalog—not the AI—sets the price at nine hundred rupees, with a suggested four hundred and fifty rupee advance.","₹900 TOTAL  /  ₹450 ADVANCE"),
("aanya_reserve","Only my approval reserves the cake. Preparing the draft never books it.","OWNER APPROVAL  /  RESERVE"),
("aanya_reply","I approve the reply separately. Here it appears in the demo chat; it's not a real WhatsApp send.","REPLY APPROVED  /  DEMO CHAT"),
("aanya_orders","The order book now shows Aanya's nine hundred rupee order. No payment has been recorded.","ORDER BOOK  /  NOT YET PAID"),
("rohan","Rohan wants Red Velvet. Let's check what happens when a product is sold out.","ROHAN  /  RED VELVET"),
("rohan_blocked","Capacity is zero. MADHAV blocks the booking and offers available alternatives. It never substitutes a product automatically.","SOLD OUT  /  ALTERNATIVES"),
("rohan_followup","Rohan chooses vanilla in a follow-up. The new customer message is fictional demo data.","CUSTOMER CHOOSES VANILLA"),
("rohan_parse","We review the new proposal: one vanilla cake, seven hundred and fifty rupees.","VANILLA CLOUD  /  ₹750"),
("rohan_reserve","Now I approve the vanilla order and its reply. Red Velvet remains unbooked.","VANILLA APPROVED"),
("meera","Meera needs two cupcake boxes tomorrow.","MEERA  /  TWO BOXES"),
("meera_parse","The catalog price is four hundred and twenty per box. That's eight hundred and forty in total.","2 × ₹420  =  ₹840"),
("meera_reserve","I reserve this order and approve the confirmation separately.","OWNER RESERVES"),
("meera_orders","In Orders, we can see the full eight hundred and forty rupee total.","ORDER VALUE  /  ₹840"),
("meera_payment","Now I manually record four hundred and twenty rupees received, after independent confirmation.","RECORD ₹420 RECEIVED"),
("meera_balance","MADHAV shows four hundred and twenty paid, and four hundred and twenty still due. A payment claim never changes the ledger automatically.","₹420 PAID  /  ₹420 DUE"),
("close","AMD handles language understanding. Our code enforces prices, stock and owner approval. This is a chat simulation; official WhatsApp integration comes later. That's MADHAV.","OWNER-CONTROLLED COMMERCE")
]
async def generate():
    for i,(_,speech,_) in enumerate(BEATS):
        path=DIR/"voice"/f"{i:02}.mp3"
        for retry in range(3):
            try:
                await edge_tts.Communicate(speech,"en-US-AriaNeural",rate="+15%").save(str(path))
                if path.stat().st_size<2500: raise ValueError("bad voice output")
                break
            except Exception:
                if retry==2:raise
                await asyncio.sleep(retry+1)
asyncio.run(generate())
voices=[AudioSegment.from_file(DIR/"voice"/f"{i:02}.mp3") for i in range(len(BEATS))]
def check(expr,msg):
    if not expr:raise AssertionError(msg)
    print("PASS:",msg,flush=True)
def choose(page,locator,msg):
    locator.click(timeout=7000);print("ACTION:",msg,flush=True)
def setup(page):
    page.goto(URL,wait_until="domcontentloaded",timeout=90000)
    page.get_by_text("Aanya Kapoor").first.wait_for(timeout=30000)
    page.wait_for_timeout(3800) # hydration before first React action
    choose(page,page.locator("nav button").filter(has_text="Setup"),"Setup")
    page.get_by_text("Choose your engine").wait_for(timeout=20000)
    choose(page,page.locator("label.modechoice").filter(has_text="AMD live mode"),"AMD live mode")
    choose(page,page.get_by_role("button",name="Reset sample workspace"),"Open reset")
    choose(page,page.get_by_role("button",name="Reset demo"),"Reset")
    choose(page,page.locator("nav button").filter(has_text="Inbox"),"Inbox")
    page.locator(".desk").wait_for(timeout=15000)
    check("AMD live mode" in page.locator("body").inner_text(),"AMD live mode selected")
def overlay(page,label,n):
    page.evaluate("""({label,n})=>{
      if(!document.getElementById('studio-style')){
        let s=document.createElement('style');s.id='studio-style';
        s.textContent='#studio-bar{position:fixed;bottom:10px;left:260px;right:20px;z-index:9900;border-radius:10px;background:rgba(22,32,47,.94);padding:13px 18px;color:white;box-shadow:0 4px 20px #0003;font:600 17px/1.1 Arial,sans-serif;pointer-events:none} #studio-tag{position:fixed;top:10px;right:14px;z-index:9900;border-radius:40px;background:#fff;color:#334155;padding:7px 12px;font:600 11px Arial,sans-serif;pointer-events:none}';
        document.head.appendChild(s);
      }
      let b=document.getElementById('studio-bar');if(!b){b=document.createElement('div');b.id='studio-bar';document.body.appendChild(b)}
      b.textContent=String(n).padStart(2,'0')+'   /   '+label;
      if(!document.getElementById('studio-tag')){
        let t=document.createElement('div');t.id='studio-tag';t.textContent='FICTIONAL CUSTOMERS · AMD LIVE';document.body.appendChild(t)
      }
    }""",{"label":label,"n":n})
def action(page,k):
    select=lambda who:choose(page,page.locator("button.chatrow").filter(has_text=who),who)
    nav=lambda tab:choose(page,page.locator("nav button").filter(has_text=tab),tab)
    def prepare():
        choose(page,page.get_by_role("button",name="Prepare reply"),"Prepare reply")
        page.locator(".proposal").wait_for(timeout=60000)
        check("AMD" in page.locator(".sourcelabel").inner_text(),"Live AMD result visible")
    reserve=lambda:choose(page,page.get_by_role("button",name="Approve & reserve order"),"Reserve")
    send=lambda:choose(page,page.get_by_role("button",name="Approve reply"),"Approve reply")
    if k=="intro":check("Good conversations" in page.locator("body").inner_text(),"Overview")
    elif k=="aanya":
        select("Aanya Kapoor")
        check("chocolate cake" in page.locator(".conversation").inner_text(),"Aanya's chat")
    elif k=="aanya_parse":
        prepare();check("₹900" in page.locator(".proposal").inner_text(),"Aanya's proposal")
    elif k=="aanya_price":
        check("₹900" in page.locator(".total").inner_text(),"₹900 catalog total")
        check(page.get_by_role("button",name="Approve & reserve order").is_enabled(),"Aanya reserve permitted")
    elif k=="aanya_reserve":
        reserve();check("Order reserved" in page.locator("body").inner_text(),"Aanya reserved")
    elif k=="aanya_reply":
        send();check("You · approved reply" in page.locator(".conversation").inner_text(),"Aanya reply")
    elif k=="aanya_orders":
        nav("Orders");check("Aanya Kapoor" in page.locator(".ordertable").inner_text(),"Aanya in Orders")
    elif k=="rohan":
        nav("Inbox");select("Rohan Mehta")
        check("red velvet" in page.locator(".conversation").inner_text().lower(),"Rohan chat")
    elif k=="rohan_blocked":
        prepare()
        out=page.locator(".proposal").inner_text()
        check("Not enough capacity" in out and "Available alternatives" in out and "Vanilla Cloud" in out,"Rohan blocked and alternatives")
        check(not page.get_by_role("button",name="Approve & reserve order").is_enabled(),"No red velvet reservation")
    elif k=="rohan_followup":
        page.locator("#message-input").fill("Kal 1 vanilla cake kar do")
        page.wait_for_timeout(500)
        choose(page,page.get_by_role("button",name="Add simulated customer message"),"Add customer follow-up")
        check("Kal 1 vanilla cake kar do" in page.locator(".conversation").inner_text(),"Vanilla follow-up shown")
    elif k=="rohan_parse":
        prepare();check("₹750" in page.locator(".total").inner_text(),"₹750 vanilla proposal")
        check(page.get_by_role("button",name="Approve & reserve order").is_enabled(),"Vanilla bookable")
    elif k=="rohan_reserve":
        reserve();check("Order reserved" in page.locator("body").inner_text(),"Vanilla reserved")
        send()
    elif k=="meera":
        select("Meera Shah");check("2 boxes of cupcakes" in page.locator(".conversation").inner_text(),"Meera chat")
    elif k=="meera_parse":
        prepare();check("₹840" in page.locator(".total").inner_text(),"₹840 proposal")
    elif k=="meera_reserve":
        reserve();check("Order reserved" in page.locator("body").inner_text(),"Meera reserved")
        send()
    elif k=="meera_orders":
        nav("Orders");check("Meera Shah" in page.locator(".ordertable").inner_text(),"Meera order")
    elif k=="meera_payment":
        row=page.locator(".ordertable tbody tr").filter(has_text="Meera Shah")
        choose(page,row.get_by_role("button",name="Record payment"),"Record payment")
        page.get_by_role("spinbutton").last.fill("420")
        page.wait_for_timeout(450)
        choose(page,page.get_by_role("button",name="Confirm received payment"),"Confirm received payment")
    elif k=="meera_balance":
        row=page.locator(".ordertable tbody tr").filter(has_text="Meera Shah")
        check("₹420 paid" in row.inner_text() and "₹420 due" in row.inner_text(),"₹420 paid and due")
    elif k=="close":
        nav("Inbox");check("Active orders" in page.locator(".stats").inner_text(),"Final overview")
    else:raise ValueError(k)
def stamp(sec):
    ms=round(sec*1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    ctx=browser.new_context(viewport={"width":1600,"height":900},device_scale_factor=1,
        record_video_dir=str(DIR/"recordings"),record_video_size={"width":1600,"height":900})
    prep=ctx.new_page();setup(prep);prep.close()
    start=time.monotonic()
    page=ctx.new_page();video=page.video
    page.goto(URL,wait_until="domcontentloaded",timeout=90000)
    page.get_by_text("Aanya Kapoor").first.wait_for(timeout=30000)
    page.wait_for_timeout(3800)
    events=[]
    for i,(key,speech,label) in enumerate(BEATS):
        action(page,key)
        overlay(page,label,i+1)
        page.wait_for_timeout(550)
        begin=time.monotonic()-start
        events.append({"step":key,"start":round(begin,3),"duration":round(len(voices[i])/1000,3),"spoken":speech})
        print("VOICE SYNC:",key,"at",round(begin,2),"for",round(len(voices[i])/1000,2),"seconds",flush=True)
        time.sleep(len(voices[i])/1000+0.6)
    page.screenshot(path=str(DIR/"verified-final-frame.png"))
    page.wait_for_timeout(1000)
    elapsed=time.monotonic()-start
    page.close();ctx.close();browser.close()
    raw=Path(video.path())
    probe=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",str(raw)],text=True)
    raw_duration=float(probe.strip())
    drift=raw_duration-elapsed
    check(abs(drift)<2.5,f"Timing drift <2.5 seconds: {drift:.2f}")
    silence=AudioSegment.silent(duration=round((raw_duration+1)*1000),frame_rate=44100)
    cues=[]
    for i,e in enumerate(events):
        t=e["start"]+max(0,drift)
        silence=silence.overlay(voices[i],position=round(t*1000))
        words=e["spoken"].split()
        groups=[" ".join(words[j:j+10]) for j in range(0,len(words),10)]
        start_c=t
        for group in groups:
            d=e["duration"]*len(group.split())/len(words)
            cues.append((start_c,start_c+d,group))
            start_c+=d
    sub=DIR/"MADHAV-Synced-Captions.srt"
    with sub.open("w",encoding="utf8") as f:
        for n,(a,b,c) in enumerate(cues,1):
            f.write(f"{n}\n{stamp(a)} --> {stamp(b)}\n{c}\n\n")
    wav=DIR/"narration.wav";silence.export(wav,format="wav")
    report={"sample_mode":False,"verified_steps":len(events),"duration":raw_duration,
        "narration":"en-US-AriaNeural","timing_drift":drift,"actions":events}
    (DIR/"recording-verification.json").write_text(json.dumps(report,indent=2))
    mp4=DIR/"MADHAV-Order-Desk-Showcase-v2.mp4"
    filt=f"scale=1920:1080,subtitles={sub}:force_style='FontName=DejaVu Sans,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101E31,Outline=2,Shadow=1,MarginV=115,Alignment=2'"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),"-i",str(wav),
        "-filter_complex",f"[0:v]{filt}[v]","-map","[v]","-map","1:a",
        "-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","160k","-movflags","+faststart","-shortest",str(mp4)],check=True)
    check(mp4.exists() and mp4.stat().st_size>250000,"MP4 rendered")
    print("VIDEO_OUTPUT:",mp4,mp4.stat().st_size,flush=True)
