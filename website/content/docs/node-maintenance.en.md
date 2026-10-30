# Maintenance

Updating the node, backups, moving to another server, logs and routine server care. All `docker compose` commands are run on the server from the `/opt/nevod/installer/docker` folder:

```
cd /opt/nevod/installer/docker
```

## Updating the node

New versions of the node are released in the [source code on GitHub](https://github.com/avk0978/nevod-messenger) — to hear about them, press **Watch** there. To update:

```
cd /opt/nevod
git pull
cd installer/docker
docker compose up -d --build
```

The node restarts with the new version; users reconnect by themselves, and the data in the `data/` folder is kept. After updating, check the panel's **Diagnostics** → **Check**.

After a few updates, old images take up disk space — you can delete them:

```
docker image prune -f
```

## Backup

The most valuable thing on the server is the `data/` folder, and in it the `node.json` file: this is the node's identity. Lose it and the node will have to be created again, with a new identifier, and all users will have to register on it again. Make a copy at least once a week and after every change of settings.

**Make a copy** (the node stops for a few seconds):

```
docker compose stop nevod_node
tar czf ~/nevod-backup-$(date +%F).tar.gz data .env
docker compose start nevod_node
```

**Download it.** On your computer:

```
scp root@node.example.org:~/nevod-backup-*.tar.gz .
```

Don't keep the copy on the same server: if something happens to the server, the copy is lost with it.

> The copy contains the node's keys and the panel password from `.env`. Keep it as carefully as a password: an encrypted disk, a password manager with attachments or a similar place.

## Restoring and moving to another server

This is also how you move a node to a new server. The domain stays the same — only the server it points to changes.

1. On the new server, do steps 1 and 3–6 of the [installation](../node-install/) (server, Docker, firewall, download Nevod) — **without** steps 7–8.
2. Copy the backup to the new server and unpack it in the kit's folder:

   ```
   scp nevod-backup-DATE.tar.gz root@NEW-IP:/opt/nevod/installer/docker/
   ```

   and on the new server:

   ```
   cd /opt/nevod/installer/docker
   tar xzf nevod-backup-DATE.tar.gz
   ```

3. **Stop the node on the old server** (`docker compose down`) — two nodes with the same identity must not run at the same time.
4. Change the domain's A record to the new server's IP and wait until `ping node.example.org` shows the new address.
5. Start the node on the new server: `docker compose up -d --build`. Caddy obtains the certificate again by itself.

Users don't need to do anything: the app connects to the same domain and finds the same node there.

> The node's **domain** can't be changed that easily: the address for connections with other nodes is written into the node's identity on its first start. Choose a domain you won't have to change.

## Logs

```
docker compose logs --tail 100 nevod_node
docker compose logs -f nevod_node
```

The first command shows the last 100 lines, the second follows the log in real time (exit with **Ctrl+C**). Caddy's log — `docker compose logs caddy`. The node's latest entries are also visible in the panel: **Diagnostics → Logs**.

Logs are limited in size: 3 files of 10 MB per container, and old entries are overwritten by themselves. Message text never gets into the log.

## Restart, stop, password

| What you need | Command |
|---|---|
| Restart the node (for example, after changing the name or visibility in the panel) | `docker compose restart nevod_node` |
| Stop everything | `docker compose down` |
| Start again | `docker compose up -d` |
| See what's running | `docker compose ps` |

**Change the main panel password:** put the new one on the `NEVOD_ADMIN_PASSWORD` line in `.env` (`nano .env`) and run `docker compose up -d` — the node restarts with the new password. Personal accounts from the "Security" page aren't affected.

## Server care

- **System updates** — once a month or more often:

  ```
  apt update && apt upgrade -y
  reboot
  ```

  After a reboot, the node, Caddy and coturn (if you installed it) start by themselves.
- **Disk space** — `df -h /`. If space is low, delete old images (`docker image prune -f`) and old backups on the server.
- **The HTTPS certificate** is renewed by Caddy by itself. There's nothing to do, but port 80 must stay open.
- **Node unreachable?** The easiest way to find out right away is to point a free website uptime monitor at `https://node.example.org`: it emails you if the node stops responding.

## If the node was down for a long time

The node keeps messages for users who haven't come online for up to 72 hours, then deletes them. Other nodes of the network remove a node that hasn't been in touch for 72 hours from their lists — after it starts, it gets back into them by itself as the lists are exchanged.
