"""Admin panel: buffered mail counted apart from service packets (acks, reactions, signals)."""

import msgpack

from node.storage import buffer_kind


def packed(ptype: str) -> bytes:
    return msgpack.packb({"type": ptype, "id": "x", "payload": b""}, use_bin_type=True)


def test_kinds():
    assert buffer_kind(packed("msg")) == "msg"
    assert buffer_kind(packed("msg_chunk")) == "msg"
    for t in ("ack", "react", "msg_silent", "vcall_offer"):
        assert buffer_kind(packed(t)) == "service"
    assert buffer_kind(b"\xff not msgpack") == "msg"


async def test_counts_apart(storage):
    await storage.buffer_message("m1", "anna", "n", packed("msg"))
    await storage.buffer_message("c1", "anna", "n", packed("msg_chunk"))
    for i in range(3):
        await storage.buffer_message(f"a{i}", "anna", "n", packed("ack"))
    await storage.buffer_message("r1", "bob", "n", packed("react"))
    assert await storage.buffer_counts() == {"anna": (2, 3), "bob": (0, 1)}
    assert await storage.buffer_count() == {"anna": 5, "bob": 1}


async def test_rows_from_before_the_column_get_classified(tmp_path):
    from node.storage import Storage
    path = str(tmp_path / "b.db")
    st = Storage(path)
    await st.open()
    await st.buffer_message("a1", "anna", "n", packed("ack"))
    await st.buffer_message("m1", "anna", "n", packed("msg"))
    await st._db.execute("UPDATE message_buffer SET kind=''")   # as if buffered by an older node
    await st._db.commit()
    await st.close()
    st = Storage(path)
    await st.open()
    try:
        assert await st.buffer_counts() == {"anna": (1, 1)}
    finally:
        await st.close()
