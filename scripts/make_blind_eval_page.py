"""生成 T6.2 盲评校准网页：human/blind_eval/blind_eval.html。
用户亲判 30 对（来源/顺序随机、无标签）。固定问题“哪个让你更快拿到需要的信息，而且不缺东西？”
选项 A/B/一样（不问哪个更好）。裁判–用户一致率 ≥80% 才采纳裁判盲评。导出 JSON 发回助手。
运行：.venv\\Scripts\\python.exe -m scripts.make_blind_eval_page（须先有 blind_pairs.jsonl）
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>盲评校准 T6.2（30 对）</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#f6f7f9;color:#1a1a1a}
 h1{font-size:20px}.hint{font-size:13px;color:#555;margin:8px 0;line-height:1.6}
 .bar{position:sticky;top:0;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:16px;z-index:5}
 .bar button{background:#33c;color:#fff;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;margin-right:8px}
 .card{background:#fff;border-radius:10px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .pair{display:flex;gap:12px}.col{flex:1;min-width:0}
 .col h3{font-size:14px;margin:4px 0}.txt{white-space:pre-wrap;font-size:13px;background:#fafafa;padding:10px;border-radius:6px;max-height:300px;overflow:auto}
 .choice{margin-top:10px}.choice button{border:1px solid #ccc;background:#fff;border-radius:6px;padding:6px 16px;cursor:pointer;margin-right:8px}
 .choice button.sel{background:#33c;color:#fff;border-color:#33c}
 .meta{font-size:12px;color:#666}
</style></head><body>
<h1>盲评校准 · T6.2（30 对，约 40 分钟）</h1>
<div class="hint">每对两份回答（顺序随机、不带方案标签）。问题固定：<b>“哪个让你更快拿到需要的信息，而且不缺东西？”</b> 选 A / B / 一样。<b>不是问“哪个更好”。</b>判完点「导出盲评结果」发回助手算一致率（≥80% 才采纳裁判盲评）。</div>
<div class="bar">已判 <b id="prog">0</b>/30 · <button onclick="exp()">导出盲评结果</button><button onclick="cp()">复制</button></div>
<div id="list"></div>
<script>
const DATA=__DATA__;
const state=DATA.map(d=>({id:d.id,choice:null}));
const list=document.getElementById('list');
DATA.forEach((d,i)=>{
 const card=document.createElement('div');card.className='card';
 const meta=document.createElement('div');meta.className='meta';meta.textContent=`#${i+1} · ${d.id}`;
 const pair=document.createElement('div');pair.className='pair';
 ['A','B'].forEach(side=>{const col=document.createElement('div');col.className='col';const h=document.createElement('h3');h.textContent=side;const t=document.createElement('div');t.className='txt';t.textContent=side==='A'?d.text_a:d.text_b;col.appendChild(h);col.appendChild(t);pair.appendChild(col);});
 const ch=document.createElement('div');ch.className='choice';
 ['A','B','一样'].forEach(opt=>{const b=document.createElement('button');b.textContent=opt;b.onclick=()=>{state[i].choice=opt;[...ch.children].forEach(x=>x.className='');b.className='sel';refresh();};ch.appendChild(b);});
 card.appendChild(meta);card.appendChild(pair);card.appendChild(ch);list.appendChild(card);
});
function refresh(){document.getElementById('prog').textContent=state.filter(s=>s.choice).length;}
function exp(){const b=new Blob([JSON.stringify(state,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='blind_eval_user.json';a.click();}
function cp(){navigator.clipboard.writeText(JSON.stringify(state,null,2)).then(()=>alert('已复制，发回助手'));}
refresh();
</script></body></html>"""


def render_blind_page(items):
    return TEMPLATE.replace("__DATA__", json.dumps(items, ensure_ascii=False))


def main():
    src = os.path.join(ROOT, "human", "blind_eval", "blind_pairs.jsonl")
    if not os.path.exists(src):
        print("NO_BLIND_PAIRS（须先有方案输出+随机配对）")
        return
    with open(src, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    out = os.path.join(ROOT, "human", "blind_eval", "blind_eval.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_blind_page(items))
    print("WROTE", out, "items", len(items))


if __name__ == "__main__":
    main()
