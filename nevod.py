#!/usr/bin/env python3
"""
nevod — Nevod node & cell CLI

Node commands:
  nevod init    <address>                         Generate node keypair
  nevod genesis <address>                         Init first node in a new network
  nevod start                                     Start node
  nevod join    <bootstrap_addr>                  Start and join via bootstrap
  nevod join    --invite <TOKEN>                  Start and join via invite token (approval-gated)
  nevod info                                      Print node identity

Cell commands:
  nevod cell init   <name>                        Generate cell identity
  nevod cell info   <identity.cell.json>          Print cell info
  nevod cell connect <identity.cell.json> <addr>  Connect and chat

Examples:
  python nevod.py genesis 127.0.0.1:8765
  python nevod.py cell init alice
  python nevod.py cell connect alice.cell.json 127.0.0.1:8765
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

import click

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


@click.group()
def cli():
    """Nevod — Zero Knowledge Infrastructure node."""


@cli.command()
@click.argument("address")
@click.option("--out", default="node.json", show_default=True, help="Identity file path")
@click.option("--type", "node_type", default="permanent",
              type=click.Choice(["permanent", "temporary"]), show_default=True)
@click.option("--access", default="closed",
              type=click.Choice(["open", "closed"]), show_default=True)
@click.option("--name", default="", help="Human-friendly node name (gossiped to the network)")
def init(address, out, node_type, access, name):
    """Generate a new node identity (keypair) and save to file."""
    from node.identity import NodeIdentity
    identity = NodeIdentity.generate(address, node_type=node_type, access=access, name=name)
    identity.save(out)
    click.echo(f"node_id : {identity.node_id}")
    click.echo(f"name    : {name or '(none)'}")
    click.echo(f"address : {address}")
    click.echo(f"type    : {node_type} / {access}")
    click.echo(f"saved   : {out}")


@cli.command()
@click.argument("address")
@click.option("--identity", default="node.json", show_default=True)
@click.option("--db", default="node.db", show_default=True)
@click.option("--access", default="open",
              type=click.Choice(["open", "closed"]), show_default=True)
@click.option("--name", default="", help="Human-friendly node name (gossiped to the network)")
def genesis(address, identity, db, access, name):
    """Create the first node in a new Nevod network."""
    asyncio.run(_genesis(address, identity, db, access, name))


async def _genesis(address, identity_path, db_path, access, name=""):
    from node.node import Node
    node = await Node.create_genesis(address, identity_path, db_path, access=access, name=name)
    click.echo(f"genesis node: {node.identity.node_id}")
    click.echo(f"name        : {name or '(none)'}")
    click.echo(f"address     : {address}")
    click.echo(f"identity    → {identity_path}")
    click.echo(f"database    → {db_path}")
    await node.start()
    click.echo("node running — Ctrl+C to stop")
    await _run_until_signal(node)


@cli.command()
@click.option("--identity", default="node.json", show_default=True)
@click.option("--db", default="node.db", show_default=True)
def start(identity, db):
    """Start a node (already initialised, existing network)."""
    asyncio.run(_start(identity, db))


async def _start(identity_path, db_path):
    import os
    from node.node import Node
    node = await Node.create(identity_path, db_path)
    await node.start()
    click.echo(f"node : {node.identity.node_id[:16]}...")

    admin_password = os.environ.get("NEVOD_ADMIN_PASSWORD")
    if admin_password:
        from node.admin import AdminServer
        admin_port = int(os.environ.get("NEVOD_ADMIN_PORT", 8766))
        admin_username = os.environ.get("NEVOD_ADMIN_USERNAME") or None
        admin = AdminServer(node, admin_password, admin_username, identity_path=identity_path)
        await admin.start(admin_port)
        click.echo(f"admin: http://0.0.0.0:{admin_port}/admin  (password protected)")
    else:
        admin = None
        click.echo("admin: disabled (set NEVOD_ADMIN_PASSWORD to enable)")

    click.echo("running — Ctrl+C to stop")
    await _run_until_signal(node)

    if admin:
        await admin.stop()


@cli.command()
@click.argument("bootstrap", required=False)
@click.option("--identity", default="node.json", show_default=True)
@click.option("--db", default="node.db", show_default=True)
@click.option("--fingerprint", default=None,
              help="Expected SHA-256 TLS fingerprint of the bootstrap node")
@click.option("--invite", "invite_token", default=None,
              help="Node-invite token from an existing node's admin panel "
                   "(bundles bootstrap address, TLS fingerprint, and invite code — "
                   "makes BOOTSTRAP/--fingerprint unnecessary)")
def join(bootstrap, identity, db, fingerprint, invite_token):
    """Start node and join existing network via bootstrap address (host:port),
    or via --invite TOKEN for an approval-gated join."""
    asyncio.run(_join(bootstrap, identity, db, fingerprint, invite_token))


async def _join(bootstrap_addr, identity_path, db_path, fingerprint=None, invite_token=None):
    from node.node import Node
    from node.protocol import parse_node_invite_token

    invite_code = None
    if invite_token:
        bootstrap_addr, fingerprint, invite_code = parse_node_invite_token(invite_token)
    if not bootstrap_addr:
        raise click.UsageError("either BOOTSTRAP address or --invite TOKEN is required")

    node = await Node.create(identity_path, db_path)
    await node.start()
    reachable = await node.join(bootstrap_addr, expected_fingerprint=fingerprint,
                                invite_code=invite_code)
    click.echo(f"node : {node.identity.node_id[:16]}...")
    click.echo(f"joined via {bootstrap_addr}" + (" (invite approved)" if invite_code else ""))
    if reachable is True:
        click.echo(f"reachability: OK — recommender could reach {node.identity.address}")
    elif reachable is False:
        click.echo(f"reachability: FAILED — recommender could NOT reach {node.identity.address} "
                   "(check port forwarding / firewall)")
    click.echo("running — Ctrl+C to stop")
    await _run_until_signal(node)


@cli.command()
@click.option("--identity", default="node.json", show_default=True)
def info(identity):
    """Print identity info without starting the node."""
    from node.identity import NodeIdentity
    try:
        idt = NodeIdentity.load(identity)
    except FileNotFoundError:
        click.echo(f"not found: {identity}", err=True)
        sys.exit(1)
    click.echo(f"node_id         : {idt.node_id}")
    click.echo(f"name            : {idt.name or '(none)'}")
    click.echo(f"address         : {idt.address}")
    click.echo(f"type            : {idt.node_type} / {idt.access}")
    click.echo(f"tls_fingerprint : {idt.tls_fingerprint}")
    click.echo(f"enc_pub         : {idt.encryption.public.hex()}")


@cli.command("set-access")
@click.option("--identity", default="node.json", show_default=True)
@click.option("--access", type=click.Choice(["open", "closed"]), required=True,
              help="open = publicly listed (gossip presence-sharing + client node directory); "
                   "closed = not listed. Does NOT affect invite_mode / who can join.")
def set_access(identity, access):
    """Change whether this node advertises itself as publicly discoverable. Requires
    restarting the node process to take effect (identity is only read at startup)."""
    from node.identity import NodeIdentity
    try:
        idt = NodeIdentity.load(identity)
    except FileNotFoundError:
        click.echo(f"not found: {identity}", err=True)
        sys.exit(1)
    idt.access = access
    idt.save(identity)
    click.echo(f"access set to '{access}' for node {idt.node_id[:8]}… — restart the node to apply")


@cli.command("set-address")
@click.option("--identity", default="node.json", show_default=True)
@click.argument("address")
def set_address(identity, address):
    """Correct the address this node advertises about itself (host:port). Only
    read at genesis time from NEVOD_ADDRESS -- if that env var was wrong when
    the node was first created (e.g. a shared docker-compose.yml with another
    deployment's address baked in), the identity file keeps the wrong value
    forever until fixed here. Requires restarting the node to apply."""
    from node.identity import NodeIdentity
    try:
        idt = NodeIdentity.load(identity)
    except FileNotFoundError:
        click.echo(f"not found: {identity}", err=True)
        sys.exit(1)
    old = idt.address
    idt.address = address
    idt.save(identity)
    click.echo(f"address changed '{old}' -> '{address}' for node {idt.node_id[:8]}… — restart the node to apply")


@cli.command()
@click.option("--admin-url", default="http://127.0.0.1:8766", show_default=True,
              help="Admin API base of the (already running) node to diagnose")
@click.option("--username", default=None, help="Admin username, if one is configured")
@click.option("--password", default=None,
              help="Admin password (falls back to the NEVOD_ADMIN_PASSWORD env var)")
def diagnose(admin_url, username, password):
    """Run self-diagnostics against a running node via its admin API and print the results.

    Requires the node to already be up (this hits its admin HTTP API, same auth as the
    web panel) -- for a node that won't even start, check its process/logs directly first.
    Exit code: 0 all ok, 1 at least one warning, 2 at least one failure -- suitable for cron.
    """
    import os as _os
    password = password or _os.environ.get("NEVOD_ADMIN_PASSWORD")
    asyncio.run(_diagnose(admin_url.rstrip("/"), username, password))


async def _diagnose(admin_url: str, username: Optional[str], password: Optional[str]):
    import httpx
    auth = (username or "", password) if password else None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{admin_url}/nevod-admin/api/diagnostics", auth=auth)
    except Exception as e:
        click.echo(f"could not reach admin API at {admin_url}: {e}", err=True)
        sys.exit(1)
    if resp.status_code == 401:
        click.echo("401 unauthorized — check --username/--password (or NEVOD_ADMIN_PASSWORD)", err=True)
        sys.exit(1)
    if resp.status_code != 200:
        click.echo(f"admin API returned {resp.status_code}: {resp.text}", err=True)
        sys.exit(1)

    icons = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}
    exit_code = 0
    for check in resp.json()["checks"]:
        icon = icons.get(check["status"], "?   ")
        click.echo(f"[{icon}] {check['label']}: {check['detail']}")
        if check["status"] == "fail":
            exit_code = 2
        elif check["status"] == "warn" and exit_code == 0:
            exit_code = 1
    sys.exit(exit_code)


# ─── release commands (signed auto-update artifacts, see update_checker.py) ───
# Only the maintainer runs these, never a regular node operator. The whole trust
# model of update_checker.py rests on the private key generated by `release
# keygen` NEVER leaving the maintainer's machine (never committed, never on a
# node server) -- its public half is what gets hardcoded into
# update_checker.py's MAINTAINER_PUBLIC_KEY_HEX, which is the one thing every
# node checks before applying anything it downloaded.

@cli.group()
def release():
    """Sign RELEASE.json/RELEASE.sig so nodes can verify and auto-apply updates."""


@release.command("keygen")
@click.option("--out", default="release_key.json", show_default=True)
def release_keygen(out):
    """Generate a new Ed25519 maintainer signing keypair. Keep OUT secret and
    offline -- do not commit it to this (or any) git repo."""
    import json
    from node.crypto import gen_signing, signing_priv_to_bytes

    kp = gen_signing()
    with open(out, "w") as f:
        json.dump({
            "signing_priv": signing_priv_to_bytes(kp.private).hex(),
            "signing_pub": kp.public.hex(),
        }, f, indent=2)
    click.echo(f"wrote {out} — keep it secret, keep it offline, never git add it")
    click.echo(f"public key (hardcode into update_checker.py MAINTAINER_PUBLIC_KEY_HEX): {kp.public.hex()}")


@release.command("sign")
@click.option("--key", required=True, help="Path to the maintainer key file from `release keygen`")
@click.option("--commit", default=None, help="Commit SHA to sign (default: current HEAD)")
@click.option("--version", "version_", type=int, required=True,
              help="Monotonically increasing release version number (nodes reject a signed "
                   "release with a version <= what they already have -- prevents replaying "
                   "an old, still-validly-signed release to force a downgrade)")
@click.option("--out-dir", default=".", show_default=True)
def release_sign(key, commit, version_, out_dir):
    """Build and sign RELEASE.json/RELEASE.sig for a commit. Commit and push the two
    output files afterwards -- that's what every node's update_checker.py verifies
    against MAINTAINER_PUBLIC_KEY_HEX before applying anything."""
    import json
    import subprocess
    import time
    from node.crypto import sign, signing_priv_from_bytes, SigningKeypair

    with open(key) as f:
        keydata = json.load(f)
    keypair = SigningKeypair(
        private=signing_priv_from_bytes(bytes.fromhex(keydata["signing_priv"])),
        public=bytes.fromhex(keydata["signing_pub"]),
    )

    if commit is None:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()

    # Canonical serialization (sorted keys, no extra whitespace) so signing and
    # verifying operate on an unambiguous byte sequence -- update_checker.py
    # verifies against these exact raw bytes, never a re-serialized copy.
    manifest = {"commit": commit, "version": version_, "timestamp": int(time.time())}
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    signature = sign(manifest_bytes, keypair)

    release_path = f"{out_dir}/RELEASE.json"
    sig_path = f"{out_dir}/RELEASE.sig"
    with open(release_path, "wb") as f:
        f.write(manifest_bytes)
    with open(sig_path, "w") as f:
        f.write(signature.hex())

    click.echo(f"wrote {release_path} (commit={commit[:8]} version={version_})")
    click.echo(f"wrote {sig_path}")
    click.echo("now: git add RELEASE.json RELEASE.sig && git commit && git push")


# ─── cell commands ────────────────────────────────────────────────────────────

@cli.group()
def cell():
    """Cell (user / AI agent) identity and E2E messaging."""


@cell.command("init")
@click.argument("name")
@click.option("--out", default=None,
              help="Output file (default: <name>.cell.json)")
def cell_init(name, out):
    """Generate a new cell identity (keypair) and save to file."""
    from node.identity import CellIdentity
    if out is None:
        out = f"{name}.cell.json"
    idt = CellIdentity.generate(name)
    idt.save(out)
    click.echo(f"name    : {name}")
    click.echo(f"cell_id : {idt.cell_id}")
    click.echo(f"enc_pub : {idt.encryption.public.hex()}")
    click.echo(f"saved   : {out}")


@cell.command("info")
@click.argument("identity")
def cell_info(identity):
    """Print cell identity info (cell_id, enc_pub)."""
    from node.identity import CellIdentity
    try:
        idt = CellIdentity.load(identity)
    except FileNotFoundError:
        click.echo(f"not found: {identity}", err=True)
        sys.exit(1)
    click.echo(f"name    : {idt.name}")
    click.echo(f"cell_id : {idt.cell_id}")
    click.echo(f"enc_pub : {idt.encryption.public.hex()}")


@cell.command("connect")
@click.argument("identity")
@click.argument("node_addr")
@click.option("--fingerprint", default=None,
              help="Expected SHA-256 TLS fingerprint of the node")
def cell_connect_cmd(identity, node_addr, fingerprint):
    """Connect cell to a node and start interactive chat.

    \b
    Inside the REPL:
      /add <alias> <cell_id>[@<node_id>] <enc_pub_hex>   — save contact
      /contacts                                           — list contacts
      <alias>: <message>                                  — send to contact
      <cell_id>[@<node_id>] <enc_pub_hex>: <message>     — send directly
      /quit                                               — disconnect
    """
    asyncio.run(_cell_connect(identity, node_addr, fingerprint))


async def _cell_connect(identity_path: str, node_addr: str,
                        expected_fingerprint: Optional[str] = None):
    from node.identity import CellIdentity
    from node.client import CellClient

    try:
        idt = CellIdentity.load(identity_path)
    except FileNotFoundError:
        click.echo(f"not found: {identity_path}", err=True)
        sys.exit(1)

    # in-session contact book: alias → (cell_id, node_id, enc_pubkey)
    contacts: dict = {}

    async def on_message(from_addr: str, plaintext: bytes):
        text = plaintext.decode(errors="replace")
        click.echo(f"\n  [{from_addr[:24]}]: {text}")
        click.echo("> ", nl=False)

    cell = CellClient(idt, on_message=on_message)
    try:
        await cell.connect(node_addr, expected_fingerprint=expected_fingerprint)
    except Exception as e:
        click.echo(f"connect failed: {e}", err=True)
        sys.exit(1)

    click.echo(f"connected : {node_addr}")
    click.echo(f"cell_id   : {idt.cell_id}")
    click.echo(f"enc_pub   : {idt.encryption.public.hex()}")
    click.echo()
    click.echo("  /add <alias> <cell_id>[@<node>] <enc_pub>")
    click.echo("  /contacts")
    click.echo("  <alias>: <msg>   OR   <cell_id>[@<node>] <enc_pub>: <msg>")
    click.echo("  /quit")
    click.echo()

    loop = asyncio.get_event_loop()

    try:
        while cell.connected:
            click.echo("> ", nl=False)
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
            except (EOFError, KeyboardInterrupt):
                break
            if not line:          # EOF (pipe closed / Ctrl+D)
                break
            line = line.strip()
            if not line:
                continue

            # ── /quit ──────────────────────────────────────────────────────
            if line in ("/quit", "/exit", "quit", "exit"):
                break

            # ── /contacts ──────────────────────────────────────────────────
            if line == "/contacts":
                if not contacts:
                    click.echo("  (no contacts)")
                else:
                    for alias, (cid, nid, _) in contacts.items():
                        click.echo(f"  {alias}: {cid[:16]}...@{nid[:16]}...")
                continue

            # ── /add <alias> <addr> <enc_pub> ─────────────────────────────
            if line.startswith("/add "):
                parts = line[5:].split()
                if len(parts) != 3:
                    click.echo("  usage: /add <alias> <cell_id>[@<node_id>] <enc_pub_hex>")
                    continue
                alias, addr_str, enc_hex = parts
                to_cell_id, to_node_id = _split_addr(addr_str, cell._node_id)
                try:
                    enc_pub = bytes.fromhex(enc_hex)
                    if len(enc_pub) != 32:
                        raise ValueError("enc_pub must be 32 bytes")
                except ValueError as e:
                    click.echo(f"  bad enc_pub: {e}")
                    continue
                contacts[alias] = (to_cell_id, to_node_id, enc_pub)
                click.echo(f"  saved: {alias}")
                continue

            # ── <alias>: <msg>   OR   <addr> <enc_pub>: <msg> ─────────────
            if ": " in line:
                head, message = line.split(": ", 1)
                head = head.strip()

                if head in contacts:
                    to_cell_id, to_node_id, enc_pub = contacts[head]
                elif " " in head:
                    addr_str, enc_hex = head.split(" ", 1)
                    to_cell_id, to_node_id = _split_addr(addr_str, cell._node_id)
                    try:
                        enc_pub = bytes.fromhex(enc_hex.strip())
                        if len(enc_pub) != 32:
                            raise ValueError("enc_pub must be 32 bytes")
                    except ValueError as e:
                        click.echo(f"  bad enc_pub: {e}")
                        continue
                else:
                    click.echo(f"  unknown alias '{head}' — use /add or provide enc_pub")
                    continue

                try:
                    await cell.send(to_cell_id, to_node_id, enc_pub,
                                    message.encode())
                    click.echo("  [sent]")
                except Exception as e:
                    click.echo(f"  send error: {e}")
                continue

            click.echo("  ?  type /quit to exit or see usage above")

    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        click.echo("\ndisconnecting...")
        await cell.disconnect()


def _split_addr(addr_str: str, default_node_id: str):
    """Split 'cell_id@node_id' or 'cell_id' into (cell_id, node_id)."""
    if "@" in addr_str:
        cell_id, node_id = addr_str.split("@", 1)
        return cell_id, node_id
    return addr_str, default_node_id


# ─── webui ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--node-addr", default="127.0.0.1:8765", show_default=True,
              help="Address for the embedded genesis node")
@click.option("--http-port", default=8080, show_default=True,
              help="Port for the HTTP web interface")
@click.option("--cells", default="alice,bob,charlie", show_default=True,
              help="Comma-separated list of cell names to create")
def webui(node_addr, http_port, cells):
    """Start embedded node + web UI for testing (http://127.0.0.1:<http-port>)."""
    from webui import run as webui_run
    cell_names = [c.strip() for c in cells.split(",") if c.strip()]
    asyncio.run(webui_run(node_addr, http_port, cell_names))


# ─── signal / shutdown ────────────────────────────────────────────────────────

async def _run_until_signal(node):
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    def _signal_handler():
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows: signals not supported in asyncio event loop
            pass

    try:
        await stop.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        click.echo("\nstopping...")
        await node.stop()


if __name__ == "__main__":
    cli()
