# Installation step by step

How to set up a Nevod node on a rented server from scratch: from buying the server to your first login to the admin panel. The example uses a server with Ubuntu 26.04 and the domain `node.example.org`; replace it with your own everywhere.

All the commands below are entered in the server's terminal; you can copy them whole. What a node is and what it stores — see [How a node works](../node-how/).

## 1. Rent a server

Any VPS from any provider will do: 1 CPU, 1 GB of memory, 10 GB of disk, **Ubuntu 24.04** or **26.04**. When you order, the provider gives you the server's **IP address** and the password of the `root` user (or asks you to upload an SSH key).

If the provider has its own network firewall in the control panel (for example, Firewalls at Hetzner, Security groups elsewhere), open the incoming ports **22, 80, 443 and 8765** (TCP) in it.

## 2. Point the domain at the server

The node needs a domain or subdomain of its own, for example `node.example.org`. There are two reasons it can't do without one:

- **Phones connect to the node at `https://domain/nevod-ws`.** Caddy gets the HTTPS certificate that an iPhone trusts without any setup from Let's Encrypt, for a domain name.
- **The node's address is stored everywhere:** on users' phones, in their contact cards, on other nodes in the network. If you move to another server or your provider changes the IP address, you fix one DNS record and users notice nothing. With a bare IP address, a move would cut everyone off, and you would have to send out invitations again.

If you don't have a domain yet, you can buy one from any registrar (Cloudflare, Namecheap, Porkbun, Gandi and others) — usually a few dollars or euros a year. One subdomain is enough for the node, and the domain itself can serve other purposes too.

In your domain's control panel, create an **A record**: name — for example `node` (giving `node.example.org`), value — the server's IP address.

Wait a few minutes and check from any computer:

```
ping node.example.org
```

The reply should show your server's IP address. Until it does, there's no point going further: an HTTPS certificate is issued only for a domain that already points at the server.

> If the domain is served by Cloudflare, turn off proxying for this record (grey cloud, "DNS only"). Otherwise phones and other nodes will connect to Cloudflare instead of your server.

## 3. Connect to the server

On your computer, open a terminal (PowerShell on Windows, Terminal on a Mac) and enter:

```
ssh root@node.example.org
```

On the first connection, answer `yes` and enter the password from the provider.

## 4. Install Docker and git

```
apt update && apt upgrade -y
apt install -y git
curl -fsSL https://get.docker.com | sh
```

The last command is the official Docker installer. Check that everything is in place:

```
docker compose version
```

You should see a line like `Docker Compose version v…`.

> If after the update you see `*** System restart required ***` (on screen or at your next login), restart the server with `reboot`, reconnect a minute later (step 3) and carry on.

## 5. Turn on the firewall

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8765/tcp
ufw enable
```

Answer `y` to the question. Ports 80 and 443 are needed for HTTPS (phones and the panel), 8765 for talking to other nodes.

> Docker opens its containers' ports by itself, bypassing `ufw`. That's why in our kit the admin panel (port 8766) is published only to the server itself — don't change this in `docker-compose.yml`.

## 6. Download Nevod

> All the commands below are typed on the server: the prompt on the left should start with `root@…`. If it shows `PS C:\…>` or your computer's name, the connection to the server has closed — reconnect (step 3).

```
git clone https://github.com/avk0978/nevod-messenger.git /opt/nevod
cd /opt/nevod/installer/docker
```

## 7. Fill in the settings

Create the settings file from the template:

```
cp .env.example .env
```

Come up with a password for the admin panel. The easiest is to generate a long random one:

```
openssl rand -base64 24
```

Copy the result and save it somewhere safe — for example, in a password manager (Bitwarden, KeePass, Passwords on iPhone and Mac). Now open the settings file:

```
nano .env
```

Change two lines:

```
NEVOD_DOMAIN=node.example.org
NEVOD_ADMIN_PASSWORD=the-generated-password-here
```

Leave the rest as it is. Save the file: **Ctrl+O**, then **Enter**; exit with **Ctrl+X**.

| Setting | What it means |
|---|---|
| `NEVOD_DOMAIN` | The node's domain. Phones connect to `https://domain/nevod-ws`, other nodes to `domain:8765`. |
| `NEVOD_ADMIN_PASSWORD` | The admin panel password. The node won't start without it. |
| `NEVOD_ADMIN_PUBLIC` | `true` — the panel opens in a browser at `https://domain/nevod-admin`; `false` — the panel is closed to the internet (see step 10). |
| `TURN_SECRET` | Only if you set up your own call relay, see [Calls through your own node](../node-turn/). Usually empty. |

## 8. Start the node

```
docker compose up -d --build
```

The first start takes a few minutes: Docker builds the node image and downloads Caddy. When the command finishes, check:

```
docker compose ps
```

Both containers — `nevod_node` and `nevod_caddy` — should be `Up` (or `running`).

## 9. Check that everything works

Open `https://node.example.org` in a browser — you should see the line "Nevod node — https://nevod.network", and the browser shouldn't complain about the certificate.

Now open `https://node.example.org/nevod-admin`. The browser asks for a user name and password: any user name, and the password you put in `.env`. The admin panel opens. What to do in it first — see [First setup in the admin panel](../node-panel/).

> Five wrong passwords in a row from one address lock the panel for that address for 15 minutes. If this happens, just wait.

## 10. Optional: close the panel to the internet

If you don't want the panel's address to open from the internet at all, change the line `NEVOD_ADMIN_PUBLIC=true` in `.env` to `NEVOD_ADMIN_PUBLIC=false` and apply it:

```
docker compose up -d
```

Then the panel is reachable only through an SSH tunnel. On your computer, run

```
ssh -L 8766:127.0.0.1:8766 root@node.example.org
```

and, while that window stays open, open `http://localhost:8766/nevod-admin` in a browser.

If port 8766 is already taken on your computer (for example, another Nevod node runs there), pick another one: `ssh -L 18766:127.0.0.1:8766 root@node.example.org` and `http://localhost:18766/nevod-admin`. The first number is the port on your computer, the second is the panel's port on the server — leave that one as it is.

## If something is wrong

| What you see | What's usually the cause |
|---|---|
| The browser says the certificate is invalid, or the site doesn't open | The domain doesn't point at the server yet (step 2), or port 80/443 is closed (steps 1 and 5). Look at Caddy's log: `docker compose logs caddy`. Once the cause is fixed, Caddy retries by itself. |
| `docker compose up` says `address already in use` | Another web server is already running on the server (often Apache or nginx from the provider). Stop it: `systemctl disable --now apache2` or `systemctl disable --now nginx`. |
| The error `set NEVOD_ADMIN_PASSWORD in .env` or `set NEVOD_DOMAIN in .env` | That line in `.env` isn't filled in (step 7). |
| You made a typo in the domain in `.env` (no certificate, `NXDOMAIN` in Caddy's log) | Stop the node: `docker compose down`, fix `NEVOD_DOMAIN` in `.env`, delete the data folder: `rm -rf data`, and start again: `docker compose up -d`. Delete `data` only while nobody is registered on the node yet — otherwise the node keeps the old address and you would have to fix it by hand. |
| The panel keeps asking for the password | Wrong password. To see which one is set: `grep PASSWORD .env`. |
| The panel replies "Too many failed logins" | The brute-force protection kicked in — wait 15 minutes. |
| `nevod_node` keeps restarting | The node's log shows why: `docker compose logs --tail 50 nevod_node`. |

The full logs of both containers: `docker compose logs`. All `docker compose` commands are run from the `/opt/nevod/installer/docker` folder.
