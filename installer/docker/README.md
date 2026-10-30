# Running a Nevod node in Docker

Two ready setups live in this folder:

| File | For |
|---|---|
| `docker-compose.yml` + `Caddyfile` | **A server with its own domain** (a rented VPS, an office server). The node plus Caddy, which gets a Let's Encrypt certificate by itself. Start here. |
| `docker-compose.home.yml` | A home computer whose reverse proxy already runs on the host itself. |

The step-by-step guide, written for someone doing this for the first time, is on the site: https://nevod.network/en/docs/

## Server with a domain (`docker-compose.yml`)

You need: a Linux server with Docker, a domain whose DNS **A record points to the server**, open ports **80**, **443** (Caddy, certificates and phones) and **8765** (other nodes).

```bash
git clone https://github.com/avk0978/nevod-messenger.git
cd nevod-messenger/installer/docker
cp .env.example .env
nano .env          # NEVOD_DOMAIN and NEVOD_ADMIN_PASSWORD
docker compose up -d --build
```

| Variable | Meaning |
|---|---|
| `NEVOD_DOMAIN` | The node's domain, e.g. `node.example.org`. Phones connect to `https://NEVOD_DOMAIN/nevod-ws`, other nodes to `NEVOD_DOMAIN:8765`. |
| `NEVOD_ADMIN_PASSWORD` | Admin panel password — **required**, the node doesn't start without it. Long and random (`openssl rand -base64 24`). It stays a permanent emergency login; more admin accounts can be added in the panel. |
| `NEVOD_ADMIN_PUBLIC` | `true` (default): the panel is at `https://NEVOD_DOMAIN/nevod-admin`. `false`: closed to the internet, see below. |
| `TURN_SECRET` | Only if this node runs its own TURN relay for calls. |

Then open `https://NEVOD_DOMAIN/nevod-admin` (any user name, the password from `.env`; the panel is available in 8 languages — switch it in the header) and set the node's name and admission mode.

What is where:

| Port | Who | Notes |
|---|---|---|
| 80, 443 | Caddy | certificate, `/nevod-ws` (phones), `/nevod-card/` (contact cards), `/nevod-admin` |
| 8765 | node | other nodes, TLS with a self-signed certificate pinned by fingerprint |
| 8766 | node | admin panel, published on **127.0.0.1 only** — never publish it on all addresses: Docker bypasses `ufw` |

Five wrong passwords from one address lock that address out of the panel for 15 minutes (`NEVOD_ADMIN_MAX_FAILED_LOGINS`).

### Panel closed to the internet (`NEVOD_ADMIN_PUBLIC=false`)

Caddy then answers 404 on `/nevod-admin`. Reach the panel through an SSH tunnel from your own computer:

```bash
ssh -L 8766:127.0.0.1:8766 user@your-server
```

and, while that session is open, browse to `http://localhost:8766/nevod-admin`.

## Home computer (`docker-compose.home.yml`)

```bash
cp .env.home.example .env
docker compose -f docker-compose.home.yml up -d --build
```

| Variable | Meaning |
|---|---|
| `NEVOD_DATA_DIR` | Absolute host path for the node's data (identity, database, admin account). Forward slashes on Windows too. |
| `NEVOD_ADDRESS` | `host:port` the node announces to other nodes. Used only on the very first start, when the data folder has no `node.json` yet. |
| `NEVOD_PUBLIC_CLIENT_ADDR` | Address phones get in invitation codes — usually `yourdomain/path` served by your reverse proxy. |
| `NEVOD_ADMIN_PASSWORD` | As above — required. |
| `TURN_SECRET` | Only if this node runs its own TURN relay for calls. |

The node listens for clients on port **8765** (WebSocket over TLS, self-signed certificate pinned by fingerprint) and serves the panel on **127.0.0.1:8766**. Your reverse proxy on the host forwards `/nevod-ws` to `https://127.0.0.1:8765` (skip certificate verification for that hop) and `/nevod-card/`, `/nevod-admin` to `http://127.0.0.1:8766`, setting `X-Real-IP`.

## Updating

```bash
git pull
docker compose up -d --build          # or: -f docker-compose.home.yml
```

The data folder (`data/`, or `NEVOD_DATA_DIR`) is kept between rebuilds — back it up: it holds the node's identity, and a node can't be recreated with the same identity without it. Logs are capped at 3 × 10 MB per container.
