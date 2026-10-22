# Running a Nevod node in Docker

`docker-compose.home.yml` builds the node image from the repository root and runs it with its data in a folder on the host.

## Steps

1. Install Docker (Docker Desktop on Windows/macOS, Docker Engine on Linux).
2. Copy the example settings and fill them in:
   ```bash
   cp .env.home.example .env
   ```
   | Variable | Meaning |
   |---|---|
   | `NEVOD_DATA_DIR` | Absolute host path for the node's data (identity, database, admin account). Forward slashes on Windows too. |
   | `NEVOD_ADDRESS` | `host:port` the node announces to other nodes. Used only on the very first start, when the data folder has no `node.json` yet. |
   | `NEVOD_PUBLIC_CLIENT_ADDR` | Address phones get in invitation codes — usually `yourdomain/path` served by your reverse proxy. |
   | `NEVOD_ADMIN_PASSWORD` | Password for the web admin panel — **required**: without it the panel doesn't start. It stays a permanent emergency login; further admin accounts can be added in the panel. |
   | `TURN_SECRET` | Only if this node runs its own TURN relay for calls. |
3. Start it:
   ```bash
   docker compose -f docker-compose.home.yml up -d --build
   ```
4. Open the admin panel on port **8766** (HTTP Basic Auth, the password from step 2; the interface is available in 8 languages — switch it in the header) and set the node's name, admission mode (open / invitation code / administrator approval) and invitation codes.

The node listens for clients on port **8765** (WebSocket over TLS, self-signed certificate pinned by fingerprint). To reach it from the internet, forward the port or put it behind a reverse proxy such as Caddy or nginx under your domain.

## Updating

```bash
git pull
docker compose -f docker-compose.home.yml up -d --build
```

The data folder is kept between rebuilds. Logs are capped at 3 × 10 MB.
