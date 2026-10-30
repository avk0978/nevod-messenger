# Calls through your own node

How Nevod connects calls, when a node needs its own call relay (TURN), and how to set one up on the same server. If you are just starting, you can skip this section: a node connected to the network gets a relay from the project nodes.

## How a call connects

Sound and video go **directly between the phones**, and the node only helps them agree on the connection. But a direct connection doesn't always work: mobile operators and many routers hide phones behind shared addresses (NAT), and two such phones can't reach each other. Then the call goes through a **relay (TURN)** — a server that forwards packets between the phones.

A call is encrypted from phone to phone (DTLS-SRTP). The relay sees only encrypted packets, the phones' addresses, and the call's time and volume — it can't hear or see the conversation.

## Do you need your own relay

**Without your own relay**, a node [connected to the network](../node-network/) requests access to a relay for each user who signs in, from one of the network's nodes that has one — chosen at random. Calls work, and there's nothing to set up. A node that isn't connected to the network gets no relay: calls between phones behind NAT may not connect for its users.

**Your own relay** is worth setting up if:

- you want your users' calls not to depend on the project nodes;
- your users are far from the project servers, and calls through them have a delay;
- you have many users and many calls.

What to keep in mind:

- **traffic.** The whole call goes through the relay: voice — about 100 kbit/s each way, video — 1–2 Mbit/s. Most VPS plans include several terabytes of traffic a month — for a node with dozens of users that's more than enough;
- **your relay will help other nodes of the network too.** The node tells the network it has a relay, and nodes without their own will hand it out to their users at random. The configuration below has limits so this doesn't eat the server's whole bandwidth.

## Installing coturn

We install coturn — the most common relay — right on the node's server. All commands are run on the server.

**1. Install coturn and create a secret:**

```
apt install -y coturn
openssl rand -hex 32
```

Save the output of the second command — it's the secret shared by the relay and the node.

**2. Find out the server's external IP address:**

```
curl -4 ifconfig.me
```

**3. Write the configuration.** Open the file:

```
nano /etc/turnserver.conf
```

delete everything in it and paste the following, with your IP address and secret:

```
listening-port=3478
external-ip=SERVER-IP-ADDRESS
realm=nevod
use-auth-secret
static-auth-secret=SECRET
min-port=49152
max-port=65535
no-tls
no-dtls
fingerprint
no-loopback-peers
no-multicast-peers
denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=100.64.0.0-100.127.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
total-quota=200
user-quota=10
max-bps=4000000
```

Save: **Ctrl+O**, **Enter**, **Ctrl+X**.

The `denied-peer-ip` lines forbid the relay to forward anything to internal addresses — including into Docker on this same server. Don't delete them. `total-quota`, `user-quota` and `max-bps` limit the number of simultaneous connections and the speed of one connection (4 Mbit/s).

**4. Start coturn:**

```
systemctl enable --now coturn
systemctl status coturn
```

The output should say `active (running)`. If coturn doesn't start, open `/etc/default/coturn` and uncomment the line `TURNSERVER_ENABLED=1` — some package versions need this.

**5. Open the ports:**

```
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
```

And the same ports in the provider's firewall, if there is one.

**6. Give the secret to the node.** In the `/opt/nevod/installer/docker` folder:

```
nano .env
```

put the same secret on the `TURN_SECRET=` line and apply:

```
docker compose up -d
```

## Checking

- **Diagnostics → Check → Dependencies and configuration** — there should be no warnings about TURN.
- The node gives phones the relay address `turn:your-domain:3478` — the domain must point to this server (it already does if the node works).
- Call from a phone on mobile data to a phone on Wi-Fi. If the call connects and both of you can be heard, the relay works. The coturn log: `journalctl -u coturn -n 50`.

> The relay works over UDP and TCP on port 3478 without encrypting the channel to the relay (the call itself is always encrypted). Some corporate networks block such ports — then calls from those networks won't go through the relay.
