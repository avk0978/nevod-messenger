# The admin panel: every page and setting

A reference for the node's admin panel: what's on each page and what each setting does. If you have just installed the node, start with [First setup in the admin panel](../node-panel/) — it covers the essentials step by step.

The panel opens at `https://your-domain/nevod-admin` (or through an SSH tunnel if you closed it — see the [installation](../node-install/), step 10). Any user name; the password is `NEVOD_ADMIN_PASSWORD` from `.env` or a personal one created on the "Security" page. The language is switched in the header.

## Header

At the top of every page — the node's name, its identifier (`node_id`) and badges with the current state: whether the node is visible in "Explore Network", the cell admission mode, who sees the published cells.

## Overview

A list of all cells (users and bots) registered on the node.

| Column | What it shows |
|---|---|
| Name | Your own label for this cell — only you see it, in the panel. Type it and press ✓ or Enter. It doesn't change the name the user chose. |
| `cell_id` | The cell's identifier. The full one is in the tooltip. |
| Status | Online or offline — whether the app is connected right now. |
| Buffer | How many messages are waiting for the user to come online (kept up to 72 hours). |
| Registration | When the cell registered. |

Buttons:

- **✕** in a row — delete the cell. This fully revokes its admission: the registration, undelivered messages and notification tokens are deleted, and the name is freed. To come back, the person will need a new invite code or a new request. The node never deletes cells by itself — only you do.
- **Reset registrations** — all cells re-register on their next connection; no need to enter a code again.
- **Full reset** — irreversible: all members will have to sign in again with an invite code. In practice it's needed only when moving or completely changing the node's membership.

## Settings

| Setting | What it does | When it takes effect |
|---|---|---|
| **Node name** | The node's name that users see. Service words (Nevod, admin, support, official and the like) can't be used. | In the panel — immediately; for other nodes — after a restart. |
| **Node type** *(in development)* | `permanent` — a regular node. `temporary` — a temporary node, for example for the duration of an event; the app doesn't use such nodes yet. Leave `permanent`. | After a restart. |
| **Parent node ID** *(in development)* | Needed only by a temporary node: which permanent node it belongs to. Leave it empty. | Immediately. |
| **Visibility in "Explore Network"** | `closed` — the node isn't shown to users of other nodes. `open` — the node appears in their "Explore Network". This doesn't open registration. | After a restart. |
| **Visibility of published cells** | Who sees the list of bots and pages from the "Publishing" page: `off` — no one, `members` — only this node's users, `public` — everyone. | Immediately. |
| **Cell admission mode** | `delegated` — invite code only; `admin` — with a code or by request with your approval; `open` — anyone who knows the address. | Immediately. |
| **Administrators** | The identifiers (`cell_id`) of your own cells, comma-separated. In `admin` mode they get a message in Nevod about every new request. You can find your `cell_id` on the "Overview" page. | Immediately. |

Restart the node on the server, in the `/opt/nevod/installer/docker` folder:

```
docker compose restart nevod_node
```

## Join requests

Works in the `admin` admission mode. When someone without a code tries to register, the app sends a request by itself — it appears here with a name and a note. **Approve** — the person gets access and a notification on the phone right away. **Deny** — the app shows them that the request was declined.

## Inbox

Messages the node's users sent to its **administrator** account from the app: reports about messages, questions. Every node has an administrator account; it is created by itself on the first start.

Open a conversation, write a reply and press **Reply** — the reply goes to the user in Nevod, encrypted, on behalf of administrator. Users' messages are answered only this way, in the app, not by email.

If the user attached the app's log to the message (to investigate a problem), a **download nevod.log** link appears in the conversation.

Users see your node's administrator account marked **Node administrator** with the node's name. The mark is confirmed by your node's key, so no one else can pose as your node's administrator. The blue ✓ badge is the sign of the Nevod project administration: it is confirmed by the project curator's signature and exists only on project nodes.

## Invitations

**Create a code:** choose the validity (1 hour, 24 hours, 7 days) → **+ Create code**. A QR code and a link appear — you can show them on screen, forward them or press **Copy link**. The link opens Nevod with the node address and code already filled in. The short code like `ABCD-EFGH` works only if the person's app already has your node set.

Each code works once. Below are all the codes with their validity and status: active, used, by whom.

**Admitted cells** — who joined and on whose invitation. The **Can invite** switch lets that person create codes from the app (Profile → Invite someone) — in `delegated` mode this is how you entrust invitations to people you trust.

More in [Inviting people](../node-invite/).

## Nodes

**Joining the Nevod network.** The status ("joined · nodes online" or "not joined") and the **Join the Nevod network** button. A joined node gets push notifications for phones and a call relay from the project nodes. The **Token from another node's administrator** field is for joining through another node instead of Nevod Open. More in [Joining the Nevod network](../node-network/).

**Known nodes** — all the network nodes your node knows about: name, address, online or not, when last in touch. A node that hasn't been in touch for 72 hours is removed from the list and comes back by itself when it appears in the network again.

**Node invitations** — a token another node can use to join through yours. It's valid for 10 minutes; give it to the other node's administrator in person, not publicly.

## Publishing

The bots and pages your node shows users in the app — on the node's "planet" in "Explore Network". Choose a cell, set a title, a type (`bot` — a bot, `page` — a page with text) and a description → **Publish**. **Unpublish** removes it from the list; the cell itself stays.

The Claude, ChatGPT, Gemini checkboxes are for an external AI bot that works on the user's key: which providers it accepts. For a regular bot, leave them unchecked.

Who sees this list is set in "Settings" → "Visibility of published cells".

## AI bots

AI bots that run right inside the node and answer through Claude, ChatGPT or Gemini **on the user's key**: a person adds their key in the chat with the bot, the key arrives with every message and isn't stored by the bot. The node has no keys of its own and doesn't pay for AI.

**Add a bot** — set a name, a description, an instruction for the model and the providers, or take a ready template (AI Assistant, Tolmach the translator) and adjust it. An enabled bot appears for the node's users in the "On this node" list. A disabled one is stopped and hidden, and keeps its name. Deleting is permanent: the bot's keys and name are deleted, while users keep their conversations.

> Conversations with an AI bot are decrypted by code on your node and passed to the chosen provider. Users are warned about this in the [Privacy Policy](../../privacy/) (section 5). If you turn on AI bots, you as the node owner take part in this transfer.

## Security

Personal administrator accounts: **Add / change password** — a login and password (stored as a hash). One account per administrator; when someone leaves, delete their account without changing the main password. The main password from `.env` always works as a fallback.

Five wrong passwords in a row from one address lock sign-in for that address for 15 minutes.

## Diagnostics

**Check** — the node's self-check (up to 10 seconds):

| Check | What it means |
|---|---|
| Code up to date | Whether the installed node build is behind the protocol — if it is, update the node (see [Maintenance](../node-maintenance/)). |
| identity/DB consistency | Whether the settings in `node.json` match the database. |
| Dependencies and configuration | Whether there are errors in the settings (for example, a call relay without `TURN_SECRET`). |
| External reachability | Whether another node of the network can reach yours from outside. While the node isn't connected to the network, it shows "No known peers" — that's expected. |

**Logs** — the latest entries of the node's log. Message text never gets into the log.
