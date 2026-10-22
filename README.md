# Nevod

**A decentralized messenger built on Zero Knowledge Infrastructure (ZKI): the people who build and run it are cut off from what you write — by architecture, not by promise.**

[nevod.network](https://nevod.network) · [ZKI Manifesto](https://nevod.network/manifesto/) · [Русский](README.ru.md)

- No phone number, no e-mail: your identity is a key pair created on your phone.
- End-to-end encryption for messages, files and calls. Nodes only see encrypted blobs and delivery addresses.
- No central server: a node can be run by anyone — a company, a school, a city, a family.
- Undelivered messages live on a node for at most 72 hours, then disappear.

---

## Why

Every popular messenger has a server that someone owns. That server can be hacked, seized, ordered to hand data over, or switched off. Federation spreads the problem over more servers, it doesn't remove it.

Nevod starts from the opposite question: *what if the infrastructure has nothing to hand over?* Private keys are generated on the device and never leave it. Nodes store and forward ciphertext. The developer owns no master key, no escrow and no backups.

```
Request to the developer: "Hand over the keys."
The developer: "There are no keys here. By design."
```

The principle is described in the [ZKI Manifesto](PHILOSOPHY.md) (Russian original; English at [nevod.network/manifesto](https://nevod.network/manifesto/)).

## How it works

```
 phone ──wss──  Node A ──── Node B ──wss── phone
                  │  gossip    │
                Node C ──── Node D
```

- **Cell** — a participant (a person or an AI agent): an Ed25519 signing key + an X25519 encryption key. A contact is shared as a card or a QR code.
- **Node** — a small server that routes encrypted packets between cells, keeps the node table up to date by gossip, and buffers messages for offline recipients (72 h TTL).
- **Home node** — the node a cell is registered on. Each node decides who may join: open, by invitation code, or with administrator approval.

What a node sees in a message packet: the sender's and recipient's `cell_id@node_id` (routing metadata) and an opaque `{ephemeral_pubkey, nonce, ciphertext}` blob. Nothing else.

| Layer | Technology |
|---|---|
| Transport | WebSocket over TLS, the node's certificate pinned by fingerprint |
| Authentication (cell↔node, node↔node) | Schnorr zero-knowledge proof on Edwards25519 (Fiat–Shamir) |
| End-to-end encryption | X25519 + ChaCha20-Poly1305, HKDF-SHA256 |
| Signatures | Ed25519 — every packet is signed |
| Wire format | MessagePack |
| Node storage | SQLite, local only |
| Calls | WebRTC (DTLS-SRTP), TURN relay on the node |
| Push notifications | APNs — the push carries no message content |
| Node updates | Ed25519-signed release manifest |

## What's in this repository

| Path | What |
|---|---|
| [`node/`](node/) | The node — Python 3, asyncio: routing, gossip, storage, authentication, web admin panel, push, AI bots |
| [`nevod.py`](nevod.py) | Command line: create/start/join a node, test cells |
| [`tests/`](tests/) | Test suite (pytest) |
| [`ios/`](ios/) | The iOS app — Swift, SwiftUI, CryptoKit, WebRTC, CallKit |
| [`installer/`](installer/) | Running a node in Docker; desktop installer sources |
| [`website/`](website/) | Source of nevod.network (static generator, 8 languages) |
| [`CONCEPT.md`](CONCEPT.md), `TZ_*.md` | Concept and specifications (Russian) |
| [`Nevod_ZKI_v2.pdf`](Nevod_ZKI_v2.pdf) | ZKI concept paper |

## The iOS app

Text, photos, video, voice and video messages, files, voice calls through CallKit, reactions, editing, delete for everyone, chat lock, contacts by QR code, several nodes at once, AI assistants with your own API key. Interface in English, Ukrainian, Russian, German, Turkish, Spanish, Italian and French. Includes a Church Slavonic keyboard extension.

App Store release is in progress — see [nevod.network](https://nevod.network). To build it yourself: open `ios/Nevod/Nevod.xcodeproj` in Xcode, choose your team in *Signing & Capabilities* and change the bundle identifiers to your own. See [`ios/README.md`](ios/README.md).

An Android app is in development.

## Run a node

Requirements: Docker, 1 GB of RAM, and a public address or domain if phones should reach it from the internet (a local address is enough for a LAN).

```bash
git clone https://github.com/avk0978/nevod-messenger.git
cd nevod-messenger/installer/docker
cp .env.home.example .env        # fill in the values — see the comments inside
docker compose -f docker-compose.home.yml up -d --build
```

On first start the node creates its identity and database in `NEVOD_DATA_DIR`. The web admin panel listens on port 8766 (login with `NEVOD_ADMIN_PASSWORD`; its interface is in Russian for now): set the node's name, admission mode and invitation codes there. Details: [`installer/docker/README.md`](installer/docker/README.md).

## Development

```bash
pip install -r requirements.txt
python -m pytest            # 400+ tests

# a local node and two command-line cells
python nevod.py genesis 127.0.0.1:8765
python nevod.py cell init alice && python nevod.py cell connect alice.cell.json 127.0.0.1:8765
python nevod.py cell init bob   && python nevod.py cell connect bob.cell.json 127.0.0.1:8765
```

## People and AI agents in one network

A cell is a cell, whoever is inside. AI agents of different platforms can talk over Nevod the same way people do, end-to-end encrypted, with no operator seeing the content. Today a node can host AI assistant bots that answer with the user's own provider key (BYOK); the wider agent network is described in [`TZ_AGENTS.md`](TZ_AGENTS.md).

## Security

Found a vulnerability? Please don't open a public issue — write to **a.v.kolpakov@gmail.com**.

## Author

**Kolpakov Andrey** — author of the ZKI manifesto and developer of Nevod.
GitHub [@avk0978](https://github.com/avk0978) · ORCID [0009-0004-8678-077X](https://orcid.org/0009-0004-8678-077X) · DOI [10.5281/zenodo.19734648](https://doi.org/10.5281/zenodo.19734648) · a.v.kolpakov@gmail.com

The concept was first documented on 24 April 2026; its priority date is fixed by the Zenodo publication (DOI above).

## License

- Code: [GNU AGPL-3.0](LICENSE), with an additional permission to distribute through app stores (end of the LICENSE file). If you run a modified node as a service, its users are entitled to your source code.
- Concept and documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Third-party components: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Copyright © 2026 Kolpakov Andrey
