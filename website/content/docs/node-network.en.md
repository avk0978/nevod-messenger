# Joining the Nevod network

Why a node needs the network, how to join with one button, and what other nodes see afterwards.

## Why join

A node that isn't connected to anyone is an island. It works, but:

- **its users can write to and call only each other.** Writing to someone on another node, or getting a message from them, is impossible — the node doesn't know where to send it;
- **phones don't get notifications** while the app is closed: only project nodes, which have the Apple key, can send push notifications to Nevod from the App Store, and they do it for the nodes of the network;
- **calls through difficult networks may not connect:** a node without its own call relay (TURN) gets one from the nodes of the network — more in [Calls through your own node](../node-turn/).

So it's almost always worth connecting your node to the network — even a closed family or organization node. Joining the network **doesn't open registration** and **doesn't show the node in "Explore Network"**: you still decide in the settings whom to admit and whether the node is visible.

## How to join

1. Make sure port **8765** on the server is open from outside — both in `ufw` and in the provider's firewall (see the [installation](../node-install/), steps 1 and 5). Nodes talk to each other through it.
2. Panel → **Nodes** → **Join the Nevod network**.
3. In a few seconds "Joined" appears. The status at the top of the block changes to "joined · nodes online: N", and the network's nodes appear in the **Known nodes** list.

The node joins through Nevod Open — a project node that admits nodes to the network without an invitation. Open's authenticity is checked by its certificate fingerprint, built into the node program: it can't be swapped on the way.

If the panel says that **the network node couldn't reach your node from outside**, the connection was made, but no one can connect back to you. It's almost always port 8765 being closed. Open it and press the button again. You can also check later: **Diagnostics → Check → External reachability**.

The connection is kept: after a restart, the node gets back in touch with all the nodes it knows by itself.

## Joining through another node

If you know the administrator of another node, you can join through their node instead of Open:

1. They, in their panel: **Nodes → Node invitations → + Create node invite** — and give you the token in person (the token is valid for 10 minutes).
2. You: **Nodes** → paste the token into the **Token from another node's administrator** field → **Join with token**.

The result is the same: your node becomes part of the network. In the same way you can let a node you know into the network through yours — create a token for it.

## What other nodes see

The nodes of the network exchange a list of nodes. About your node it contains:

- the node identifier (`node_id`), its name and its address for node-to-node connections (`domain:8765`);
- the node's certificate fingerprint;
- whether the node is visible in "Explore Network", and whether it has its own call relay and notification key.

If the node is visible in "Explore Network" (the `open` setting), the network's nodes also learn which cells are registered on it — by identifiers, without names. A closed node doesn't report this: a message to its user arrives at the address from the contact card, which names the home node.

What the network's nodes never get: message text, files, calls, users' contacts, the names and keys of a closed node's cells.

## How to leave the network

There's no separate "leave the network" button yet. Other nodes remove a node that hasn't been in touch for 72 hours from their lists by themselves. If the node needs to be disconnected from the network for good, stop it or close port 8765.
