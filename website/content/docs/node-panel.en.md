# First setup in the admin panel

The node is running — now you need to name it, decide whom to admit, and register on it yourself. All of this is done in the admin panel at `https://node.example.org/nevod-admin` (how to open it — step 9 of the [installation](../node-install/)).

The panel's language is switched in its header. A detailed description of every page and setting — see [The admin panel: every page and setting](../node-admin/).

## What's where in the panel

| Page | What it's for |
|---|---|
| **Overview** | The cells (users) registered on the node. |
| **Settings** | The node's name, admission mode, visibility. |
| **Join requests** | Users' requests, if the node works in approval mode. |
| **Inbox** | Users' messages to the node's administrator — reports, questions. You can reply right from here. |
| **Invitations** | Invite codes for users. |
| **Nodes** | Joining the Nevod network and the other nodes your node knows. |
| **Publishing**, **AI bots** | The bots and channels the node shows its users. |
| **Security** | Additional administrator accounts. |
| **Diagnostics** | The node's self-check and its log. |

## 1. Name the node

**Settings → Node name** → enter a name, for example "The Smiths" or "School No. 5" → **Save**.

Users see the name in the app. Other nodes of the network learn the new name after the node restarts (see below). You can't use names that pass the node off as a project node: with the words Nevod, admin, support, official and the like.

## 2. Decide whom to admit

**Settings → Cell admission mode.** A new node works **by invitation** by default: you can register only with a code you issued. Usually that's exactly what you need.

| Mode in the panel | Who can register | Who creates invite codes |
|---|---|---|
| `delegated` — invite code only (default) | Only with an invite code. Without a code the node doesn't accept the registration. | You in the panel, and users you have given the **Can invite** right. |
| `admin` — request + your approval | With a code — right away. Without a code the app sends a request by itself and shows "Waiting for approval"; you approve or decline it on the **Join requests** page. | Only you, in the panel. |
| `open` — no code | Anyone who knows the node's address. Suits an open community; keep in mind that you'll have to sort out registrations and taken names by hand later. | No code needed. |

The mode takes effect immediately.

## 3. Register on your node

1. In the panel: **Invitations** → choose how long the code is valid (1 hour, 24 hours or 7 days) → **+ Create code**. A QR code and a short code like `ABCD-EFGH` appear.
2. Install Nevod from the App Store on your phone.
3. Scan the QR code with the phone's regular camera. It's a link: the invitation page opens — tap **Open in Nevod** on it. The app opens with your node's address and the code already filled in.
4. Enter your name and tap **Get started**.

If scanning is inconvenient, tap **Copy link** in the panel and send it to yourself. If "Open in Nevod" didn't work: in the app tap **Start messaging**, enter your name, tap **Have an invite code?** and paste the link into the code field. The short code instead of the link works only when your node is already set in the app.

> If Nevod on this phone is already registered on another node (for example, Nevod Open), the invitation won't move you to your node by itself — the app warns that you first need to reset your identity: **Profile → Reset identity…**. A reset permanently deletes your identity, contacts, the messages on your phone and your registration on the old node. After the reset, open the invitation link again.

Each code works once. Create a separate one for each person — more in [Inviting people](../node-invite/).

## 4. Decide whether the node is visible in the network

**Settings → Visibility in "Explore Network"**:

- `closed` (default) — the node isn't shown in "Explore Network" to users of other nodes. Suits a family, an organization, any closed group.
- `open` — the node appears in "Explore Network", and users of other nodes can find it. Suits an open community. The node is visible while it's connected to the network, and only to people already registered on some node: before registering, the app shows only the project's nodes.

This choice doesn't open registration: whom to admit is still decided by the cell admission mode (step 2). The gold ring of a verified node in "Explore Network" currently exists only on Nevod project nodes.

This setting, like the node's name for other nodes, takes effect after the node restarts. On the server, in the `/opt/nevod/installer/docker` folder:

```
docker compose restart nevod_node
```

## 5. Check the node

**Diagnostics → Check.** In a few seconds the node shows whether everything is in order: whether its code is up to date, whether its settings match the database, whether there are configuration problems, whether the node is reachable from outside.

The node checks external reachability through other nodes of the network. While your node isn't connected to anyone, this line says "No known peers" — that's expected. Joining the network is the next step, and it matters: without it, phones won't get notifications while the app is closed. See [Joining the Nevod network](../node-network/).

## 6. Optional: more administrators

**Security → Add / change password** — each administrator gets their own login and password, and you can revoke them without changing the main password from `.env`. The main password stays as a fallback in case the others are lost.
