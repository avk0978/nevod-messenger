"""The admin panel in 8 languages (node/admin_i18n.py): every Russian phrase of the templates
and of the server messages the panel shows has a full row, pages in other languages carry no
Russian left over, and the language comes from the cookie / browser.
"""

import ast
import base64
import pathlib
import re

import pytest
from aiohttp.test_utils import TestClient, TestServer

import node.admin as admin
from node.admin import AdminServer
from node.admin_i18n import CATALOG, COOKIE, LANG_NAMES, LANGS, SEGMENT, localize, pick_lang

NODE_DIR = pathlib.Path(admin.__file__).parent
CYRILLIC = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ]")
RUSSIAN_ONLY = re.compile(r"[ЫыЭэЪъЁё]")   # letters Ukrainian doesn't have
UNSAFE = set("'\"`<>&\\")                    # would break the HTML/JS the text lands in

PASSWORD = "test-password"


def _segments(text):
    return {m.group().strip() for m in SEGMENT.finditer(text)} - {""}


def _template_phrases():
    phrases = {label for _, label in admin._NAV}
    for name in dir(admin):
        if re.match(r"_(BODY|SCRIPT)_|_HEADER_HTML$|_QR_HTML$|_SHARED_JS$", name):
            phrases |= _segments(getattr(admin, name))
    return phrases


def _constants(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.value


def _server_phrases():
    """Russian texts the server sends to the panel: diagnostics, AIBotError, error replies."""
    phrases = set()
    tree = ast.parse((NODE_DIR / "diagnostics.py").read_text(encoding="utf-8"))
    for fn in tree.body:
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for stmt in fn.body[1:] if ast.get_docstring(fn) else fn.body:
                for s in _constants(stmt):
                    phrases |= _segments(s)
    tree = ast.parse((NODE_DIR / "ai_bots.py").read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "AIBotError":
            for s in _constants(n):
                phrases |= _segments(s)
    tree = ast.parse((NODE_DIR / "admin.py").read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "error":
                    for s in _constants(v):
                        phrases |= _segments(s)
    return phrases


class TestCatalog:
    def test_every_template_phrase_is_translated(self):
        missing = sorted(_template_phrases() - CATALOG.keys())
        assert not missing, missing

    def test_every_server_phrase_is_translated(self):
        missing = sorted(_server_phrases() - CATALOG.keys())
        assert not missing, missing

    def test_rows_are_complete_and_safe(self):
        for src, row in CATALOG.items():
            assert len(row) == len(LANGS), src
            for lang, text in zip(LANGS, row):
                if text is None:
                    continue
                for ch in UNSAFE:
                    assert text.count(ch) <= src.count(ch), (src, lang, ch)
                if lang not in ("uk", "ru"):
                    assert not CYRILLIC.search(text.replace("Толмач", "")), (src, lang)
                # Russian source phrases are left as-is only where the word really is the same
                if lang == "uk":
                    assert not RUSSIAN_ONLY.search(text), (src, text)

    def test_cookie_name_matches_the_page_script(self):
        assert f"document.cookie='{COOKIE}=" in admin._SHARED_JS


class TestPickLang:
    def test_cookie_wins(self):
        assert pick_lang("de", "fr-FR,fr;q=0.9") == "de"

    def test_browser_language_then_english(self):
        assert pick_lang(None, "uk-UA,uk;q=0.9,en;q=0.8") == "uk"
        assert pick_lang("xx", "pl-PL,es;q=0.5") == "es"
        assert pick_lang(None, "pl-PL") == "en"
        assert pick_lang(None, None) == "en"


class TestLocalize:
    def test_translation_is_never_translated_again(self):
        # "Видалити" (uk for "Удалить") must not be touched by any other Russian phrase.
        assert localize("Удалить ячейку", "uk") == "Видалити комірку"
        assert localize("Удалить", "uk") == "Видалити"

    def test_dynamic_parts_survive(self):
        assert localize("APNS_PRIVATE_KEY указывает на несуществующий файл: /x.p8", "en") == \
            "APNS_PRIVATE_KEY points to a file that doesn’t exist: /x.p8"

    def test_russian_is_the_source(self):
        assert localize("Сохранить", "ru") == "Сохранить"
        assert localize("no pending request", "ru") == "нет ожидающей заявки"


def _auth():
    return {"Authorization": "Basic " + base64.b64encode(f":{PASSWORD}".encode()).decode()}


PAGES = ("/nevod-admin/", "/nevod-admin/settings", "/nevod-admin/join-requests",
         "/nevod-admin/appeals", "/nevod-admin/invites", "/nevod-admin/nodes",
         "/nevod-admin/published", "/nevod-admin/ai-bots", "/nevod-admin/security",
         "/nevod-admin/diagnostics")


@pytest.mark.parametrize("lang", LANGS)
async def test_every_page_in_every_language(genesis_node, lang):
    client = TestClient(TestServer(AdminServer(genesis_node, password=PASSWORD)._make_app()))
    await client.start_server()
    try:
        for path in PAGES:
            r = await client.get(path, headers=_auth(), cookies={COOKIE: lang})
            assert r.status == 200, path
            body = await r.text()
            assert f'<html lang="{lang}">' in body
            assert f'<option value="{lang}" selected>' in body
            if lang in ("uk", "ru"):
                assert CYRILLIC.search(body)
                if lang == "uk":
                    assert not RUSSIAN_ONLY.search(body), (path, RUSSIAN_ONLY.findall(body)[:5])
            else:
                left = sorted(set(m.group() for m in re.finditer(r"[^\s<>'\"]*[А-Яа-яЁё][^\s<>'\"]*", body)) - {"Толмач", *LANG_NAMES.values()})
                assert not left, (path, left[:10])
    finally:
        await client.close()


async def test_error_replies_and_diagnostics_follow_the_language(genesis_node):
    client = TestClient(TestServer(AdminServer(genesis_node, password=PASSWORD)._make_app()))
    await client.start_server()
    try:
        r = await client.post("/nevod-admin/api/admins", headers={**_auth(), "Accept-Language": "de-DE"},
                              json={"username": "x", "password": "short"})
        assert (await r.json())["error"] == "das Passwort muss mindestens 8 Zeichen haben"

        r = await client.get("/nevod-admin/api/diagnostics", headers=_auth(), cookies={COOKIE: "fr"})
        checks = (await r.json())["checks"]
        assert checks and all(not CYRILLIC.search(c["label"] + c["detail"]) for c in checks)
    finally:
        await client.close()
