"""生成 T4.5 分歧裁决网页：human/adjudication/adjudication.html。
G1/G2 label 不一致的单元（保守原则 留>压>删 已先采纳），用户随机抽 50 个裁决最终 label。
报告保守原则与用户裁决一致率。代码块限删/留。导出 JSON 发回助手。
运行：.venv\\Scripts\\python.exe -m scripts.make_adjudication_page（须先有 disagreement_units.jsonl）
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>分歧裁决 T4.5（50 单元）</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;max-width:860px;margin:0 auto;padding:20px;background:#f6f7f9;color:#1a1a1a}
 h1{font-size:20px}.hint{font-size:13px;color:#555;margin:8px 0;line-height:1.6}
 .bar{position:sticky;top:0;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:16px;z-index:5}
 .bar button{background:#33c;color:#fff;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;margin-right:8px}
 .card{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .meta{font-size:12px;color:#666;margin-bottom:6px}
 .utext{white-space:pre-wrap;font-size:13px;background:#fafafa;padding:8px;border-radius:6px;max-height:160px;overflow:auto;margin:6px 0}
 .code{background:#f0f0f7;font-family:monospace}
 .labels{font-size:13px;margin:6px 0}.g{display:inline-block;padding:1px 8px;border-radius:10px;background:#eef;color:#33c;margin-right:8px}
 select{font-size:13px;padding:4px}
</style></head><body>
<h1>分歧裁决 · T4.5（50 单元，约 30 分钟）</h1>
<div class="hint">这些单元 G1 与 G2 标注不一致（已按保守原则 留&gt;压&gt;删 暂采）。请裁决最终 label：删 / 压 / 留。<b>代码块只能 删/留。</b>判完点「导出裁决结果」发回助手算一致率。</div>
<div class="bar">已判 <b id="prog">0</b>/50 · <button onclick="exp()">导出裁决结果</button><button onclick="cp()">复制</button></div>
<div id="list"></div>
<script>
const DATA=__DATA__;
const state=DATA.map(d=>({response_id:d.response_id,uid:d.uid,user_label:null}));
const list=document.getElementById('list');
DATA.forEach((d,i)=>{
 const card=document.createElement('div');card.className='card';
 const meta=document.createElement('div');meta.className='meta';meta.textContent=`#${i+1} · ${d.response_id} · 单元${d.uid} · ${d.type}`;
 const ut=document.createElement('div');ut.className='utext'+(d.type==='code'?' code':'');ut.textContent=d.text;
 const lb=document.createElement('div');lb.className='labels';
 const g1=document.createElement('span');g1.className='g';g1.textContent='G1: '+d.g1_label;
 const g2=document.createElement('span');g2.className='g';g2.textContent='G2: '+d.g2_label;
 const cons=document.createElement('span');cons.className='g';cons.textContent='保守暂采: '+d.conservative;
 lb.appendChild(g1);lb.appendChild(g2);lb.appendChild(cons);
 const sel=document.createElement('select');const ph=document.createElement('option');ph.value='';ph.textContent='— 裁决 —';sel.appendChild(ph);
 (d.type==='code'?['留','删']:['留','压','删']).forEach(o=>{const op=document.createElement('option');op.value=o;op.textContent=o;sel.appendChild(op);});
 sel.onchange=()=>{state[i].user_label=sel.value||null;refresh();};
 card.appendChild(meta);card.appendChild(ut);card.appendChild(lb);card.appendChild(sel);list.appendChild(card);
});
function refresh(){document.getElementById('prog').textContent=state.filter(s=>s.user_label).length;}
function exp(){const b=new Blob([JSON.stringify(state,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='adjudication_user.json';a.click();}
function cp(){navigator.clipboard.writeText(JSON.stringify(state,null,2)).then(()=>alert('已复制，发回助手'));}
refresh();
</script></body></html>"""


def render_adjudication_page(items):
    return TEMPLATE.replace("__DATA__", json.dumps(items, ensure_ascii=False))


def main():
    src = os.path.join(ROOT, "human", "adjudication", "disagreement_units.jsonl")
    if not os.path.exists(src):
        print("NO_DISAGREEMENT_UNITS（须先有 G1/G2 标注+分歧清单）")
        return
    with open(src, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    out = os.path.join(ROOT, "human", "adjudication", "adjudication.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_adjudication_page(items))
    print("WROTE", out, "items", len(items))


if __name__ == "__main__":
    main()
