#!/usr/bin/env python3
"""MOTIONVC: Gemini -> three editorial slides -> Uzbek TTS -> Telegram."""
import os, sys, json, re, io, base64, pathlib, subprocess, datetime
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path("output")
ROOT.mkdir(exist_ok=True)
BOT = os.environ["TELEGRAM_BOT_TOKEN"]
KEY = os.environ["GEMINI_API_KEY"]
CHANNEL = "@motionvc"
TZ = datetime.timezone(datetime.timedelta(hours=5))
TODAY = datetime.datetime.now(TZ).date()
API = "https://generativelanguage.googleapis.com/v1beta/models/"
TOPICS = [
 "AI'ga maxfiy ma'lumot yubormaslik", "To'g'ri prompt yozish",
 "Deepfake ovozdan himoyalanish", "AI javobini faktcheking qilish",
 "Chatbot xotirasi va maxfiylik", "Ishdagi hujjatlarni anonimlashtirish",
 "Sun'iy intellektning foydali tomonlari", "AI'ga haddan ortiq ishonmaslik",
 "Phishing va AI", "Shaxsiy ma'lumotlar xavfsizligi",
 "Bugungi fikr: texnologiya va mas'uliyat", "AI yaratgan rasmlarni aniqlash",
 "Mualliflik va AI", "AI xizmatlari maxfiylik sozlamalari",
]
def gemini(model, body):
    r = requests.post(API + model + ":generateContent",
        headers={"x-goog-api-key": KEY, "Content-Type": "application/json"},
        json=body, timeout=110)
    if not r.ok:
        raise RuntimeError("Gemini API HTTP %s: %s" % (r.status_code, r.text[:450]))
    return r.json()

def editorial():
    topic = TOPICS[(TODAY.toordinal() - datetime.date(2026, 1, 1).toordinal()) % len(TOPICS)]
    prompt = f"""O'zbekcha professional Telegram kanali uchun mavzu: {topic}.
Bugungi sana {TODAY.isoformat()}. Kontent axborot beruvchi, tekshiriladigan,
qo'rqitmaydigan, xavfsizlikni muvozanatli tushuntiradigan bo'lsin.
Faqat quyidagi obyektli JSON qaytar:
{{"slides":[{{"title":"maksimum 6 so'z","body":"maksimum 24 so'z"}},
{{"title":"maksimum 6 so'z","body":"maksimum 24 so'z"}},
{{"title":"maksimum 6 so'z","body":"maksimum 24 so'z"}}],
"caption":"uchta qisqa satr; satrlar newline bilan ajratilgan",
"voice":"o'zbek tilida 105–115 so'zli puxta diktor matni. 'Bugungi fikr' yoki 'Sun'iy intellekt' deb boshla."}}
Mazmun: 1-slid kuchli hook, 2-slayd aniq xatar/fakt, 3-slayd amaliy tavsiya.
Imloni to'g'ri yoz; noaniq va asossiz raqamlardan qoch.
"""
    data = gemini("gemini-3.8-flash", {
        "contents":[{"parts":[{"text":prompt}]}],
        "generationConfig":{"responseMimeType":"application/json","temperature":0.6}
    })
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    post = json.loads(text)
    assert isinstance(post["slides"],list) and len(post["slides"]) == 3
    assert all(s.get("title") and s.get("body") for s in post["slides"])
    assert post.get("caption") and post.get("voice")
    (ROOT/"post.json").write_text(json.dumps(post,ensure_ascii=False,indent=2),encoding="utf-8")
    return post

def f(size, bold=False):
    fn = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else "")
    return ImageFont.truetype(fn,size)

def fit_lines(draw, text, font, max_width):
    words = re.split(r"\s+",text.strip())
    lines=[]; cur=""
    for word in words:
        candidate=(cur+" "+word).strip()
        if cur and draw.textbbox((0,0),candidate,font=font)[2] > max_width:
            lines.append(cur);cur=word
        else:cur=candidate
    if cur:lines.append(cur)
    return lines

def make_slide(item, n):
    im=Image.new("RGB",(1080,1350),(249,249,247))
    d=ImageDraw.Draw(im)
    black=(19,19,20); grey=(86,86,86);yellow=(246,224,23)
    d.text((80,72),"MOTIONVC / AI JOURNAL",font=f(27,True),fill=black)
    d.text((926,76),"2026",font=f(24),fill=black)
    d.line((80,133,1000,133),fill=black,width=3)
    d.rounded_rectangle((80,183,374,246),radius=25,fill=yellow)
    d.text((106,198),"BUGUNGI MAVZU",font=f(23,True),fill=black)
    d.text((81,286),"0"+str(n),font=f(36,True),fill=black)
    y=400
    titlefont=f(70,True)
    for line in fit_lines(d,item["title"],titlefont,900)[:5]:
        d.text((78,y),line,font=titlefont,fill=black)
        y+=92
    y=max(830,y+65)
    d.rounded_rectangle((80,y-28,1000,1150),radius=33,fill=black if n==2 else (233,233,231))
    x=117
    bodyfont=f(34)
    ink=(250,250,250) if n==2 else black
    for line in fit_lines(d,item["body"],bodyfont,842)[:6]:
        d.text((x,y+20),line,font=bodyfont,fill=ink)
        y+=62
    d.rectangle((80,1220,1000,1226),fill=yellow)
    d.text((80,1260),"@motionvc",font=f(28,True),fill=black)
    d.text((890,1260),f"0{n} / 03",font=f(24),fill=black)
    path=ROOT/f"slide_{n}.png"
    im.save(path,optimize=True)
    return path

def make_voice(text):
    data=gemini("gemini-3.8-flash-tts", {
        "contents":[{"role":"user","parts":[{
            "text":text,
            "speech_metadata":{"style":"Clear, calm and professional Uzbek narration; measured pace, warm and confident tone, no music."}
        }]}],
        "generationConfig":{"responseModalities":["AUDIO"],
           "speechConfig":{"voiceConfig":{"voice":"Gacrux"}}}
    })
    parts=data["candidates"][0]["content"]["parts"]
    inline=next((part.get("inlineData") or part.get("inline_data")
                 for part in parts if part.get("inlineData") or part.get("inline_data")),None)
    if not inline:raise RuntimeError("Gemini audio qaytarmadi")
    raw=base64.b64decode(inline["data"])
    wav=ROOT/"voice.wav"; ogg=ROOT/"voice.ogg"
    # Gemini uncompressed audio is normally 24kHz mono signed 16-bit PCM.
    if raw[:4]==b"RIFF":
        wav.write_bytes(raw)
        cmd=["ffmpeg","-y","-loglevel","error","-i",str(wav),"-c:a","libopus","-b:a","48k",str(ogg)]
    else:
        pcm=ROOT/"voice.pcm";pcm.write_bytes(raw)
        cmd=["ffmpeg","-y","-loglevel","error","-f","s16le","-ar","24000",
             "-ac","1","-i",str(pcm),"-c:a","libopus","-b:a","48k",str(ogg)]
    subprocess.run(cmd,check=True)
    if not ogg.exists() or ogg.stat().st_size < 1000:raise RuntimeError("OGG invalid")
    return ogg

def tg(method, data, files=None):
    response=requests.post("https://api.telegram.org/bot"+BOT+"/"+method,
                           data=data,files=files,timeout=110)
    ans=response.json()
    if not ans.get("ok"):raise RuntimeError("Telegram "+method+": "+str(ans.get("description")))
    return ans

def publish(post, images, audio):
    # Caption belongs to the first image; voice follows in a new message.
    media=[]
    for i in range(3):
        item={"type":"photo","media":f"attach://s{i+1}"}
        if i==0:item["caption"]=post["caption"][:1024]
        media.append(item)
    handles=[open(img,"rb") for img in images]
    try:
        files={f"s{i+1}":(f"slide_{i+1}.png",handles[i],"image/png") for i in range(3)}
        tg("sendMediaGroup",{"chat_id":CHANNEL,"media":json.dumps(media,ensure_ascii=False)},files)
    finally:
        for h in handles:h.close()
    with open(audio,"rb") as h:
        tg("sendVoice",{"chat_id":CHANNEL}, {"voice":("voice.ogg",h,"audio/ogg")})

def main():
    if not KEY or not BOT:raise RuntimeError("GitHub Secrets yetishmayapti")
    post=editorial()
    images=[make_slide(s,n+1) for n,s in enumerate(post["slides"])]
    voice=make_voice(post["voice"])
    if os.getenv("PREVIEW_ONLY","false").lower()=="true":
        print("Preview created, not published")
        return
    publish(post,images,voice)
    print("Telegram @motionvc album and voice sent successfully")

if __name__=="__main__":
    try: main()
    except Exception as e:
        print("MOTIONVC ERROR:",str(e),file=sys.stderr)
        sys.exit(1)
