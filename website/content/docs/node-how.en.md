# How a node works

A node is a program on a server through which phones exchange messages and set up calls. Here, briefly, is what a node does, what it stores and what it can't see — so that before installing you know what you are taking on.

## Node, cell and home node

Every Nevod user is a **cell**: a pair of encryption keys that is created on the phone and never leaves it. A cell registers on one node — its **home node**. Through it the phone receives messages that were sent while it was switched off.

Nodes are linked into one network. If you write to someone on another node, your node passes the encrypted message to their node. There is no central server: the network is the nodes themselves.

The load on a node depends only on its own circle — its users and bots — and not on the size of the whole network: a node neither relays nor stores other nodes' messages. That's why an ordinary computer is enough for a node, and it won't get any heavier no matter how many people join Nevod on other nodes. Such networks are called **low-load** (class LL-0) — see the article ["Low-Load Distributed Data Networks"](../../publications/low-load-networks/) (DOI 10.5281/zenodo.23621073).

## Kinds of nodes

All nodes run the same program. What a node becomes — a closed family node, an open community node or an organization's node — is decided by three settings in the [admin panel](../node-admin/):

- **whom to admit** — the cell admission mode: only with an invite code, with a code or by request with your approval, or everyone (details in the table in [First setup](../node-panel/), step 2);
- **whether the node is visible in "Explore Network"** to users of other nodes;
- **what the node shows its users** — the bots and pages published on it.

| What kind of node | Whom to admit | Visible in "Explore Network" | Example |
|---|---|---|---|
| Closed: family, friends, organization | with an invite code | no | a company node where the administrator invites every employee |
| Community with selection | with a code or by request with approval | yes | a club node: anyone can find it, but the administrator approves members |
| Open community | everyone | yes | a public node like Nevod Open |

**Where the node runs** — on a rented server with a domain or at home on your own computer — doesn't affect what it can do. A home node needs to be reachable from the internet: port forwarding on the router and a domain. That's why it's easier to start with a rented server — all the documentation is written for one.

**Important for a home node: from your home network it is reached by different rules.** Phones connect to the node by its domain, and the domain points to your router's external address. A phone on your home Wi-Fi reaches that external address from inside the network, and many routers don't let such connections through. Then the node works over mobile data, but over home Wi-Fi the app says "No connection". Connecting by the server's local address (for example, `192.168.1.10`) won't work either: the certificate is issued for the domain, not for the address. This is solved on the router, in one of two ways:

- turn on **NAT loopback** (also called NAT hairpinning or NAT reflection), if the router supports it;
- or add a local record to the router's DNS: your domain → the server's local address.

Check this right after installing: connect to the node from a phone both over home Wi-Fi and over mobile data.

**Nevod project nodes** — Nevod Open, Dev Planet and a few others — differ from the rest not in their program but in three things:

- they have an Apple key for push notifications and a call relay, and they share them with the nodes of the network (see below);
- in "Explore Network" they are marked with a **gold ring** of a verified node and a purpose label — "Community", "Informational", "AI Agent". The ring is confirmed by the project curator's signature and currently exists only on project nodes;
- **Nevod Open** is the node on which the app registers users by default, and the entry point to the network for new nodes: you can connect to it without an invitation.

> The panel settings also have "Node type" — `permanent` or `temporary` — and "Parent node ID". These are **in development**: temporary nodes (for example, for the duration of an event). The app doesn't use them yet — leave `permanent` and the parent node ID empty.

## What a node stores

- **Cell registrations**: the identifier, public keys and the display name the user chose.
- **Undelivered messages** — encrypted, until the recipient comes online, but no longer than 72 hours. After delivery the message is deleted.
- **Notification tokens** of phones — to "wake up" a phone when a message or call arrives.
- **Invite codes**, join requests, users' messages to the node's administrator.
- **The list of other nodes in the network** and its own settings.
- **Technical logs** — limited in size (3 files of 10 MB per container); old entries are overwritten.

## What a node can't see

- **The text of messages, photos, videos, voice messages and files.** They are encrypted on the sender's phone with the recipient's key. The node delivers them without having the key that could open them.
- **The content of calls.** Sound and video go between the phones directly or through a relay (TURN), encrypted.
- **Contacts and conversations on the phone.** They are stored only on the device.

What the node does see: which cells are registered on it and under which names, who writes to whom and when, message sizes, the IP addresses of connections. This is delivery data — the node couldn't work without it. More in the [Privacy Policy](../../privacy/).

> The node owner is responsible for keeping the node running and for backing up its data. They can't read users' conversations — this follows from how the network is built, not from a promise.

## Notifications and calls through project nodes

Only a node that has an Apple key can send push notifications to the Nevod app from the App Store, and only project nodes have it. So a node connected to the network asks a project node to send the notification for it. The project node sees the phone's token and the sender's name for the notification title, and the text is always the same — "New message". If the sender is in the recipient's contacts, the phone itself substitutes the name they are saved under.

**Can I send notifications from my node directly?** No. Notifications to an app from the App Store are accepted only with a key of the Apple developer account the app was released under — and Nevod is released by the project. This key can't be given to node owners: it can't be limited to one node, and it lets you send any notification with any text to any Nevod user. That's why notifications go through project nodes, and their text is always "New message".

In the same way, a node without its own call relay (TURN) gets one from the nodes of the network — more in [Calls through your own node](../node-turn/).

Hence an important conclusion: **a node that isn't connected to the network will deliver messages, but phones won't get notifications** while the app is closed. How to connect — see [Joining the Nevod network](../node-network/).

## What the installation consists of

The ready-made server kit (the `installer/docker` folder in the [source code](https://github.com/avk0978/nevod-messenger)) is two Docker containers:

| Container | What it does | Ports |
|---|---|---|
| `nevod_node` | the node itself | 8765 — for other nodes; 8766 — the admin panel, reachable only from the server itself |
| `nevod_caddy` | the Caddy web server: obtains an HTTPS certificate for your domain by itself and passes phone and panel connections to the node | 80 and 443 |

All the node's data is in the `data/` folder next to the settings file:

- `node.json` — **the node's identity**: its keys. Lose this file and you lose the node: a node with the same identity can't be created again, and all users would have to register on a new one. Keep a backup.
- `node.db` — the database: registrations, invitations, the message buffer.

## What you'll need

- **A Linux server** — the cheapest rented VPS will do: 1 CPU, 1 GB of memory, 10 GB of disk. That's enough for tens and hundreds of users.
- **A domain** (or subdomain) you can point at the server — for example `node.example.org`. Without a domain, phones can't verify the HTTPS certificate.
- **About half an hour** and the ability to connect to the server over SSH. All commands are in [Installation step by step](../node-install/) — you can copy them as they are.
