# Security and backups

What Nevod protects by itself, how it protects you from fraudsters and hacking, what you should do, how to keep strangers away, how to lock a chat with a password, how to block and report — and why Nevod has no message backups.

## What is protected without your involvement

- **Messages and calls are encrypted** on your phone with the other person's key. Nodes, the Nevod developers and Apple can't see them.
- **Keys, contacts and message history are stored only on your phone.** They are not in iCloud or computer backups, not on nodes and not with the developer.
- **A node knows only what it needs to deliver a message:** who is registered on it, whom you write to and when — but not what.

How this works in more detail — on the [Security](../../security/) page.

## Protection from fraudsters and hacking

- **No one can find you by phone number.** Nevod has no phone numbers or email addresses, so they can't be taken from a leaked database and used for spam or scam calls. Only someone who has your card, or a member of your node, can write to you.
- **There is no account password — nothing to steal.** It can't be spied on, guessed or tricked out of you. When connecting, the phone proves to the node that it holds the key, but the key itself never leaves the phone.
- **No one can pose as the administration.** Service names — administrator, support, Nevod and look-alikes — can't be registered. The real administration has a blue ✓ badge, and a private node's administrator is marked **Node administrator**. An account with a service name but without the badge or the mark gets an orange ⚠ from the app and a warning in the chat.
- **Fake notifications won't get through.** A new-message notification contains no text an outsider could set: only "New message" and the sender's name, and service names in it are replaced with "Nevod". A notification "from Nevod" asking you to enter a code or follow a link is a scam.
- **Your node can't be impersonated.** Everything that comes from the node is signed with its key, and the app checks the signature. Even on someone else's Wi-Fi, no one in the middle can pose as your node or slip in fake messages in its name.
- **Dangerous files and images are filtered out.** The most dangerous attacks on phones — such as the Pegasus spyware — arrive as a specially crafted image or file and work without a single tap. That's why Nevod checks everything it receives from other people: file size is limited, and the type must match the content — otherwise the file isn't shown as an image or video and doesn't open by itself. Avatars are accepted only from your contacts and members of your node, and the app never shows the image it was sent — it redraws it itself.
- **While the phone is locked, files are closed.** Photos, videos and files from chats are encrypted by iOS and become inaccessible a few seconds after the phone locks — even to someone who has gained access to the phone's storage. The app switcher shows a Nevod cover instead of your conversation.
- **Hacking a node won't expose your messages.** A node holds neither message text nor your keys: even with access to the node, an attacker can't read your conversations.
- **Verified nodes are marked.** Nevod project nodes in **Explore Network** have a gold ring — it is confirmed by the project's signature, and a fake node can't get it.

## What you should do

The most vulnerable point is the phone itself: whoever unlocks your phone sees your conversations too. And if spyware that has hacked iOS itself is already on the phone, it sees everything you see on the screen — no app, including Nevod, can protect you from that. So it's important to keep it from getting there.

- **A passcode on your iPhone** — a must, and not a simple one like 000000.
- **Keep iOS up to date** — updates close the vulnerabilities spyware relies on.
- **Restart your phone from time to time.** Many kinds of spyware don't survive a restart.
- **If you are a journalist, a human rights defender or could be a target for another reason** — turn on iPhone **Lockdown Mode**: **Settings → Privacy & Security → Lockdown Mode**. It closes many of the paths that attacks like Pegasus use.
- **A password on important chats** — see below.
- **Never give anyone codes or keys.** The Nevod administration writes only in the app, from the **administrator** account with the ✓ badge (on a private node — marked **Node administrator**), never by email, and never asks for passwords, keys or codes. Anyone who asks is a scammer.

## Chat password

You can lock a single chat with a password — then even someone holding your unlocked phone can't open that chat.

1. Open the chat → the gear icon at the top right → turn on **Password protection**.
2. Set two passwords:
   - **Unlock password** — you open the chat with it;
   - **Duress password** — for when you are forced to open the chat. If you enter it instead of the real one, the conversation in this chat is **silently deleted** from your phone, and the screen shows the usual "Incorrect password" — to an onlooker it looks like a typo.
3. The passwords must be different. To change them — in the same place, **Change passwords**.

> The chat password is stored only on this phone, and not the password itself but its hash. **A forgotten password can't be recovered** — neither by you nor by the developers. If you've forgotten it, tap **Forgot password?** on the sign-in screen: the conversation in this chat is deleted from the phone, the password lock is removed, and the chat opens again — empty. Choose a password you won't forget. The duress password deletes the conversation only on your phone: the other person keeps it.

## Protection from strangers

It's not only people you gave your card to who can write to you and call you. On an open node, such as Nevod Open, anyone can register, and node members see each other in **Contacts → On this node**. Besides, someone you talk to may forward your card to another person. A stranger here means someone who isn't in your contacts. Official Nevod accounts and your node's administrator don't count as strangers.

**Profile → Security** has two settings. Whether to turn them on is up to you; both are off at first:

- **Calls only from contacts** — a call from someone who isn't in your contacts is silently declined, and the phone doesn't ring. For the caller, the call ends at once; in your call history it shows as **Declined: not in contacts**.
- **Images from strangers — on tap** — photos and videos from someone who isn't in your contacts aren't shown right away: the chat shows a **Photo — show** or **Video — show** placeholder, and the app opens the file only after you tap it. That way even a specially crafted image can't go off by itself.

On a closed node where the administrator knows all the members, these settings are usually not needed. On an open node, it's worth turning them on.

## Blocking and reporting

- To **block** someone — chat settings (the gear) → **Block**. They won't be able to write to you or call you and won't know about it. The list of blocked people — **Profile → Security → Blocked**.
- To **report a message** — touch and hold it → **Report**. To report a person — chat settings → **Report**.
- To **report abuse** without a specific chat — **Profile → Security → Report abuse**.

The report goes to your node's administration — as an in-app message to the administrator account (or by email to abuse@nevod.network). Messages in Nevod are encrypted and the administration can't see them, so the app attaches the text of the message you are reporting to the report. The answer comes in the chat with administrator. You can block the person along with the report — **Also block**.

## There are no backups — on purpose

Keys, contacts and message history exist only on your phone. Therefore:

- **if the phone is lost, broken or reset, your conversations can't be recovered;**
- **deleting the app also erases the history;**
- **there is no transfer to a new phone yet.** On a new phone you create a new identity, and your contacts will need your new card.

This follows from how Nevod is built: a copy from which your conversations could be restored would also be a copy someone else could get access to. If you need to keep something from a conversation for a long time, save it separately: photos and files — via **Share**.

## Identity reset

**Profile → Reset identity…** permanently deletes your identity, contacts, the messages on your phone and your registration on the node. The app asks you to type a confirmation word so a reset can't happen by accident.

You need a reset if you want to start from scratch or move to another node. Your contacts will see **Identity deleted** in your chat; to write to you again, they'll need your new card.
