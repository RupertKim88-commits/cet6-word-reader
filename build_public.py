from pathlib import Path
import csv
import json
import re
import shutil


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
CSV_PATH = next(WORKSPACE.glob("*700*.csv"))
AUDIO_SOURCE = WORKSPACE / "word_audio"
AUDIO_TARGET = ROOT / "word_audio"


SPECIAL_SPEAK = {
    "odo(u)r": "odor",
    "behavio(u)r": "behavior",
    "fulfil(l)": "fulfill",
    "connection/-exion": "connection",
    "specialize/-ise": "specialize",
    "industrialize/-ise": "industrialize",
    "analyze/-yse": "analyze",
    "minimize/-ise": "minimize",
    "cozy/cosy": "cozy",
    "skeptical/sceptical": "skeptical",
}


def speak_text(word):
    if word in SPECIAL_SPEAK:
        return SPECIAL_SPEAK[word]
    if "/" in word:
        return word.split("/")[0]
    return word.replace("(", "").replace(")", "")


def safe_name(index, spoken):
    base = re.sub(r"[^a-z0-9]+", "_", spoken.lower()).strip("_")
    return f"{index:04d}_{base or ('word_' + str(index))}.wav"


rows = []
with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    next(reader)
    for values in reader:
        index, day, group, word, ipa = values[:5]
        index = int(index)
        spoken = speak_text(word)
        rows.append(
            {
                "index": index,
                "day": int(day),
                "group": int(group),
                "word": word,
                "speak": spoken,
                "ipa": ipa,
                "audio": "word_audio/" + safe_name(index, spoken),
            }
        )

if AUDIO_TARGET.exists():
    shutil.rmtree(AUDIO_TARGET)
shutil.copytree(AUDIO_SOURCE, AUDIO_TARGET)

data = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))

html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>CET-6 Word Reader</title>
<style>
:root{{--bg:#f6f1e8;--paper:#fffdf8;--ink:#1f2933;--muted:#667085;--line:#ded5c7;--accent:#0f766e;--accent-soft:#e0f2ef;--accent-dark:#0b5f59;--mark:#a16207}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.55}} header{{position:sticky;top:0;z-index:10;background:rgba(255,253,248,.96);border-bottom:1px solid var(--line);padding:14px 22px}} .head-inner{{max-width:1040px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap}} h1{{margin:0;font-size:26px;line-height:1.2;letter-spacing:0}} .hint{{margin:0;color:var(--muted);font-size:14px}} main{{max-width:1040px;margin:0 auto;padding:20px 22px 40px}} .day-title{{margin:22px 0 10px;padding:9px 12px;background:#2f4858;color:#fff;font-size:20px;border-radius:4px;letter-spacing:0}} .group-title{{margin:14px 0 6px;padding:6px 10px;background:#e8ded0;border-left:5px solid var(--accent);color:#25313d;font-size:17px;border-radius:3px;letter-spacing:0}} .word-list{{background:var(--paper);border:1px solid var(--line);border-radius:6px;overflow:hidden}} .entry{{display:grid;grid-template-columns:54px minmax(130px,260px) minmax(120px,1fr);gap:12px;align-items:start;padding:8px 12px;border-top:1px solid #eee7dc}} .entry:first-child{{border-top:0}} .num{{color:var(--muted);font-size:14px;font-variant-numeric:tabular-nums;text-align:right;padding-top:3px}} .word{{border:0;background:transparent;color:var(--accent-dark);cursor:pointer;padding:0;text-align:left;font-size:20px;font-weight:800;letter-spacing:0;overflow-wrap:anywhere}} .word:hover,.word:focus{{color:#fff;background:var(--accent);outline:0;box-shadow:0 0 0 4px var(--accent);border-radius:2px}} .entry.active{{background:var(--accent-soft)}} .ipa{{color:var(--mark);font-family:"Segoe UI",Arial,sans-serif;font-size:16px;padding-top:3px;overflow-wrap:anywhere}} #playerBar{{position:fixed;right:18px;bottom:18px;width:min(420px,calc(100vw - 36px));padding:10px 12px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--muted);box-shadow:0 12px 32px rgba(31,41,51,.14);font-size:14px}} #status{{margin-bottom:8px}} audio{{display:block;width:100%;height:32px}} #writingCanvas{{position:fixed;inset:0;z-index:30;width:100vw;height:100vh;pointer-events:none}} .write-tools{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}} .write-toggle{{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 10px;border:1px solid var(--line);border-radius:6px;background:#fffaf1;color:var(--muted);font-size:13px;user-select:none}} .write-toggle input{{width:16px;height:16px;accent-color:var(--accent)}} #clearInk{{height:32px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--accent-dark);padding:0 10px;font:inherit;font-size:13px;cursor:pointer}} #inkNote{{color:var(--muted);font-size:13px}} body.touch-writing{{touch-action:none}}
@media(max-width:760px){{header{{position:static;padding:13px 14px}} h1{{font-size:22px}} main{{padding:14px 12px 88px}} .entry{{grid-template-columns:38px minmax(0,1fr);gap:4px 10px}} .ipa{{grid-column:2/-1}} .num{{text-align:left}} #playerBar{{left:12px;right:12px;bottom:12px;width:auto}}}}
</style>
</head>
<body>
<canvas id="writingCanvas" aria-hidden="true"></canvas>
<header><div class="head-inner"><h1>CET-6 Word Reader</h1><p class="hint">点单词播放读音。平板笔可直接书写，笔迹会自动消失。</p><div class="write-tools"><label class="write-toggle"><input id="touchWrite" type="checkbox">手写</label><button id="clearInk" type="button">清空</button><span id="inkNote">笔迹约 3 秒后消失</span></div></div></header>
<main id="content"></main>
<div id="playerBar"><div id="status" aria-live="polite">点任意单词可以听发音</div><audio id="audioPlayer" controls preload="none"></audio></div>
<script id="wordData" type="application/json">{data}</script>
<script>
const words=JSON.parse(document.getElementById('wordData').textContent);const content=document.getElementById('content');const status=document.getElementById('status');const audioPlayer=document.getElementById('audioPlayer');let selectedVoice=null;const canvas=document.getElementById('writingCanvas');const ctx=canvas.getContext('2d');const touchWrite=document.getElementById('touchWrite');const clearInk=document.getElementById('clearInk');const strokes=[];const inkDelay=2800;const fadeTime=1200;let activeStroke=null;let frame=0;let suppressClickUntil=0;
function pickVoice(){{if(!('speechSynthesis'in window))return;const voices=speechSynthesis.getVoices();selectedVoice=voices.find(v=>v.lang==='en-US')||voices.find(v=>v.lang&&v.lang.startsWith('en'))||null}} if('speechSynthesis'in window){{pickVoice();speechSynthesis.onvoiceschanged=pickVoice}}
function speechFallback(item){{if(!('speechSynthesis'in window))return false;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(item.speak);u.lang='en-US';u.rate=.9;u.pitch=1;u.volume=1;if(selectedVoice)u.voice=selectedVoice;u.onstart=()=>status.textContent='正在读：'+item.word;u.onend=()=>status.textContent='已播放：'+item.word;u.onerror=()=>status.textContent='如果没听到声音，请点底部播放条的播放按钮';speechSynthesis.speak(u);return true}}
async function speak(item,entry){{document.querySelectorAll('.entry.active').forEach(n=>n.classList.remove('active'));entry.classList.add('active');if('speechSynthesis'in window)speechSynthesis.cancel();audioPlayer.pause();audioPlayer.currentTime=0;audioPlayer.src=item.audio;status.textContent='正在读：'+item.word;audioPlayer.onended=()=>status.textContent='已播放：'+item.word;audioPlayer.onerror=()=>{{if(!speechFallback(item))status.textContent='如果没听到声音，请点底部播放条的播放按钮'}};try{{await audioPlayer.play()}}catch(e){{if(!speechFallback(item))status.textContent='如果没听到声音，请点底部播放条的播放按钮'}}}}
function heading(text,cls){{const h=document.createElement('h2');h.className=cls;h.textContent=text;content.appendChild(h)}} function groupList(items){{const list=document.createElement('section');list.className='word-list';items.forEach(item=>{{const entry=document.createElement('div');entry.className='entry';const num=document.createElement('div');num.className='num';num.textContent=item.index;const word=document.createElement('button');word.type='button';word.className='word';word.textContent=item.word;word.title=item.speak;word.addEventListener('click',()=>speak(item,entry));const ipa=document.createElement('div');ipa.className='ipa';ipa.textContent=item.ipa;entry.append(num,word,ipa);list.appendChild(entry)}});content.appendChild(list)}} let d=null,g=null,b=[];function flush(){{if(b.length)groupList(b);b=[]}} words.forEach(item=>{{if(item.day!==d){{flush();d=item.day;g=null;heading('Day '+item.day,'day-title')}} if(item.group!==g){{flush();g=item.group;heading('Group '+item.group,'group-title')}} b.push(item)}});flush();
function resize(){{const r=window.devicePixelRatio||1;canvas.width=Math.ceil(innerWidth*r);canvas.height=Math.ceil(innerHeight*r);ctx.setTransform(r,0,0,r,0,0);draw()}} function req(){{if(!frame)frame=requestAnimationFrame(draw)}} function draw(now=performance.now()){{frame=0;ctx.clearRect(0,0,innerWidth,innerHeight);for(let i=strokes.length-1;i>=0;i--){{const s=strokes[i];const fade=s.expiresAt||Infinity;const op=now<=fade?1:Math.max(0,1-(now-fade)/fadeTime);if(op<=0){{strokes.splice(i,1);continue}} if(s.points.length<2)continue;ctx.save();ctx.globalAlpha=op;ctx.lineCap='round';ctx.lineJoin='round';ctx.strokeStyle='#123b36';ctx.beginPath();ctx.moveTo(s.points[0].x,s.points[0].y);for(let j=1;j<s.points.length;j++){{const a=s.points[j-1],p=s.points[j];ctx.lineWidth=Math.max(3,Math.min(9,3+(p.pressure||.5)*8));ctx.quadraticCurveTo(a.x,a.y,(a.x+p.x)/2,(a.y+p.y)/2)}} ctx.stroke();ctx.restore()}} if(strokes.length)req()}} function shouldWrite(e){{if(e.target.closest('#playerBar,.write-tools'))return false;return e.pointerType==='pen'||touchWrite.checked}} function pt(e){{return{{x:e.clientX,y:e.clientY,pressure:e.pressure||.5}}}} function down(e){{if(!shouldWrite(e))return;activeStroke={{pointerId:e.pointerId,points:[pt(e)],expiresAt:0}};strokes.push(activeStroke);req()}} function move(e){{if(!activeStroke||activeStroke.pointerId!==e.pointerId)return;const last=activeStroke.points[activeStroke.points.length-1],p=pt(e);const dist=Math.hypot(p.x-last.x,p.y-last.y);if(dist<2)return;activeStroke.points.push(p);if(dist>4||activeStroke.points.length>3)suppressClickUntil=Date.now()+450;e.preventDefault();req()}} function up(e){{if(!activeStroke||activeStroke.pointerId!==e.pointerId)return;if(activeStroke.points.length===1){{const p=activeStroke.points[0];activeStroke.points.push({{x:p.x+.5,y:p.y+.5,pressure:p.pressure}})}} activeStroke.expiresAt=performance.now()+inkDelay;activeStroke=null;req()}} addEventListener('resize',resize);document.addEventListener('pointerdown',down,{{capture:true,passive:false}});document.addEventListener('pointermove',move,{{capture:true,passive:false}});document.addEventListener('pointerup',up,{{capture:true,passive:false}});document.addEventListener('pointercancel',up,{{capture:true,passive:false}});document.addEventListener('click',e=>{{if(Date.now()<suppressClickUntil&&e.target.closest('.word')){{e.preventDefault();e.stopImmediatePropagation()}}}},true);touchWrite.addEventListener('change',()=>document.body.classList.toggle('touch-writing',touchWrite.checked));clearInk.addEventListener('click',()=>{{strokes.length=0;activeStroke=null;draw()}});resize();
</script>
</body></html>"""

(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "README.md").write_text(
    "# CET-6 Word Reader\n\nTablet-friendly vocabulary reader with pronunciation audio and fading handwriting practice.\n",
    encoding="utf-8",
)
(ROOT / ".nojekyll").write_text("", encoding="utf-8")

print(f"built {len(rows)} words")
