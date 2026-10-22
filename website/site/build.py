"""Static site generator for nevod.network.

Output: website/public/ — deployed as-is into the web root (/root/Nevod/pwa on node1's
shared nginx; that folder is bind-mounted whole, no restart needed). The deploy must NOT
delete what isn't ours to generate there: nodes.json, official.json, manifest.json.

Languages: every page must exist in all 8 site languages (en, ru, uk, de, tr, es, it, fr —
see memory "feedback_everything_in_8_languages"). Content lives in content_<lang>.py; a
language is built only once its content module exists. The root / picks the visitor's
browser language (fallback: English).

Usage:  python website/site/build.py
"""
import html
import json
import re
import importlib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "public"
sys.path.insert(0, str(HERE))

ALL_LANGS = ["uk", "en", "ru", "de", "tr", "es", "it", "fr"]
LANG_NAMES = {"uk": "Українська", "en": "English", "ru": "Русский", "de": "Deutsch",
              "tr": "Türkçe", "es": "Español", "it": "Italiano", "fr": "Français"}

# Russian is not advertised (user, 2026-10-17): its pages live under /xx/ instead of /ru/, it is
# left out of the language menus and hreflang alternates, its own menu shows an empty label, and
# the root page sends a visitor there only when Russian is the browser's PRIMARY language.
SLUG = {"ru": "xx"}
HIDDEN_LANGS = {"ru"}

MENU_LABEL = {"uk": "Меню", "en": "Menu", "ru": "Меню", "de": "Menü", "tr": "Menü", "es": "Menú",
              "it": "Menu", "fr": "Menu"}

# The author's Nevod contact card (Profile -> "Share my card" in the app): cell_id@node|node_id|enc_pub.
# Public data only (id + public keys). The QR is pre-rendered into author_card_qr.svg (segno, error level M)
# so the build stays dependency-free — regenerate both together if the card ever changes.
AUTHOR_CARD = ("b3d0a5c7c20111fc57bd0508c07dcbcbbb072ff057a788b197b22b2695201bbf@node1.nevod.network/nevod-ws"
               "|0c69eee506cc5f897b65f231df37f0214130e9c3f461393983a6794a99f4f2cd"
               "|82de270ba1af87929d136a294c2c72349e53a870de845a814e78281447f5fd4c")
AUTHOR_CARD_QR = (HERE / "author_card_qr.svg").read_text(encoding="utf-8")
# (heading, hint, copy button, copied) — the hint uses the app's own labels for "Contacts" / "Add Contact".
CARD_TEXT = {
    "en": ("Write to me in Nevod", "Scan the QR code in Nevod (Contacts → Add Contact) or copy the card and paste it there.", "Copy card", "Copied"),
    "ru": ("Написать мне в Nevod", "Отсканируйте QR-код в Nevod (Контакты → Добавить контакт) или скопируйте карточку и вставьте её туда.", "Скопировать карточку", "Скопировано"),
    "uk": ("Написати мені в Nevod", "Відскануйте QR-код у Nevod (Контакти → Додати контакт) або скопіюйте картку й вставте її туди.", "Скопіювати картку", "Скопійовано"),
    "de": ("Schreib mir in Nevod", "Scanne den QR-Code in Nevod (Kontakte → Kontakt hinzufügen) oder kopiere die Karte und füge sie dort ein.", "Karte kopieren", "Kopiert"),
    "tr": ("Bana Nevod'dan yazın", "QR kodunu Nevod'da tarayın (Kişiler → Kişi ekle) ya da kartı kopyalayıp oraya yapıştırın.", "Kartı kopyala", "Kopyalandı"),
    "es": ("Escríbeme en Nevod", "Escanea el código QR en Nevod (Contactos → Añadir contacto) o copia la tarjeta y pégala allí.", "Copiar tarjeta", "Copiada"),
    "it": ("Scrivimi su Nevod", "Scansiona il codice QR in Nevod (Contatti → Aggiungi contatto) oppure copia la scheda e incollala lì.", "Copia scheda", "Copiata"),
    "fr": ("M'écrire sur Nevod", "Scannez le QR code dans Nevod (Contacts → Ajouter un contact) ou copiez la carte et collez-la là.", "Copier la carte", "Copiée"),
}

PAGES = ["index", "manifesto", "compare", "security", "cities", "download", "node", "about",
         "support", "privacy", "terms"]

CSS = """
:root { --ink:#14213D; --paper:#F7F6F1; --card:#FFFFFF; --line:#DCDFE6; --muted:#4A5568;
        --accent:#F2C230; --accent-ink:#8A6A00; --dark2:#1E2F55; --soft:#C9D3E6; }
* { box-sizing:border-box; }
html { -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--paper); color:var(--ink); font:17px/1.6 'IBM Plex Sans', Arial, sans-serif; }
a { color:#1F4E9E; }
h1,h2,h3 { font-family:'Rubik', Arial, sans-serif; line-height:1.15; margin:0 0 .5em;
  overflow-wrap:break-word; hyphens:auto; }
main, .hero { overflow-wrap:break-word; }
h1 { font-size:clamp(28px,5vw,56px); } h2 { font-size:clamp(24px,3.2vw,34px); margin-top:1.4em; } h3 { font-size:20px; }
[id] { scroll-margin-top:76px; }  /* sticky header must not cover an anchor target */
main.article h2 { margin-top:1.6em; } main.article h1 { font-size:clamp(26px,4vw,44px); }
main.article hr { border:0; border-top:1px solid var(--line); margin:28px 0; }
main.article code { font-size:.9em; background:var(--card); border:1px solid var(--line); border-radius:4px; padding:0 4px; }
main.article ol li, main.article ul li { margin-bottom:.35em; overflow-wrap:anywhere; }
.pub { margin:16px 0; } .pub h3 a { text-decoration:none; } .pub-date { font-size:14px; color:var(--muted); }
.pub-back { font-size:15px; }
p, ul, ol, table { margin:0 0 1em; }
.wrap { max-width:1080px; margin:0 auto; padding:0 16px; }
header.top { background:var(--ink); color:var(--paper); position:sticky; top:0; z-index:10; }
header.top .wrap { display:flex; align-items:center; gap:16px; min-height:60px; }
header.top a { color:var(--paper); text-decoration:none; }
.brand { font-family:'Rubik', Arial, sans-serif; font-weight:700; font-size:20px; margin-right:auto; }
.brand span { color:var(--accent); }
nav.main { display:flex; gap:14px; font-size:15px; }
nav.main a { opacity:.85; white-space:nowrap; } nav.main a[aria-current] { opacity:1; border-bottom:2px solid var(--accent); }
details.menu { display:none; order:3; }
details.menu summary { list-style:none; cursor:pointer; width:44px; height:44px; margin-right:-10px;
  display:flex; align-items:center; justify-content:center; }
details.menu summary::-webkit-details-marker { display:none; }
.burger, .burger::before, .burger::after { display:block; width:22px; height:2px; background:var(--paper);
  border-radius:2px; position:relative; transition:transform .2s, background .2s; }
.burger::before, .burger::after { content:""; position:absolute; left:0; }
.burger::before { top:-7px; } .burger::after { top:7px; }
details.menu[open] .burger { background:transparent; }
details.menu[open] .burger::before { transform:translateY(7px) rotate(45deg); }
details.menu[open] .burger::after { transform:translateY(-7px) rotate(-45deg); }
details.menu nav { position:absolute; left:0; right:0; top:100%; background:var(--ink);
  border-top:1px solid var(--dark2); box-shadow:0 12px 24px rgba(0,0,0,.25); padding:6px 0 12px; }
details.menu nav a { display:block; padding:12px 16px; font-size:17px; opacity:.9; }
details.menu nav a[aria-current] { opacity:1; color:var(--accent); }
details.lang { position:relative; font-size:15px; }
details.lang summary { list-style:none; cursor:pointer; border:1px solid var(--accent); color:var(--accent);
  padding:3px 12px; border-radius:999px; }
details.lang summary::-webkit-details-marker { display:none; }
details.lang summary:empty { min-width:6em; height:calc(1.6em + 8px); box-sizing:border-box; }
details.lang ul { position:absolute; right:0; top:34px; background:var(--card); color:var(--ink); list-style:none;
  padding:8px 0; margin:0; border-radius:10px; box-shadow:0 8px 24px rgba(0,0,0,.2); min-width:160px; }
details.lang li a { color:var(--ink); display:block; padding:6px 16px; }
@media (max-width:960px) {
  nav.main { display:none; }
  details.menu { display:block; }
  header.top .wrap { min-height:56px; gap:12px; }
  details.lang li a { padding:10px 16px; }
}
.hero { background:var(--ink); color:var(--paper); padding:56px 0 64px; }
.hero p.lead { font-size:clamp(18px,2.2vw,22px); color:var(--soft); max-width:760px; }
.eyebrow { font-size:14px; letter-spacing:3px; text-transform:uppercase; color:var(--accent); margin-bottom:12px; }
.btns { display:flex; gap:12px; flex-wrap:wrap; margin-top:24px; }
.btn { display:inline-block; padding:12px 22px; border-radius:10px; text-decoration:none; font-weight:600; }
.btn.primary { background:var(--accent); color:var(--ink); } .btn.ghost { border:1px solid var(--soft); color:var(--paper); }
main { padding:40px 0 56px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; margin:16px 0 8px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:20px; }
.card h3 { margin-bottom:6px; } .card p { margin:0; color:var(--muted); }
.status td:first-child { font-weight:600; }
.tbl { overflow-x:auto; }
table { border-collapse:collapse; width:100%; background:var(--card); border:1px solid var(--line); border-radius:12px; }
th, td { text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
th { background:var(--ink); color:var(--paper); font-weight:600; }
.note { background:#FBF3D6; border-left:4px solid var(--accent); padding:14px 16px; border-radius:8px; }
.legal h2 { font-size:22px; }
.ncard { display:flex; gap:20px; align-items:flex-start; background:var(--card); border:1px solid var(--line);
  border-radius:14px; padding:20px; margin:8px 0 16px; }
.ncard-qr { flex:0 0 220px; } .ncard-qr svg { display:block; width:100%; height:auto; }
.ncard-body { min-width:0; } .ncard-body h3 { margin-bottom:6px; } .ncard-body p { color:var(--muted); }
.ncard code { display:block; font-size:12px; line-height:1.45; word-break:break-all; background:var(--paper);
  border:1px solid var(--line); border-radius:8px; padding:8px 10px; margin:0 0 12px; user-select:all; }
.ncard .btn { border:0; cursor:pointer; font:inherit; font-weight:600; }
@media (max-width:640px) { .ncard { flex-direction:column; align-items:stretch; } .ncard-qr { flex-basis:auto; width:220px; margin:0 auto; } }
footer.site { background:var(--ink); color:var(--soft); font-size:14px; padding:28px 0; }
footer.site a { color:var(--soft); }
footer.site .wrap { display:flex; flex-wrap:wrap; gap:8px 24px; justify-content:space-between; }
@media (max-width:640px) {
  body { font-size:16px; }
  .hero { padding:36px 0 44px; }
  main { padding:28px 0 40px; }
  .btns .btn { flex:1 1 auto; text-align:center; }
  .card { padding:16px; }
  /* Wide tables (4+ columns) become one card per row: the first cell is the row title,
     every other cell is prefixed with its column header (data-label, added by stack_tables). */
  table.stack, table.stack tbody, table.stack tr, table.stack td { display:block; width:auto !important; }
  table.stack { background:none; border:0; }
  table.stack tr:first-child { display:none; }
  table.stack tr { background:var(--card); border:1px solid var(--line); border-radius:12px; margin-bottom:12px; overflow:hidden; }
  table.stack td { border-bottom:1px solid var(--line); padding:8px 14px; }
  table.stack td:last-child { border-bottom:0; }
  table.stack td:first-child { background:var(--ink); color:var(--paper); font-weight:600; }
  table.stack td:not(:first-child)::before { content:attr(data-label); display:block; font-size:13px;
    font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }
  footer.site .wrap { flex-direction:column; }
}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rubik:wght@500..700'
         '&family=IBM+Plex+Sans:wght@400;600&display=swap">')


def url(lang, page):
    slug = SLUG.get(lang, lang)
    return f"/{slug}/" if page == "index" else f"/{slug}/{page}/"


def _label_row(row, labels):
    cells = iter(labels)
    return re.sub(r"<td(?=[ >])", lambda m: f'<td data-label="{html.escape(re.sub(r"<[^>]+>", "", next(cells, "")), quote=True)}"', row)


def stack_tables(body):
    """Mark tables with 4+ columns for the mobile card layout and give each cell its column header."""
    def one(m):
        table = m.group(0)
        rows = re.findall(r"<tr>.*?</tr>", table, re.S)
        if not rows:
            return table
        labels = re.findall(r"<th[^>]*>(.*?)</th>", rows[0], re.S)
        if len(labels) < 4:
            return table
        table = table.replace("<table", '<table class="stack"', 1) if "<table>" in table[:8] else table
        for r in rows[1:]:
            table = table.replace(r, _label_row(r, labels), 1)
        return table
    return re.sub(r"<table[^>]*>.*?</table>", one, body, flags=re.S)


# ── Publications ──────────────────────────────────────────────────────────────
# Articles live as Markdown in website/content/articles/<slug>.<lang>.md (all 8 languages —
# see feedback_everything_in_8_languages). Each becomes /<lang>/publications/<slug>/, and
# /<lang>/publications/ lists them. First "# " line = title; the first paragraph after the
# abstract heading = listing summary / meta description.
ARTICLES_DIR = HERE.parent / "content" / "articles"
ARTICLES = [("low-load-networks", "2026-09-30")]   # (slug, date), newest first

# (nav label, page title, page description, intro, "read" link, date label)
PUB_TEXT = {
    "ru": ("Публикации", "Публикации", "Статьи и исследования проекта Nevod.",
           "Статьи и исследования, выросшие из работы над Nevod.", "Читать статью →", "Опубликовано"),
    "uk": ("Публікації", "Публікації", "Статті та дослідження проєкту Nevod.",
           "Статті та дослідження, що виросли з роботи над Nevod.", "Читати статтю →", "Опубліковано"),
    "en": ("Publications", "Publications", "Articles and research from the Nevod project.",
           "Articles and research that grew out of the work on Nevod.", "Read the article →", "Published"),
    "de": ("Publikationen", "Publikationen", "Artikel und Forschung aus dem Projekt Nevod.",
           "Artikel und Forschung, die aus der Arbeit an Nevod entstanden sind.", "Artikel lesen →", "Veröffentlicht"),
    "tr": ("Yayınlar", "Yayınlar", "Nevod projesinden makaleler ve araştırmalar.",
           "Nevod üzerindeki çalışmalardan doğan makaleler ve araştırmalar.", "Makaleyi oku →", "Yayın tarihi"),
    "es": ("Publicaciones", "Publicaciones", "Artículos e investigación del proyecto Nevod.",
           "Artículos e investigación surgidos del trabajo en Nevod.", "Leer el artículo →", "Publicado"),
    "it": ("Pubblicazioni", "Pubblicazioni", "Articoli e ricerche del progetto Nevod.",
           "Articoli e ricerche nati dal lavoro su Nevod.", "Leggi l'articolo →", "Pubblicato"),
    "fr": ("Publications", "Publications", "Articles et recherches du projet Nevod.",
           "Articles et recherches issus du travail sur Nevod.", "Lire l'article →", "Publié le"),
}


def _md_inline(s: str) -> str:
    s = html.escape(s, quote=False)
    keep = []

    def stash(v):
        keep.append(v)
        return f"\x00{len(keep) - 1}\x00"
    s = re.sub(r"`([^`]+)`", lambda m: stash(f"<code>{m.group(1)}</code>"), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: stash(f'<a href="{m.group(2)}">{m.group(1)}</a>'), s)
    s = re.sub(r"(https?://[^\s<]+[^\s<.,;:)])",
               lambda m: stash(f'<a href="{m.group(1)}">{m.group(1)}</a>'), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], s)


def md_to_html(text: str) -> str:
    """Minimal Markdown for our articles: headings, paragraphs, hr, pipe tables,
    ordered/unordered lists with indented continuation lines, inline bold/italic/code/links."""
    out, para, lst = [], [], None   # lst = [tag, items(list of str), start]
    lines = text.splitlines()

    def flush_para():
        if para:
            out.append("<p>" + _md_inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            tag, items, start = lst
            attr = f' start="{start}"' if tag == "ol" and start != 1 else ""
            out.append(f"<{tag}{attr}>" + "".join(f"<li>{_md_inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        st = ln.strip()
        m_ol = re.match(r"^(\d+)\.\s+(.*)$", st) if not ln.startswith(" ") else None
        m_ul = re.match(r"^[-*]\s+(.*)$", st) if not ln.startswith(" ") else None
        if not st:
            flush_para(); flush_list()
        elif lst and ln.startswith("  ") and not (m_ol or m_ul):
            lst[1][-1] += " " + st
        elif st.startswith("#"):
            flush_para(); flush_list()
            level = len(st) - len(st.lstrip("#"))
            out.append(f"<h{level}>{_md_inline(st[level:].strip())}</h{level}>")
        elif st == "---":
            flush_para(); flush_list()
            out.append("<hr>")
        elif st.startswith("|"):
            flush_para(); flush_list()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            head = "<tr>" + "".join(f"<th>{_md_inline(c)}</th>" for c in rows[0]) + "</tr>"
            body = "".join("<tr>" + "".join(f"<td>{_md_inline(c)}</td>" for c in r) + "</tr>"
                           for r in rows[1:])
            out.append(f'<div class="tbl"><table>{head}{body}</table></div>')
            continue
        elif m_ol or m_ul:
            flush_para()
            tag = "ol" if m_ol else "ul"
            item = (m_ol.group(2) if m_ol else m_ul.group(1))
            if not lst or lst[0] != tag:
                flush_list()
                lst = [tag, [], int(m_ol.group(1)) if m_ol else 1]
            lst[1].append(item)
        else:
            flush_list()
            para.append(st)
        i += 1
    flush_para(); flush_list()
    return "\n".join(out)


# The reference list is shared by all translations (<slug>.refs.md) — only these few words
# (and the GOST title: translation first, Russian original in parentheses) inside it are localized, so the 39 entries can never drift apart between languages.
REF_WORDS = {
    "ru": ("обзор", "см. также", "ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения"),
    "uk": ("огляд", "див. також", "ГОСТ 22348-86. Єдина автоматизована мережа зв'язку. Терміни та визначення (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
    "en": ("overview", "see also", "GOST 22348-86. Unified automated communication network. Terms and definitions (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
    "de": ("Überblick", "siehe auch", "GOST 22348-86. Einheitliches automatisiertes Kommunikationsnetz. Begriffe und Definitionen (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
    "tr": ("genel bakış", "ayrıca bkz.", "GOST 22348-86. Birleşik otomatik iletişim ağı. Terimler ve tanımlar (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
    "es": ("resumen", "véase también", "GOST 22348-86. Red de comunicaciones automatizada unificada. Términos y definiciones (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
    "it": ("panoramica", "vedi anche", "GOST 22348-86. Rete di comunicazione automatizzata unificata. Termini e definizioni (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
    "fr": ("aperçu", "voir aussi", "GOST 22348-86. Réseau de communication automatisé unifié. Termes et définitions (ГОСТ 22348-86. Сеть связи автоматизированная единая. Термины и определения)"),
}


def article(lang, slug):
    """(title, summary, body_html) for one article in one language."""
    text = (ARTICLES_DIR / f"{slug}.{lang}.md").read_text(encoding="utf-8")
    refs_file = ARTICLES_DIR / f"{slug}.refs.md"
    if "{{REFS}}" in text and refs_file.exists():
        overview, see_also, gost_tr = REF_WORDS[lang]
        refs = (refs_file.read_text(encoding="utf-8").replace("{overview}", overview)
                .replace("{see_also}", see_also).replace("{gost_tr}", gost_tr))
        text = text.replace("{{REFS}}", refs)
    title = next(l[2:].strip() for l in text.splitlines() if l.startswith("# "))
    # Summary = first paragraph after the first "## " heading (the abstract).
    after = text.split("\n## ", 1)[1].split("\n", 1)[1]
    summary = " ".join(after.strip().split("\n\n", 1)[0].split())
    summary = re.sub(r"[*`]", "", summary)   # plain text for the listing and <meta>
    return title, summary, md_to_html(text)


def publication_page(lang, page):
    """(title, desc, body) for /publications/ and /publications/<slug>/."""
    nav_label, ptitle, pdesc, intro, read, date_label = PUB_TEXT[lang]
    if page == "publications":
        items = []
        for slug, date in ARTICLES:
            if not (ARTICLES_DIR / f"{slug}.{lang}.md").exists():
                continue
            title, summary, _ = article(lang, slug)
            items.append(f'<div class="card pub"><h3><a href="{url(lang, "publications/" + slug)}">'
                         f'{html.escape(title)}</a></h3><p class="pub-date">{date_label}: {date}</p>'
                         f'<p>{html.escape(summary)}</p><p><a href="{url(lang, "publications/" + slug)}">'
                         f'{html.escape(read)}</a></p></div>')
        body = (f'<main><div class="wrap"><h1>{html.escape(ptitle)}</h1><p>{html.escape(intro)}</p>'
                + "".join(items) + "</div></main>")
        return ptitle, pdesc, body
    slug = page.split("/", 1)[1]
    title, summary, body = article(lang, slug)
    back = f'<p class="pub-back"><a href="{url(lang, "publications")}">← {html.escape(nav_label)}</a></p>'
    return title, summary, f'<main class="article"><div class="wrap">{back}{body}{back}</div></main>'


def author_card(lang):
    head, hint, copy, copied = CARD_TEXT[lang]
    return f"""<div class="ncard">
<div class="ncard-qr">{AUTHOR_CARD_QR}</div>
<div class="ncard-body">
<h3>{html.escape(head)}</h3>
<p>{html.escape(hint)}</p>
<code id="ncard">{html.escape(AUTHOR_CARD)}</code>
<button type="button" class="btn primary" data-done="{html.escape(copied, quote=True)}"
 onclick="var b=this;navigator.clipboard.writeText(document.getElementById('ncard').textContent).then(function(){{b.textContent=b.dataset.done}})">{html.escape(copy)}</button>
</div>
</div>"""


def render(lang, page, c, langs):
    t = c.T
    # ZKI manifesto sits right after Home: it's the foundation of the project (user, 2026-09-28).
    nav_pages = ["index", "manifesto", "compare", "security", "cities", "download", "publications", "about"]
    nav = "".join(
        f'<a href="{url(lang, p)}"'
        f'{" aria-current=\"page\"" if p == page or (p == "publications" and page.startswith("publications/")) else ""}>'
        f'{html.escape(t["nav"].get(p) or PUB_TEXT[lang][0])}</a>'
        for p in nav_pages)
    switch = "".join(f'<li><a href="{url(l, page)}" hreflang="{l}" lang="{l}">{LANG_NAMES[l]}</a></li>'
                     for l in langs if l not in HIDDEN_LANGS)
    alternates = "".join(f'<link rel="alternate" hreflang="{l}" href="https://nevod.network{url(l, page)}">'
                         for l in langs if l not in HIDDEN_LANGS or l == lang)
    title, desc, body = (publication_page(lang, page) if page.startswith("publications")
                         else c.PAGES[page])
    body = stack_tables(body)
    if page == "about":
        body = body.replace("<!--BIO-->", "<!--BIO-->\n" + author_card(lang), 1)
    full_title = "Nevod" if page == "index" else f"{title} — Nevod"
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://nevod.network{url(lang, page)}">
{alternates}
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{url(lang, 'index')}">Nevod<span>.</span></a>
<nav class="main">{nav}</nav>
<details class="menu"><summary aria-label="{MENU_LABEL[lang]}"><span class="burger"></span></summary><nav>{nav}</nav></details>
<details class="lang"><summary>{"" if lang in HIDDEN_LANGS else LANG_NAMES[lang]}</summary><ul>{switch}</ul></details>
</div></header>
{body}
<footer class="site"><div class="wrap">
<div>{t["footer_owner"]}</div>
<div><a href="{url(lang, 'support')}">{t["nav_support"]}</a> · <a href="{url(lang, 'privacy')}">{t["nav_privacy"]}</a> · <a href="{url(lang, 'terms')}">{t["nav_terms"]}</a> · <a href="{url(lang, 'node')}">{t["nav_node"]}</a> · <a href="https://github.com/avk0978/nevod-messenger">{t["nav_source"]}</a></div>
</div></footer>
</body>
</html>
"""


ROOT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nevod</title>
<meta name="description" content="Nevod — an end-to-end encrypted messenger on a distributed network of nodes.">
<script>
  (function () {
    var have = %s, slug = %s, primaryOnly = %s;
    var want = (navigator.languages || [navigator.language || "en"]);
    for (var i = 0; i < want.length; i++) {
      var l = String(want[i]).toLowerCase().slice(0, 2);
      if (primaryOnly.indexOf(l) >= 0 && i > 0) continue;
      if (have.indexOf(l) >= 0) { location.replace("/" + (slug[l] || l) + "/"); return; }
    }
    location.replace("/en/");
  })();
</script>
<style>body{font:18px/1.6 Arial,sans-serif;background:#14213D;color:#F7F6F1;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0}a{color:#F2C230;margin:0 10px}</style>
</head>
<body><p>Nevod — %s</p></body>
</html>
"""


def main():
    langs = [l for l in ALL_LANGS if (HERE / f"content_{l}.py").exists()]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for lang in langs:
        c = importlib.import_module(f"content_{lang}")
        pages = PAGES + ["publications"] + [f"publications/{slug}" for slug, _ in ARTICLES
                                            if (ARTICLES_DIR / f"{slug}.{lang}.md").exists()]
        for page in pages:
            d = OUT / SLUG.get(lang, lang) if page == "index" else OUT / SLUG.get(lang, lang) / page
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(render(lang, page, c, langs), encoding="utf-8", newline="\n")
    links = " ".join(f'<a href="{url(l, "index")}">{LANG_NAMES[l]}</a>' for l in langs if l not in HIDDEN_LANGS)
    (OUT / "index.html").write_text(ROOT % (json.dumps(langs), json.dumps(SLUG), json.dumps(sorted(HIDDEN_LANGS)), links), encoding="utf-8", newline="\n")
    # The manifesto keeps its original standalone page, unchanged (authorship line included —
    # see memory feedback-manifesto-authorship-required).
    (OUT / "manifesto").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE.parent / "index.html", OUT / "manifesto" / "index.html")
    # Invite links (https://nevod.network/join/#t=…) — one page for all languages, see join_page.py.
    import join_page
    (OUT / "join").mkdir(parents=True, exist_ok=True)
    (OUT / "join" / "index.html").write_text(join_page.render(), encoding="utf-8", newline="\n")
    print("built:", ", ".join(langs), "->", OUT)


if __name__ == "__main__":
    main()
