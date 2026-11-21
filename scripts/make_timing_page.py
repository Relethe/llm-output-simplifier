"""生成 T7.4 单人计时阅读网页：human/timing/timing_reading.html。
40 条（随机半原版/半简化，同一提问只读一版）：点开始显示文本计时→读完隐藏→不回看答 11.3 的题。
记录每条实际阅读时间 + 答题。单人初步证据（不判通过）。导出 JSON 发回助手拟合阅读速度。
运行：.venv\\Scripts\\python.exe -m scripts.make_timing_page（须先有 timing_items.jsonl）
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>计时阅读 T7.4</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;max-width:820px;margin:0 auto;padding:20px;background:#f6f7f9;color:#1a1a1a}
 h1{font-size:20px}.hint{font-size:13px;color:#555;margin:8px 0;line-height:1.6}
 .card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .q{font-weight:600;margin:8px 0;white-space:pre-wrap}
 .text{white-space:pre-wrap;font-size:14px;line-height:1.6;background:#fafafa;padding:12px;border-radius:6px;max-height:420px;overflow:auto;margin:10px 0}
 button{background:#33c;color:#fff;border:none;border-radius:6px;padding:8px 18px;cursor:pointer;font-size:14px;margin-right:8px}
 button:disabled{background:#aaa;cursor:default}
 .quiz{margin:10px 0}.quiz div{margin:8px 0}.quiz input{width:100%;box-sizing:border-box;padding:6px;font-size:13px;border:1px solid #ccc;border-radius:4px}
 .timer{font-size:13px;color:#666}.bar{margin:12px 0}
 .hidden{display:none}
</style></head><body>
<h1>计时阅读 · T7.4（40 条，约 1 小时）</h1>
<div class="hint">每条：点「开始阅读」显示文本并计时；读完点「我读完了」隐藏文本；<b>不回看原文</b>，凭记忆答题。记录实际阅读时间。这是单人初步证据。全部做完点「导出计时结果」发回助手。</div>
<div class="bar">第 <b id="idx">1</b>/<span id="total"></span> 条 · <span class="timer" id="timer"></span></div>
<div class="card" id="card"></div>
<div class="bar"><button id="next" onclick="nextItem()" disabled>下一条</button><button onclick="exportTiming()">导出计时结果</button></div>
<script>
const DATA=__DATA__;
const results=DATA.map(d=>({id:d.id,version:d.version,reading_ms:null,answers:d.quiz.map(()=>""),correct:null}));
let idx=0,t0=null,timerId=null;
document.getElementById('total').textContent=DATA.length;
function render(){
 const d=DATA[idx];const card=document.getElementById('card');card.innerHTML='';
 document.getElementById('idx').textContent=idx+1;document.getElementById('next').disabled=true;
 const q=document.createElement('div');q.className='q';q.textContent='提问：'+d.question;card.appendChild(q);
 const start=document.createElement('button');start.textContent='开始阅读';
 const text=document.createElement('div');text.className='text hidden';text.textContent=d.text;
 const finish=document.createElement('button');finish.textContent='我读完了';finish.className='hidden';
 const quiz=document.createElement('div');quiz.className='quiz hidden';
 d.quiz.forEach((qq,qi)=>{const row=document.createElement('div');const lab=document.createElement('div');lab.textContent=(qi+1)+'. '+qq.q;const inp=document.createElement('input');inp.placeholder='凭记忆作答，找不到填“找不到”';inp.oninput=()=>{results[idx].answers[qi]=inp.value;checkQuiz();};row.appendChild(lab);row.appendChild(inp);quiz.appendChild(row);});
 const tm=document.createElement('div');tm.className='timer';
 start.onclick=()=>{text.classList.remove('hidden');finish.classList.remove('hidden');start.classList.add('hidden');t0=performance.now();timerId=setInterval(()=>{tm.textContent='阅读中 '+(Math.round((performance.now()-t0)/1000))+'s';},200);};
 finish.onclick=()=>{clearInterval(timerId);results[idx].reading_ms=Math.round(performance.now()-t0);text.classList.add('hidden');finish.classList.add('hidden');quiz.classList.remove('hidden');tm.textContent='阅读用时 '+(results[idx].reading_ms/1000).toFixed(1)+'s（文本已隐藏，请凭记忆答题）';};
 card.appendChild(start);card.appendChild(text);card.appendChild(finish);card.appendChild(tm);card.appendChild(quiz);
}
function checkQuiz(){const done=results[idx].answers.every(a=>a.trim());document.getElementById('next').disabled=!done||results[idx].reading_ms===null;}
function nextItem(){if(idx<DATA.length-1){idx++;render();}else{document.getElementById('next').disabled=true;alert('全部完成，请导出计时结果');}}
function exportTiming(){const b=new Blob([JSON.stringify(results,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='timing_results.json';a.click();}
render();
</script></body></html>"""


def render_timing_page(items):
    return TEMPLATE.replace("__DATA__", json.dumps(items, ensure_ascii=False))


def main():
    src = os.path.join(ROOT, "human", "timing", "timing_items.jsonl")
    if not os.path.exists(src):
        print("NO_TIMING_ITEMS（须先完成阶段7.3出题 + 版本分配）")
        return
    with open(src, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    out = os.path.join(ROOT, "human", "timing", "timing_reading.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_timing_page(items))
    print("WROTE", out, "items", len(items))


if __name__ == "__main__":
    main()
