# Inviting people

How people get onto your node — by invitation, by request or freely — and how they then find each other, including people on other nodes. Which mode to use is decided in the panel: **Settings → Cell admission mode** (see [First setup](../node-panel/), step 2).

## An invitation from the administrator

The main way — and the only one while the node works in the default mode (`delegated`).

1. Panel → **Invitations** → choose how long the code is valid: 1 hour, 24 hours or 7 days → **+ Create code**.
2. Give the person the invitation in one of these ways:
   - **show the QR code** on screen — the person scans it with the phone's regular camera;
   - **Copy link** — and send it through any messenger or by email;
   - **read out the short code** like `ABCD-EFGH` — this works only if the person's app already has your node set.
3. The person installs Nevod from the App Store, opens the link (the invitation page has an **Open in Nevod** button), enters a name and taps **Get started**.

What to know about codes:

- **Each code works once.** One code per person. A used code is marked "used" in the list, with who joined with it.
- **Validity period.** Don't choose a week for a code you post in a group chat: until the code is used, anyone who gets hold of it can use it. 1 hour is for a code you show someone in person.
- **The link reveals nothing extra.** It contains only the node's address and the code. The invitation page on nevod.network sees neither the code nor the address: they stay in the part of the link after `#`, which the browser doesn't send to the server.

If the person already uses Nevod on another node, the invitation won't move them by itself: the app warns that they first need to reset their identity (**Profile → Reset identity…**). A reset permanently deletes their identity, contacts, the messages on their phone and their registration on the old node. To simply chat with them, they don't need to move: exchanging contacts is enough (see below).

## Members invite people themselves

In `delegated` mode you can entrust invitations to people you trust: panel → **Invitations** → **Admitted cells** → turn on **Can invite** for the person. Then **Profile → Invite someone** in their app creates a code, and the app shows a QR code to scan.

In `open` mode any member can invite — but in this mode no code is needed anyway.

## Requests with approval

`admin` mode suits you if you want people to be able to find the node and ask to join, while you decide.

1. The person finds your node in "Explore Network" and taps **Join this node** (if the node is visible there, see [First setup](../node-panel/), step 4) — or, on the app's first launch, taps **Change server…** and enters the node's address `node.example.org/nevod-ws`.
2. The app sends a request by itself and shows "Waiting for approval".
3. The request appears in the panel on the **Join requests** page. If your `cell_id` is entered in **Settings → Administrators**, you also get a message in Nevod.
4. **Approve** — the person gets a notification and is in right away. **Deny** — the app shows them that the request was declined.

Invite codes work in `admin` mode too — with a code a person gets in right away, without a request.

## Free registration

In `open` mode anyone who knows the node's address can register. This suits an open community. Keep in mind:

- the node never deletes registrations or frees names by itself — you'll have to clean up by hand, on the **Overview** page (the ✕ button);
- service names (Nevod, administrator, support and the like) can't be taken in any mode.

## How members find each other

Registering on the same node doesn't make people each other's contacts. To chat, they need to exchange contacts:

- **Profile → Share my card** — shows a QR code and the card text; the other person: **Contacts → Add Contact**, then scans the QR code or pastes the text;
- the card can be sent any way — there's nothing secret in it, only an identifier and public keys.

People **on other nodes** are added the same way — the card contains the address of their home node. For such conversations to work, your node must be [connected to the Nevod network](../node-network/).

> Deleting a user (panel → **Overview** → ✕) fully revokes their admission: the registration, undelivered messages and notification tokens are deleted. To come back, the person will need a new invitation.
