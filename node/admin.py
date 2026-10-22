"""
Nevod Admin — production admin panel.

HTTP Basic Auth. NEVOD_ADMIN_PASSWORD (plus an optional installer-set username)
is a permanent break-glass login; the Безопасность page manages additional
per-admin accounts on top of it, hashed (PBKDF2-SHA256) in storage.py's
admin_users table.
Port: NEVOD_ADMIN_PORT (default 8766).
Aliases: data/aliases.json  (cell_id → display name).
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from .node import Node

log = logging.getLogger(__name__)


def _repo_root() -> Path:
    """This file lives at <repo>/node/admin.py, so its grandparent is the repo
    root — where RELEASE.json/RELEASE.sig live (see update_checker.py)."""
    return Path(__file__).resolve().parent.parent


# ─── Password hashing (Безопасность page's per-admin accounts) ────────────────
#
# Only used for rows in storage.py's admin_users table — the single legacy
# NEVOD_ADMIN_PASSWORD/installer credential AdminServer is constructed with
# stays a plain in-memory string compared with hmac.compare_digest, same as
# before this existed; it was never stored anywhere on disk in the first
# place, so there's nothing to hash there. PBKDF2-HMAC-SHA256 (stdlib only,
# no new dependency) with a random per-row salt and the format made
# self-describing ("pbkdf2_sha256$iterations$salt$hash", same idea as
# Django's) so a later iteration-count bump doesn't strand old rows.
_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations))
        return hmac.compare_digest(digest, bytes.fromhex(hash_hex))
    except Exception:
        return False


# ─── In-memory log ring buffer ────────────────────────────────────────────────

class _RingHandler(logging.Handler):
    def __init__(self, capacity=300):
        super().__init__()
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(name)s — %(message)s",
                                            datefmt="%H:%M:%S"))
        self._buf: deque[str] = deque(maxlen=capacity)

    def emit(self, record):
        try:
            self._buf.append(self.format(record))
        except Exception:
            pass

    def lines(self) -> list[str]:
        return list(self._buf)


_ring = _RingHandler()
logging.getLogger().addHandler(_ring)


# ─── HTML ─────────────────────────────────────────────────────────────────────

# Nav: (path segment under /nevod-admin/, label). "" is the Обзор/overview page
# itself. Split 2026-09-13 from one single 700-line page into these six — each
# page fetches only the data it needs instead of every section polling on
# every view, and the admin isn't scrolling past six unrelated tables to find
# the one they came for.
_NAV = [
    ("", "Обзор"),
    ("settings", "Настройки"),
    ("join-requests", "Заявки на подключение"),
    ("appeals", "Обращения"),
    ("invites", "Приглашения"),
    ("nodes", "Узлы"),
    ("published", "Публикация"),
    ("ai-bots", "AI-боты"),
    ("security", "Безопасность"),
    ("diagnostics", "Диагностика"),
]

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:monospace;background:#0d1117;color:#c9d1d9;min-height:100vh}
header{background:#161b22;border-bottom:1px solid #30363d;padding:16px 24px;
  display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap}
#node-title{font-size:24px;font-weight:bold;color:#58a6ff;letter-spacing:.3px;line-height:1.2}
#node-sub{font-size:10px;color:#484f58;letter-spacing:1px;margin-top:2px}
#node-detail{font-size:11px;color:#8b949e;margin-top:6px}
#status-box{display:flex;gap:8px;flex-wrap:wrap}
.status-pill{font-size:11px;padding:7px 14px;border-radius:6px;border:1px solid;
  white-space:nowrap;line-height:1.3}
.status-pill b{display:block;font-size:12px}
.pill-open{background:#0d2818;border-color:#238636;color:#3fb950}
.pill-closed{background:#2d1618;border-color:#6e3030;color:#f85149}
.pill-public{background:#0d2818;border-color:#238636;color:#3fb950}
.pill-members{background:#12233a;border-color:#1f6feb;color:#58a6ff}
.pill-off{background:#21262d;border-color:#30363d;color:#8b949e}
.pill-clickable{cursor:pointer}
.pill-clickable:hover{opacity:.8}
nav{background:#0d1117;border-bottom:1px solid #21262d;display:flex;gap:4px;
  padding:0 24px;overflow-x:auto}
nav a{color:#8b949e;text-decoration:none;font-size:12px;padding:12px 14px;
  display:inline-block;border-bottom:2px solid transparent;white-space:nowrap}
nav a:hover{color:#c9d1d9}
nav a.active{color:#58a6ff;border-bottom-color:#58a6ff}
main{padding:24px;display:flex;flex-direction:column;gap:24px}
section{background:#161b22;border:1px solid #21262d;border-radius:8px;overflow:hidden}
section h2{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#8b949e;
  padding:12px 16px;border-bottom:1px solid #21262d;display:flex;align-items:center;gap:12px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 16px;color:#8b949e;font-size:11px;
  border-bottom:1px solid #21262d;font-weight:normal}
td{padding:10px 16px;border-bottom:1px solid #161b22;vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1c2128}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.online .dot{background:#3fb950}
.offline .dot{background:#6e3030}
.cell-id{color:#484f58;font-size:11px}
.alias-inp{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;
  padding:4px 8px;border-radius:4px;font-family:monospace;font-size:12px;width:140px}
.alias-inp:focus{border-color:#58a6ff;outline:none}
button{font-family:monospace;font-size:12px;border:none;border-radius:4px;
  padding:4px 12px;cursor:pointer;transition:opacity .15s}
button:hover{opacity:.8}
.btn-save{background:#1a4a1a;color:#3fb950}
.btn-del{background:#4a1a1a;color:#f85149}
.btn-danger{background:#6e3030;color:#f85149;font-size:12px;padding:6px 14px}
.btn-warn{background:#4a3a00;color:#d29922;font-size:12px;padding:6px 14px}
.buf{color:#d29922;font-size:11px}
#logs-box{background:#0d1117;padding:14px 16px;font-size:11px;line-height:1.6;
  max-height:400px;overflow-y:auto;color:#8b949e;white-space:pre-wrap;word-break:break-all}
.err{color:#f85149;font-size:11px;padding:6px 16px}
.stat{color:#3fb950}
.code-badge{display:inline-block;background:#0d1117;border:1px solid #30363d;
  border-radius:4px;padding:2px 8px;font-size:13px;letter-spacing:2px;color:#58a6ff;
  cursor:pointer;user-select:all}
.code-badge:hover{border-color:#58a6ff}
.used{opacity:.4;text-decoration:line-through}
.tag-ok{color:#3fb950;font-size:11px}
.tag-no{color:#f85149;font-size:11px}
.tag-warn{color:#d29922;font-size:11px}
#diag-body .dot{margin-right:8px}
#diag-body .ok .dot{background:#3fb950}
#diag-body .warn .dot{background:#d29922}
#diag-body .fail .dot{background:#f85149}
#diag-body .diag-row{padding:10px 16px;border-bottom:1px solid #161b22;font-size:13px}
#diag-body .diag-row:last-child{border-bottom:none}
#diag-body .diag-detail{color:#8b949e;font-size:11px;margin-top:4px;margin-left:16px}
.qr-wrap{text-align:center;padding:12px 16px}
#qr-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);
  z-index:100;align-items:center;justify-content:center;flex-direction:column;gap:16px}
#qr-overlay.open{display:flex}
#qr-box{background:#161b22;border:1px solid #30363d;border-radius:12px;
  padding:24px;text-align:center;max-width:340px;width:90%}
#qr-canvas{border-radius:8px;background:#fff;padding:8px}
#qr-code-text{font-size:14px;letter-spacing:.3px;color:#58a6ff;margin:12px 0 4px;
  word-break:break-all;line-height:1.4;padding:0 4px}
#qr-exp{color:#8b949e;font-size:11px}
#qr-close{background:#2d333b;border:1px solid #444;color:#c9d1d9;border-radius:6px;
  padding:6px 20px;cursor:pointer;font-family:monospace;font-size:13px;margin-top:8px}
"""

_HEADER_HTML = """
<header>
  <div>
    <div id="node-title">загрузка...</div>
    <div id="node-sub">◈ NEVOD ADMIN</div>
    <div id="node-detail">загрузка...</div>
  </div>
  <div id="status-box">
    <span id="status-access" class="status-pill">—</span>
    <span id="status-visibility" class="status-pill">—</span>
  </div>
</header>
"""

_QR_HTML = """
<div id="qr-overlay" onclick="closeQR()">
  <div id="qr-box" onclick="event.stopPropagation()">
    <div style="color:#8b949e;font-size:11px;margin-bottom:8px">Покажи экран новому участнику</div>
    <canvas id="qr-canvas" width="220" height="220"></canvas>
    <div id="qr-code-text">—</div>
    <div id="qr-exp" style="color:#8b949e;font-size:11px"></div>
    <button id="qr-close" onclick="closeQR()">Закрыть</button>
  </div>
</div>
"""

# Shared by every page: DOM-agnostic helpers, the QR overlay, and the header/access
# pill (every page shows the same header, so it needs the same renderer).
_SHARED_JS = """
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function ts(sec){return new Date(sec*1000).toLocaleString('ru-RU')}
function shortId(id){return esc(id.slice(0,16))+'…'}

// ── tiny QR encoder (data-URL via canvas) ────────────────────────────
let _qrlib = null;
async function _getQR(){
  if(_qrlib) return _qrlib;
  try{
    await new Promise((res,rej)=>{
      const s=document.createElement('script');
      s.src='https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js';
      s.onload=res; s.onerror=rej; document.head.appendChild(s);
    });
    _qrlib=window.qrcode; return _qrlib;
  }catch(e){return null;}
}
async function drawQR(text){
  const canvas=document.getElementById('qr-canvas');
  const ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,220,220);
  const lib=await _getQR();
  if(!lib){ctx.fillStyle='#888';ctx.font='14px monospace';ctx.fillText('QR недоступен',10,110);return;}
  const qr=lib(0,'M'); qr.addData(text); qr.make();
  const n=qr.getModuleCount(), cell=Math.floor(220/n);
  ctx.fillStyle='#fff'; ctx.fillRect(0,0,220,220);
  ctx.fillStyle='#000';
  for(let r=0;r<n;r++) for(let c=0;c<n;c++)
    if(qr.isDark(r,c)) ctx.fillRect(c*cell,r*cell,cell,cell);
}
// qrText defaults to the label itself (node invites: the token IS what gets scanned). Cell
// invites pass their https link; the label stays the short code people can read aloud.
function showQR(code, expiresAt, qrText){
  document.getElementById('qr-code-text').textContent=code;
  const min=Math.round((expiresAt-Date.now()/1000)/60);
  document.getElementById('qr-exp').textContent='Действует ещё ~'+
    (min>=2880 ? Math.round(min/1440)+' дн' : min>=120 ? Math.round(min/60)+' ч' : min+' мин');
  drawQR(qrText||code);
  document.getElementById('qr-overlay').classList.add('open');
}
function closeQR(){ document.getElementById('qr-overlay').classList.remove('open'); }

// ── header / access pill (every page) ───────────────────────────────
function renderHeader(data){
  document.getElementById('node-title').textContent =
    data.node_name || ('Node ' + data.node_id.slice(0,16) + '…');
  document.getElementById('node-detail').textContent =
    'node: ' + data.node_id.slice(0,16) + '…  |  ' + data.address +
    '  |  инвайт: ' + (data.invite_mode || 'open');

  // Read-only status here — the actual controls live on the Настройки page now
  // (2026-09-13: used to be a click-to-toggle pill, moved so every Node setting
  // has one home instead of some living only in the header).
  const accessOpen = data.access === 'open';
  const accessEl = document.getElementById('status-access');
  accessEl.className = 'status-pill ' + (accessOpen ? 'pill-open' : 'pill-closed');
  accessEl.innerHTML = '<b>' + (accessOpen ? 'Открытая' : 'Закрытая') + '</b>допуск узлов';

  const vis = data.cells_visibility || 'members';
  const visLabel = {off:'Никто', members:'Участники ноды', public:'Все'}[vis] || vis;
  const visEl = document.getElementById('status-visibility');
  visEl.className = 'status-pill ' + (vis === 'public' ? 'pill-public' : vis === 'off' ? 'pill-off' : 'pill-members');
  visEl.innerHTML = '<b>' + visLabel + '</b>видят ячейки';
}
async function loadHeader(){
  const r = await fetch('/nevod-admin/api/cells');
  const data = await r.json();
  renderHeader(data);
  return data;
}
async function toggleAccess(newAccess){
  const label = newAccess === 'open' ? 'Открытая' : 'Закрытая';
  if(!confirm('Сменить на "' + label + '"? Изменение допуска узлов применяется только после ' +
              'перезапуска ноды (как и через nevod.py set-access).')) return;
  const r = await fetch('/nevod-admin/api/access', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({access: newAccess})
  });
  const data = await r.json();
  if(!data.ok){ alert('Ошибка: ' + data.error); return; }
  alert('Сохранено — перезапустите ноду, чтобы изменение вступило в силу.');
  loadHeader();
}
"""


def _nav_html(active: str) -> str:
    links = []
    for path, label in _NAV:
        href = "/nevod-admin/" + path if path else "/nevod-admin/"
        cls = " class=\"active\"" if path == active else ""
        links.append("<a href=\"" + href + "\"" + cls + ">" + label + "</a>")
    return "<nav>" + "".join(links) + "</nav>"


def _shell(active: str, body: str, script: str) -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<title>Nevod Admin</title>\n<style>" + _CSS + "</style>\n</head>\n<body>\n"
        + _HEADER_HTML + _nav_html(active) + _QR_HTML
        + "<main>\n" + body + "\n</main>\n<script>" + _SHARED_JS + "\n" + script + "\n</script>\n</body>\n</html>"
    )


# ── Обзор ────────────────────────────────────────────────────────────────────

_BODY_OVERVIEW = """
<section>
  <h2>Ячейки <span id="cell-stat" class="stat"></span>
    <span style="margin-left:auto;display:flex;gap:8px">
      <button class="btn-warn" onclick="resetRegs()" title="Очистить регистрации — участники войдут снова без нового кода">Сбросить регистрации</button>
      <button class="btn-danger" onclick="fullReset()" title="Полный сброс — все должны заново ввести код приглашения">Полный сброс</button>
    </span>
  </h2>
  <table>
    <thead><tr><th>Имя</th><th>cell_id</th><th>Статус</th><th>Буфер</th><th>Регистрация</th><th></th></tr></thead>
    <tbody id="cells-body"></tbody>
  </table>
  <div id="cells-err" class="err"></div>
</section>
"""

_SCRIPT_OVERVIEW = """
async function loadCells(){
  const r = await fetch('/nevod-admin/api/cells');
  const data = await r.json();
  renderHeader(data);

  const cells = data.cells;
  const online = cells.filter(c=>c.online).length;
  document.getElementById('cell-stat').textContent =
    online + ' онлайн / ' + cells.length + ' всего';
  const tbody = document.getElementById('cells-body');
  tbody.innerHTML = '';
  for(const c of cells){
    const tr = document.createElement('tr');
    tr.className = c.online ? 'online' : 'offline';
    tr.innerHTML = `
      <td><input class="alias-inp" value="${esc(c.alias)}" data-id="${esc(c.cell_id)}"
          onkeydown="if(event.key==='Enter')saveAlias(this)"></td>
      <td class="cell-id" title="${esc(c.cell_id)}">${shortId(c.cell_id)}</td>
      <td><span class="dot"></span>${c.online ? 'онлайн' : 'офлайн'}</td>
      <td class="buf">${c.buffered > 0 ? c.buffered + ' msg' : '—'}</td>
      <td>${ts(c.registered_at)}</td>
      <td><button class="btn-save" onclick="saveAlias(this.closest('tr').querySelector('.alias-inp'))">✓</button>
          <button class="btn-del" onclick="delCell('${esc(c.cell_id)}',this.closest('tr'))">✕</button></td>`;
    tbody.appendChild(tr);
  }
}

async function saveAlias(inp){
  const cell_id = inp.dataset.id;
  const alias = inp.value.trim();
  await fetch('/nevod-admin/api/cells/' + encodeURIComponent(cell_id) + '/alias', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({alias})
  });
  inp.style.borderColor='#3fb950';
  setTimeout(()=>inp.style.borderColor='',1000);
}

async function delCell(cell_id, tr){
  if(!confirm('Удалить ячейку ' + cell_id.slice(0,16) + '…?\\n\\n' +
              'Это ПОЛНОСТЬЮ и НЕОБРАТИМО отзывает допуск ячейки к сети — ' +
              'не просто убирает её из списка. Ячейка потеряет регистрацию, ' +
              'буферизованные сообщения и push-токены; чтобы вернуться, ей ' +
              'понадобится новый инвайт-код или заявка на подключение заново.'))
    return;
  const r = await fetch('/nevod-admin/api/cells/' + encodeURIComponent(cell_id), {method:'DELETE'});
  if(r.ok) tr.remove(); else alert('Ошибка: ' + await r.text());
}

async function resetRegs(){
  if(!confirm('Сбросить регистрации?\\nЯчейки войдут снова без повторного ввода кода.')) return;
  const r = await fetch('/nevod-admin/api/reset/registrations', {method:'POST'});
  if(r.ok) loadCells(); else alert('Ошибка: ' + await r.text());
}

async function fullReset(){
  if(!confirm('ПОЛНЫЙ СБРОС?\\nВсе участники должны будут заново ввести код приглашения.\\nЭто необратимо.')) return;
  const r = await fetch('/nevod-admin/api/reset/full', {method:'POST'});
  if(r.ok) loadCells();
  else alert('Ошибка: ' + await r.text());
}

loadCells();
setInterval(loadCells, 5000);
"""

# ── Настройки ────────────────────────────────────────────────────────────────
#
# Every Node-level setting in one place (2026-09-13, at the user's request —
# node_type used to live on Обзор, cells_visibility on Публикация, access only
# as a click-to-toggle header pill, and the node's own name had no control at
# all: a node with `name` unset just showed its raw node_id everywhere in the
# panel, which is exactly how node1 ended up admin'd for weeks with nothing
# in the UI marking it as "Dev Planet").

_BODY_SETTINGS = """
<section>
  <h2>Имя ноды</h2>
  <div style="padding:10px 16px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    <input id="name-input" placeholder="напр. Dev Planet"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;flex:1;min-width:200px">
    <button onclick="saveName()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="name-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;color:#484f58;font-size:11px">
    Видно сразу здесь в шапке; другие ноды увидят новое имя после перезапуска этой ноды.
  </div>
</section>

<section>
  <h2>Тип ноды</h2>
  <div style="padding:10px 16px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    <select id="node-type-select" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px">
      <option value="permanent">permanent — обычная нода</option>
      <option value="temporary">temporary — временная/дочерняя нода</option>
    </select>
    <button onclick="saveNodeType()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="node-type-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    ID родительской ноды:
    <input id="parent-node-input" placeholder="node_id родителя (только для temporary)"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;flex:1;min-width:260px">
    <button onclick="saveParentNode()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="parent-node-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;color:#484f58;font-size:11px">
    Имеет смысл только при типе temporary — по нему дочерняя нода уведомляет родителя о своих ячейках. Применяется сразу, без перезапуска. Пусто = не привязана к родителю.
  </div>
</section>

<section>
  <h2>Допуск узлов</h2>
  <div style="padding:10px 16px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    <select id="access-select" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px">
      <option value="open">open — любой узел может присоединиться</option>
      <option value="closed">closed — только по инвайту узла</option>
    </select>
    <button onclick="saveAccess()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="access-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;color:#484f58;font-size:11px">
    Применяется после перезапуска ноды.
  </div>
</section>

<section>
  <h2>Видимость опубликованных ячеек</h2>
  <div style="padding:10px 16px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    <select id="pub-visibility-select" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px">
      <option value="off">off — никто</option>
      <option value="members">members — только участники ноды</option>
      <option value="public">public — все</option>
    </select>
    <button onclick="saveVisibility()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="pub-vis-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;color:#484f58;font-size:11px">
    Кто видит список ячеек на странице <a href="/nevod-admin/published" style="color:#58a6ff">Публикация</a>. Применяется сразу, без перезапуска.
  </div>
</section>

<section>
  <h2>Режим допуска ячеек</h2>
  <div style="padding:10px 16px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    <select id="invite-mode-select" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px">
      <option value="open">open — без кода</option>
      <option value="delegated">delegated — код от участников</option>
      <option value="admin">admin — заявка + ваше одобрение</option>
    </select>
    <button onclick="saveInviteMode()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="invite-mode-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;display:flex;gap:8px;align-items:center;font-size:12px;color:#8b949e;flex-wrap:wrap">
    Администраторы (cell_id через запятую):
    <input id="admin-cells-input" placeholder="cell_id1, cell_id2…"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;flex:1;min-width:220px">
    <button onclick="saveAdminCells()" style="background:#1a2a3a;color:#58a6ff">Сохранить</button>
    <span id="admin-cells-err" class="err"></span>
  </div>
  <div style="padding:0 16px 10px;color:#484f58;font-size:11px">
    Кто может подключаться как ячейка, и кому приходит уведомление о заявке (режим admin) — заявки на подключение смотреть и одобрять на странице <a href="/nevod-admin/join-requests" style="color:#58a6ff">Заявки на подключение</a>. Применяется сразу, без перезапуска.
  </div>
</section>
"""

_SCRIPT_SETTINGS = """
async function loadSettings(){
  const data = await loadHeader();
  document.getElementById('name-input').value = data.node_name || '';
  document.getElementById('node-type-select').value = data.node_type || 'permanent';
  document.getElementById('parent-node-input').value = data.parent_node_id || '';
  document.getElementById('access-select').value = data.access || 'closed';
  document.getElementById('pub-visibility-select').value = data.cells_visibility || 'members';
  document.getElementById('invite-mode-select').value = data.invite_mode || 'open';
  document.getElementById('admin-cells-input').value = (data.admin_cell_ids || []).join(', ');
}

async function saveName(){
  const name = document.getElementById('name-input').value.trim();
  const errEl = document.getElementById('name-err');
  errEl.textContent = '';
  const r = await fetch('/nevod-admin/api/name', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name})
  });
  const data = await r.json();
  if(!data.ok){ errEl.textContent = 'Ошибка: ' + data.error; return; }
  loadSettings();
}

async function saveNodeType(){
  const node_type = document.getElementById('node-type-select').value;
  const errEl = document.getElementById('node-type-err');
  errEl.textContent = '';
  if(!confirm('Сменить тип ноды на "' + node_type + '"? Изменение применяется только после ' +
              'перезапуска ноды (как и через nevod.py init --type).')) return;
  const r = await fetch('/nevod-admin/api/node-type', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({node_type})
  });
  const data = await r.json();
  if(!data.ok){ errEl.textContent = 'Ошибка: ' + data.error; return; }
  alert('Сохранено — перезапустите ноду, чтобы изменение вступило в силу.');
  loadSettings();
}

async function saveParentNode(){
  const parent_node_id = document.getElementById('parent-node-input').value.trim();
  const errEl = document.getElementById('parent-node-err');
  errEl.textContent = '';
  const r = await fetch('/nevod-admin/api/parent-node-id', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({parent_node_id})
  });
  const data = await r.json();
  if(!data.ok){ errEl.textContent = 'Ошибка: ' + data.error; return; }
  loadSettings();
}

async function saveAccess(){
  const access = document.getElementById('access-select').value;
  const errEl = document.getElementById('access-err');
  errEl.textContent = '';
  await toggleAccess(access);
  loadSettings();
}

async function saveVisibility(){
  const cells_visibility = document.getElementById('pub-visibility-select').value;
  const errBox = document.getElementById('pub-vis-err');
  errBox.textContent = '';
  const r = await fetch('/nevod-admin/api/cells-visibility', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cells_visibility})
  });
  const data = await r.json();
  if(!data.ok){ errBox.textContent = 'Ошибка: ' + data.error; return; }
  errBox.style.color = '#3fb950';
  errBox.textContent = 'Сохранено ✓';
  setTimeout(()=>{ errBox.textContent=''; errBox.style.color=''; }, 2000);
  loadSettings();
}

async function saveInviteMode(){
  const invite_mode = document.getElementById('invite-mode-select').value;
  const errEl = document.getElementById('invite-mode-err');
  errEl.textContent = '';
  const r = await fetch('/nevod-admin/api/invite-mode',
    {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({invite_mode})});
  if(r.ok) loadSettings(); else errEl.textContent = (await r.json()).error || 'Ошибка';
}

async function saveAdminCells(){
  const raw = document.getElementById('admin-cells-input').value;
  const admin_cell_ids = raw.split(',').map(s=>s.trim()).filter(Boolean);
  const errEl = document.getElementById('admin-cells-err');
  errEl.textContent = '';
  const r = await fetch('/nevod-admin/api/admin-cells',
    {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({admin_cell_ids})});
  if(r.ok) loadSettings(); else errEl.textContent = (await r.json()).error || 'Ошибка';
}

loadSettings();
"""

# ── Заявки на подключение ────────────────────────────────────────────────────

_BODY_JOIN_REQUESTS = """
<section>
  <h2>Заявки на подключение <span id="joinreq-stat" class="stat"></span>
    <button onclick="loadJoinRequests()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <div style="padding:0 16px 10px;color:#8b949e;font-size:12px">
    Режим допуска и список администраторов — на странице <a href="/nevod-admin/settings" style="color:#58a6ff">Настройки</a>.
  </div>
  <table>
    <thead><tr><th>Имя</th><th>cell_id</th><th>Заметка</th><th>Подана</th><th></th></tr></thead>
    <tbody id="joinreq-body"></tbody>
  </table>
  <div id="joinreq-err" class="err"></div>
</section>
"""

_SCRIPT_JOIN_REQUESTS = """
async function loadJoinRequests(){
  const r = await fetch('/nevod-admin/api/join-requests');
  const data = await r.json();
  document.getElementById('joinreq-stat').textContent = data.requests.length + ' шт';
  const tbody = document.getElementById('joinreq-body');
  tbody.innerHTML = '';
  for(const req of data.requests){
    const cid = esc(req.cell_id);
    const name = req.display_name
      ? `<span style="color:#c9d1d9;font-weight:500">${esc(req.display_name)}</span>`
      : '<span class="cell-id">без имени</span>';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${name}</td>
      <td class="cell-id" title="${cid}">${shortId(req.cell_id)}</td>
      <td>${esc(req.note || '—')}</td>
      <td>${ts(req.created_at)}</td>
      <td>
        <button style="background:#1a3a1a;color:#3fb950;font-family:monospace;font-size:11px;border:none;border-radius:4px;padding:3px 8px;cursor:pointer"
            onclick="approveJoinRequest('${cid}')">Одобрить</button>
        <button style="background:#3a1a1a;color:#f85149;font-family:monospace;font-size:11px;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;margin-left:4px"
            onclick="denyJoinRequest('${cid}')">Отклонить</button>
      </td>`;
    tbody.appendChild(tr);
  }
  if(!data.requests.length) tbody.innerHTML='<tr><td colspan="5" style="color:#484f58;padding:12px 16px">нет заявок</td></tr>';
}

async function approveJoinRequest(cell_id){
  const r = await fetch('/nevod-admin/api/join-requests/'+encodeURIComponent(cell_id)+'/approve', {method:'POST'});
  if(r.ok){ loadJoinRequests(); } else alert('Ошибка: ' + await r.text());
}

async function denyJoinRequest(cell_id){
  const r = await fetch('/nevod-admin/api/join-requests/'+encodeURIComponent(cell_id)+'/deny', {method:'POST'});
  if(r.ok) loadJoinRequests(); else alert('Ошибка: ' + await r.text());
}

loadHeader();
loadJoinRequests();
setInterval(loadJoinRequests, 8000);
"""

# ── Обращения (built-in administrator cell) ─────────────────────────────────

_BODY_APPEALS = """
<section>
  <h2>Обращения <span id="appeals-stat" class="stat"></span>
    <button onclick="loadThreads()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <div style="padding:10px 16px;color:#8b949e;font-size:12px;line-height:1.6">
    Жалобы и вопросы, которые пользователи отправили аккаунту <b style="color:#c9d1d9">administrator</b> этой ноды
    из приложения. Ответ уходит пользователю в Nevod, зашифрованным, от имени administrator.
    По e-mail мы не отвечаем никогда.
  </div>
  <table>
    <thead><tr><th>Отправитель</th><th>Последнее сообщение</th><th>Когда</th><th></th></tr></thead>
    <tbody id="threads-body"></tbody>
  </table>
</section>

<section id="thread-box" style="display:none">
  <h2>Переписка с <span id="thread-title" style="color:#c9d1d9;text-transform:none;letter-spacing:0"></span>
    <span id="thread-id" class="cell-id" style="text-transform:none;letter-spacing:0"></span>
  </h2>
  <div id="thread-msgs" style="padding:12px 16px;display:flex;flex-direction:column;gap:10px;max-height:480px;overflow-y:auto"></div>
  <div style="padding:12px 16px;border-top:1px solid #21262d;display:flex;gap:8px;align-items:flex-end">
    <textarea id="reply-text" rows="3" placeholder="Ответ от administrator…"
      style="flex:1;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:8px;font-family:monospace;font-size:13px;resize:vertical"></textarea>
    <button class="btn-save" style="padding:8px 16px" onclick="sendReply()">Ответить</button>
  </div>
  <div id="reply-err" class="err"></div>
</section>

<section>
  <h2>Аккаунт administrator этой ноды</h2>
  <div style="padding:10px 16px;color:#8b949e;font-size:12px;line-height:1.7">
    Чтобы у administrator появился значок ✓, куратор подписывает эти данные в official.json:
    <div id="admin-info" style="margin-top:8px;color:#c9d1d9;word-break:break-all">загрузка…</div>
  </div>
</section>
"""

_SCRIPT_APPEALS = """
let currentCell = null;

async function loadThreads(){
  const r = await fetch('/nevod-admin/api/appeals');
  const data = await r.json();
  const unread = data.threads.reduce((s,t)=>s+t.unread, 0);
  document.getElementById('appeals-stat').textContent =
    data.threads.length + ' диалогов' + (unread ? ' · новых: ' + unread : '');
  const tbody = document.getElementById('threads-body');
  tbody.innerHTML = '';
  for(const t of data.threads){
    const name = t.display_name ? esc(t.display_name) : '<span class="cell-id">без имени</span>';
    const badge = t.unread ? ` <span class="tag-warn">● ${t.unread}</span>` : '';
    const who = t.last_direction === 'out' ? '<span class="cell-id">вы: </span>' : '';
    const preview = esc(t.last_text.length > 90 ? t.last_text.slice(0, 90) + '…' : t.last_text);
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.onclick = () => openThread(t.cell_id, t.display_name);
    tr.innerHTML = `<td>${name}${badge}<div class="cell-id">${shortId(t.cell_id)}</div></td>
      <td>${who}${preview}</td><td>${ts(t.last_at)}</td>
      <td><button style="background:#1a2a3a;color:#58a6ff">открыть</button></td>`;
    tbody.appendChild(tr);
  }
  if(!data.threads.length) tbody.innerHTML='<tr><td colspan="4" style="color:#484f58;padding:12px 16px">обращений нет</td></tr>';
  if(currentCell) loadThread();
}

function openThread(cell_id, name){
  currentCell = cell_id;
  document.getElementById('thread-title').textContent = name || 'без имени';
  document.getElementById('thread-id').textContent = cell_id;
  document.getElementById('thread-box').style.display = '';
  loadThread().then(()=>{ document.getElementById('thread-box').scrollIntoView({behavior:'smooth'}); });
}

async function loadThread(){
  if(!currentCell) return;
  const r = await fetch('/nevod-admin/api/appeals/' + encodeURIComponent(currentCell));
  const data = await r.json();
  const box = document.getElementById('thread-msgs');
  box.innerHTML = '';
  for(const m of data.messages){
    const out = m.direction === 'out';
    const div = document.createElement('div');
    div.style.cssText = 'max-width:80%;padding:8px 12px;border-radius:8px;white-space:pre-wrap;word-break:break-word;font-size:13px;' +
      (out ? 'align-self:flex-end;background:#12233a;border:1px solid #1f6feb'
           : 'align-self:flex-start;background:#0d1117;border:1px solid #30363d');
    const body = esc(m.text).replace(/\\[log:(\\d+)\\]/g,
      '<a href="/nevod-admin/api/diag-logs/$1" style="color:#58a6ff">скачать nevod.log</a>');
    div.innerHTML = body + `<div class="cell-id" style="margin-top:4px">${out ? 'administrator · ' : ''}${ts(m.created_at)}</div>`;
    box.appendChild(div);
  }
  box.scrollTop = box.scrollHeight;
}

async function sendReply(){
  const ta = document.getElementById('reply-text');
  const text = ta.value.trim();
  const err = document.getElementById('reply-err');
  err.textContent = '';
  if(!text || !currentCell) return;
  const r = await fetch('/nevod-admin/api/appeals/' + encodeURIComponent(currentCell) + '/reply', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text})
  });
  const data = await r.json();
  if(!data.ok){ err.textContent = 'Не отправлено: ' + (data.error || r.status); return; }
  ta.value = '';
  loadThreads();
}

async function loadAdminInfo(){
  const r = await fetch('/nevod-admin/api/administrator');
  const d = await r.json();
  const el = document.getElementById('admin-info');
  if(!d.cell_id){ el.textContent = 'administrator не создан на этой ноде'; return; }
  el.innerHTML = `cell_id: ${esc(d.cell_id)}<br>enc_pub: ${esc(d.enc_pub)}<br>node_id: ${esc(d.node_id)}` +
    `<br><span class="cell-id">python -m node.curator_sign sign-official --role administrator --name administrator ` +
    `--cell-id ${esc(d.cell_id)} --enc-pub ${esc(d.enc_pub)} --node-id ${esc(d.node_id)} --privkey-file &lt;ключ куратора&gt;</span>`;
}

loadHeader();
loadThreads();
loadAdminInfo();
setInterval(loadThreads, 8000);
"""

# ── Приглашения (+ Допущенные ячейки) ────────────────────────────────────────

_BODY_INVITES = """
<section>
  <h2>Приглашения
    <select id="inv-ttl" title="Срок действия кода" style="margin-left:8px">
      <option value="3600">1 час</option>
      <option value="86400" selected>24 часа</option>
      <option value="604800">7 дней</option>
    </select>
    <button onclick="createInvite()" style="background:#1a3a1a;color:#3fb950;margin-left:4px">+ Создать код</button>
    <button onclick="loadInvites()" style="background:#1a2a3a;color:#58a6ff;margin-left:4px">обновить</button>
  </h2>
  <div id="inv-token" style="display:none;padding:10px 16px;font-size:11px;color:#8b949e">
    QR — это ссылка: её можно отсканировать обычной камерой телефона или переслать. Она откроет Nevod с уже заполненными адресом узла и кодом.
    <a id="inv-link" href="#" onclick="copyInviteLink();return false" style="color:#58a6ff">Скопировать ссылку</a> ·
    Короткий код (ввести вручную на этом же узле): <span id="inv-token-text" class="code-badge" style="letter-spacing:0;font-size:12px"></span>
  </div>
  <table>
    <thead><tr><th>Код</th><th>Создан</th><th>Действует до</th><th>Статус</th><th>Использован</th></tr></thead>
    <tbody id="inv-body"></tbody>
  </table>
  <div id="inv-err" class="err"></div>
</section>

<section>
  <h2>Допущенные ячейки <span id="allowed-stat" class="stat"></span>
    <button onclick="loadAllowed()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <table>
    <thead><tr><th>cell_id</th><th>Кем приглашён</th><th>Вошёл</th><th>Может приглашать</th><th></th></tr></thead>
    <tbody id="allowed-body"></tbody>
  </table>
</section>
"""

_SCRIPT_INVITES = """
let _lastInviteLink = '';
async function createInvite(){
  const ttl = parseInt(document.getElementById('inv-ttl').value, 10);
  const r = await fetch('/nevod-admin/api/invites', {method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({ttl_secs: ttl})});
  const data = await r.json();
  if(!data.ok){ document.getElementById('inv-err').textContent = 'Ошибка: ' + data.error; return; }
  await loadInvites();
  _lastInviteLink = data.link;
  document.getElementById('inv-token-text').textContent = data.code;
  document.getElementById('inv-link').textContent = 'Скопировать ссылку';
  document.getElementById('inv-token').style.display = 'block';
  showQR(data.code, data.expires_at, data.link);
}
function copyInviteLink(){
  if(!_lastInviteLink) return;
  navigator.clipboard?.writeText(_lastInviteLink);
  document.getElementById('inv-link').textContent = 'Ссылка скопирована';
}

async function loadInvites(){
  const r = await fetch('/nevod-admin/api/invites');
  const data = await r.json();
  const tbody = document.getElementById('inv-body');
  tbody.innerHTML = '';
  for(const inv of data.invites){
    const tr = document.createElement('tr');
    tr.className = inv.used ? 'used' : '';
    tr.innerHTML = `
      <td><span class="code-badge" onclick="showQR('${esc(inv.code)}',${inv.expires_at},'${esc(inv.link)}')" title="Показать QR">${esc(inv.code)}</span></td>
      <td>${ts(inv.created_at)}</td>
      <td>${ts(inv.expires_at)}</td>
      <td>${inv.used ? '<span class="tag-no">использован</span>' : '<span class="tag-ok">активен</span>'}</td>
      <td class="cell-id">${inv.used_by ? shortId(inv.used_by) : '—'}</td>`;
    tbody.appendChild(tr);
  }
  if(!data.invites.length) tbody.innerHTML='<tr><td colspan="5" style="color:#484f58;padding:12px 16px">нет кодов</td></tr>';
}

async function loadAllowed(){
  const r = await fetch('/nevod-admin/api/allowed');
  const data = await r.json();
  document.getElementById('allowed-stat').textContent = data.cells.length + ' шт';
  const tbody = document.getElementById('allowed-body');
  tbody.innerHTML = '';
  for(const c of data.cells){
    const cid=esc(c.cell_id);
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td title="${cid}" style="cursor:default">
        ${c.display_name
          ? `<span style="color:#c9d1d9;font-weight:500">${esc(c.display_name)}</span>
             <span class="cell-id" style="margin-left:6px;font-size:10px">${shortId(c.cell_id)}</span>`
          : `<span class="cell-id">${shortId(c.cell_id)}</span>`}
      </td>
      <td>${c.invited_by==='admin'
            ? '<span style="color:#d29922">admin</span>'
            : c.invited_by_name
              ? `<span style="color:#c9d1d9">${esc(c.invited_by_name)}</span>`
              : `<span class="cell-id">${shortId(c.invited_by)}</span>`
          }</td>
      <td>${ts(c.joined_at)}</td>
      <td>${c.can_invite
        ? '<span class="tag-ok">да</span>'
        : '<span class="tag-no">нет</span>'}</td>
      <td><button style="background:#1a2a3a;color:#58a6ff;font-family:monospace;font-size:11px;border:none;border-radius:4px;padding:3px 8px;cursor:pointer"
          onclick="toggleInvite('${cid}',${c.can_invite})">${c.can_invite?'Забрать право':'Дать право'}</button></td>`;
    tbody.appendChild(tr);
  }
  if(!data.cells.length) tbody.innerHTML='<tr><td colspan="5" style="color:#484f58;padding:12px 16px">нет допущенных ячеек</td></tr>';
}

async function toggleInvite(cell_id, current){
  const action = current ? 'revoke' : 'grant';
  await fetch('/nevod-admin/api/allowed/'+encodeURIComponent(cell_id)+'/invite-right',
    {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action})});
  loadAllowed();
}

loadHeader();
loadInvites();
loadAllowed();
setInterval(loadInvites, 15000);
setInterval(loadAllowed, 15000);
"""

# ── Узлы (+ Приглашения нод) ─────────────────────────────────────────────────

_BODY_NODES = """
<section>
  <h2>Известные узлы <span id="nodes-stat" class="stat"></span>
    <button onclick="loadNodes()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <table>
    <thead><tr><th>Название</th><th>node_id</th><th>Адрес</th><th>Статус</th><th>Тип</th><th>Последний раз на связи</th></tr></thead>
    <tbody id="nodes-body"></tbody>
  </table>
  <div id="nodes-err" class="err"></div>
</section>

<section>
  <h2>Приглашения нод
    <button onclick="createNodeInvite()" style="background:#1a3a1a;color:#3fb950;margin-left:8px">+ Создать инвайт ноды</button>
    <button onclick="loadNodeInvites()" style="background:#1a2a3a;color:#58a6ff;margin-left:4px">обновить</button>
  </h2>
  <div id="node-inv-token" style="display:none;padding:10px 16px;font-size:11px;color:#8b949e">
    Токен для нового узла (передать администратору лично, не публично):
    <div style="margin-top:6px">
      <span id="node-inv-token-text" class="code-badge" style="letter-spacing:0;font-size:12px" onclick="copyNodeToken()"></span>
    </div>
  </div>
  <table>
    <thead><tr><th>Код</th><th>Создан</th><th>Действует до</th><th>Статус</th><th>Кем использован</th></tr></thead>
    <tbody id="node-inv-body"></tbody>
  </table>
  <div id="node-inv-err" class="err"></div>
</section>
"""

_SCRIPT_NODES = """
async function loadNodes(){
  const r = await fetch('/nevod-admin/api/nodes');
  const data = await r.json();
  document.getElementById('nodes-stat').textContent = data.nodes.length + ' шт';
  const tbody = document.getElementById('nodes-body');
  tbody.innerHTML = '';
  for(const n of data.nodes){
    const tr = document.createElement('tr');
    tr.className = n.status === 'online' ? 'online' : 'offline';
    tr.innerHTML = `
      <td>${n.name ? esc(n.name) : '<span class="cell-id">—</span>'}</td>
      <td class="cell-id" title="${esc(n.node_id)}">${shortId(n.node_id)}</td>
      <td>${esc(n.address)}</td>
      <td><span class="dot"></span>${n.status === 'online' ? 'онлайн' : 'офлайн'}</td>
      <td>${esc(n.type)}</td>
      <td>${ts(n.last_seen)}</td>`;
    tbody.appendChild(tr);
  }
  if(!data.nodes.length) tbody.innerHTML='<tr><td colspan="6" style="color:#484f58;padding:12px 16px">нет известных узлов</td></tr>';
}

let _lastNodeToken = '';
async function createNodeInvite(){
  const r = await fetch('/nevod-admin/api/node-invites', {method:'POST'});
  const data = await r.json();
  if(!data.ok){ alert('Ошибка: ' + data.error); return; }
  await loadNodeInvites();
  _lastNodeToken = data.token;
  document.getElementById('node-inv-token-text').textContent = data.token;
  document.getElementById('node-inv-token').style.display = 'block';
  showQR(data.token, data.expires_at);
}
function copyNodeToken(){
  if(!_lastNodeToken) return;
  navigator.clipboard?.writeText(_lastNodeToken);
}
async function loadNodeInvites(){
  const r = await fetch('/nevod-admin/api/node-invites');
  const data = await r.json();
  const tbody = document.getElementById('node-inv-body');
  tbody.innerHTML = '';
  for(const inv of data.invites){
    const tr = document.createElement('tr');
    tr.className = inv.used ? 'used' : '';
    tr.innerHTML = `
      <td><span class="code-badge">${esc(inv.code)}</span></td>
      <td>${ts(inv.created_at)}</td>
      <td>${ts(inv.expires_at)}</td>
      <td>${inv.used ? '<span class="tag-no">использован</span>' : '<span class="tag-ok">активен</span>'}</td>
      <td class="cell-id">${inv.used_by ? shortId(inv.used_by) : '—'}</td>`;
    tbody.appendChild(tr);
  }
  if(!data.invites.length) tbody.innerHTML='<tr><td colspan="5" style="color:#484f58;padding:12px 16px">нет кодов</td></tr>';
}

loadHeader();
loadNodes();
loadNodeInvites();
setInterval(loadNodes, 15000);
setInterval(loadNodeInvites, 15000);
"""

# ── Публикация ────────────────────────────────────────────────────────────────

_BODY_PUBLISHED = """
<section>
  <h2>Опубликованные ячейки <span id="pub-stat" class="stat"></span>
    <button onclick="loadPublishedCells()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <div style="padding:10px 16px;color:#8b949e;font-size:12px">
    Видимость этого списка другим — на странице <a href="/nevod-admin/settings" style="color:#58a6ff">Настройки</a>.
  </div>
  <div style="padding:0 16px 10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
    <select id="pub-cell-select" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px"></select>
    <input id="pub-name" placeholder="Название" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;width:160px">
    <select id="pub-kind" onchange="onPubKindChange()" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px">
      <option value="bot">bot</option>
      <option value="page">page</option>
    </select>
    <input id="pub-desc" placeholder="Описание" style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;flex:1;min-width:160px">
    <button onclick="publishCell()" style="background:#1a3a1a;color:#3fb950">Опубликовать</button>
  </div>
  <div id="pub-ai-wrap" style="padding:0 16px 10px;color:#8b949e;font-size:12px">
    AI-бот на ключе пользователя (node.bot): провайдеры, которые бот принимает —
    <label><input type="checkbox" class="pub-ai" value="anthropic"> Claude</label>
    <label><input type="checkbox" class="pub-ai" value="openai"> ChatGPT</label>
    <label><input type="checkbox" class="pub-ai" value="gemini"> Gemini</label>
    · ничего не отмечено = обычный бот без ключа (например, эхо-бот). Должно совпадать с флагом --providers бота.
  </div>
  <div id="pub-landing-wrap" style="display:none;padding:0 16px 10px">
    <textarea id="pub-landing" placeholder="Markdown-текст лендинга (только для kind=page)" rows="4"
              style="width:100%;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:8px;border-radius:4px;font-family:monospace;box-sizing:border-box"></textarea>
  </div>
  <table>
    <thead><tr><th>Название</th><th>cell_id</th><th>Тип</th><th>AI (ключ пользователя)</th><th>Описание</th><th>Опубликовано</th><th></th></tr></thead>
    <tbody id="pub-body"></tbody>
  </table>
  <div id="pub-err" class="err"></div>
</section>
"""

_SCRIPT_PUBLISHED = """
function onPubKindChange(){
  const isPage = document.getElementById('pub-kind').value === 'page';
  document.getElementById('pub-landing-wrap').style.display = isPage ? 'block' : 'none';
  document.getElementById('pub-ai-wrap').style.display = isPage ? 'none' : 'block';
}
async function loadPublishedCells(){
  // Own cells list re-fetched here just to populate the picker AND the shared
  // header — simplest way to keep this page self-contained.
  const cellsR = await fetch('/nevod-admin/api/cells');
  const cellsData = await cellsR.json();
  renderHeader(cellsData);
  const sel = document.getElementById('pub-cell-select');
  const prevValue = sel.value;
  sel.innerHTML = '';
  for(const c of cellsData.cells){
    const opt = document.createElement('option');
    opt.value = c.cell_id;
    opt.textContent = (c.alias || shortId(c.cell_id)) + '  ' + c.cell_id.slice(0,12) + '…';
    sel.appendChild(opt);
  }
  if(prevValue) sel.value = prevValue;

  const r = await fetch('/nevod-admin/api/published-cells');
  const data = await r.json();
  document.getElementById('pub-stat').textContent = data.cells.length + ' шт';
  const tbody = document.getElementById('pub-body');
  tbody.innerHTML = '';
  for(const p of data.cells){
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${esc(p.name)}</td>
      <td class="cell-id">${shortId(p.cell_id)}</td>
      <td>${esc(p.kind)}</td>
      <td>${esc((p.ai_providers || []).join(', ') || '—')}</td>
      <td>${esc(p.description || '—')}</td>
      <td>${ts(p.published_at)}</td>
      <td><button style="background:#3a1a1a;color:#f85149;font-family:monospace;font-size:11px;border:none;border-radius:4px;padding:3px 8px;cursor:pointer"
          onclick="unpublishCell('${esc(p.cell_id)}', this.closest('tr'))">Снять</button></td>`;
    tbody.appendChild(tr);
  }
  if(!data.cells.length) tbody.innerHTML='<tr><td colspan="7" style="color:#484f58;padding:12px 16px">нет опубликованных ячеек</td></tr>';
}
async function publishCell(){
  const cell_id = document.getElementById('pub-cell-select').value;
  const name = document.getElementById('pub-name').value.trim();
  const kind = document.getElementById('pub-kind').value;
  const description = document.getElementById('pub-desc').value.trim();
  const landing_md = document.getElementById('pub-landing').value;
  const ai_providers = kind === 'bot'
    ? [...document.querySelectorAll('.pub-ai:checked')].map(c => c.value) : [];
  const errBox = document.getElementById('pub-err');
  errBox.textContent = '';
  if(!cell_id || !name){ errBox.textContent = 'Выбери ячейку и укажи название'; return; }
  const r = await fetch('/nevod-admin/api/published-cells', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cell_id, name, kind, description, landing_md, ai_providers})
  });
  const data = await r.json();
  if(!data.ok){ errBox.textContent = 'Ошибка: ' + data.error; return; }
  document.getElementById('pub-name').value = '';
  document.getElementById('pub-desc').value = '';
  document.getElementById('pub-landing').value = '';
  document.querySelectorAll('.pub-ai').forEach(c => { c.checked = false; });
  await loadPublishedCells();
}
async function unpublishCell(cell_id, tr){
  if(!confirm('Снять с публикации?')) return;
  const r = await fetch('/nevod-admin/api/published-cells/' + encodeURIComponent(cell_id), {method:'DELETE'});
  if(r.ok) tr.remove(); else alert('Ошибка: ' + await r.text());
}

loadPublishedCells();
"""

# ── AI-боты ──────────────────────────────────────────────────────────────────

_BODY_AI_BOTS = """
<section>
  <h2>AI-боты этой ноды <span id="aib-stat" class="stat"></span>
    <button onclick="loadAIBots()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <div style="padding:10px 16px;color:#8b949e;font-size:12px;line-height:1.6">
    Бот работает внутри этой ноды и отвечает через Claude, ChatGPT или Gemini <b>на ключе пользователя</b>:
    ключ пользователь добавляет в чате с ботом, он приходит с каждым сообщением, бот его не хранит.
    У ноды своих ключей нет и платить ей за AI не нужно.<br>
    Включённый бот появляется в списке «На этой ноде» в приложении. Выключенный остановлен и скрыт, его имя остаётся за ним.<br>
    ⚠ Переписку с ботом расшифровывает код на этой ноде и передаёт выбранному провайдеру — так и сказано пользователям
    в <a href="https://nevod.network/xx/privacy/" style="color:#58a6ff">политике конфиденциальности</a> (раздел 5).
  </div>
  <table>
    <thead><tr><th>Имя</th><th>cell_id</th><th>Провайдеры</th><th>Состояние</th><th>Описание</th><th></th></tr></thead>
    <tbody id="aib-body"></tbody>
  </table>
  <div id="aib-err" class="err"></div>
</section>
<section>
  <h2 id="aib-form-title">Добавить бота</h2>
  <div style="padding:10px 16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
    <span style="color:#8b949e;font-size:12px">Готовые:</span>
    <button onclick="fillPreset('assistant')" style="background:#1a2a3a;color:#58a6ff">AI Assistant</button>
    <button onclick="fillPreset('tolmach')" style="background:#1a2a3a;color:#58a6ff">Толмач (переводчик)</button>
    <span style="color:#484f58;font-size:11px">— заполняют форму, перед сохранением можно изменить</span>
  </div>
  <div style="padding:0 16px 10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
    <input id="aib-name" placeholder="Имя бота" maxlength="64"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;width:180px">
    <input id="aib-desc" placeholder="Описание для пользователей" maxlength="280"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;flex:1;min-width:200px">
  </div>
  <div style="padding:0 16px 10px">
    <textarea id="aib-prompt" rows="6" maxlength="4000" placeholder="Инструкция для модели (system prompt): кто этот бот и как отвечает"
              style="width:100%;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:8px;border-radius:4px;font-family:monospace;box-sizing:border-box"></textarea>
  </div>
  <div style="padding:0 16px 10px;color:#8b949e;font-size:12px;display:flex;gap:14px;flex-wrap:wrap;align-items:center">
    Провайдеры, ключи которых бот принимает:
    <label><input type="checkbox" class="aib-p" value="anthropic" checked> Claude</label>
    <label><input type="checkbox" class="aib-p" value="openai" checked> ChatGPT</label>
    <label><input type="checkbox" class="aib-p" value="gemini" checked> Gemini</label>
  </div>
  <div style="padding:0 16px 14px;display:flex;gap:8px;align-items:center">
    <button id="aib-save" onclick="saveAIBot()" style="background:#1a3a1a;color:#3fb950">Добавить и включить</button>
    <button id="aib-cancel" onclick="resetForm()" style="display:none;background:#21262d;color:#8b949e">Отмена</button>
    <span id="aib-form-err" class="err"></span>
  </div>
</section>
"""

_SCRIPT_AI_BOTS = """
let aibPresets = {}, aibBots = [], aibEditing = null;
const AIB_STATE = {online:'🟢 работает', connecting:'🟡 подключается', off:'⚪ выключен'};
const AIB_NAMES = {anthropic:'Claude', openai:'ChatGPT', gemini:'Gemini'};
function aibBtn(color, bg, label, onclick){
  return `<button style="background:${bg};color:${color};font-family:monospace;font-size:11px;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;margin-right:4px" onclick="${onclick}">${label}</button>`;
}
async function loadAIBots(){
  const r = await fetch('/nevod-admin/api/ai-bots');
  const data = await r.json();
  aibPresets = data.presets; aibBots = data.bots;
  document.getElementById('aib-stat').textContent = data.bots.length + ' шт';
  const tbody = document.getElementById('aib-body');
  tbody.innerHTML = '';
  for(const b of data.bots){
    const id = esc(b.cell_id);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${esc(b.name)}</td>
      <td class="cell-id">${shortId(b.cell_id)}</td>
      <td>${esc(b.providers.map(p => AIB_NAMES[p] || p).join(', '))}</td>
      <td>${AIB_STATE[b.status] || esc(b.status)}</td>
      <td>${esc(b.description || '—')}</td>
      <td style="white-space:nowrap">
        ${b.enabled ? aibBtn('#d29922','#2a2210','Выключить',`setEnabled('${id}',false)`)
                    : aibBtn('#3fb950','#1a3a1a','Включить',`setEnabled('${id}',true)`)}
        ${aibBtn('#58a6ff','#1a2a3a','Изменить',`editBot('${id}')`)}
        ${aibBtn('#f85149','#3a1a1a','Удалить',`deleteBot('${id}')`)}
      </td>`;
    tbody.appendChild(tr);
  }
  if(!data.bots.length) tbody.innerHTML='<tr><td colspan="6" style="color:#484f58;padding:12px 16px">ботов нет — добавь готового или своего ниже</td></tr>';
}
function setForm(name, desc, prompt, providers){
  document.getElementById('aib-name').value = name;
  document.getElementById('aib-desc').value = desc;
  document.getElementById('aib-prompt').value = prompt;
  document.querySelectorAll('.aib-p').forEach(c => { c.checked = providers.includes(c.value); });
}
function fillPreset(key){
  const p = aibPresets[key]; if(!p) return;
  if(!aibEditing) setForm(p.name, p.description, p.system_prompt, ['anthropic','openai','gemini']);
  else document.getElementById('aib-prompt').value = p.system_prompt;
}
function editBot(cell_id){
  const b = aibBots.find(x => x.cell_id === cell_id); if(!b) return;
  aibEditing = cell_id;
  setForm(b.name, b.description, b.system_prompt, b.providers);
  document.getElementById('aib-form-title').textContent = 'Изменить «' + b.name + '»';
  document.getElementById('aib-save').textContent = 'Сохранить';
  document.getElementById('aib-cancel').style.display = '';
  document.getElementById('aib-name').scrollIntoView({behavior:'smooth'});
}
function resetForm(){
  aibEditing = null;
  setForm('', '', '', ['anthropic','openai','gemini']);
  document.getElementById('aib-form-title').textContent = 'Добавить бота';
  document.getElementById('aib-save').textContent = 'Добавить и включить';
  document.getElementById('aib-cancel').style.display = 'none';
  document.getElementById('aib-form-err').textContent = '';
}
async function saveAIBot(){
  const body = {
    name: document.getElementById('aib-name').value.trim(),
    description: document.getElementById('aib-desc').value.trim(),
    system_prompt: document.getElementById('aib-prompt').value.trim(),
    providers: [...document.querySelectorAll('.aib-p:checked')].map(c => c.value),
  };
  const errEl = document.getElementById('aib-form-err');
  errEl.textContent = '';
  const url = '/nevod-admin/api/ai-bots' + (aibEditing ? '/' + encodeURIComponent(aibEditing) : '');
  const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const data = await r.json();
  if(!data.ok){ errEl.textContent = 'Ошибка: ' + data.error; return; }
  resetForm();
  await loadAIBots();
  setTimeout(loadAIBots, 2500);   // "подключается" -> "работает"
}
async function setEnabled(cell_id, enabled){
  const r = await fetch('/nevod-admin/api/ai-bots/' + encodeURIComponent(cell_id) + '/enabled', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({enabled})});
  const data = await r.json();
  document.getElementById('aib-err').textContent = data.ok ? '' : 'Ошибка: ' + data.error;
  await loadAIBots();
  if(enabled) setTimeout(loadAIBots, 2500);
}
async function deleteBot(cell_id){
  const b = aibBots.find(x => x.cell_id === cell_id);
  if(!confirm('Удалить бота «' + (b ? b.name : cell_id) + '» навсегда? Его ключи и имя будут удалены; переписка у пользователей останется, но бот больше не ответит.')) return;
  const r = await fetch('/nevod-admin/api/ai-bots/' + encodeURIComponent(cell_id), {method:'DELETE'});
  const data = await r.json();
  document.getElementById('aib-err').textContent = data.ok ? '' : 'Ошибка: ' + data.error;
  if(aibEditing === cell_id) resetForm();
  await loadAIBots();
}

loadHeader();
loadAIBots();
"""

# ── Безопасность ──────────────────────────────────────────────────────────────

_BODY_SECURITY = """
<section>
  <h2>Администраторы панели <span id="admins-stat" class="stat"></span>
    <button onclick="loadAdmins()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">обновить</button>
  </h2>
  <div id="fallback-note" style="padding:10px 16px;font-size:11px;color:#8b949e"></div>
  <div style="padding:10px 16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
    <input id="admin-username" placeholder="Логин" autocomplete="off"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;width:160px">
    <input id="admin-password" placeholder="Пароль (мин. 8 символов)" type="password" autocomplete="new-password"
           style="background:#0d1117;color:#c9d1d9;border:1px solid #30363d;padding:6px;border-radius:4px;width:200px">
    <button onclick="addAdmin()" style="background:#1a3a1a;color:#3fb950">Добавить / сменить пароль</button>
    <span id="admin-add-err" class="err"></span>
  </div>
  <table>
    <thead><tr><th>Логин</th><th>Добавлен</th><th></th></tr></thead>
    <tbody id="admins-body"></tbody>
  </table>
</section>
"""

_SCRIPT_SECURITY = """
async function loadAdmins(){
  const r = await fetch('/nevod-admin/api/admins');
  const data = await r.json();
  document.getElementById('admins-stat').textContent = data.admins.length + ' шт';
  document.getElementById('fallback-note').textContent = data.fallback_username
    ? 'Основной вход (' + data.fallback_username + ' / NEVOD_ADMIN_PASSWORD) работает всегда, даже если этот список пуст.'
    : 'Основной вход по паролю (NEVOD_ADMIN_PASSWORD, без логина) работает всегда, даже если этот список пуст.';
  const tbody = document.getElementById('admins-body');
  tbody.innerHTML = '';
  for(const a of data.admins){
    const uname = esc(a.username);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${uname}</td>
      <td>${ts(a.created_at)}</td>
      <td><button style="background:#3a1a1a;color:#f85149;font-family:monospace;font-size:11px;border:none;border-radius:4px;padding:3px 8px;cursor:pointer"
          onclick="deleteAdmin('${uname}', this.closest('tr'))">Удалить</button></td>`;
    tbody.appendChild(tr);
  }
  if(!data.admins.length) tbody.innerHTML='<tr><td colspan="3" style="color:#484f58;padding:12px 16px">нет отдельных логинов</td></tr>';
}

async function addAdmin(){
  const username = document.getElementById('admin-username').value.trim();
  const password = document.getElementById('admin-password').value;
  const errEl = document.getElementById('admin-add-err');
  errEl.textContent = '';
  const r = await fetch('/nevod-admin/api/admins', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({username, password})
  });
  const data = await r.json();
  if(!data.ok){ errEl.textContent = 'Ошибка: ' + data.error; return; }
  document.getElementById('admin-username').value = '';
  document.getElementById('admin-password').value = '';
  loadAdmins();
}

async function deleteAdmin(username, tr){
  if(!confirm('Удалить логин «' + username + '»?')) return;
  const r = await fetch('/nevod-admin/api/admins/' + encodeURIComponent(username), {method:'DELETE'});
  if(r.ok) tr.remove(); else alert('Ошибка: ' + await r.text());
}

loadHeader();
loadAdmins();
"""

# ── Диагностика ───────────────────────────────────────────────────────────────

_BODY_DIAGNOSTICS = """
<section>
  <h2>Самодиагностика
    <button id="diag-btn" onclick="runDiagnostics()" style="background:#1a2a3a;color:#58a6ff;margin-left:auto">Проверить</button>
  </h2>
  <div id="diag-body">
    <div class="diag-row" style="color:#484f58">Нажмите «Проверить» — займёт до ~10 секунд (проверка внешней доступности ждёт ответ пира).</div>
  </div>
  <div id="diag-err" class="err"></div>
</section>

<section>
  <h2>Логи <button onclick="loadLogs()" style="background:#1a2a3a;color:#58a6ff;margin-left:8px">обновить</button></h2>
  <div id="logs-box">...</div>
</section>
"""

_SCRIPT_DIAGNOSTICS = """
async function runDiagnostics(){
  const btn = document.getElementById('diag-btn');
  const body = document.getElementById('diag-body');
  const err = document.getElementById('diag-err');
  err.textContent = '';
  btn.disabled = true;
  body.innerHTML = '<div class="diag-row" style="color:#484f58">Проверяю…</div>';
  try{
    const r = await fetch('/nevod-admin/api/diagnostics');
    const data = await r.json();
    body.innerHTML = '';
    for(const c of data.checks){
      const row = document.createElement('div');
      row.className = 'diag-row ' + c.status;
      row.innerHTML = `<span class="dot"></span><b>${esc(c.label)}</b>
        <div class="diag-detail">${esc(c.detail)}</div>`;
      body.appendChild(row);
    }
  }catch(e){
    err.textContent = 'Не удалось получить результаты: ' + e;
    body.innerHTML = '';
  }finally{
    btn.disabled = false;
  }
}

async function loadLogs(){
  const r = await fetch('/nevod-admin/api/logs');
  const data = await r.json();
  const box = document.getElementById('logs-box');
  box.textContent = data.lines.join('\\n');
  box.scrollTop = box.scrollHeight;
}

loadHeader();
loadLogs();
setInterval(loadLogs, 10000);
"""
# ─── Admin server ─────────────────────────────────────────────────────────────

class AdminServer:
    def __init__(self, node: "Node", password: str, username: str | None = None,
                 identity_path: str | None = None):
        self._node = node
        self._password = password
        # None preserves the historical password-only check (production VPS
        # deployment via NEVOD_ADMIN_PASSWORD has no username concept) — only
        # the installer-driven local node supplies both and gets both checked.
        self._username = username or None
        self._runner = None
        # Needed to persist admin-panel identity edits (e.g. cells_visibility)
        # back to disk — Node itself doesn't retain the path it was loaded
        # from. None (unlikely: only if a caller doesn't pass it) means such
        # edits apply live but don't survive a restart.
        self._identity_path = identity_path

    async def _check_auth(self, request: web.Request) -> bool:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            user, pwd = decoded.split(":", 1)
        except Exception:
            return False
        # Legacy single shared credential (NEVOD_ADMIN_PASSWORD, or the installer's
        # username+password for a local node) — kept as a permanent break-glass
        # login so the per-admin list below can never lock everyone out (an empty
        # admin_users table right after an upgrade, a bad row, etc).
        if (self._username is None or user == self._username) \
                and hmac.compare_digest(pwd, self._password):
            return True
        # Individually managed accounts from the Безопасность page — hashed,
        # stored in this node's own DB (storage.py's admin_users table).
        stored_hash = await self._node.storage.get_admin_password_hash(user)
        return bool(stored_hash) and _verify_password(pwd, stored_hash)

    @web.middleware
    async def _auth_middleware(self, request: web.Request, handler):
        if request.path.startswith("/nevod-card") or request.path.startswith("/nevod-update"):
            return await handler(request)
        if not await self._check_auth(request):
            return web.Response(
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="Nevod Admin"'},
                text="Unauthorized",
            )
        return await handler(request)

    async def _handle_page_overview(self, _req):
        return web.Response(text=_shell("", _BODY_OVERVIEW, _SCRIPT_OVERVIEW),
                             content_type="text/html")

    async def _handle_page_settings(self, _req):
        return web.Response(text=_shell("settings", _BODY_SETTINGS, _SCRIPT_SETTINGS),
                             content_type="text/html")

    async def _handle_page_security(self, _req):
        return web.Response(text=_shell("security", _BODY_SECURITY, _SCRIPT_SECURITY),
                             content_type="text/html")

    async def _handle_page_join_requests(self, _req):
        return web.Response(
            text=_shell("join-requests", _BODY_JOIN_REQUESTS, _SCRIPT_JOIN_REQUESTS),
            content_type="text/html")

    async def _handle_page_appeals(self, _req):
        return web.Response(text=_shell("appeals", _BODY_APPEALS, _SCRIPT_APPEALS),
                             content_type="text/html")

    async def _handle_list_appeals(self, _req):
        return web.json_response({"threads": await self._node.storage.list_appeal_threads()})

    async def _handle_get_appeal_thread(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        thread = await self._node.storage.get_appeal_thread(cell_id)
        await self._node.storage.mark_appeals_seen(cell_id)
        return web.json_response({"messages": [
            {"direction": m.direction, "text": m.text, "created_at": m.created_at}
            for m in thread]})

    async def _handle_reply_appeal(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        data = await request.json()
        text = str(data.get("text", "")).strip()
        if not text:
            return web.json_response({"ok": False, "error": "пустой ответ"}, status=400)
        if len(text) > 4000:
            return web.json_response({"ok": False, "error": "слишком длинный ответ"}, status=400)
        ok = await self._node.reply_as_administrator(cell_id, text)
        if not ok:
            return web.json_response(
                {"ok": False, "error": "нет ключа шифрования этого пользователя"}, status=400)
        log.info("admin: appeal reply sent to %s", cell_id[:8])
        return web.json_response({"ok": True})

    async def _handle_get_diag_log(self, request: web.Request):
        import zlib
        try:
            log_id = int(request.match_info["log_id"])
        except ValueError:
            raise web.HTTPNotFound()
        row = await self._node.storage.get_diag_log(log_id)
        if not row:
            raise web.HTTPNotFound()
        cell_id, created_at, packed = row
        raw = zlib.decompress(packed, -15)
        day = time.strftime("%Y-%m-%d_%H%M", time.gmtime(created_at))
        return web.Response(body=raw, content_type="text/plain", charset="utf-8", headers={
            "Content-Disposition": f'attachment; filename="nevod-{cell_id[:8]}-{day}.log"'})

    async def _handle_administrator_info(self, _req):
        return web.json_response(self._node.administrator_info() or {})

    async def _handle_page_invites(self, _req):
        return web.Response(text=_shell("invites", _BODY_INVITES, _SCRIPT_INVITES),
                             content_type="text/html")

    async def _handle_page_nodes(self, _req):
        return web.Response(text=_shell("nodes", _BODY_NODES, _SCRIPT_NODES),
                             content_type="text/html")

    async def _handle_page_published(self, _req):
        return web.Response(text=_shell("published", _BODY_PUBLISHED, _SCRIPT_PUBLISHED),
                             content_type="text/html")

    async def _handle_page_ai_bots(self, _req):
        return web.Response(text=_shell("ai-bots", _BODY_AI_BOTS, _SCRIPT_AI_BOTS),
                             content_type="text/html")

    # --- AI bots run inside the node (node/ai_bots.py) ---

    async def _handle_list_ai_bots(self, _req):
        from .ai_bots import PRESETS
        mgr = self._node.ai_bots
        bots = await self._node.storage.list_ai_bots() if mgr else []
        return web.json_response({
            "presets": PRESETS,
            "bots": [{
                "cell_id": b.cell_id, "name": b.name, "description": b.description,
                "system_prompt": b.system_prompt, "providers": b.providers,
                "enabled": b.enabled, "status": mgr.status(b.cell_id),
                "created_at": b.created_at,
            } for b in bots],
        })

    async def _ai_bot_call(self, action):
        """Runs action(manager); an AIBotError becomes {"ok": false, "error": text for the admin}."""
        from .ai_bots import AIBotError
        if self._node.ai_bots is None:
            return web.json_response({"ok": False, "error": "AI-боты недоступны на этой ноде"},
                                     status=400)
        try:
            await action(self._node.ai_bots)
        except AIBotError as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)
        return web.json_response({"ok": True})

    @staticmethod
    def _ai_bot_fields(data: dict):
        providers = data.get("providers") or []
        if not isinstance(providers, list):
            providers = []
        return (str(data.get("name", "")), str(data.get("description", "")),
                str(data.get("system_prompt", "")), [str(p) for p in providers])

    async def _handle_create_ai_bot(self, request: web.Request):
        fields = self._ai_bot_fields(await request.json())
        return await self._ai_bot_call(lambda m: m.create(*fields))

    async def _handle_update_ai_bot(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        fields = self._ai_bot_fields(await request.json())
        return await self._ai_bot_call(lambda m: m.update(cell_id, *fields))

    async def _handle_set_ai_bot_enabled(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        enabled = bool((await request.json()).get("enabled"))
        return await self._ai_bot_call(lambda m: m.set_enabled(cell_id, enabled))

    async def _handle_delete_ai_bot(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        return await self._ai_bot_call(lambda m: m.delete(cell_id))

    async def _handle_page_diagnostics(self, _req):
        return web.Response(text=_shell("diagnostics", _BODY_DIAGNOSTICS, _SCRIPT_DIAGNOSTICS),
                             content_type="text/html")

    async def _handle_cells(self, _req):
        storage = self._node.storage
        cells = await storage.list_cells()
        buf_counts = await storage.buffer_count()
        connected_ids = {c.peer_node_id for c in await self._node.transport.connections.all()}

        return web.json_response({
            "node_id":          self._node.identity.node_id,
            "node_name":        self._node.identity.name,
            "node_type":        self._node.identity.node_type,
            "parent_node_id":   self._node.identity.parent_node_id,
            "address":          self._node.identity.address,
            "invite_mode":      self._node.identity.invite_mode,
            "admin_cell_ids":   self._node.identity.admin_cell_ids,
            "access":           self._node.identity.access,
            "cells_visibility": self._node.identity.cells_visibility,
            "cells": [
                {
                    "cell_id":       c.cell_id,
                    "alias":         c.display_name,
                    "online":        c.cell_id in connected_ids,
                    "buffered":      buf_counts.get(c.cell_id, 0),
                    "registered_at": c.registered_at,
                    "is_home":       c.is_home,
                }
                for c in cells
            ],
        })

    async def _handle_set_alias(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        data = await request.json()
        alias = str(data.get("alias", "")).strip()
        await self._node.storage.set_display_name(cell_id, alias)
        return web.json_response({"ok": True})

    async def _handle_delete_cell(self, request: web.Request):
        from .protocol import Packet, T, encode_payload, sign_packet
        cell_id = request.match_info["cell_id"]
        if self._node.ai_bots and await self._node.storage.get_ai_bot(cell_id):
            # Stop it first, or its runner would just reconnect and register again.
            await self._node.ai_bots.delete(cell_id)
        await self._node.storage.delete_cell(cell_id)
        conn = await self._node.transport.connections.get(cell_id)
        if conn:
            try:
                pkt = Packet(type=T.CELL_REMOVED,
                             payload=encode_payload({"reason": "admin_deleted"}),
                             from_addr=self._node.identity.node_id, to_addr=cell_id)
                sign_packet(pkt, self._node.identity.signing)
                await self._node.transport.send_via(conn, pkt)
            except Exception:
                pass
            await conn.close()
        log.info("admin: deleted cell %s", cell_id[:16])
        return web.json_response({"ok": True})

    async def _handle_wipe_all(self, _req):
        await self._node.storage.wipe_all()
        for conn in await self._node.transport.connections.all():
            try:
                await conn.close()
            except Exception:
                pass
        log.warning("admin: wiped all cells and buffers")
        return web.json_response({"ok": True})

    async def _handle_reset_registrations(self, _req):
        """Close all WSs and wipe cells/presence/buffers but keep allowed_cells."""
        for conn in await self._node.transport.connections.all():
            try:
                await conn.close()
            except Exception:
                pass
        await self._node.storage.wipe_registrations()
        log.warning("admin: reset registrations (allowed_cells preserved)")
        return web.json_response({"ok": True})

    async def _handle_full_reset(self, _req):
        """Wipe everything including allowed_cells — all users must re-invite."""
        for conn in await self._node.transport.connections.all():
            try:
                await conn.close()
            except Exception:
                pass
        await self._node.storage.full_reset()
        log.warning("admin: full reset — all registrations and invites cleared")
        return web.json_response({"ok": True})

    def _invite_link(self, code: str) -> str:
        from .protocol import make_cell_invite_token, make_cell_invite_link
        address, fingerprint = self._node._public_client_endpoint()
        return make_cell_invite_link(make_cell_invite_token(address, fingerprint, code))

    async def _handle_create_invite(self, req):
        from .protocol import make_cell_invite_token, make_cell_invite_link
        from .storage import CELL_INVITE_TTL_SECS, CELL_INVITE_TTL_CHOICES
        ttl = CELL_INVITE_TTL_SECS
        if req.can_read_body:
            try:
                ttl = int((await req.json()).get("ttl_secs", ttl))
            except Exception:
                return web.json_response({"ok": False, "error": "bad request"}, status=400)
        if ttl not in CELL_INVITE_TTL_CHOICES:
            return web.json_response({"ok": False, "error": "ttl_secs not allowed"}, status=400)
        code = await self._node.storage.create_invite(created_by="admin", ttl_secs=ttl)
        expires_at = int(time.time()) + ttl
        address, fingerprint = self._node._public_client_endpoint()
        token = make_cell_invite_token(address, fingerprint, code)
        log.info("admin: created invite code %s (ttl %d h)", code, ttl // 3600)
        return web.json_response({"ok": True, "code": code, "token": token,
                                  "link": make_cell_invite_link(token), "expires_at": expires_at})

    async def _handle_list_invites(self, _req):
        invites = await self._node.storage.list_invites()
        return web.json_response({
            "invites": [
                {
                    "code":       inv.code,
                    "link":       self._invite_link(inv.code),
                    "created_by": inv.created_by,
                    "created_at": inv.created_at,
                    "expires_at": inv.expires_at,
                    "used":       inv.used,
                    "used_by":    inv.used_by,
                }
                for inv in invites
            ]
        })

    async def _handle_list_published_cells(self, _req):
        published = await self._node.storage.get_published_cells()
        return web.json_response({
            "cells_visibility": self._node.identity.cells_visibility,
            "cells": [
                {
                    "cell_id":       p.cell_id,
                    "name":          p.name,
                    "description":   p.description,
                    "kind":          p.kind,
                    "landing_md":    p.landing_md,
                    "ai_providers":  p.ai_providers,
                    "published_at":  p.published_at,
                }
                for p in published
            ],
        })

    async def _handle_publish_cell(self, request: web.Request):
        """Admin explicitly opts a cell into the "Explore Network" cell/moon list —
        separate from CELL_REGISTER, which merely makes a cell exist on this node at
        all. See PublishedCellEntry in storage.py for why these are different tables."""
        data = await request.json()
        cell_id = str(data.get("cell_id", "")).strip()
        name = str(data.get("name", "")).strip()
        if not cell_id or not name:
            return web.json_response({"ok": False, "error": "cell_id and name required"},
                                     status=400)
        kind = str(data.get("kind", "bot")).strip()
        if kind not in ("bot", "page"):
            return web.json_response({"ok": False, "error": "kind must be 'bot' or 'page'"},
                                     status=400)
        description = str(data.get("description", "")).strip()
        landing_md = str(data.get("landing_md", ""))
        from .ai_providers import PROVIDERS
        ai_providers = data.get("ai_providers") or []
        if (kind != "bot" and ai_providers) or not isinstance(ai_providers, list) \
                or any(p not in PROVIDERS for p in ai_providers):
            return web.json_response(
                {"ok": False, "error": f"ai_providers: bot only, any of {', '.join(PROVIDERS)}"},
                status=400)
        ai_providers = [p for p in PROVIDERS if p in ai_providers]   # canonical order, no dups
        await self._node.storage.publish_cell(cell_id, name, description, kind, landing_md,
                                              ai_providers)
        log.info("admin: published cell %s (%s)", cell_id[:16], kind)
        return web.json_response({"ok": True})

    async def _handle_unpublish_cell(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        await self._node.storage.unpublish_cell(cell_id)
        log.info("admin: unpublished cell %s", cell_id[:16])
        return web.json_response({"ok": True})

    async def _handle_set_access(self, request: web.Request):
        """Mirrors nevod.py's `set-access` CLI command exactly (same identity field, same
        persistence) — just reachable from the web UI too. Unlike cells_visibility, this does
        NOT take effect live: node.py's start() is the only place that re-propagates
        identity.access into node_table (see Storage.refresh_own_node_flags's own comment on
        why upsert_node deliberately never touches it) — so this only writes the identity file,
        the caller is told a restart is still required, same as the CLI's own echo message."""
        data = await request.json()
        access = str(data.get("access", "")).strip()
        if access not in ("open", "closed"):
            return web.json_response(
                {"ok": False, "error": "access must be 'open' or 'closed'"}, status=400)
        self._node.identity.access = access
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        log.info("admin: access set to '%s' (restart required to apply)", access)
        return web.json_response({"ok": True, "restart_required": True})

    async def _handle_set_name(self, request: web.Request):
        """Human-friendly node label (e.g. "Dev Planet") — shown in the panel's own
        header immediately (renderHeader reads it straight from /api/cells, which
        reads the live identity object), but only reaches node_table (what OTHER
        nodes actually see gossiped) on the next restart, same as access/node_type
        — Node.start() is the only place that re-propagates it. Found 2026-09-13:
        there was no way to set this at all before — a node with no name set just
        showed its raw node_id in the panel, which is how node1 ended up admin'd
        for weeks with nothing marking it as "Dev Planet" anywhere in the UI."""
        data = await request.json()
        name = str(data.get("name", "")).strip()[:64]
        self._node.identity.name = name
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        log.info("admin: node name set to %r", name)
        return web.json_response({"ok": True})

    async def _handle_set_node_type(self, request: web.Request):
        """Same shape as _handle_set_access right above — mirrors nevod.py init's
        `--type` choice, just reachable (and changeable after the fact) from the web
        UI. Also does NOT take effect live: Node.start() is the only place that
        re-propagates identity.node_type into node_table (see node.py's own comment on
        the 2026-09-13 bug where it used to silently re-feed the OLD stored value
        instead, making this a permanent no-op — fixed alongside adding this
        endpoint), so this only writes the identity file; a restart is still required."""
        data = await request.json()
        node_type = str(data.get("node_type", "")).strip()
        if node_type not in ("permanent", "temporary"):
            return web.json_response(
                {"ok": False, "error": "node_type must be 'permanent' or 'temporary'"},
                status=400)
        self._node.identity.node_type = node_type
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        log.info("admin: node_type set to '%s' (restart required to apply)", node_type)
        return web.json_response({"ok": True, "restart_required": True})

    async def _handle_set_parent_node_id(self, request: web.Request):
        """Only meaningful when node_type="temporary" (a child node) — see
        _handle_cell_register's "Child node: tell parent..." check, which reads
        self.identity.parent_node_id straight off the live identity object, not
        node_table. That means this specific behavior (whether a newly-registered
        cell here triggers a CHILD_PRESENCE_UPDATE to the parent) takes effect
        IMMEDIATELY — no restart needed, unlike node_type/access/name above.
        Doesn't validate the value is a real, reachable node_id — same trust level
        as everything else on this password-gated panel; an unreachable/bogus
        parent just means that notification silently goes nowhere, same as any
        other node the router can't currently connect to. Empty string clears it."""
        data = await request.json()
        parent_node_id = str(data.get("parent_node_id", "")).strip()
        self._node.identity.parent_node_id = parent_node_id
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        log.info("admin: parent_node_id set to %r",
                 parent_node_id[:16] + "…" if parent_node_id else "(cleared)")
        return web.json_response({"ok": True})

    async def _handle_set_cells_visibility(self, request: web.Request):
        """Who can query this node's published-cells list — see NodeIdentity.
        cells_visibility's own docstring for what each value means. Applied to
        the live identity object immediately (unlike `access`/`invite_mode`,
        this field has no other startup-time side effect to redo — it's read
        fresh on every NODE_CELLS_REQUEST) and persisted to disk so it survives
        a restart too."""
        data = await request.json()
        visibility = str(data.get("cells_visibility", "")).strip()
        if visibility not in ("off", "members", "public"):
            return web.json_response(
                {"ok": False, "error": "cells_visibility must be 'off', 'members', or 'public'"},
                status=400)
        self._node.identity.cells_visibility = visibility
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        log.info("admin: cells_visibility set to '%s'", visibility)
        return web.json_response({"ok": True})

    async def _handle_set_invite_mode(self, request: web.Request):
        """Read fresh on every CELL_REGISTER/INVITE_CREATE/JOIN_REQUEST (node.py never
        caches it at startup the way it does `access` into node_table) — applies live,
        same as cells_visibility, no restart needed."""
        data = await request.json()
        mode = str(data.get("invite_mode", "")).strip()
        if mode not in ("open", "admin", "delegated"):
            return web.json_response(
                {"ok": False, "error": "invite_mode must be 'open', 'admin', or 'delegated'"},
                status=400)
        self._node.identity.invite_mode = mode
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        # _ensure_registrar() normally only runs once, at node startup — gated on
        # invite_mode=="admin" there specifically (see its own doc comment). Switching
        # into "admin" live, from here, without a restart in between, used to leave
        # self._registrar_identity permanently None for the rest of that process's
        # life: _notify_admins silently no-ops without it, so a real join request
        # could come in and get approved with the admin never actually notified in
        # their Nevod chat. Found 2026-09-13 tracing exactly that: the admin's account
        # never got a message for a request that arrived shortly after this same
        # live flip. Idempotent — safe to call again even if it already ran at startup.
        await self._node._ensure_registrar()
        log.info("admin: invite_mode set to '%s'", mode)
        return web.json_response({"ok": True})

    async def _handle_set_admin_cells(self, request: web.Request):
        """Full replace of NodeIdentity.admin_cell_ids — the list of cells notified on
        a JOIN_REQUEST (invite_mode="admin"). Editable only here, with the panel
        password — see admin_cell_ids' own doc comment on why there's no separate
        "owner" concept."""
        data = await request.json()
        cell_ids = data.get("admin_cell_ids", [])
        if not isinstance(cell_ids, list) or not all(isinstance(c, str) for c in cell_ids):
            return web.json_response(
                {"ok": False, "error": "admin_cell_ids must be a list of strings"}, status=400)
        self._node.identity.admin_cell_ids = cell_ids
        if self._identity_path:
            self._node.identity.save(self._identity_path)
        log.info("admin: admin_cell_ids set to %d cell(s)", len(cell_ids))
        return web.json_response({"ok": True})

    async def _handle_list_join_requests(self, _req):
        pending = await self._node.storage.list_join_requests(status="pending")
        return web.json_response({
            "requests": [
                {
                    "cell_id":      r.cell_id,
                    "display_name": r.display_name,
                    "note":         r.note,
                    "created_at":   r.created_at,
                }
                for r in pending
            ]
        })

    async def _handle_approve_join_request(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        ok = await self._node.approve_join_request(cell_id)
        if not ok:
            return web.json_response({"ok": False, "error": "no pending request"}, status=404)
        return web.json_response({"ok": True})

    async def _handle_deny_join_request(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        ok = await self._node.deny_join_request(cell_id)
        if not ok:
            return web.json_response({"ok": False, "error": "no pending request"}, status=404)
        return web.json_response({"ok": True})

    async def _handle_list_nodes(self, _req):
        nodes = await self._node.storage.get_all_nodes()
        return web.json_response({
            "nodes": [
                {
                    "node_id":   n.node_id,
                    "name":      n.name,
                    "address":   n.address,
                    "status":    n.status,
                    "type":      n.type,
                    "last_seen": n.last_seen,
                }
                for n in nodes
            ]
        })

    async def _handle_diagnostics(self, _req):
        from .diagnostics import run_diagnostics
        checks = await run_diagnostics(self._node)
        return web.json_response({"checks": checks})

    async def _handle_join_node(self, request: web.Request):
        """Join this already-running node to another network by invite token —
        node.join() was previously only ever called once, at initial startup
        (nevod.py join / the installer wizard); there was no way to introduce
        two nodes that were both already up and running to each other."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"ok": False, "error": "invalid JSON body"}, status=400)
        token = str(body.get("token", "")).strip()
        bootstrap = str(body.get("address", "")).strip()
        fingerprint = str(body.get("fingerprint", "")).strip() or None
        invite_code = None
        if token:
            from .protocol import parse_node_invite_token
            try:
                bootstrap, fingerprint, invite_code = parse_node_invite_token(token)
            except ValueError as e:
                return web.json_response({"ok": False, "error": str(e)}, status=400)
        if not bootstrap:
            return web.json_response({"ok": False, "error": "address or token required"}, status=400)
        try:
            reachable = await self._node.join(bootstrap, expected_fingerprint=fingerprint,
                                              invite_code=invite_code)
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=400)
        return web.json_response({"ok": True, "reachable": reachable})

    async def _handle_create_node_invite(self, _req):
        from .protocol import make_node_invite_token
        code = await self._node.storage.create_node_invite(created_by=self._node.identity.node_id)
        expires_at = int(time.time()) + 600
        token = make_node_invite_token(
            self._node.identity.address, self._node.identity.tls_fingerprint, code,
        )
        log.info("admin: created node invite code %s", code)
        return web.json_response({"ok": True, "code": code, "token": token, "expires_at": expires_at})

    async def _handle_list_node_invites(self, _req):
        invites = await self._node.storage.list_node_invites()
        return web.json_response({
            "invites": [
                {
                    "code":       inv.code,
                    "created_by": inv.created_by,
                    "created_at": inv.created_at,
                    "expires_at": inv.expires_at,
                    "used":       inv.used,
                    "used_by":    inv.used_by,
                }
                for inv in invites
            ]
        })

    async def _handle_list_allowed(self, _req):
        cells = await self._node.storage.list_allowed_cells()
        return web.json_response({
            "cells": [
                {
                    "cell_id":        c.cell_id,
                    "display_name":   c.display_name,
                    "invited_by":     c.invited_by,
                    "invited_by_name": c.invited_by_name,
                    "joined_at":      c.joined_at,
                    "can_invite":     c.can_invite,
                }
                for c in cells
            ]
        })

    async def _handle_toggle_invite_right(self, request: web.Request):
        cell_id = request.match_info["cell_id"]
        data = await request.json()
        action = data.get("action", "grant")
        if action == "grant":
            await self._node.storage.grant_invite_right(cell_id)
        else:
            await self._node.storage.revoke_invite_right(cell_id)
        log.info("admin: %s invite right for %s", action, cell_id[:16])
        return web.json_response({"ok": True})

    async def _handle_logs(self, _req):
        return web.json_response({"lines": _ring.lines()})

    # ── Admin panel logins (Безопасность page) ──────────────────────────────────

    async def _handle_list_admins(self, _req):
        users = await self._node.storage.list_admin_users()
        return web.json_response({
            "admins": [{"username": u.username, "created_at": u.created_at} for u in users],
            # So the page can explain, not just assert, that this account can never
            # be locked out — see _check_auth's own comment.
            "fallback_username": self._username,
        })

    async def _handle_set_admin(self, request: web.Request):
        """Add a new admin, or change an existing one's password — same write
        either way (storage.set_admin_password is an upsert)."""
        data = await request.json()
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))
        if not username or not password:
            return web.json_response(
                {"ok": False, "error": "username and password are required"}, status=400)
        if len(password) < 8:
            return web.json_response(
                {"ok": False, "error": "password must be at least 8 characters"}, status=400)
        await self._node.storage.set_admin_password(username, _hash_password(password))
        log.info("admin: panel login set for %r", username)
        return web.json_response({"ok": True})

    async def _handle_delete_admin(self, request: web.Request):
        username = request.match_info["username"]
        await self._node.storage.delete_admin_user(username)
        log.info("admin: panel login removed for %r", username)
        return web.json_response({"ok": True})

    async def _handle_card_lookup(self, request: web.Request):
        """Public endpoint (no auth) — resolve short card code to cell_id + enc_pub."""
        code = request.match_info["code"].strip().upper()
        card = await self._node.storage.lookup_contact_card(code)
        if not card:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response(card)

    # Public (no auth) fallback transport for update_checker.py — hands out THIS
    # node's own local copy of RELEASE.json/RELEASE.sig, whatever that currently
    # is (could itself be behind). No auth needed: the requester independently
    # verifies the Ed25519 signature against the hardcoded maintainer public key
    # before trusting anything, so serving this to anyone who asks reveals
    # nothing sensitive and can't be used to push a fake update — a forged or
    # stale response just fails verification on the requester's side.
    async def _handle_release_json(self, _req):
        path = _repo_root() / "RELEASE.json"
        if not path.exists():
            return web.json_response({"error": "not_found"}, status=404)
        return web.Response(body=path.read_bytes(), content_type="application/json")

    async def _handle_release_sig(self, _req):
        path = _repo_root() / "RELEASE.sig"
        if not path.exists():
            return web.json_response({"error": "not_found"}, status=404)
        return web.Response(body=path.read_bytes(), content_type="text/plain")

    def _make_app(self) -> web.Application:
        app = web.Application(middlewares=[self._auth_middleware])
        app.router.add_get("/nevod-admin",                                          self._handle_page_overview)
        app.router.add_get("/nevod-admin/",                                         self._handle_page_overview)
        app.router.add_get("/nevod-admin/settings",                                 self._handle_page_settings)
        app.router.add_get("/nevod-admin/join-requests",                            self._handle_page_join_requests)
        app.router.add_get("/nevod-admin/invites",                                  self._handle_page_invites)
        app.router.add_get("/nevod-admin/appeals",                                  self._handle_page_appeals)
        app.router.add_get("/nevod-admin/api/appeals",                              self._handle_list_appeals)
        app.router.add_get("/nevod-admin/api/appeals/{cell_id}",                    self._handle_get_appeal_thread)
        app.router.add_post("/nevod-admin/api/appeals/{cell_id}/reply",             self._handle_reply_appeal)
        app.router.add_get("/nevod-admin/api/administrator",                        self._handle_administrator_info)
        app.router.add_get("/nevod-admin/api/diag-logs/{log_id}",                   self._handle_get_diag_log)
        app.router.add_get("/nevod-admin/nodes",                                    self._handle_page_nodes)
        app.router.add_get("/nevod-admin/published",                                self._handle_page_published)
        app.router.add_get("/nevod-admin/ai-bots",                                  self._handle_page_ai_bots)
        app.router.add_get("/nevod-admin/api/ai-bots",                              self._handle_list_ai_bots)
        app.router.add_post("/nevod-admin/api/ai-bots",                             self._handle_create_ai_bot)
        app.router.add_post("/nevod-admin/api/ai-bots/{cell_id}",                   self._handle_update_ai_bot)
        app.router.add_post("/nevod-admin/api/ai-bots/{cell_id}/enabled",           self._handle_set_ai_bot_enabled)
        app.router.add_delete("/nevod-admin/api/ai-bots/{cell_id}",                 self._handle_delete_ai_bot)
        app.router.add_get("/nevod-admin/security",                                 self._handle_page_security)
        app.router.add_get("/nevod-admin/diagnostics",                              self._handle_page_diagnostics)
        app.router.add_get("/nevod-admin/api/cells",                                self._handle_cells)
        app.router.add_post("/nevod-admin/api/cells/{cell_id}/alias",               self._handle_set_alias)
        app.router.add_delete("/nevod-admin/api/cells/{cell_id}",                   self._handle_delete_cell)
        app.router.add_delete("/nevod-admin/api/cells",                             self._handle_wipe_all)
        app.router.add_post("/nevod-admin/api/reset/registrations",                 self._handle_reset_registrations)
        app.router.add_post("/nevod-admin/api/reset/full",                          self._handle_full_reset)
        app.router.add_post("/nevod-admin/api/invites",                             self._handle_create_invite)
        app.router.add_get("/nevod-admin/api/invites",                              self._handle_list_invites)
        app.router.add_post("/nevod-admin/api/node-invites",                        self._handle_create_node_invite)
        app.router.add_get("/nevod-admin/api/node-invites",                         self._handle_list_node_invites)
        app.router.add_get("/nevod-admin/api/published-cells",                      self._handle_list_published_cells)
        app.router.add_post("/nevod-admin/api/published-cells",                     self._handle_publish_cell)
        app.router.add_delete("/nevod-admin/api/published-cells/{cell_id}",         self._handle_unpublish_cell)
        app.router.add_post("/nevod-admin/api/cells-visibility",                    self._handle_set_cells_visibility)
        app.router.add_post("/nevod-admin/api/access",                              self._handle_set_access)
        app.router.add_post("/nevod-admin/api/name",                                self._handle_set_name)
        app.router.add_post("/nevod-admin/api/node-type",                           self._handle_set_node_type)
        app.router.add_post("/nevod-admin/api/parent-node-id",                      self._handle_set_parent_node_id)
        app.router.add_post("/nevod-admin/api/invite-mode",                         self._handle_set_invite_mode)
        app.router.add_post("/nevod-admin/api/admin-cells",                         self._handle_set_admin_cells)
        app.router.add_get("/nevod-admin/api/join-requests",                        self._handle_list_join_requests)
        app.router.add_post("/nevod-admin/api/join-requests/{cell_id}/approve",     self._handle_approve_join_request)
        app.router.add_post("/nevod-admin/api/join-requests/{cell_id}/deny",        self._handle_deny_join_request)
        app.router.add_get("/nevod-admin/api/nodes",                                self._handle_list_nodes)
        app.router.add_post("/nevod-admin/api/join-node",                           self._handle_join_node)
        app.router.add_get("/nevod-admin/api/diagnostics",                          self._handle_diagnostics)
        app.router.add_get("/nevod-admin/api/allowed",                              self._handle_list_allowed)
        app.router.add_post("/nevod-admin/api/allowed/{cell_id}/invite-right",      self._handle_toggle_invite_right)
        app.router.add_get("/nevod-admin/api/logs",                                 self._handle_logs)
        app.router.add_get("/nevod-admin/api/admins",                               self._handle_list_admins)
        app.router.add_post("/nevod-admin/api/admins",                              self._handle_set_admin)
        app.router.add_delete("/nevod-admin/api/admins/{username}",                 self._handle_delete_admin)
        app.router.add_get("/nevod-card/{code}",                                    self._handle_card_lookup)
        app.router.add_get("/nevod-update/release.json",                            self._handle_release_json)
        app.router.add_get("/nevod-update/release.sig",                             self._handle_release_sig)
        return app

    async def start(self, port: int = 8766):
        self._runner = web.AppRunner(self._make_app())
        await self._runner.setup()
        await web.TCPSite(self._runner, "0.0.0.0", port).start()
        log.info("admin panel started on port %d", port)

    async def stop(self):
        if self._runner:
            await self._runner.cleanup()
