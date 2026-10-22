"""
Node and Cell identity management.

NodeIdentity: Ed25519 signing keypair + X25519 encryption keypair + address + TLS cert
CellIdentity: same structure but for a user cell

Persisted as JSON with raw private keys encoded as hex.
In a future version, keys will be encrypted with a passphrase (AES-GCM or Argon2+ChaCha20).
"""

import datetime
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

from .crypto import (
    SigningKeypair, EncryptionKeypair,
    gen_signing, gen_encryption,
    signing_priv_to_bytes, signing_priv_from_bytes,
    enc_priv_to_bytes, enc_priv_from_bytes,
)
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _generate_tls_cert(node_id: str) -> tuple[bytes, bytes, str]:
    """Generate self-signed EC TLS cert for WSS transport.
    Returns (cert_pem, key_pem, sha256_fingerprint_hex).
    """
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, f"nevod-{node_id[:16]}"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    cert_der = cert.public_bytes(serialization.Encoding.DER)
    fingerprint = hashlib.sha256(cert_der).hexdigest()
    return cert_pem, key_pem, fingerprint


@dataclass
class NodeIdentity:
    signing: SigningKeypair
    encryption: EncryptionKeypair
    address: str                    # "host:port" where this node listens
    node_type: str     = "permanent"  # permanent | temporary
    access: str        = "closed"     # open | closed
    invite_mode: str   = "open"       # open | admin | delegated
    # "admin" — registration needs approval from a real person, not a portable code:
    # a not-yet-admitted cell can send JOIN_REQUEST (see node.py's _handle_join_request),
    # which notifies every cell_id in admin_cell_ids below; approval inserts that exact
    # cell_id into allowed_cells directly (no code to generate/leak/share) and wakes the
    # requester with a push. See MD_Discuss/DISCUSS_REGISTRATION_CHANNEL.md for the full
    # design and why this replaced the original "bot" idea.
    # Governs admission of OTHER NODES into node_table (not cells — see invite_mode
    # for that). "invite" (default) is today's unchanged behavior: node_register
    # always needs a valid invite_code. "open" additionally accepts a node_register
    # with none — see DISCUSS_NODE_ADMISSION.md for why this is safe to make fully
    # permissionless at the node-admission layer specifically (mere node_table
    # presence grants no power over any cell's data, unlike a cell actually
    # registering its home there).
    node_join_mode: str = "invite"    # invite | open
    # Who can query this node's admin-curated published-cells list (the "Explore
    # Network" cell/moon list under this node's planet) via NODE_CELLS_REQUEST —
    # see node.py's _handle_node_cells_request and PublishedCellEntry in storage.py.
    # Separate from invite_mode/node_join_mode: publishing a cell list leaks no
    # admission power, just discovery metadata the operator explicitly opted into
    # showing. "members" (default) is the safe choice for both closed nodes (whose
    # published cells, if any, should stay member-only) and open nodes that haven't
    # explicitly decided to broadcast their list network-wide.
    cells_visibility: str = "members"  # off | members | public
    # Who a member sees in this node's member list (GROUP_MEMBERS_REQUEST). "all" (default)
    # is a family/team node where everyone knows everyone. "service" is for a public open
    # node (Nevod Open): strangers registering there must not get a directory of each other
    # — only the node's service cells (administrator, registrar, published bots, official
    # cells) are listed; people find each other by contact card as usual.
    members_visibility: str = "all"    # all | service
    # cell_ids treated as "administrators" for invite_mode="admin" — each gets a
    # notification (via the registrar identity, see node.py) when a JOIN_REQUEST
    # arrives, and admin.py's approve/deny endpoints are meant to be operated by
    # whoever controls the admin panel on their behalf. No separate "owner" concept —
    # whoever holds NEVOD_ADMIN_PASSWORD already IS the ultimate authority (can edit
    # this list itself); see the DISCUSS file referenced above for the reasoning.
    admin_cell_ids: List[str] = field(default_factory=list)
    parent_node_id: str = ""          # set for child (temporary) nodes
    name: str = ""                    # human-friendly label, gossiped to node_table
    tls_cert_pem:    bytes = field(default=b"", repr=False)
    tls_key_pem:     bytes = field(default=b"", repr=False)
    tls_fingerprint: str   = ""

    @property
    def node_id(self) -> str:
        return self.signing.public.hex()

    @classmethod
    def generate(cls, address: str, node_type: str = "permanent",
                 access: str = "closed", invite_mode: str = "open",
                 node_join_mode: str = "invite", cells_visibility: str = "members",
                 admin_cell_ids: Optional[List[str]] = None,
                 parent_node_id: str = "", name: str = "") -> "NodeIdentity":
        signing    = gen_signing()
        encryption = gen_encryption()
        node_id    = signing.public.hex()
        cert_pem, key_pem, fingerprint = _generate_tls_cert(node_id)
        return cls(
            signing=signing,
            encryption=encryption,
            address=address,
            node_type=node_type,
            access=access,
            invite_mode=invite_mode,
            node_join_mode=node_join_mode,
            cells_visibility=cells_visibility,
            admin_cell_ids=admin_cell_ids or [],
            parent_node_id=parent_node_id,
            name=name,
            tls_cert_pem=cert_pem,
            tls_key_pem=key_pem,
            tls_fingerprint=fingerprint,
        )

    def save(self, path: str):
        data = {
            "signing_priv":    signing_priv_to_bytes(self.signing.private).hex(),
            "signing_pub":     self.signing.public.hex(),
            "enc_priv":        enc_priv_to_bytes(self.encryption.private).hex(),
            "enc_pub":         self.encryption.public.hex(),
            "address":         self.address,
            "node_type":       self.node_type,
            "access":          self.access,
            "invite_mode":     self.invite_mode,
            "node_join_mode":  self.node_join_mode,
            "cells_visibility": self.cells_visibility,
            "members_visibility": self.members_visibility,
            "admin_cell_ids":  self.admin_cell_ids,
            "parent_node_id":  self.parent_node_id,
            "name":            self.name,
            "tls_cert_pem":    self.tls_cert_pem.decode(),
            "tls_key_pem":     self.tls_key_pem.decode(),
            "tls_fingerprint": self.tls_fingerprint,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "NodeIdentity":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        signing_priv = signing_priv_from_bytes(bytes.fromhex(data["signing_priv"]))
        signing = SigningKeypair(
            private=signing_priv,
            public=bytes.fromhex(data["signing_pub"]),
        )
        enc_priv = enc_priv_from_bytes(bytes.fromhex(data["enc_priv"]))
        encryption = EncryptionKeypair(
            private=enc_priv,
            public=bytes.fromhex(data["enc_pub"]),
        )
        tls_cert_pem    = data.get("tls_cert_pem", "").encode()
        tls_key_pem     = data.get("tls_key_pem",  "").encode()
        tls_fingerprint = data.get("tls_fingerprint", "")
        # Migrate old identity files that have no TLS cert
        if not tls_cert_pem:
            node_id = signing.public.hex()
            tls_cert_pem, tls_key_pem, tls_fingerprint = _generate_tls_cert(node_id)
        return cls(
            signing=signing,
            encryption=encryption,
            address=data["address"],
            node_type=data.get("node_type", "permanent"),
            access=data.get("access", "closed"),
            invite_mode=data.get("invite_mode", "open"),
            node_join_mode=data.get("node_join_mode", "invite"),
            cells_visibility=data.get("cells_visibility", "members"),
            members_visibility=data.get("members_visibility", "all"),
            admin_cell_ids=data.get("admin_cell_ids", []),
            parent_node_id=data.get("parent_node_id", ""),
            name=data.get("name", ""),
            tls_cert_pem=tls_cert_pem,
            tls_key_pem=tls_key_pem,
            tls_fingerprint=tls_fingerprint,
        )

    def as_node_entry_dict(self) -> dict:
        return {
            "node_id":         self.node_id,
            "address":         self.address,
            "type":            self.node_type,
            "access":          self.access,
            "parent_node":     self.parent_node_id,
            "enc_pub":         self.encryption.public.hex(),
            "tls_fingerprint": self.tls_fingerprint,
            "name":            self.name,
        }


@dataclass
class CellIdentity:
    signing: SigningKeypair
    encryption: EncryptionKeypair
    name: str = ""

    @property
    def cell_id(self) -> str:
        return self.signing.public.hex()

    @classmethod
    def generate(cls, name: str = "") -> "CellIdentity":
        return cls(
            signing=gen_signing(),
            encryption=gen_encryption(),
            name=name,
        )

    def save(self, path: str):
        data = {
            "signing_priv": signing_priv_to_bytes(self.signing.private).hex(),
            "signing_pub":  self.signing.public.hex(),
            "enc_priv":     enc_priv_to_bytes(self.encryption.private).hex(),
            "enc_pub":      self.encryption.public.hex(),
            "name":         self.name,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "CellIdentity":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        signing_priv = signing_priv_from_bytes(bytes.fromhex(data["signing_priv"]))
        signing = SigningKeypair(
            private=signing_priv,
            public=bytes.fromhex(data["signing_pub"]),
        )
        enc_priv = enc_priv_from_bytes(bytes.fromhex(data["enc_priv"]))
        encryption = EncryptionKeypair(
            private=enc_priv,
            public=bytes.fromhex(data["enc_pub"]),
        )
        return cls(
            signing=signing,
            encryption=encryption,
            name=data.get("name", ""),
        )
