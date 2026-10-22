"""
Nevod WebUI — embedded HTTP test interface.

Starts a genesis node + N in-process cell clients, serves a chat UI at localhost.
Supports disconnect/reconnect per cell to test message buffering (TTL 72h).
"""

import asyncio
import logging
import time

from aiohttp import web

from node.node import Node
from node.identity import CellIdentity
from node.client import CellClient

log = logging.getLogger(__name__)

_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Nevod</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:monospace;background:#0d1117;color:#c9d1d9;height:100vh;display:flex;flex-direction:column}

header{background:#161b22;border-bottom:1px solid #30363d;padding:10px 20px;display:flex;align-items:center;gap:16px}
header h1{font-size:15px;color:#58a6ff;letter-spacing:1px}
#node-status{font-size:11px;color:#8b949e}

.cells-bar{background:#161b22;border-bottom:1px solid #30363d;padding:8px 20px;display:flex;gap:10px;flex-wrap:wrap}
.cell-pill{display:flex;align-items:center;gap:7px;background:#0d1117;border:1px solid #21262d;
  border-radius:20px;padding:4px 10px 4px 8px;font-size:12px;transition:border-color .2s}
.cell-pill.online{border-color:#238636}
.cell-pill.offline{border-color:#6e3030;opacity:.7}
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.online .dot{background:#3fb950}
.offline .dot{background:#f85149}
.cell-name{color:#c9d1d9}
.toggle-btn{background:none;border:none;cursor:pointer;font-family:monospace;font-size:11px;
  padding:1px 5px;border-radius:3px;color:#8b949e;transition:all .15s}
.online .toggle-btn:hover{background:#6e3030;color:#f85149}
.offline .toggle-btn{color:#3fb950}
.offline .toggle-btn:hover{background:#1a3a1a;color:#3fb950}

.compose{background:#161b22;border-bottom:1px solid #30363d;padding:10px 20px;display:flex;gap:8px;align-items:center}
.compose select,.compose input{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;
  padding:6px 10px;border-radius:4px;font-family:monospace;font-size:13px;outline:none}
.compose select:focus,.compose input:focus{border-color:#58a6ff}
.compose input{flex:1}
#send-btn{background:#238636;color:#fff;border:none;padding:6px 18px;border-radius:4px;
  cursor:pointer;font-family:monospace;font-size:13px}
#send-btn:hover:not(:disabled){background:#2ea043}
#send-btn:disabled{opacity:.4;cursor:default}
.arrow{color:#484f58;font-size:16px}
.err{color:#f85149;font-size:12px;margin-left:4px}

.feed{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:6px}
.empty{color:#484f58;font-size:13px;text-align:center;margin-top:60px}
.msg{background:#161b22;border:1px solid #21262d;border-radius:6px;padding:9px 14px;animation:fi .2s}
@keyframes fi{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.msg.buffered{border-left:3px solid #d29922}
.msg .meta{font-size:11px;color:#8b949e;margin-bottom:3px;display:flex;gap:6px;align-items:center}
.msg .from{color:#58a6ff}
.msg .to{color:#3fb950}
.msg .ts{color:#484f58}
.msg .badge{font-size:10px;background:#5a4000;color:#d29922;border-radius:3px;padding:1px 5px}
.msg .text{font-size:13px;color:#e6edf3;word-break:break-word}
</style>
</head>
<body>
<header>
  <h1>◈ NEVOD</h1>
  <span id="node-status">подключение...</span>
</header>

<div class="cells-bar" id="cells-bar"></div>

<div class="compose">
  <select id="from-sel"></select>
  <span class="arrow">→</span>
  <select id="to-sel"></select>
  <input id="msg-input" type="text" placeholder="сообщение..." autocomplete="off">
  <button id="send-btn" disabled>send</button>
  <span id="err" class="err"></span>
</div>

<div class="feed" id="feed">
  <div class="empty" id="empty">сообщений пока нет</div>
</div>

<script>
let cellsData = {};
let lastId = 0;

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

async function loadCells(){
  try{
    const r = await fetch('/api/cells');
    cellsData = await r.json();
    renderCells();
    document.getElementById('send-btn').disabled = false;
  }catch(e){
    document.getElementById('node-status').textContent = 'ошибка подключения';
  }
}

function renderCells(){
  const names = Object.keys(cellsData);
  const online = names.filter(n => cellsData[n].online);

  // node status
  document.getElementById('node-status').textContent =
    `${online.length}/${names.length} online`;

  // cells bar
  const bar = document.getElementById('cells-bar');
  bar.innerHTML = '';
  for(const name of names){
    const isOnline = cellsData[name].online;
    const pill = document.createElement('div');
    pill.className = 'cell-pill ' + (isOnline ? 'online' : 'offline');
    pill.innerHTML = `
      <span class="dot"></span>
      <span class="cell-name">${esc(name)}</span>
      <button class="toggle-btn" data-name="${esc(name)}">
        ${isOnline ? 'disconnect' : 'connect'}
      </button>`;
    bar.appendChild(pill);
  }
  bar.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.onclick = () => toggleCell(btn.dataset.name);
  });

  // selects
  const fromSel = document.getElementById('from-sel');
  const toSel   = document.getElementById('to-sel');
  const prevFrom = fromSel.value;
  const prevTo   = toSel.value;
  fromSel.innerHTML = online.map(n => `<option${n===prevFrom?' selected':''}>${n}</option>`).join('');
  toSel.innerHTML   = names.map(n  => `<option${n===prevTo?' selected':''}>${n}</option>`).join('');
}

async function toggleCell(name){
  await fetch(`/api/cells/${encodeURIComponent(name)}/toggle`, {method:'POST'});
  await refreshCells();
}

async function refreshCells(){
  try{
    const r = await fetch('/api/cells');
    cellsData = await r.json();
    renderCells();
  }catch(e){}
}

async function pollMessages(){
  try{
    const r = await fetch('/api/messages?since_id='+lastId);
    const msgs = await r.json();
    if(!msgs.length) return;
    const feed = document.getElementById('feed');
    const empty = document.getElementById('empty');
    if(empty) empty.remove();
    for(const m of msgs){
      const el = document.createElement('div');
      el.className = 'msg' + (m.buffered ? ' buffered' : '');
      const t = new Date(m.ts).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
      el.innerHTML = `
        <div class="meta">
          <span class="from">${esc(m.from)}</span>
          <span>→</span>
          <span class="to">${esc(m.to)}</span>
          <span class="ts">${t}</span>
          ${m.buffered ? '<span class="badge">из буфера</span>' : ''}
        </div>
        <div class="text">${esc(m.text)}</div>`;
      feed.appendChild(el);
      if(m.id > lastId) lastId = m.id;
    }
    feed.scrollTop = feed.scrollHeight;
  }catch(e){}
}

async function send(){
  const from = document.getElementById('from-sel').value;
  const to   = document.getElementById('to-sel').value;
  const inp  = document.getElementById('msg-input');
  const text = inp.value.trim();
  const errEl= document.getElementById('err');
  errEl.textContent = '';

  if(!text) return;
  if(from === to){ errEl.textContent = 'нельзя отправить себе'; return; }

  const btn = document.getElementById('send-btn');
  btn.disabled = true;
  inp.value = '';
  try{
    const r = await fetch('/api/send',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({from,to,message:text}),
    });
    if(!r.ok){
      const d = await r.json();
      errEl.textContent = d.error || 'ошибка';
      inp.value = text;
    }
  }catch(e){
    errEl.textContent = 'сеть недоступна';
    inp.value = text;
  }finally{
    btn.disabled = false;
    inp.focus();
  }
}

document.getElementById('send-btn').onclick = send;
document.getElementById('msg-input').onkeydown = e => { if(e.key==='Enter') send(); };

loadCells();
setInterval(pollMessages, 500);
setInterval(refreshCells, 2000);
</script>
</body>
</html>"""


class WebUI:
    def __init__(self, node_addr: str, http_port: int, cell_names: list[str]):
        self.node_addr = node_addr
        self.http_port = http_port
        self.cell_names = cell_names
        self.node: Node | None = None
        self.cells: dict[str, CellClient] = {}
        self.identities: dict[str, CellIdentity] = {}  # kept for reconnect
        self.messages: list[dict] = []
        self._msg_id = 0

    async def start(self):
        self.node = await Node.create_genesis(
            self.node_addr, "webui.node.json", "webui.node.db"
        )
        await self.node.start()
        await asyncio.sleep(0.15)

        for name in self.cell_names:
            idt = CellIdentity.generate(name)
            self.identities[name] = idt
            client = CellClient(idt, on_message=self._make_handler(name))
            await client.connect(self.node_addr)
            self.cells[name] = client
            log.info("cell '%s': %s", name, idt.cell_id[:16])

    def _make_handler(self, cell_name: str, buffered: bool = False):
        async def handler(from_addr: str, plaintext: bytes):
            text = plaintext.decode(errors="replace")
            from_name = self._resolve_name(from_addr)
            self._msg_id += 1
            self.messages.append({
                "id":       self._msg_id,
                "from":     from_name,
                "to":       cell_name,
                "text":     text,
                "ts":       int(time.time() * 1000),
                "buffered": False,  # will be True if cell was offline
            })
            status = "(из буфера)" if self.cells[cell_name].connected and \
                not self.cells[cell_name].connected else ""
            log.info("[%s → %s] %s %s", from_name, cell_name, text, status)
        return handler

    def _resolve_name(self, from_addr: str) -> str:
        cell_id = from_addr.split("@")[0] if "@" in from_addr else from_addr
        for name, idt in self.identities.items():
            if idt.cell_id == cell_id:
                return name
        return from_addr[:12]

    async def disconnect_cell(self, name: str):
        client = self.cells.get(name)
        if client and client.connected:
            await client.disconnect()
            log.info("cell '%s' disconnected (offline)", name)

    async def reconnect_cell(self, name: str):
        client = self.cells.get(name)
        idt = self.identities.get(name)
        if client and idt and not client.connected:
            # Re-attach handler that marks messages as buffered
            client.on_message = self._make_buffered_handler(name)
            await client.connect(self.node_addr)
            # After first flush, switch back to normal handler
            asyncio.create_task(self._reset_handler_after_flush(name))
            log.info("cell '%s' reconnected, flushing buffer", name)

    def _make_buffered_handler(self, cell_name: str):
        async def handler(from_addr: str, plaintext: bytes):
            text = plaintext.decode(errors="replace")
            from_name = self._resolve_name(from_addr)
            self._msg_id += 1
            self.messages.append({
                "id":       self._msg_id,
                "from":     from_name,
                "to":       cell_name,
                "text":     text,
                "ts":       int(time.time() * 1000),
                "buffered": True,
            })
            log.info("[%s → %s] %s (из буфера)", from_name, cell_name, text)
        return handler

    async def _reset_handler_after_flush(self, cell_name: str):
        # Buffer flush happens synchronously in node during CELL_REGISTER handling.
        # A short yield is enough to let all buffered deliveries land before we reset.
        await asyncio.sleep(0.5)
        client = self.cells.get(cell_name)
        if client:
            client.on_message = self._make_handler(cell_name)

    async def stop(self):
        for client in self.cells.values():
            if client.connected:
                await client.disconnect()
        if self.node:
            await self.node.stop()

    # ── HTTP handlers ─────────────────────────────────────────────────────────

    async def handle_index(self, _req):
        return web.Response(text=_HTML, content_type="text/html")

    async def handle_cells(self, _req):
        return web.json_response({
            name: {
                "cell_id":       c.cell_id,
                "cell_id_short": c.cell_id[:16],
                "online":        c.connected,
            }
            for name, c in self.cells.items()
        })

    async def handle_toggle(self, request):
        name = request.match_info["name"]
        if name not in self.cells:
            return web.json_response({"error": "unknown cell"}, status=404)
        if self.cells[name].connected:
            await self.disconnect_cell(name)
            return web.json_response({"ok": True, "online": False})
        else:
            await self.reconnect_cell(name)
            return web.json_response({"ok": True, "online": True})

    async def handle_send(self, request):
        try:
            data      = await request.json()
            from_name = data["from"]
            to_name   = data["to"]
            text      = data["message"].strip()
        except Exception:
            return web.json_response({"error": "bad request"}, status=400)

        if not text:
            return web.json_response({"error": "empty message"}, status=400)
        if from_name == to_name:
            return web.json_response({"error": "cannot send to self"}, status=400)

        sender    = self.cells.get(from_name)
        recipient = self.cells.get(to_name)
        if not sender or not recipient:
            return web.json_response({"error": "unknown cell"}, status=400)
        if not sender.connected:
            return web.json_response({"error": f"{from_name} offline"}, status=400)

        rec_idt = self.identities.get(to_name)
        if not rec_idt:
            return web.json_response({"error": "no recipient identity"}, status=500)

        try:
            await sender.send(
                recipient.cell_id,
                sender._node_id,
                rec_idt.encryption.public,
                text.encode(),
            )
        except Exception as e:
            log.error("send error: %s", e)
            return web.json_response({"error": str(e)}, status=500)

        return web.json_response({"ok": True})

    async def handle_messages(self, request):
        since_id = int(request.query.get("since_id", 0))
        return web.json_response([m for m in self.messages if m["id"] > since_id])

    def make_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/",                        self.handle_index)
        app.router.add_get("/api/cells",               self.handle_cells)
        app.router.add_post("/api/cells/{name}/toggle", self.handle_toggle)
        app.router.add_post("/api/send",               self.handle_send)
        app.router.add_get("/api/messages",            self.handle_messages)
        return app


async def run(node_addr: str, http_port: int, cell_names: list[str]):
    ui = WebUI(node_addr, http_port, cell_names)
    await ui.start()

    runner = web.AppRunner(ui.make_app())
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", http_port).start()

    print(f"\nNevod WebUI  →  http://127.0.0.1:{http_port}")
    print(f"node         →  {node_addr}")
    print(f"cells        →  {', '.join(cell_names)}")
    print("Ctrl+C to stop\n")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await runner.cleanup()
        await ui.stop()
