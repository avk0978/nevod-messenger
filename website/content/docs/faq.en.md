# Questions and problems

Short answers to common questions and what to do if something doesn't work. If your question isn't here, write to us (see the end of this section).

## General questions

**Is Nevod paid?**
No. The app is free, with no subscriptions and no ads. You may only need to pay an AI provider if you use AI assistants with your own key — see [Bots and AI assistants](../bots/).

**Do I need a phone number?**
No. Nevod doesn't need a phone number or an email address and doesn't ask for them. Only people you exchanged cards with know you.

**Is there Nevod for Android or a computer?**
Right now — only iPhone and iPad. An Android version is in development.

**Can I use Nevod on two devices at once?**
Not yet: an identity lives on one device. On a second iPhone or iPad you'll have a separate identity with its own contacts.

**I changed my phone. How do I move my conversations?**
There is no way yet: there's no transfer to a new device, and Nevod deliberately makes no message backups. On the new phone, create a new identity and send your contacts your new card. More in [Security and backups](../security/).

**How do I move to another node?**
Only through an identity reset: **Profile → Reset identity…**, then open the invitation to the new node. A reset permanently deletes your identity, contacts, the messages on your phone and your registration on the old node. To simply chat with someone on another node, you don't need to move — their card is enough.

## Registration

| What you see | What to do |
|---|---|
| "Name already taken, choose another" | this name already exists on the node, or it's a service name (administrator, support, Nevod…). Choose another. |
| "Invite code required" | the node admits people only by invitation. Ask the node's administrator for an invitation or choose another node. |
| "Invalid or expired code — get a new one" | the code has already been used or has expired. Ask for a new one. |
| "Waiting for approval" | the node admits people by request — wait for the administrator's decision; you'll get a notification. |
| "Request denied" | the node's administrator declined your request. You can choose another node, such as Nevod Open. |
| you opened an invitation and the app says "Invitation to another node" | you are already registered on a node. See "How do I move to another node?" above. |

## Connection

**Above the input field the chat says "No connection" or "Connecting…" for a long time, and you can't send a message.**
Check your internet: open any website. If you use a VPN, try turning it off or switching servers. Switch between Wi-Fi and mobile data. If that doesn't help, your node may be temporarily unavailable — wait a few minutes; if you are on a private node, tell its administrator.

**Notifications don't arrive while Nevod is closed.**
- **iPhone Settings → Nevod → Notifications** — they must be allowed.
- Check that Do Not Disturb or another Focus mode isn't on.
- Check that notifications aren't turned off for this chat: chat settings (the gear) → **Notifications**.
- On a private node: ask the administrator to check that the node is [connected to the Nevod network](../node-network/) — without that, notifications don't arrive.

**A call doesn't connect.** See [Calls](../calls/), "If a call doesn't connect".

## Messages and files

**There's an orange clock next to a message.**
The other person is offline: the message is waiting for them on the node and will be delivered when they connect. The node keeps such messages for up to 72 hours — if the person doesn't come online in that time, the message won't be delivered.

**"Message not sent. Send again?"**
There was no connection when you sent it. Tap this line when the connection is back.

**A file won't send.**
- Larger than 50 MB — the app will tell you. Choose videos via **Photo or video**: they get compressed.
- "Couldn't load the video" — if the clip is stored in iCloud, the phone may have only a reduced copy of it. Open the video in the Photos app, wait until it has fully downloaded and try again. If the error repeats, tell us (see "Report a problem" below).
- "Couldn't compress the video" — try a shorter clip or send it via **File** if it's smaller than 50 MB.

**"Failed to save file: storage full".**
Received files take up space on your phone within Nevod's quota. Increase it: **Profile → Storage → Quota** — or delete chats you don't need (in the chat list, swipe left → **Delete**).

## AI assistants

**The bot says a key is needed, or the key isn't accepted.**
Check that the key was copied in full and hasn't been revoked on the provider's website, and that your provider account has funds or the free limit isn't used up. You can change the key in the chat with the bot — **Change**. More in [Bots and AI assistants](../bots/).

## Report a problem

**Profile → Diagnostics** — describe what happened and roughly when (for example, "2 of 3 photos didn't arrive, around 9 pm") and tap **Send to developers**. The app's technical log goes along with your description: it is stored only on your phone and contains no message text. The log is sent by email to support@nevod.network, or, if no email account is set up on the phone, to your node's administrator in Nevod; the answer comes in the chat with them.

To report a person or a message — see [Security](../security/), "Blocking and reporting".
