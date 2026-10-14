"""Valida referências documentais e destinos locais de todas as páginas geradas."""
import json, hashlib
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parent
records=sum([json.loads((ROOT/f).read_text()) for f in ('cases.json','statements.json')],[])
extra=json.loads((ROOT/'lula_records.json').read_text())
records += extra['cases'] + extra['statements']
docs=json.loads((ROOT/'documents.json').read_text()); bydoc={d['id']:d for d in docs}; ids={r['id'] for r in records}
assert len(ids)==len(records)
assert len({r['slug'] for r in records})==len(records)
def walk(x):
    if isinstance(x,dict):
        if 'document' in x:
            assert x['document'] in bydoc,x
            assert 1<=x['page']<=bydoc[x['document']]['pages'],x
        if 'url' in x: assert x['url'].startswith('https://'),x
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
walk(records)
for r in records:
    for related in r.get('dossier',{}).get('related',[]):assert related in ids
for d in docs:
    for g in d['guide']:assert 1<=g['page']<=d['pages']
    for rid in d['recordIds']:assert rid in ids
    if d.get('local'):
        p=ROOT/'dist'/d['path'];assert p.is_file(),p
        assert hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256'],p
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k not in ('href','src') or not v:continue
            u=urlsplit(v)
            if u.scheme or u.netloc or not u.path:continue
            target=((ROOT/'dist'/unquote(u.path).lstrip('/')) if u.path.startswith('/') else (self.path.parent/unquote(u.path))).resolve()
            assert target.is_file() or (target/'index.html').is_file(),(self.path,v)
pages=list((ROOT/'dist').rglob('*.html'))
for p in pages:
    parser=Links();parser.path=p;parser.feed(p.read_text())
assert len(pages)>=1+len(records),len(pages)
print(f'OK: {len(pages)} páginas, {len(records)} fichas, hashes dos PDFs locais e referências por página.')
