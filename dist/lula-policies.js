/* Catálogo documental independente dos episódios e das falas. */
(async function(){
'use strict';
const main=document.getElementById('main');if(!main)return;
const box=document.createElement('section');box.id='lula-policies';box.hidden=true;box.setAttribute('aria-label','Políticas dos governos Lula desde 2003');
const anchor=document.getElementById('featured-dossiers');main.insertBefore(box,anchor||main.firstChild);
const style=document.createElement('link');style.rel='stylesheet';style.href='/lula-policies.css?v=20261013';document.head.append(style);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data,theme='',period='',query='';
const sync=()=>{box.hidden=!document.querySelector('[data-view="lula"].active');};
new MutationObserver(sync).observe(document.querySelector('.sidebar nav')||main,{subtree:true,attributes:true,attributeFilter:['class']});sync();
box.innerHTML='<p>Carregando políticas documentadas…</p>';
try{const response=await fetch('/lula-policies.json?v=20261013');if(!response.ok)throw new Error('HTTP '+response.status);data=await response.json();}catch(error){box.innerHTML='<p>Não foi possível carregar as políticas. <button type="button" onclick="location.reload()">Recarregar a página</button></p>';return;}
const themes=[...new Set(data.records.map(r=>r.theme))].sort();
box.innerHTML=`<div class="lp-heading"><span>HISTÓRICO DE GOVERNO · FONTES OFICIAIS</span><h2>Políticas públicas desde 2003</h2><p>Programas, leis e mudanças institucionais nos três mandatos de Lula. Explore por período e área.</p></div><p class="lp-coverage">${esc(data.coverage)} A existência de uma lei não comprova, sozinha, a eficácia da política.</p><div class="lp-controls"><label>Buscar medida<input id="lp-query" type="search" placeholder="Ex.: ProUni, habitação, medicamentos"></label><label>Mandato<select id="lp-period"><option value="">Todos os mandatos</option><option>2003–2006</option><option>2007–2010</option><option>2023–2026</option></select></label><button id="lp-clear" type="button">Limpar</button></div><div class="lp-charts"><div><h3>Medidas por área</h3><div id="lp-themes"></div></div><div><h3>Marcos por ano</h3><div id="lp-years"></div></div></div><p id="lp-count" aria-live="polite"></p><div id="lp-records" class="lp-records"></div><p class="lp-foot">Fontes legais conferidas em 13/10/2026. A seção abaixo mantém os episódios do acervo em catálogo próprio.</p>`;
const normalize=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
let year=0;
function render(){const base=data.records.filter(r=>(!period||r.period===period)&&(!query||normalize([r.title,r.summary,r.theme].join(' ')).includes(normalize(query))));const list=base.filter(r=>(!theme||r.theme===theme)&&(!year||r.year===year));
box.querySelector('#lp-count').textContent=`${list.length} de ${data.records.length} medidas legais documentadas`;
box.querySelector('#lp-themes').innerHTML=themes.map(t=>{const count=base.filter(r=>r.theme===t).length;return `<button type="button" data-lp-theme="${esc(t)}" aria-pressed="${t===theme}"><span>${esc(t)}</span><b>${count}</b><i style="width:${count/Math.max(1,base.length)*100}%"></i></button>`;}).join('');
box.querySelector('#lp-years').innerHTML=[...new Set(data.records.map(r=>r.year))].sort().map(y=>`<button type="button" data-lp-year="${y}" aria-pressed="${year===y}">${y}<b>${base.filter(r=>r.year===y).length}</b></button>`).join('');
box.querySelector('#lp-records').innerHTML=list.sort((a,b)=>a.year-b.year||a.title.localeCompare(b.title)).map(r=>`<article><div class="lp-meta">${r.year} · ${esc(r.theme)} · ${esc(r.period)}</div><h3>${esc(r.title)}</h3><p>${esc(r.summary)}</p><div class="lp-nature">${esc(r.nature)}</div><details><summary>Atribuição e limites da evidência</summary><p>${esc(r.limits)}</p></details><a href="${esc(r.source)}" target="_blank" rel="noopener noreferrer">${esc(r.sourceLabel)} ↗</a></article>`).join('')||'<p>Nenhuma medida neste recorte. Limpe os filtros para ver o catálogo.</p>';
}
box.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.dataset.lpTheme){theme=theme===b.dataset.lpTheme?'':b.dataset.lpTheme;render();}if(b.dataset.lpYear){year=year===+b.dataset.lpYear?0:+b.dataset.lpYear;render();}if(b.id==='lp-clear'){theme='';year=0;period='';query='';box.querySelector('#lp-query').value='';box.querySelector('#lp-period').value='';render();}});
box.querySelector('#lp-query').addEventListener('input',event=>{query=event.target.value;render();});box.querySelector('#lp-period').addEventListener('change',event=>{period=event.target.value;render();});render();
})();
