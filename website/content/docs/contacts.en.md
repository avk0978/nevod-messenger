# Contacts

How to add someone, how cards and node members work, and how to rename, delete or block a contact.

Nevod has no search for people by phone number or by name across the network: no one can find you unless you shared your card with them or you are on the same node. This is intentional.

## Your card

A card is your address in Nevod: your identifier, the address of your home node and your public encryption key. There is nothing secret in it — you can send it any way you like.

**Profile → Share my card** — the app shows:

- **a QR code** — for the other person to scan when you are together;
- **Copy to clipboard** — the card text;
- **Share…** — send the card through another messenger, email or AirDrop.

## Add a contact

**Contacts** → the person-with-a-plus icon at the top right → **Add Contact**:

1. In the **Contact card** field, enter the card text you received — or tap the QR code icon next to the field and scan the card from the other person's screen.
2. In the **Alias** field, enter what this person will be called in your app. Only you see this name.
3. Tap **Add**.

If the app says "Invalid card format", the text wasn't copied completely — ask for it again.

When you add someone, they are notified: "… added you as a contact" appears at the top of their screen, with a field for a name and the buttons **Add** and **Ignore**. Likewise, "New contact wants to chat" appears when someone who isn't in your contacts writes to you for the first time. Whether to reply or add them is up to you.

## People on your node

The **Contacts** tab has two lists:

- **My contacts** — people you added yourself;
- **On this node** — members of your home node you haven't added yet. You can write to them and call them right away. To move someone to "My contacts", swipe the row left → **Add to My Contacts**.

Each node decides what "On this node" shows. On a private family or organization node, all members are usually visible. On a public node such as Nevod Open, members don't see each other — the list shows only the node's administration and bots.

## People on other nodes

Someone on another node is added the same way — by their card: it names their home node, and messages go there. You don't need to move to their node. If you were sent an **invitation** to another node but only want to chat, ask for a card instead.

One identity has one home node. If you are already registered and open an invitation to another node, the app changes nothing and warns you: to move, you first have to reset your identity (**Profile → Reset identity…**). A reset permanently deletes your identity, contacts, the messages on your phone and your registration on the old node. On the new node you will be a new user — people will have to add you again from your new card.

## Rename, delete, block

Open the chat with the person and tap the gear icon at the top right — **chat settings** open:

- **Name** — what the contact is called in your app;
- **Notifications** — turn off for no sounds and no notifications from this chat;
- **Block** — a blocked person can't write to you or call you and won't know about it. You can unblock them in the same place;
- **Report** — the report goes to the node's administration (more in [Security](../security/));
- **User ID** — the person's identifier, in case the administration asks for it.

**Delete a contact:** in the **Contacts** tab, swipe the row left → **Delete**. The conversation stays. If the person is a member of your node, instead of "Delete" you'll see **Move to On this node**: they simply go back to the list of node members.

> If a contact shows **Identity deleted**, this person has reset their identity or it was removed from the node. Writing to the old card is pointless — ask for a new one.
