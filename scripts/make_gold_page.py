"""生成 T4.2 金标标注网页（直接原文操作版）：human/gold/gold_annotation.html。
改进：单元原文直接点击切换 留/压/删（颜色区分）；点「+」把单元加为必留点（无需复制）；
⇧ 前移；病理下拉；每条「重置」按钮恢复默认；原始原文存于 DATA 并随导出保留。
中文翻译对照助读（标注仍针对原文单元，保 κ 有效）。
运行：.venv\\Scripts\\python.exe -m scripts.make_gold_page
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>金标标注 T4.2（30 条 · 直接原文操作）</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;max-width:960px;margin:0 auto;padding:20px;background:#f6f7f9;color:#1a1a1a}
 h1{font-size:20px}.hint{font-size:13px;color:#555;margin:8px 0;line-height:1.7}
 .bar{position:sticky;top:0;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:16px;z-index:5}
 .bar button{background:#33c;color:#fff;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;margin-right:8px}
 .card{background:#fff;border-radius:10px;padding:16px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .meta{font-size:12px;color:#666;margin-bottom:6px}
 .zhref{margin:8px 0;border:1px solid #d8e0d8;border-radius:6px;background:#f4f8f4;padding:6px 10px}
 .zhref summary{cursor:pointer;font-size:13px;color:#2a6;font-weight:600}
 .zhq{font-size:13px;margin:6px 0;font-weight:600}.zhr{white-space:pre-wrap;font-size:13px;line-height:1.6;max-height:260px;overflow:auto;margin:6px 0}
 label.f{font-size:13px;display:inline-block;margin:6px 12px 6px 0}
 select,input[type=text]{font-size:13px;padding:4px;border:1px solid #ccc;border-radius:4px}
 .resp{border:1px solid #eee;border-radius:6px;padding:10px;margin:8px 0;line-height:2}
 .unit{cursor:pointer;padding:1px 3px;border-radius:3px;border-bottom:1px dashed #bbb}
 .unit:hover{background:#eef}
 .u-压{background:#fff3cd}.u-删{background:#f8d7da;text-decoration:line-through;color:#842029}
 .ubar{display:inline-block;margin:0 4px;white-space:nowrap}
 .ubar button{font-size:11px;padding:1px 6px;margin:0 1px;border:1px solid #ccc;background:#fff;border-radius:4px;cursor:pointer}
 .ubar button.on{background:#33c;color:#fff;border-color:#33c}
 .ubar input{width:64px;font-size:11px;padding:1px 3px}
 .points{margin:8px 0}.chip{display:inline-block;background:#e7f0e7;border:1px solid #bcd;border-radius:12px;padding:2px 10px;margin:3px;font-size:13px}
 .chip button{border:none;background:none;color:#c00;cursor:pointer;font-weight:bold;margin-left:4px}
 .reset{background:#888;color:#fff;border:none;border-radius:6px;padding:5px 12px;cursor:pointer;font-size:12px;margin-top:8px}
 .legend{font-size:12px;color:#666;margin:6px 0}
 .lg{padding:1px 6px;border-radius:3px}.lg-压{background:#fff3cd}.lg-删{background:#f8d7da;text-decoration:line-through}
</style></head><body>
<h1>金标标注 · T4.2（30 条 · 直接原文操作）</h1>
<div class="hint"><b>独立标注，别看 AI 标注。</b>下方原文已切成单元：<b>点击单元文字</b>切换 <span class="lg">留</span>→<span class="lg lg-压">压</span>→<span class="lg lg-删">删</span>（代码块只能 留/删）。<b>「+」</b>把该单元加为必留点（无需复制）；<b>「⇧」</b>标记直接回答前移；病理下拉选 P1–P11。每条有<b>重置</b>按钮。原始原文已存好并随导出保留。判完点「导出金标 JSON」存 human/gold/user/ 发助手。</div>
<div class="bar">已标 <b id="prog">0</b>/30 · <button onclick="exportGold()">导出金标 JSON</button><button onclick="copyGold()">复制 JSON</button></div>
<div class="legend">图例：<span class="lg">留</span> 保留 · <span class="lg lg-压">压</span> 可压缩 · <span class="lg lg-删">删</span> 删除 · 点单元文字循环切换</div>
<div id="list"></div>
<script>
const DATA=__DATA__;
const PATHS=["","P1","P2","P3","P4","P5","P6","P7","P8","P9","P10","P11"];
const state=DATA.map(d=>({response_id:d.response_id,intent:"normal",correctness_issue:"",points:[],units:d.units.map(u=>({uid:u.uid,label:"留",move_first:false,pathology:"",note:""}))}));
const list=document.getElementById('list');
function touched(s){return s.intent!=='normal'||s.correctness_issue||s.points.length||s.units.some(u=>u.label!=='留'||u.move_first||u.pathology||u.note);}
function refresh(){document.getElementById('prog').textContent=state.filter(touched).length;}
DATA.forEach((d,i)=>{
 const card=document.createElement('div');card.className='card';
 const meta=document.createElement('div');meta.className='meta';meta.textContent=`#${i+1} · ${d.response_id} · ${d.category} · ${d.role} · ${d.lang||'?'}`;card.appendChild(meta);
 if(d.zh_question||d.zh_response){const zh=document.createElement('details');zh.className='zhref';const sm=document.createElement('summary');sm.textContent='中文翻译对照（读此理解，标注针对下方原文单元）';const zq=document.createElement('div');zq.className='zhq';zq.textContent='提问译文：'+(d.zh_question||'');const zr=document.createElement('div');zr.className='zhr';zr.textContent='回答译文：'+(d.zh_response||'');zh.appendChild(sm);zh.appendChild(zq);zh.appendChild(zr);card.appendChild(zh);}
 const q=document.createElement('div');q.className='zhq';q.textContent='提问原文：'+d.question;card.appendChild(q);
 const f1=document.createElement('label');f1.className='f';f1.textContent='intent: ';const isel=document.createElement('select');['normal','style_requested'].forEach(o=>{const op=document.createElement('option');op.value=o;op.textContent=o;isel.appendChild(op);});isel.onchange=()=>{state[i].intent=isel.value;refresh();};f1.appendChild(isel);card.appendChild(f1);
 const f2=document.createElement('label');f2.className='f';f2.textContent='原回答有错: ';const cin=document.createElement('input');cin.type='text';cin.size=30;cin.placeholder='有错才填';cin.oninput=()=>{state[i].correctness_issue=cin.value;refresh();};f2.appendChild(cin);card.appendChild(f2);
 const pl=document.createElement('div');pl.className='legend';pl.textContent='必留点（点单元「+」添加）：';card.appendChild(pl);
 const pbox=document.createElement('div');pbox.className='points';card.appendChild(pbox);
 function renderPoints(){pbox.innerHTML='';state[i].points.forEach((p,pi)=>{const c=document.createElement('span');c.className='chip';c.textContent=p;const x=document.createElement('button');x.textContent='×';x.onclick=()=>{state[i].points.splice(pi,1);renderPoints();refresh();};c.appendChild(x);pbox.appendChild(c);});}
 const resp=document.createElement('div');resp.className='resp';card.appendChild(resp);
 const unitEls=[];
 d.units.forEach((u,ui)=>{
  const wrap=document.createElement('span');
  const span=document.createElement('span');span.className='unit u-留';span.textContent=u.text;span.title='点击切换 留/压/删';
  function setLabel(){span.className='unit u-'+state[i].units[ui].label;}
  span.onclick=()=>{const cur=state[i].units[ui].label;const seq=u.type==='code'?['留','删']:['留','压','删'];state[i].units[ui].label=seq[(seq.indexOf(cur)+1)%seq.length];setLabel();refresh();};
  const bar=document.createElement('span');bar.className='ubar';
  const mf=document.createElement('button');mf.textContent='⇧';mf.title='直接回答前移';mf.onclick=()=>{state[i].units[ui].move_first=!state[i].units[ui].move_first;mf.className=state[i].units[ui].move_first?'on':'';refresh();};
  const ap=document.createElement('button');ap.textContent='+';ap.title='加为必留点';ap.onclick=()=>{if(!state[i].points.includes(u.text)){state[i].points.push(u.text);renderPoints();refresh();}};
  const ps=document.createElement('select');ps.title='病理';PATHS.forEach(p=>{const op=document.createElement('option');op.value=p;op.textContent=p||'病理';ps.appendChild(op);});ps.onchange=()=>{state[i].units[ui].pathology=ps.value;refresh();};
  const ni=document.createElement('input');ni.type='text';ni.placeholder='note';ni.title='备注';ni.oninput=()=>{state[i].units[ui].note=ni.value;};
  bar.appendChild(mf);bar.appendChild(ap);bar.appendChild(ps);bar.appendChild(ni);
  wrap.appendChild(span);wrap.appendChild(bar);resp.appendChild(wrap);resp.appendChild(document.createTextNode(' '));
  unitEls.push({span,mf,ps,ni,setLabel});
 });
 const reset=document.createElement('button');reset.className='reset';reset.textContent='重置本条';reset.onclick=()=>{state[i].intent='normal';state[i].correctness_issue='';state[i].points=[];state[i].units=d.units.map(u=>({uid:u.uid,label:'留',move_first:false,pathology:'',note:''}));isel.value='normal';cin.value='';renderPoints();unitEls.forEach((e,ui)=>{e.setLabel();e.mf.className='';e.ps.value='';e.ni.value='';});refresh();};
 card.appendChild(reset);list.appendChild(card);renderPoints();
});
function collect(){return state.map((s,i)=>({response_id:s.response_id,annotator:"user",intent:s.intent,correctness_issue:s.correctness_issue||null,must_keep_points:s.points.map((t,j)=>({pid:j+1,text:t})),units:s.units.map((u,ui)=>({uid:u.uid,type:DATA[i].units[ui].type,text:DATA[i].units[ui].text,label:u.label,move_first:u.move_first,pathology:u.pathology?[u.pathology]:[],note:u.note})),original_response:DATA[i].response}));}
function exportGold(){const b=new Blob([JSON.stringify(collect(),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='gold_user_annotations.json';a.click();}
function copyGold(){navigator.clipboard.writeText(JSON.stringify(collect(),null,2)).then(()=>alert('已复制，发回助手即可'));}
refresh();
</script></body></html>"""


def render_gold_page(items):
    return TEMPLATE.replace("__DATA__", json.dumps(items, ensure_ascii=False))


def main():
    src = os.path.join(ROOT, "human", "gold", "gold_candidates.jsonl")
    if not os.path.exists(src):
        print("NO_GOLD_CANDIDATES（须先完成生成200 + 跑 make_gold_set）")
        return
    with open(src, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    out = os.path.join(ROOT, "human", "gold", "gold_annotation.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_gold_page(items))
    print("WROTE", out, "items", len(items))


if __name__ == "__main__":
    main()
