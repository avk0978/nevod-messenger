"""The phone's language sent with cell_register (app 1.3+) — stored for the administrator
(write in it if Nevod has it, else in English) and to see which languages to add first."""

import aiosqlite

from node.node import cell_lang, CELL_LANGS
from node.storage import Storage


class TestCellLangValue:
    def test_app_languages_kept(self):
        for lang in CELL_LANGS:
            assert cell_lang(lang) == lang
        assert cell_lang(" TR ") == "tr"

    def test_other_real_languages_kept(self):
        # outside the app's 8 on purpose — shows which languages to add first
        for lang in ("pl", "hu", "zh", "fil"):
            assert cell_lang(lang) == lang

    def test_not_a_language_code_is_unknown(self):
        for bad in (None, "", "  ", "en-US", "<script>", 5, "russian", "x", "toolong"):
            assert cell_lang(bad) == ""


class TestCellLangStorage:
    async def test_stored_and_listed(self, storage):
        await storage.register_cell("c1", b"s" * 32, b"e" * 32, display_name="Ali", lang="tr")
        assert (await storage.get_cell("c1")).lang == "tr"
        assert [c.lang for c in await storage.list_cells()] == ["tr"]

    async def test_reconnect_without_lang_keeps_it(self, storage):
        # an older app version (or a name-only re-register) sends no language
        await storage.register_cell("c1", b"s" * 32, b"e" * 32, lang="tr")
        await storage.register_cell("c1", b"s" * 32, b"e" * 32)
        assert (await storage.get_cell("c1")).lang == "tr"

    async def test_language_change_updates(self, storage):
        await storage.register_cell("c1", b"s" * 32, b"e" * 32, lang="tr")
        await storage.register_cell("c1", b"s" * 32, b"e" * 32, lang="de")
        assert (await storage.get_cell("c1")).lang == "de"

    async def test_language_outside_the_app_stored(self, storage):
        await storage.register_cell("c1", b"s" * 32, b"e" * 32, lang="hu")
        assert (await storage.get_cell("c1")).lang == "hu"

    async def test_unknown_for_old_app(self, storage):
        await storage.register_cell("c1", b"s" * 32, b"e" * 32)
        assert (await storage.get_cell("c1")).lang == ""

    async def test_appeal_threads_carry_lang(self, storage):
        await storage.register_cell("c1", b"s" * 32, b"e" * 32, display_name="Ali", lang="tr")
        await storage.add_appeal("c1", "n1", "Ali", "", "in", "Merhaba")
        threads = await storage.list_appeal_threads()
        assert threads[0]["lang"] == "tr"


async def test_existing_database_gets_the_column(tmp_path):
    """A node database from before 1.3 (cells without lang) opens and keeps its cells."""
    path = str(tmp_path / "old.db")
    async with aiosqlite.connect(path) as db:
        await db.execute("CREATE TABLE cells (cell_id TEXT PRIMARY KEY, signing_pubkey BLOB NOT NULL,"
                         " enc_pubkey BLOB NOT NULL, registered_at INTEGER NOT NULL,"
                         " is_home INTEGER NOT NULL DEFAULT 1)")
        await db.execute("INSERT INTO cells VALUES ('old', x'00', x'00', 1, 1)")
        await db.commit()
    st = Storage(path)
    await st.open()
    try:
        cell = await st.get_cell("old")
        assert cell is not None and cell.lang == "" and cell.display_name == ""
        await st.register_cell("old", b"s" * 32, b"e" * 32, lang="uk")
        assert (await st.get_cell("old")).lang == "uk"
    finally:
        await st.close()
