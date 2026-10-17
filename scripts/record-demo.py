import asyncio, json, os, subprocess, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from pydub import AudioSegment
import edge_tts

OUT=Path("demo-output"); OUT.mkdir(exist_ok=True)
HOST=os.getenv("DEMO_URL","http://127.0.0.1:5173")
VOICE="en-GB-SoniaNeural"
scenes=[
("intro", "MADHAV Order Desk helps home bakeries turn customer chats into reviewed orders. Owners need to confirm availability, pickup dates, prices, and received payments. Here's how the working demo handles those decisions.", 17),
("aanya", "Aanya asks in Hinglish for a chocolate cake tomorrow. We prepare the request, check the catalog price of nine hundred rupees, and reserve only after owner approval. The suggested advance is four hundred and fifty rupees. A prepared reply alone never books an order.", 30),
("rohan", "Rohan asks for Red Velvet, but its daily capacity is zero. The assistant flags the unavailable cake and suggests cakes that can be made on his requested date. It doesn't substitute products without permission. When Rohan chooses vanilla in a follow-up message, we prepare and approve that separate request for seven hundred and fifty rupees.", 43),
("meera", "Meera requests two boxes of cupcakes. At four hundred and twenty rupees per box, the order total is eight hundred and forty. The owner manually records four hundred and twenty rupees received, and the order book shows four hundred and twenty still due. A customer saying paid cannot update the ledger on its own.", 37),
("close", "The model can help understand customer language, while the application's own code checks catalog prices, availability and payment bounds. This recording demonstrates the clearly labelled sample mode, not a live AMD inference request. It's a WhatsApp-style simulation, not a real messaging or payment connection. Our next step is merchant pilots, followed by an official WhatsApp integration.", 31),
]
async def voice():
    for id,s,duration in scenes:
        await edge_tts.Communicate(s,VOICE,rate="+3%").save(str(OUT/f"{id}.mp3"))
asyncio.run(voice())
audio=AudioSegment.silent(duration=0)
subtitle=[]
cursor=0.0
for id,s,duration in scenes:
    segment=AudioSegment.from_file(OUT/f"{id}.mp3")
    if len(segment)>duration*1000-600:
        raise RuntimeError(f"Narration too long for {id}: {len(segment)} ms vs {duration*1000}")
    subtitle.append((cursor+0.6,cursor+0.6+len(segment)/1000,s))
    audio += AudioSegment.silent(duration=600)+segment+AudioSegment.silent(duration=duration*1000-600-len(segment))
    cursor+=duration
audio.export(OUT/"narration.wav",format="wav")
def stamp(t):
    h=int(t//3600);m=int(t//60%60);s=int(t%60);ms=int((t-int(t))*1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
with open(OUT/"MADHAV-Demo-Captions.srt","w") as f:
    for i,(a,b,s) in enumerate(subtitle,1):
        f.write(f"{i}\n{stamp(a)} --> {stamp(b)}\n{s}\n\n")

def attempt(action,desc):
    try: action(); print("STEP OK:",desc,flush=True)
    except Exception as e:\n        print("STEP FAILED:",desc,str(e)[:300],flush=True)\n        raise

def hold(t0,duration):
    remain=duration-(time.monotonic()-t0)
    if remain>0: time.sleep(remain)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    context=browser.new_context(viewport={"width":1440,"height":900},record_video_dir=str(OUT/"recordings"),record_video_size={"width":1280,"height":800},device_scale_factor=1)
    page=context.new_page()
    page.goto(HOST,wait_until="domcontentloaded",timeout=90000)
    page.wait_for_timeout(3500)
    print("LANDING:",page.title(),page.url,flush=True)
    page.screenshot(path=str(OUT/"app-start.png"))
    assert page.get_by_text("Aanya Kapoor").count()>0, "Application not loaded; refusing fictional demonstration"
    # Explicitly select sample mode. No AMD AI action is claimed in narration.
    attempt(lambda:page.get_by_role("button",name="Setup").click(),"Setup")
    attempt(lambda:page.get_by_text("Sample mode",exact=True).first.click(),"Select sample mode")
    attempt(lambda:page.get_by_role("button",name="Reset sample workspace").click(),"Reset control")
    attempt(lambda:page.get_by_role("button",name="Reset demo").click(),"Fresh workspace")
    attempt(lambda:page.locator("nav button").filter(has_text="Inbox").click(),"Inbox")
    starts=[]
    for id,script,duration in scenes:
        t=time.monotonic();starts.append((id,t))
        if id=="intro":
            attempt(lambda:page.get_by_role("button",name="Inbox").click(),"Opening inbox")
        if id=="aanya":
            attempt(lambda:page.locator("button.chatrow").filter(has_text="Aanya Kapoor").click(),"Aanya customer")
            attempt(lambda:page.get_by_role("button",name="Prepare reply").click(),"Prepare Aanya")
            page.wait_for_timeout(1300)
            attempt(lambda:page.get_by_role("button",name="Approve & reserve order").click(),"Reserve Aanya")
            page.wait_for_timeout(1400)
            attempt(lambda:page.get_by_role("button",name="Approve reply").click(),"Approve Aanya reply")
            page.wait_for_timeout(1700)
            attempt(lambda:page.get_by_role("button",name="Orders",exact=False).first.click(),"Aanya orders")
            page.wait_for_timeout(2300)
            attempt(lambda:page.get_by_role("button",name="Inbox",exact=False).first.click(),"Back to inbox")
        if id=="rohan":
            attempt(lambda:page.locator("button.chatrow").filter(has_text="Rohan Mehta").click(),"Rohan customer")
            attempt(lambda:page.get_by_role("button",name="Prepare reply").click(),"Prepare Red Velvet")
            page.wait_for_timeout(5000)
            attempt(lambda:page.locator("#message-input").fill("Kal 1 vanilla cake kar do"),"Rohan chooses vanilla")
            attempt(lambda:page.get_by_role("button",name="Add simulated customer message").click(),"Add follow-up")
            attempt(lambda:page.get_by_role("button",name="Prepare reply").click(),"Prepare vanilla")
            page.wait_for_timeout(1500)
            attempt(lambda:page.get_by_role("button",name="Approve & reserve order").click(),"Reserve vanilla")
            page.wait_for_timeout(1300)
            attempt(lambda:page.get_by_role("button",name="Approve reply").click(),"Approve Rohan reply")
        if id=="meera":
            attempt(lambda:page.locator("button.chatrow").filter(has_text="Meera Shah").click(),"Meera customer")
            attempt(lambda:page.get_by_role("button",name="Prepare reply").click(),"Prepare cupcakes")
            page.wait_for_timeout(1600)
            attempt(lambda:page.get_by_role("button",name="Approve & reserve order").click(),"Reserve cupcakes")
            page.wait_for_timeout(1300)
            attempt(lambda:page.get_by_role("button",name="Approve reply").click(),"Approve Meera reply")
            attempt(lambda:page.get_by_role("button",name="Orders",exact=False).first.click(),"Orders")
            page.wait_for_timeout(1400)
            attempt(lambda:page.get_by_role("button",name="Record payment").last.click(),"Payment dialog")
            attempt(lambda:page.get_by_role("spinbutton").last.fill("420"),"Enter received amount")
            attempt(lambda:page.get_by_role("button",name="Confirm received payment").click(),"Confirm payment")
        if id=="close":
            attempt(lambda:page.get_by_role("button",name="Orders",exact=False).first.click(),"Final orders")
            page.wait_for_timeout(5000)
            attempt(lambda:page.get_by_role("button",name="Inbox",exact=False).first.click(),"Final overview")
        hold(t,duration)
    video=page.video
    page.close();context.close();browser.close()
    raw=Path(video.path())
    print("Recorded video:",raw,raw.stat().st_size,flush=True)
    subprocess.run(["ffmpeg","-y","-i",str(raw),"-i",str(OUT/"narration.wav"),"-map","0:v:0","-map","1:a:0","-t",str(int(cursor)),"-vf","scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2","-c:v","libx264","-preset","veryfast","-crf","25","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(OUT/"MADHAV-Actual-App-Demo.mp4")],check=True)
    print("OUTPUT:",str(OUT/"MADHAV-Actual-App-Demo.mp4"),flush=True)
