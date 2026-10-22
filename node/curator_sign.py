"""
Curator signing tool for the Nevod bootstrap manifest (nodes.json).

Not part of the node's own runtime — a standalone script a network curator runs
by hand to vet and sign an entry for the public "verified" gateway list. See
MD_Discuss/DISCUSS_NODE_ADMISSION.md for the full design/threat model: the
curator keypair is deliberately separate from any node's own identity, and the
"verified" flag is advisory metadata a client checks before trusting a node as
a walk-up bootstrap gateway — it grants no protocol-level power on its own.

Usage:
    Generate a curator keypair (once, ever — keep the private key offline). The private key
    goes straight into --out and is never printed (so it can't end up in a terminal log or
    transcript); only the public key is shown:
        python -m node.curator_sign genkey --out /path/to/offline/curator_key.json

    Every signing command takes --privkey-file <that json> (preferred) or the legacy
    --privkey <hex> (avoid: the key lands in shell history / command logs).

    Re-sign whole manifests in place (key rotation, or after editing entries by hand):
        python -m node.curator_sign resign --privkey-file <key.json> \\
            --nodes ios/Nevod/Nevod/nodes.json --official ios/Nevod/Nevod/official.json

    Sign a manifest entry:
        python -m node.curator_sign sign \\
            --node-id <hex> --address host:port --tls-fingerprint <hex> \\
            --purpose informational --privkey <hex>
        # prints a ready-to-paste nodes.json entry

    Sign an official account entry (official.json — the "✓ official Nevod account" badge,
    see ios/Nevod/Nevod/Storage/OfficialAccounts.swift):
        python -m node.curator_sign sign-official \
            --cell-id <hex> --role administrator --name administrator --privkey <hex>
        # prints a ready-to-paste official.json entry

    Verify an entry (self-check — a client does the equivalent with its own
    hardcoded public key, not by calling this script):
        python -m node.curator_sign verify \\
            --node-id <hex> --address host:port --tls-fingerprint <hex> \\
            --purpose informational --sig <hex> --pubkey <hex>
"""
import argparse
import json
import sys

from .crypto import (
    gen_signing, sign, verify, SigningKeypair,
    signing_priv_from_bytes, signing_priv_to_bytes,
)
from .crypto import RAW, RAW_PUB

VALID_PURPOSES = ("informational", "ai_agent", "community")
VALID_OFFICIAL_ROLES = ("administrator", "service", "author")  # service = registrars, bots, test accounts; author = the project author


def canonical_message(node_id: str, address: str, tls_fingerprint: str, purpose: str) -> bytes:
    """The exact bytes a curator signs and a client verifies — the single shared
    source of truth for the format, so sign/verify can never silently drift out
    of sync by each side reimplementing it slightly differently."""
    return "|".join([node_id, address, tls_fingerprint, purpose]).encode("utf-8")


def canonical_official_message(cell_id: str, role: str, enc_pub: str = "", node_id: str = "") -> bytes:
    """Bytes signed for an official.json entry. The "official|" prefix domain-separates it
    from node entries — a node entry's signature can never be replayed as an official-account
    one (or vice versa), even though both are signed with the same curator key. enc_pub and
    node_id are signed too (empty when absent): the app encrypts in-app complaints to the
    administrator with enc_pub, so a swapped key must fail verification, not silently
    redirect reports to someone else."""
    return "|".join(["official", cell_id, role, enc_pub, node_id]).encode("utf-8")


def sign_official(cell_id: str, role: str, curator_privkey_hex: str,
                  enc_pub: str = "", node_id: str = "") -> str:
    priv = signing_priv_from_bytes(bytes.fromhex(curator_privkey_hex))
    pub = priv.public_key().public_bytes(RAW, RAW_PUB)
    return sign(canonical_official_message(cell_id, role, enc_pub, node_id),
                SigningKeypair(private=priv, public=pub)).hex()


def verify_official(cell_id: str, role: str, sig_hex: str, curator_pubkey_hex: str,
                    enc_pub: str = "", node_id: str = "") -> bool:
    try:
        return verify(canonical_official_message(cell_id, role, enc_pub, node_id),
                      bytes.fromhex(sig_hex), bytes.fromhex(curator_pubkey_hex))
    except ValueError:
        return False


def sign_entry(node_id: str, address: str, tls_fingerprint: str, purpose: str,
               curator_privkey_hex: str) -> str:
    priv = signing_priv_from_bytes(bytes.fromhex(curator_privkey_hex))
    pub = priv.public_key().public_bytes(RAW, RAW_PUB)
    keypair = SigningKeypair(private=priv, public=pub)
    msg = canonical_message(node_id, address, tls_fingerprint, purpose)
    return sign(msg, keypair).hex()


def verify_entry(node_id: str, address: str, tls_fingerprint: str, purpose: str,
                  sig_hex: str, curator_pubkey_hex: str) -> bool:
    msg = canonical_message(node_id, address, tls_fingerprint, purpose)
    try:
        return verify(msg, bytes.fromhex(sig_hex), bytes.fromhex(curator_pubkey_hex))
    except ValueError:
        return False


def _load_privkey(args) -> str:
    """Curator private key hex from --privkey-file (JSON from genkey --out, or a bare hex
    file) or the legacy --privkey. Never echoed anywhere."""
    if getattr(args, "privkey_file", None):
        raw = open(args.privkey_file, encoding="utf-8").read().strip()
        try:
            return json.loads(raw)["private_key"].strip()
        except (ValueError, KeyError, TypeError):
            return raw
    if getattr(args, "privkey", None):
        return args.privkey.strip()
    print("error: pass --privkey-file (preferred) or --privkey", file=sys.stderr)
    sys.exit(1)


def _pubkey_of(priv_hex: str) -> str:
    priv = signing_priv_from_bytes(bytes.fromhex(priv_hex))
    return priv.public_key().public_bytes(RAW, RAW_PUB).hex()


def _cmd_genkey(args):
    kp = gen_signing()
    priv_hex = signing_priv_to_bytes(kp.private).hex()
    if not args.out:
        print("error: --out <file> is required — the private key is written there, never printed",
              file=sys.stderr)
        sys.exit(1)
    import os
    if os.path.exists(args.out):
        print(f"error: {args.out} already exists — refusing to overwrite a key", file=sys.stderr)
        sys.exit(1)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"private_key": priv_hex, "public_key": kp.public.hex()}, f, indent=2)
        f.write("\n")
    print(f"Private key written to {args.out} (keep OFFLINE, never commit).")
    print("Curator public key (hardcode into the client as the trust anchor):")
    print(f"  {kp.public.hex()}")


def _cmd_resign(args):
    """Re-sign every entry of nodes.json / official.json with the given key, in place.
    official.json entries are always written in the current 5-field form."""
    priv_hex = _load_privkey(args)
    pub_hex = _pubkey_of(priv_hex)
    if args.nodes:
        entries = json.load(open(args.nodes, encoding="utf-8"))
        for e in entries:
            e["verified_sig"] = sign_entry(e["node_id"], e["address"], e.get("tls_fingerprint", ""),
                                           e["purpose"], priv_hex)
            assert verify_entry(e["node_id"], e["address"], e.get("tls_fingerprint", ""),
                                e["purpose"], e["verified_sig"], pub_hex)
        _write_json(args.nodes, entries)
        print(f"{args.nodes}: re-signed {len(entries)} entries")
    if args.official:
        entries = json.load(open(args.official, encoding="utf-8"))
        for e in entries:
            e["cell_id"] = e["cell_id"].strip().lower()
            e["enc_pub"] = (e.get("enc_pub") or "").strip().lower()
            e["node_id"] = (e.get("node_id") or "").strip().lower()
            e["sig"] = sign_official(e["cell_id"], e["role"], priv_hex, e["enc_pub"], e["node_id"])
            assert verify_official(e["cell_id"], e["role"], e["sig"], pub_hex, e["enc_pub"], e["node_id"])
        _write_json(args.official, entries)
        print(f"{args.official}: re-signed {len(entries)} entries")
    print(f"signed with curator public key {pub_hex}")


def _write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _cmd_sign(args):
    if args.purpose not in VALID_PURPOSES:
        print(f"error: --purpose must be one of {VALID_PURPOSES}", file=sys.stderr)
        sys.exit(1)
    sig_hex = sign_entry(args.node_id, args.address, args.tls_fingerprint,
                         args.purpose, _load_privkey(args))
    entry = {
        "node_id": args.node_id,
        "address": args.address,
        "tls_fingerprint": args.tls_fingerprint,
        "name": args.name or "",
        "purpose": args.purpose,
        "verified": True,
        "verified_sig": sig_hex,
    }
    print(json.dumps(entry, indent=2, ensure_ascii=False))


def _cmd_sign_official(args):
    cell_id = args.cell_id.strip().lower()
    enc_pub = (args.enc_pub or "").strip().lower()
    node_id = (args.node_id or "").strip().lower()
    entry = {
        "cell_id": cell_id,
        "role": args.role,
        "name": args.name or args.role,
        "enc_pub": enc_pub,
        "node_id": node_id,
        "sig": sign_official(cell_id, args.role, _load_privkey(args), enc_pub, node_id),
    }
    print(json.dumps(entry, indent=2, ensure_ascii=False))


def _cmd_verify(args):
    ok = verify_entry(args.node_id, args.address, args.tls_fingerprint,
                      args.purpose, args.sig, args.pubkey)
    print("OK — signature valid" if ok else "FAILED — signature does not match")
    sys.exit(0 if ok else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    gp = sub.add_parser("genkey", help="generate a new curator keypair")
    gp.add_argument("--out", help="file to write the keypair JSON to (required)")

    sp = sub.add_parser("sign", help="sign a nodes.json manifest entry")
    sp.add_argument("--node-id", required=True)
    sp.add_argument("--address", required=True)
    sp.add_argument("--tls-fingerprint", default="",
                    help="empty (default) = no pinning, node is CA-trusted (e.g. behind a real "
                         "Let's Encrypt-fronted reverse proxy); omit this flag rather than "
                         "passing an empty string, which some shells (PowerShell included) drop")
    sp.add_argument("--purpose", required=True, choices=VALID_PURPOSES)
    sp.add_argument("--name", default="")
    sp.add_argument("--privkey-file", help="curator key file (genkey --out JSON, or bare hex)")
    sp.add_argument("--privkey", help="curator private key, hex (legacy — prefer --privkey-file)")

    op = sub.add_parser("sign-official", help="sign an official.json account entry")
    op.add_argument("--cell-id", required=True)
    op.add_argument("--role", required=True, choices=VALID_OFFICIAL_ROLES)
    op.add_argument("--name", default="")
    op.add_argument("--enc-pub", default="",
                    help="the account's encryption public key, hex — required for role "
                         "administrator (in-app complaints are encrypted to it)")
    op.add_argument("--node-id", default="", help="the account's home node id, hex")
    op.add_argument("--privkey-file", help="curator key file (genkey --out JSON, or bare hex)")
    op.add_argument("--privkey", help="curator private key, hex (legacy — prefer --privkey-file)")

    rp = sub.add_parser("resign", help="re-sign nodes.json / official.json in place")
    rp.add_argument("--privkey-file", help="curator key file (genkey --out JSON, or bare hex)")
    rp.add_argument("--privkey", help="curator private key, hex (legacy — prefer --privkey-file)")
    rp.add_argument("--nodes", help="path to nodes.json")
    rp.add_argument("--official", help="path to official.json")

    vp = sub.add_parser("verify", help="verify a signed entry (self-check)")
    vp.add_argument("--node-id", required=True)
    vp.add_argument("--address", required=True)
    vp.add_argument("--tls-fingerprint", default="")
    vp.add_argument("--purpose", required=True, choices=VALID_PURPOSES)
    vp.add_argument("--sig", required=True, help="verified_sig from the manifest entry, hex")
    vp.add_argument("--pubkey", required=True, help="curator public key, hex")

    args = p.parse_args()
    {"genkey": _cmd_genkey, "sign": _cmd_sign, "sign-official": _cmd_sign_official,
     "resign": _cmd_resign, "verify": _cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    main()
