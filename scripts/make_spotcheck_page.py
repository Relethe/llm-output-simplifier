"""生成 T2.2 用户抽查网页：human/classification_spotcheck.html（自包含，浏览器打开即用）。
用户逐条判 G1 分类正确/错误，实时错分率（>10% 需改提示词重跑），导出/复制结果交回。
运行：.venv\\Scripts\\python.exe -m scripts.make_spotcheck_page
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>分类抽查（T2.2 · 40 条）</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;max-width:860px;margin:0 auto;padding:20px;background:#f6f7f9;color:#1a1a1a}
 h1{font-size:20px} .bar{position:sticky;top:0;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:16px;z-index:5}
 .stat{font-size:15px} .rate{font-weight:700;font-size:18px} .ok{color:#1a7f37}.bad{color:#c0392b}
 .card{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .meta{font-size:12px;color:#666;margin-bottom:6px} .badge{display:inline-block;padding:1px 8px;border-radius:10px;background:#eef;color:#33c;font-size:12px;margin-left:6px}
 .txt{white-space:pre-wrap;font-size:14px;line-height:1.5;margin:6px 0;max-height:200px;overflow:auto;background:#fafafa;padding:8px;border-radius:6px}
 button{cursor:pointer;border:1px solid #ccc;background:#fff;border-radius:6px;padding:5px 12px;font-size:13px;margin-right:6px}
 button.sel-ok{background:#1a7f37;color:#fff;border-color:#1a7f37} button.sel-bad{background:#c0392b;color:#fff;border-color:#c0392b}
 select{padding:4px;font-size:13px;margin-left:6px} .actions{margin-top:10px}
 .top{margin-bottom:14px} .top button{background:#33c;color:#fff;border-color:#33c}
 .hint{font-size:13px;color:#555;margin:8px 0}
</style></head><body>
<h1>分类抽查 · T2.2（40 条，约 15 分钟）</h1>
<div class="hint">G1（GLM）已把每条提问预分类。请判断分类是否正确：点「正确」或「错误」（错误时选正确类别）。<b>错分率 &gt; 10% 就要改分类提示词重跑。</b>判完点「复制结果」发回给助手。</div>
<div class="bar"><span class="stat">已判 <b id="judged">0</b>/40 · 错分 <b id="wrong">0</b> · 错分率 <span class="rate" id="rate">—</span> <span id="verdict"></span></span></div>
<div class="top"><button onclick="copyResult()">复制结果 JSON</button><button onclick="downloadResult()">下载结果文件</button></div>
<div id="list"></div>
<script>
const DATA = __DATA__;
const CATS = ["问答","代码","解释","建议","排除"];
const state = DATA.map(d=>({id:d.id, judgment:null, user_category:""}));
const list = document.getElementById('list');
DATA.forEach((d,i)=>{
  const card=document.createElement('div'); card.className='card';
  const meta=document.createElement('div'); meta.className='meta';
  meta.textContent=`#${i+1} · ${d.id} · 语言:${d.lang||'?'}`;
  const badge=document.createElement('span'); badge.className='badge'; badge.textContent='G1: '+d.category_g1; meta.appendChild(badge);
  const txt=document.createElement('div'); txt.className='txt'; txt.textContent=d.text;
  const act=document.createElement('div'); act.className='actions';
  const ok=document.createElement('button'); ok.textContent='正确';
  const bad=document.createElement('button'); bad.textContent='错误';
  const sel=document.createElement('select'); sel.style.display='none';
  CATS.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;sel.appendChild(o);});
  sel.onchange=()=>{state[i].user_category=sel.value;refresh();};
  ok.onclick=()=>{state[i].judgment='correct';state[i].user_category=d.category_g1;ok.className='sel-ok';bad.className='';sel.style.display='none';refresh();};
  bad.onclick=()=>{state[i].judgment='wrong';ok.className='';bad.className='sel-bad';sel.style.display='inline';sel.value=state[i].user_category||CATS[0];state[i].user_category=sel.value;refresh();};
  act.appendChild(ok);act.appendChild(bad);act.appendChild(sel);
  card.appendChild(meta);card.appendChild(txt);card.appendChild(act);list.appendChild(card);
});
function refresh(){
  const judged=state.filter(s=>s.judgment).length;
  const wrong=state.filter(s=>s.judgment==='wrong').length;
  document.getElementById('judged').textContent=judged;
  document.getElementById('wrong').textContent=wrong;
  const rateEl=document.getElementById('rate'); const v=document.getElementById('verdict');
  if(judged===0){rateEl.textContent='—';rateEl.className='rate';v.textContent='';}
  else{const r=wrong/judged;rateEl.textContent=(r*100).toFixed(1)+'%';rateEl.className='rate '+(r>0.1?'bad':'ok');
    v.textContent=r>0.1?'⚠ 超 10%，需重跑':'✓ 达标';}
}
function resultObj(){return {task:'T2.2_classification_spotcheck',judged:state.filter(s=>s.judgment).length,wrong:state.filter(s=>s.judgment==='wrong').length,items:state};}
function copyResult(){navigator.clipboard.writeText(JSON.stringify(resultObj(),null,2)).then(()=>alert('已复制，粘贴发回给助手即可'));}
function downloadResult(){const b=new Blob([JSON.stringify(resultObj(),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='spotcheck_result.json';a.click();}
refresh();
</script></body></html>"""


def main():
    src = os.path.join(ROOT, "human", "classification_spotcheck_40.jsonl")
    with open(src, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    html = TEMPLATE.replace("__DATA__", json.dumps(items, ensure_ascii=False))
    out = os.path.join(ROOT, "human", "classification_spotcheck.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("WROTE", out, "items", len(items))


if __name__ == "__main__":
    main()
