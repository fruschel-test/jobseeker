import html
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://api.search.brave.com/res/v1/web/search"
API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
OUT = Path("public/index.html")

# These are web-search queries only. No direct requests or scraping of job-board pages.
QUERIES = [
 # General discovery queries
 {"country":"AU","label":"Australia · sponsorship","kind":"sponsorship","q":'("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") ("visa sponsorship" OR "482 visa" OR "employer sponsored") Australia jobs'},
 {"country":"AU","label":"Australia · relocation","kind":"relocation","q":'("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") ("relocation assistance" OR "relocation package") Australia jobs'},
 {"country":"AU","label":"Australia · SEEK indexed results","kind":"sponsorship","q":'site:seek.com.au ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager" OR "Head of Engineering") ("visa sponsorship" OR "482 visa" OR relocation)'},
 {"country":"AU","label":"Australia · Indeed indexed results","kind":"mixed","q":'site:au.indeed.com ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager" OR "Platform Lead") (sponsorship OR relocation) Australia'},
 {"country":"AU","label":"Australia · LinkedIn indexed results","kind":"mixed","q":'site:linkedin.com/jobs/view ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") (Australia OR Sydney OR Melbourne OR Brisbane) (sponsorship OR relocation)'},
 {"country":"AU","label":"Australia · Jora indexed results","kind":"mixed","q":'site:jora.com ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager" OR "DevOps Manager") Australia (sponsorship OR relocation)'},
 {"country":"AU","label":"Australia · employer ATS pages","kind":"mixed","q":'(site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:careers.smartrecruiters.com) ("Engineering Manager" OR "Platform Engineering Manager" OR "Head of Engineering") (Australia OR Sydney OR Melbourne) (sponsorship OR relocation)'},
 {"country":"AU","label":"Australia · company careers and cloud leadership","kind":"mixed","q":'("Cloud Engineering Manager" OR "DevOps Manager" OR "Infrastructure Engineering Manager" OR "Director of Engineering") ("visa sponsorship" OR relocation OR "subclass 482") Australia careers'},
 {"country":"NZ","label":"New Zealand · sponsorship","kind":"sponsorship","q":'("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") ("visa sponsorship" OR "accredited employer" OR "work visa") "New Zealand" jobs'},
 {"country":"NZ","label":"New Zealand · relocation","kind":"relocation","q":'("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") ("relocation assistance" OR "relocation package") "New Zealand" jobs'},
 {"country":"NZ","label":"New Zealand · SEEK indexed results","kind":"sponsorship","q":'site:seek.co.nz ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager" OR "Head of Engineering") ("visa sponsorship" OR "accredited employer" OR relocation)'},
 {"country":"NZ","label":"New Zealand · Trade Me Jobs indexed results","kind":"mixed","q":'site:trademe.co.nz/a/jobs ("Software Engineering Manager" OR "Engineering Manager" OR "Platform Lead" OR "Head of Engineering") (visa OR sponsorship OR relocation)'},
 {"country":"NZ","label":"New Zealand · Indeed indexed results","kind":"mixed","q":'site:nz.indeed.com ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") (sponsorship OR relocation) "New Zealand"'},
 {"country":"NZ","label":"New Zealand · LinkedIn indexed results","kind":"mixed","q":'site:linkedin.com/jobs/view ("Software Engineering Manager" OR "Platform Engineering Manager" OR "Engineering Manager") ("New Zealand" OR Auckland OR Wellington OR Christchurch) (sponsorship OR relocation)'},
 {"country":"NZ","label":"New Zealand · employer ATS pages","kind":"mixed","q":'(site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:careers.smartrecruiters.com) ("Engineering Manager" OR "Platform Engineering Manager" OR "Head of Engineering") ("New Zealand" OR Auckland OR Wellington) (sponsorship OR relocation)'},
 {"country":"NZ","label":"New Zealand · company careers and cloud leadership","kind":"mixed","q":'("Cloud Engineering Manager" OR "DevOps Manager" OR "Infrastructure Engineering Manager" OR "Director of Engineering") ("visa sponsorship" OR relocation OR "accredited employer") "New Zealand" careers'},
]
# Apply exclusions to every search, not only to the snippets returned by Brave.
# This helps prevent off-target listings when the snippet omits the job location.
for _query in QUERIES:
    _query["q"] += ' -remote -"United States" -USA -"United Kingdom" -Canada'

ROLE_TERMS = ["software engineering manager","platform engineering manager","engineering manager","cloud engineering manager","devops manager","head of engineering","infrastructure engineering manager","platform engineering lead","engineering lead","director of engineering","engineering director","head of platform","platform lead"]
# Require location evidence in the result itself; Brave's country parameter alone is not enough.
AU_LOCATION_TERMS = ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra", "gold coast", "hobart", "new south wales", "victoria, australia", "queensland", "western australia", "south australia", "tasmania", "act, australia"]
NZ_LOCATION_TERMS = ["new zealand", "auckland", "wellington", "christchurch", "hamilton, new zealand", "tauranga", "dunedin", "queenstown", "waikato", "canterbury, new zealand"]
REMOTE_TERMS = ["remote", "work from anywhere", "anywhere in the world", "fully distributed", "distributed team", "work remotely"]
OUTSIDE_TERMS = ["united states", "u.s.-only", "us only", "usa only", "remote us", "remote - us", "remote, us", "remote usa", "united kingdom only", "uk only", "canada only", "india only", "europe only"]
SPONSOR_TERMS = ["visa sponsorship","sponsorship available","482 visa","subclass 482","employer sponsored","employer sponsorship","accredited employer","work visa","visa support","sponsor visa"]
RELOCATION_TERMS = ["relocation","relocation assistance","relocation package","relocation support"]
NEGATIVE_TERMS = ["no sponsorship","not offering sponsorship","must have full working rights","full working rights required","unrestricted working rights","citizen or permanent resident only"]
NOISE_TERMS = ["course","training","salary guide","what is","how to become","resume template"]

def matches(text, terms):
    low = text.lower()
    return [t for t in terms if t in low]

def api_search(query, country):
    params = urllib.parse.urlencode({"q":query,"country":country,"search_lang":"en","count":10,"freshness":"pw","safesearch":"moderate"})
    req = urllib.request.Request(API_URL + "?" + params, headers={
        "Accept":"application/json","X-Subscription-Token":API_KEY,"User-Agent":"TalentBridgeJobSearch/1.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))

def classify(item, meta):
    title = (item.get("title") or "").strip()
    desc = (item.get("description") or "").strip()
    url = (item.get("url") or "").strip()
    text = f"{title} {desc} {url}".lower()
    roles = matches(text, ROLE_TERMS)
    title_roles = matches(title, ROLE_TERMS)
    sponsor = matches(text, SPONSOR_TERMS)
    relocation = matches(text, RELOCATION_TERMS)
    negatives = matches(text, NEGATIVE_TERMS)
    if not roles or matches(text, NOISE_TERMS) or not url.startswith("http"):
        return None

    # Reject remote roles entirely, per the user's requirement (including remote AU/NZ roles).
    if matches(text, REMOTE_TERMS):
        return None

    # A result must contain some evidence that the actual job is in the target country.
    # Do not trust Brave's country parameter alone: it can return unrelated countries.
    domain = urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    if meta["country"] == "AU":
        locations = matches(text, AU_LOCATION_TERMS)
        domain_country = domain.endswith(".com.au") or domain.endswith(".net.au") or domain.endswith(".org.au")
    else:
        locations = matches(text, NZ_LOCATION_TERMS)
        domain_country = domain.endswith(".co.nz") or domain.endswith(".govt.nz")
    if not locations and not domain_country:
        return None

    # Explicit off-target location/eligibility signals override a generic sponsorship mention.
    if matches(text, OUTSIDE_TERMS):
        return None

    if "seek.com.au" in domain or "seek.co.nz" in domain:
        source = "SEEK (resultado indexado)"
    elif "linkedin.com" in domain:
        source = "LinkedIn (resultado indexado)"
    elif "indeed." in domain:
        source = "Indeed (resultado indexado)"
    elif "jora.com" in domain:
        source = "Jora (resultado indexado)"
    elif "trademe.co.nz" in domain:
        source = "Trade Me Jobs (resultado indexado)"
    elif "greenhouse.io" in domain:
        source = "Greenhouse / página de carreira"
    elif "lever.co" in domain:
        source = "Lever / página de carreira"
    elif "ashbyhq.com" in domain:
        source = "Ashby / página de carreira"
    elif "smartrecruiters.com" in domain:
        source = "SmartRecruiters / página de carreira"
    else:
        source = domain
    score = 30 + (20 if title_roles else 0) + min(18,6*len(sponsor)) + min(12,6*len(relocation))
    if any(t in text for t in ["aws","kubernetes","eks","cloud platform","ci/cd","devops"]): score += 5
    if negatives: score -= 35
    score = max(0,min(100,score))
    if negatives: status, cls = "Possível restrição: verificar", "negative"
    elif sponsor and relocation: status, cls = "Menção a sponsorship e relocation", "strong"
    elif sponsor: status, cls = "Menção a sponsorship", "strong"
    elif relocation: status, cls = "Menção a relocation", "medium"
    else: status, cls = "Patrocínio não confirmado", "unknown"
    return {"title":title,"url":url,"description":desc,"country":meta["country"],"source":source,
            "sponsor":sponsor,"relocation":relocation,"negatives":negatives,"status":status,
            "cls":cls,"score":score,"query":meta["label"]}

def render(jobs, generated_at, error=None):
    jobs.sort(key=lambda j:(j["score"],j["country"]=="AU"),reverse=True)
    cards=[]
    for j in jobs:
        tags=[f'<span class="tag">{html.escape(j["country"])}</span>',f'<span class="tag">{html.escape(j["source"])}</span>',f'<span class="tag {j["cls"]}">{html.escape(j["status"])}</span>']
        if j["sponsor"]: tags.append('<span class="tag strong">Sponsorship: menção encontrada</span>')
        if j["relocation"]: tags.append('<span class="tag medium">Relocation: menção encontrada</span>')
        if j["negatives"]: tags.append('<span class="tag negative">Possível restrição</span>')
        evidence=[]
        if j["sponsor"]: evidence.append("Sponsorship: "+", ".join(j["sponsor"]))
        if j["relocation"]: evidence.append("Relocation: "+", ".join(j["relocation"]))
        if j["negatives"]: evidence.append("Restrições: "+", ".join(j["negatives"]))
        evidence_html='<p class="evidence">'+html.escape(" · ".join(evidence))+'</p>' if evidence else ""
        search_text = (j["title"] + " " + j["description"] + " " + j["source"] + " " + " ".join(j["sponsor"]) + " " + " ".join(j["relocation"]) + " " + " ".join(j["negatives"])).lower()
        cards.append(f'''<article class="job" data-country="{html.escape(j["country"], quote=True)}" data-text="{html.escape(search_text, quote=True)}" data-sponsorship="{"yes" if j["sponsor"] else ("no" if j["negatives"] else "unknown")}" data-relocation="{"yes" if j["relocation"] else "no"}" data-score="{j["score"]}"><div class="jobtop"><span class="source">{html.escape(j["source"])} · {html.escape(j["country"])}</span><span class="score">Relevância {j["score"]}/100</span></div><h2><a href="{html.escape(j["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(j["title"])}</a></h2><p class="snippet">{html.escape(j["description"] or "Sem resumo fornecido pelo mecanismo de pesquisa.")}</p><div class="tags">{"".join(tags)}</div>{evidence_html}<p class="meta">Encontrada via: {html.escape(j["query"])} · <a href="{html.escape(j["url"],quote=True)}" target="_blank" rel="noopener noreferrer">Abrir anúncio original ↗</a></p></article>''')
    empty = '<div class="empty"><h2>Nenhuma vaga passou pelos filtros nesta execução</h2><p>Isso não significa que não existam vagas: a cobertura depende da indexação do mecanismo de busca. Tente novamente na próxima execução.</p></div>' if not cards else ""
    error_html=f'<div class="warning"><strong>Aviso da execução:</strong> {html.escape(error)}</div>' if error else ""
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Talent Bridge AU/NZ — Relatório de vagas</title>
<style>
:root{{--bg:#f4f6fb;--panel:#fff;--ink:#182238;--muted:#66728a;--line:#e2e7f0;--blue:#2457d6;--green:#12684f;--amber:#8b5800;--red:#9c3030}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}header{{background:#111b31;color:#fff;padding:28px 18px}}.wrap{{max-width:1100px;margin:auto}}.eyebrow{{font-size:11px;text-transform:uppercase;letter-spacing:.13em;color:#a8bdff;font-weight:800}}h1{{font-size:clamp(27px,4vw,38px);line-height:1.1;letter-spacing:-.03em;margin:8px 0}}header p{{color:#d5deef;margin:8px 0 0}}main{{max-width:1100px;margin:22px auto;padding:0 16px 36px}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}}.stat,.job,.empty,.warning{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px}}.stat span{{display:block;font-size:12px;color:var(--muted)}}.stat strong{{font-size:24px}}.toolbar{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:14px 0}}.toolbar p{{font-size:12px;color:var(--muted);margin:0}}.joblist{{display:grid;gap:12px}}.jobtop{{display:flex;justify-content:space-between;gap:8px;align-items:center}}.source{{font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.1em;color:var(--blue)}}.score{{font-size:11px;color:var(--muted);white-space:nowrap}}.job h2{{font-size:18px;line-height:1.3;margin:9px 0}}a{{color:#214dbb}}.snippet{{font-size:13px;color:#4c5870;margin:0 0 10px}}.tags{{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0}}.tag{{font-size:10px;background:#eff2f7;color:#46536a;border-radius:99px;padding:4px 8px}}.tag.strong{{background:#e4f6ee;color:var(--green)}}.tag.medium{{background:#fff1d8;color:var(--amber)}}.tag.negative{{background:#fdeaea;color:var(--red)}}.evidence{{font-size:12px;font-weight:650}}.meta{{font-size:11px;color:var(--muted);margin:12px 0 0}}.warning{{background:#fff8e8;border-color:#ecd8a8;color:#684a14;margin-bottom:14px}}.empty p,.footnote{{font-size:13px;color:var(--muted)}}.footnote{{margin-top:18px;padding:14px;background:#fff;border:1px solid var(--line);border-radius:12px}}@media(max-width:600px){{.stats{{grid-template-columns:1fr 1fr}}.jobtop{{align-items:flex-start;flex-direction:column}}}}
.filters{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}}
.filters h2{{font-size:18px;margin:0 0 12px}}
.filter-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
.filter-field{{display:flex;flex-direction:column;gap:5px}}
.filter-field label{{font-size:12px;color:var(--muted);font-weight:700}}
.filter-field input,.filter-field select{{width:100%;min-height:40px;border:1px solid var(--line);border-radius:8px;padding:8px;background:white;color:var(--ink);font:inherit}}
.filter-check{{display:flex;gap:8px;align-items:center;margin-top:12px}}
.filter-actions{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}}
.filter-actions button{{border:1px solid var(--line);border-radius:8px;padding:9px 12px;cursor:pointer;background:white;color:var(--ink);font:inherit}}
.filter-actions .primary{{background:var(--blue);color:white;border-color:var(--blue)}}
.filter-summary{{color:var(--muted);font-size:12px;margin:10px 0 0}}
.job[hidden]{{display:none!important}}
@media(max-width:700px){{.filter-grid{{grid-template-columns:1fr}}}}
</style></head><body><header><div class="wrap"><div class="eyebrow">Relatório automatizado · três vezes por dia</div><h1>Talent Bridge <span style="color:#a8bdff">AU · NZ</span></h1><p>Vagas de liderança em software, plataformas, cloud e DevOps. Prioridade para vagas presenciais/híbridas localizadas na Austrália ou na Nova Zelândia, com evidência de visa sponsorship e/ou relocation.</p></div></header><main>{error_html}<div class="stats"><div class="stat"><span>Resultados relevantes</span><strong>{len(jobs)}</strong></div><div class="stat"><span>Austrália</span><strong>{sum(1 for j in jobs if j["country"]=="AU")}</strong></div><div class="stat"><span>Nova Zelândia</span><strong>{sum(1 for j in jobs if j["country"]=="NZ")}</strong></div></div><div class="toolbar"><p>Última execução: {html.escape(generated_at)} UTC</p></div><section class="filters" aria-labelledby="filter-title"><h2 id="filter-title">Filtros de vagas</h2>
<div class="filter-grid">
<div class="filter-field"><label for="filter-country">País</label><select id="filter-country"><option value="both">Austrália e Nova Zelândia</option><option value="AU">Somente Austrália</option><option value="NZ">Somente Nova Zelândia</option></select></div>
<div class="filter-field"><label for="filter-keyword">Cargo ou palavra-chave</label><input id="filter-keyword" value="Engineering Manager" placeholder="Ex.: Platform Engineering Manager"></div>
<div class="filter-field"><label for="filter-mode">Modalidade</label><select id="filter-mode"><option value="all">Todas as modalidades</option><option value="onsite">Presencial</option><option value="hybrid">Híbrido</option></select></div>
<div class="filter-field"><label for="filter-sponsorship">Visa sponsorship</label><select id="filter-sponsorship"><option value="all">Todas as vagas</option><option value="yes">Com menção a sponsorship</option><option value="unknown">Sem confirmação explícita</option><option value="no">Possível restrição identificada</option></select></div>
<div class="filter-field"><label for="filter-score">Relevância mínima: <output id="filter-score-value">40</output>/100</label><input id="filter-score" type="range" min="0" max="100" step="5" value="40"></div></div>
<label class="filter-check"><input id="filter-relocation" type="checkbox" checked> Priorizar vagas com relocation (ordenar primeiro)</label>
<div class="filter-actions"><button type="button" class="primary" id="apply-filters">Aplicar filtros</button><button type="button" id="reset-filters">Restaurar padrão</button></div><p class="filter-summary" id="filter-summary" aria-live="polite"></p></section>
<div class="joblist">{"".join(cards)}{empty}</div><div class="footnote"><strong>Importante:</strong> termos de sponsorship/relocation são encontrados nos títulos e resumos do mecanismo de pesquisa, não verificados contra a página completa. A menção não garante patrocínio. Confirme no anúncio original se aceitam candidatos offshore. O agente não faz scraping direto do SEEK; usa resultados devolvidos pela API de pesquisa. Sem banco de dados: cada execução substitui o relatório anterior.</div></main><script>
(() => {{
 const $ = id => document.getElementById(id);
 const list = document.querySelector('.joblist');
 if (!list) return;
 const originalOrder = [...list.querySelectorAll('.job')];
 function applyFilters() {{
  const country=$('filter-country').value, keyword=$('filter-keyword').value.trim().toLowerCase();
  const mode=$('filter-mode').value, sponsor=$('filter-sponsorship').value;
  const prioritize=$('filter-relocation').checked, score=Number($('filter-score').value);
  $('filter-score-value').textContent=score;
  const visible=[];
  for (const card of originalOrder) {{
   const text=(card.dataset.text||'').toLowerCase();
   const countryOK=country==='both'||card.dataset.country===country;
   const keywordOK=!keyword||text.includes(keyword);
   const scoreOK=Number(card.dataset.score||0)>=score;
   const sponsorValue=card.dataset.sponsorship||'unknown';
   const sponsorOK=sponsor==='all'||sponsorValue===sponsor;
   const hybrid=/\bhybrid\b|\bh[ií]brido\b/.test(text);
   const onsite=/\bon[- ]site\b|\bonsite\b|\bin[- ]office\b|\bin person\b|\bpresencial\b/.test(text);
   const modeOK=mode==='all'||(mode==='hybrid'&&hybrid)||(mode==='onsite'&&onsite);
   const show=countryOK&&keywordOK&&scoreOK&&sponsorOK&&modeOK;
   card.hidden=!show;
   if(show) visible.push(card);
  }}
  visible.sort((a,b)=>(prioritize?Number(b.dataset.relocation==='yes')-Number(a.dataset.relocation==='yes'):0)||Number(b.dataset.score||0)-Number(a.dataset.score||0));
  visible.forEach(card=>list.appendChild(card));
  $('filter-summary').textContent=`${{visible.length}} de ${{originalOrder.length}} vagas exibidas. ${{mode==='all'?'':'A modalidade é inferida do texto do anúncio. '}}${{prioritize?'Vagas com relocation aparecem primeiro.':''}}`;
 }}
 function reset() {{
  $('filter-country').value='both'; $('filter-keyword').value='Engineering Manager';
  $('filter-mode').value='all'; $('filter-sponsorship').value='all';
  $('filter-relocation').checked=true; $('filter-score').value=40; applyFilters();
 }}
 $('apply-filters').addEventListener('click',applyFilters);
 $('reset-filters').addEventListener('click',reset);
 $('filter-score').addEventListener('input',()=>$('filter-score-value').textContent=$('filter-score').value);
 $('filter-keyword').addEventListener('keydown',e=>{{if(e.key==='Enter')applyFilters();}});
 applyFilters();
}})();
</script></body></html>'''

def main():
    if not API_KEY:
        print("Missing BRAVE_SEARCH_API_KEY repository secret.", file=sys.stderr)
        sys.exit(2)
    found={}
    errors=[]
    for meta in QUERIES:
        try:
            data=api_search(meta["q"],meta["country"])
            for item in ((data.get("web") or {}).get("results") or []):
                job=classify(item,meta)
                if not job: continue
                key=job["url"].split("#",1)[0].rstrip("/")
                if key not in found or job["score"]>found[key]["score"]: found[key]=job
            time.sleep(0.7)
        except Exception as exc:
            errors.append(f'{meta["label"]}: {type(exc).__name__}: {exc}')
            print(f'Search failed for {meta["label"]}: {exc}',file=sys.stderr)
    if not found and errors:
        print("All searches failed; refusing to publish a misleading empty report.",file=sys.stderr)
        sys.exit(1)
    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    warning="; ".join(errors[:3]) if errors else None
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(render(list(found.values()),timestamp,warning),encoding="utf-8")
    print(f"Published report with {len(found)} unique candidates; {len(errors)} query errors.")

if __name__=="__main__":
    main()
