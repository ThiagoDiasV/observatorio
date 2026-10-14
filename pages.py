"""Páginas permanentes legíveis sem JavaScript, geradas com a biblioteca padrão."""
from html import escape
from pathlib import Path
import json
from datetime import date
ORIGIN='https://observatorio.leaomc.com'
def _safe_write(path, content):
    try:
        path.write_text(content)
    except PermissionError:
        pass
def e(s):return escape(str(s),quote=True)
def datebr(s):return '/'.join(reversed(s.split('-')))
def recordpath(r):return ('falas/' if r.get('kind')=='speech' else 'casos/')+r['slug']+'/'
def generate_pages(root, records, documents):
    dest=root/'dist'; docs={d['id']:d for d in documents}; index={r['id']:r for r in records}
    def refs(rs):
        out=[]
        for s in rs:
            if 'document' in s:
                d=docs[s['document']];url=d['path'] if d['path'].startswith('https://') else '../../'+d['path'];url+='#page='+str(s['page'])
            else:url=s['url']
            out.append(f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(s["label"])} ↗</a>')
        return '<div class="evidence-refs">'+''.join(out)+'</div>'
    def cards(items):return ''.join(f'<article class="evidence-card"><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p>{refs(x.get("refs",[]))}</article>' for x in items)
    for r in records:
        speech=r.get('kind')=='speech';d=r.get('dossier');path=recordpath(r);canonical=ORIGIN+'/'+path
        title=r['title']; sections=[]
        if d:
            sections.append(f'<section id="situacao"><div class="section-number">01 / SITUAÇÃO</div><h2>O que está documentado</h2><div class="evidence-grid">{cards(d["established"])}</div><h2>O que exige distinção ou continua em disputa</h2><div class="evidence-grid disputed">{cards(d["contested"])}</div></section>')
            sections.append(f'<section id="pessoas"><div class="section-number">02 / RESPONSABILIDADES</div><h2>Quem aparece e em qual condição</h2><div class="evidence-grid">{cards(d["roles"])}</div></section>')
            amounts=d.get('amounts',[])
            if amounts:
                def money(v):return ('R$ '+f'{v:,.2f}').replace(',','X').replace('.',',').replace('X','.')
                sections.append('<section id="valores"><div class="section-number">03 / VALORES</div><h2>Cada número tem uma natureza</h2><p class="section-intro">Os valores abaixo não são somados: podem se sobrepor ou representar grandezas diferentes.</p><div class="amount-grid">'+''.join(f'<article class="amount-card"><span>{e(a["nature"])}</span><strong>{money(a["value"])}</strong><h3>{e(a["label"])}</h3><p>{e(a["note"])}</p>{refs(a["refs"])}</article>' for a in amounts)+'</div></section>')
            sections.append('<section id="cronologia"><div class="section-number">04 / CRONOLOGIA</div><h2>Os marcos, com suas fontes</h2><label class="event-filter">Mostrar período <select id="event-year"><option value="">Todos os anos</option>'+''.join(f'<option>{y}</option>' for y in sorted(set(x['date'][:4] for x in d['events'])))+'</select></label><ol class="dossier-timeline">'+''.join(f'<li data-event-year="{x["date"][:4]}"><time datetime="{e(x["date"])}">{datebr(x["date"])}</time><div><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p>{refs(x["refs"])}</div></li>' for x in d['events'])+'</ol><p id="event-count" aria-live="polite"></p></section>')
        else:
            sections.append('<section id="situacao"><h2>'+('Contexto da declaração' if speech else 'O episódio')+'</h2><p>'+e(r['summary'])+'</p><h2>'+('Repercussão documentada' if speech else 'Desfecho documentado')+'</h2><p>'+e(r['outcome'])+'</p></section>')
        sections.append(f'<section id="defesa"><div class="section-number">05 / RESPOSTAS</div><h2>Defesa, resposta e contexto</h2><p>{e(r["response"])}</p>{refs(r["sources"])}</section>')
        if r.get('analysis'):
            a=r['analysis'];sections.append(f'<aside id="analise" class="critical-analysis"><span class="overline">ANÁLISE EDITORIAL · OPINIÃO</span><h2>{e(a["title"])}</h2><p>{e(a["text"])}</p><small>Interpretação das fontes identificadas neste dossiê.</small></aside>')
        selected=[x for x in documents if r['id'] in x['recordIds']]
        doccontent=''
        for doc in selected:
            url=doc['path'] if doc['path'].startswith('https://') else '../../'+doc['path']
            doccontent+=f'<article class="evidence-card"><span class="overline">{e(doc["kind"])}</span><h3>{e(doc["title"])}</h3><p>{e(doc["issuer"])}'+(f' · {doc["pages"]} páginas' if doc.get('pages') else '')+f'</p><p>{e(doc["limits"])}</p><a class="primary-link" href="{e(url)}" target="_blank" rel="noopener noreferrer">Abrir PDF ↗</a><a class="origin-link" href="{e(doc["originUrl"])}" target="_blank" rel="noopener noreferrer">Consultar origem</a>'+refs([{'document':doc['id'],'page':g['page'],'label':f'PDF p. {g["page"]}: {g["label"]}'} for g in doc['guide']])+'</article>'
        sections.append('<section id="documentos"><div class="section-number">06 / DOCUMENTOS</div><h2>Confira a peça e seu alcance</h2><p class="section-intro">Os atalhos usam a posição da página no arquivo PDF. Nos volumes parciais, ela pode diferir da numeração impressa.</p><div class="evidence-grid">'+(doccontent or '<p>Inteiro teor em PDF não incorporado. Consulte as fontes identificadas abaixo; não inferimos que um documento inexistente no acervo seja inexistente no processo.</p>')+'</div></section>')
        history=''.join(f'<li><time>{datebr(x["date"])}</time><p>{e(x["text"])}</p></li>' for x in r.get('history',[])) or '<li>Ficha migrada para endereço permanente. Não houve revisão documental aprofundada nesta edição.</li>'
        reviewed=(f'Revisão editorial em {datebr(r["reviewedAt"])}. {e(r.get("reviewScope",""))}' if r.get('reviewedAt') else 'Revisão aprofundada pendente; conteúdo da edição anterior.')
        sections.append(f'<section id="atualizacoes"><div class="section-number">07 / TRANSPARÊNCIA</div><h2>Atualizações e limites</h2><p>{reviewed}</p><p>{e(d["limits"] if d else "A ausência de desdobramento neste acervo não comprova que a situação permaneceu inalterada.")}</p><ol class="change-log">{history}</ol><details><summary>Fontes da ficha ({len(r["sources"])})</summary>{refs(r["sources"])}</details></section>')
        related=d.get('related',[]) if d else []
        if related:sections.append('<section class="related-cases"><h2>Continue a investigação</h2>'+''.join(f'<a href="../../{recordpath(index[id])}">{e(index[id]["title"])} →</a>' for id in related)+'</section>')
        quote=''
        if speech:
            quote=f'<p class="speech-date">{e(r["dateBasis"])} · {datebr(r["eventDate"])} · {e(r["medium"])}</p>'
            quote+=f'<blockquote>“{e(r["quote"])}”<cite>Trecho curto; confira o contexto e a fonte.</cite></blockquote>' if r.get('quote') else '<p class="paraphrase">Síntese editorial · não é citação literal</p>'
        desc=(d['lead'] if d else r['summary']); meta=e(desc[:250]);nav=['situacao','pessoas','valores','cronologia','defesa','documentos','atualizacoes'] if d else ['situacao','defesa','documentos','atualizacoes'];labels=['Situação','Pessoas','Valores','Cronologia','Respostas','Documentos','Atualizações'] if d else ['Contexto','Respostas','Documentos','Atualizações']
        navhtml=''.join(f'<a href="#{id}">{label}</a>' for id,label in zip(nav,labels) if id!='valores' or (d and d['amounts']))
        html=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | Lula Presidente</title><meta name="description" content="{meta}"><link rel="canonical" href="{e(canonical)}"><meta property="og:type" content="article"><meta property="og:title" content="{e(title)} | Lula Presidente"><meta property="og:description" content="{meta}"><meta property="og:url" content="{e(canonical)}"><meta name="twitter:card" content="summary"><link rel="stylesheet" href="../../style.css"><link rel="stylesheet" href="../../dossier.css"></head><body class="dossier-page"><a class="skip" href="#dossier-main">Pular para o dossiê</a><header class="dossier-header"><a class="dossier-brand" href="../../">★ LULA PRESIDENTE</a><a href="../../">← Voltar à campanha</a></header><main id="dossier-main" class="dossier-main"><div class="dossier-eyebrow">{e(r['id'])} / {e(r['theme'].upper())} / {'DOSSIÊ APROFUNDADO' if d else 'FICHA DOCUMENTAL'}</div><h1>{e(title)}</h1><div class="dossier-status"><span class="badge">{e(r['status'])}</span><span>Último marco: {datebr(r['date'])}</span></div><p class="dossier-lead">{e(desc)}</p>{quote}<p class="people">{e(' · '.join(r['people']))}</p>{f'<p class="process-number">{e(d["process"])}</p>' if d else ''}<div class="share-row"><button id="copy-link">Copiar link desta ficha</button><button id="print-page">Imprimir / salvar PDF</button><span id="share-status" role="status"></span></div><input id="share-fallback" aria-label="Link para copiar" readonly hidden><p class="review-note">{reviewed}<br>Último marco documentado: {datebr(r['date'])}. <span data-source-date="{e(r['date'])}"></span></p><nav class="dossier-nav" aria-label="Nesta ficha">{navhtml}</nav>{''.join(sections)}<footer><span>★ LULA PRESIDENTE · Apoio editorial · Fontes por registro</span><a href="../../">Voltar à campanha</a></footer></main><script src="../../dossier.js"></script></body></html>'''
        out=dest/path;out.mkdir(parents=True,exist_ok=True);_safe_write(out/'index.html', html)
    urls=[ORIGIN+'/']+[ORIGIN+'/'+recordpath(r) for r in records]
    _safe_write(dest/'sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+e(u)+'</loc></url>' for u in urls)+'</urlset>')
    _safe_write(dest/'robots.txt', 'User-agent: *\nAllow: /\nSitemap: '+ORIGIN+'/sitemap.xml\n')
