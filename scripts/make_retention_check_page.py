"""生成 T6.3 保留率复核 + 新增错误确认网页：human/retention_check/retention_check.html。
保留率校准：随机 30 个“必留点–简化版”判定，用户复核裁判结论（一致率报告）。
新增错误：裁判列出的全部说法，用户逐条确认（不抽样）。导出 JSON 发回助手。
运行：.venv\\Scripts\\python.exe -m scripts.make_retention_check_page（须先有 retention_checks.jsonl + new_errors.jsonl）
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>保留率复核 + 新增错误确认 T6.3</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;max-width:860px;margin:0 auto;padding:20px;background:#f6f7f9;color:#1a1a1a}
 h1{font-size:20px}h2{font-size:16px;margin-top:24px}.hint{font-size:13px;color:#555;margin:8px 0;line-height:1.6}
 .bar{position:sticky;top:0;background:#fff;padding:12px 16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.1);margin-bottom:16px;z-index:5}
 .bar button{background:#33c;color:#fff;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;margin-right:8px}
 .card{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .meta{font-size:12px;color:#666;margin-bottom:6px}
 .pt{font-weight:600;margin:4px 0}.simp{white-space:pre-wrap;font-size:13px;background:#fafafa;padding:8px;border-radius:6px;max-height:180px;overflow:auto;margin:6px 0}
 .verdict{font-size:13px;margin:6px 0}.v{padding:1px 8px;border-radius:10px;background:#eef;color:#33c}
 .choice button{border:1px solid #ccc;background:#fff;border-radius:6px;padding:5px 14px;cursor:pointer;margin-right:8px}
 .choice button.sel{background:#33c;color:#fff;border-color:#33c}
</style></head><body>
<h1>保留率复核 + 新增错误确认 · T6.3</h1>
<div class="hint"><b>第一部分</b>：30 个必留点判定，裁判已判“成立/不成立”，请复核（同意/不同意）。<b>第二部分</b>：裁判列出的全部疑似新增错误，<b>逐条确认</b>（不抽样）：是新增错误 / 不是。判完导出 JSON 发回助手。</div>
<div class="bar">复核 <b id="p1">0</b>/30 · 错误确认 <b id="p2">0</b>/<span id="et"></span> · <button onclick="exp()">导出结果</button><button onclick="cp()">复制</button></div>
<h2>一、保留率复核（30）</h2><div id="checks"></div>
<h2>二、新增错误确认（全部）</h2><div id="errors"></div>
<script>
const CHECKS=__CHECKS__;const ERRORS=__ERRORS__;
const cs=CHECKS.map(d=>({id:d.id,user_agree:null}));
const es=ERRORS.map(d=>({response_id:d.response_id,claim:d.claim,is_error:null}));
document.getElementById('et').textContent=ERRORS.length;
const cbox=document.getElementById('checks');
CHECKS.forEach((d,i)=>{
 const card=document.createElement('div');card.className='card';
 const meta=document.createElement('div');meta.className='meta';meta.textContent=`#${i+1} · ${d.id}`;
 const pt=document.createElement('div');pt.className='pt';pt.textContent='必留点：'+d.point;
 const sp=document.createElement('div');sp.className='simp';sp.textContent='简化版：'+d.simplified;
 const vd=document.createElement('div');vd.className='verdict';vd.innerHTML='裁判判定：<span class="v">'+(d.judge_held?'成立':'不成立')+'</span>';
 const ch=document.createElement('div');ch.className='choice';
 ['同意','不同意'].forEach(opt=>{const b=document.createElement('button');b.textContent=opt;b.onclick=()=>{cs[i].user_agree=(opt==='同意');[...ch.children].forEach(x=>x.className='');b.className='sel';refresh();};ch.appendChild(b);});
 card.appendChild(meta);card.appendChild(pt);card.appendChild(sp);card.appendChild(vd);card.appendChild(ch);cbox.appendChild(card);
});
const ebox=document.getElementById('errors');
ERRORS.forEach((d,i)=>{
 const card=document.createElement('div');card.className='card';
 const meta=document.createElement('div');meta.className='meta';meta.textContent=`${d.response_id}`;
 const cl=document.createElement('div');cl.className='pt';cl.textContent='疑似新增错误：'+d.claim;
 const ch=document.createElement('div');ch.className='choice';
 ['是新增错误','不是'].forEach(opt=>{const b=document.createElement('button');b.textContent=opt;b.onclick=()=>{es[i].is_error=(opt==='是新增错误');[...ch.children].forEach(x=>x.className='');b.className='sel';refresh();};ch.appendChild(b);});
 card.appendChild(meta);card.appendChild(cl);card.appendChild(ch);ebox.appendChild(card);
});
function refresh(){document.getElementById('p1').textContent=cs.filter(x=>x.user_agree!==null).length;document.getElementById('p2').textContent=es.filter(x=>x.is_error!==null).length;}
function result(){return {retention_checks:cs,new_errors:es};}
function exp(){const b=new Blob([JSON.stringify(result(),null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='retention_check_user.json';a.click();}
function cp(){navigator.clipboard.writeText(JSON.stringify(result(),null,2)).then(()=>alert('已复制，发回助手'));}
refresh();
</script></body></html>"""


def render_retention_page(checks, errors):
    return TEMPLATE.replace("__CHECKS__", json.dumps(checks, ensure_ascii=False)) \
                   .replace("__ERRORS__", json.dumps(errors, ensure_ascii=False))


def main():
    csrc = os.path.join(ROOT, "human", "retention_check", "retention_checks.jsonl")
    esrc = os.path.join(ROOT, "human", "retention_check", "new_errors.jsonl")
    if not os.path.exists(csrc):
        print("NO_RETENTION_CHECKS（须先有裁判保留率判定+抽样30）")
        return
    with open(csrc, encoding="utf-8") as f:
        checks = [json.loads(line) for line in f if line.strip()]
    errors = []
    if os.path.exists(esrc):
        with open(esrc, encoding="utf-8") as f:
            errors = [json.loads(line) for line in f if line.strip()]
    out = os.path.join(ROOT, "human", "retention_check", "retention_check.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_retention_page(checks, errors))
    print("WROTE", out, "checks", len(checks), "errors", len(errors))


if __name__ == "__main__":
    main()
