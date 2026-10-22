# English content for nevod.network — same facts and structure as content_uk.py; keep in sync.
# The manifesto text here is the ORIGINAL (website/index.html) — don't paraphrase it.

T = {
    "nav": {"index": "Home", "manifesto": "ZKI Manifesto", "compare": "Compare", "security": "Security",
            "cities": "For cities", "download": "Download", "about": "About"},
    "nav_support": "Support", "nav_privacy": "Privacy", "nav_terms": "Terms of Use", "nav_node": "Run a node",
    "footer_owner": "© 2026 Nevod · Kolpakov Andrey",
}

INDEX = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Zero Knowledge Infrastructure</div>
<h1>Nevod — a messenger whose developer is technically cut off from your data</h1>
<p class="lead">Not by a promise, and not by encryption alone — by architecture. The developer has none of your keys, no master key, no central server and no user database. Even if someone comes with a demand, there's nothing to hand over.</p>
<div class="btns"><a class="btn primary" href="/en/manifesto/">Read the ZKI manifesto</a><a class="btn ghost" href="/en/download/">Download</a></div>
</div></section>
<main><div class="wrap">
<h2>Encryption is a lock. ZKI means the developer has no key</h2>
<p>Most messengers encrypt messages, yet the company still runs the servers, keeps the user database, ties accounts to phone numbers and sees who talks to whom and when. Encryption protects content in transit; everything else stays in the company's hands.</p>
<p>Nevod is built on the principle of <b>Zero Knowledge Infrastructure</b>: the infrastructure is designed so its creator cannot access the content — even if they wanted to, or were forced to.</p>
<div class="grid">
<div class="card"><h3>🔑 Keys only on your device</h3><p>Keys are generated on your device and never leave it. The developer has no copy, no master key and no backup.</p></div>
<div class="card"><h3>🌐 A node for everyone</h3><p>No central server: the network is made of independent nodes, and nothing stops you from running your own. There's no single place where everything is collected.</p></div>
<div class="card"><h3>📵 Identity is a key, not a number</h3><p>No phone number, no e-mail. The developer keeps no register of people and doesn't know who you are.</p></div>
<div class="card"><h3>📭 Nothing to hand over</h3><p>If someone asks for a conversation, the developer has nothing to give. Not because it's hidden — because the developer doesn't have it.</p></div>
</div>
<p class="note">ZKI is the foundation of Nevod's development. Every technical decision is checked against one question: does the infrastructure's creator gain access to the content? <a href="/en/manifesto/">The Zero Knowledge Infrastructure manifesto →</a></p>
<h2>Low-load distributed network</h2>
<p>Each Nevod node's load is bounded by its own circle (family, home, team), not by the size of the whole network: a million new users elsewhere add not a single byte to your node. A node runs on ordinary home hardware, the network has no center, and the node itself carries only ciphertext.</p>
<p><a href="/en/compare/#low-load">A comparison of Nevod with 14 other networks, from FidoNet to Signal →</a></p>
<h2>What Nevod does</h2>
<div class="grid">
<div class="card"><h3>🔒 End-to-end encryption</h3><p>Every message, photo, voice message and call is encrypted on the phone. Nodes only ever see encrypted data.</p></div>
<div class="card"><h3>📞 Calls and video</h3><p>Voice and video calls, voice messages, photos, videos and files.</p></div>
<div class="card"><h3>🏙️ Communication without internet</h3><p>The architecture can deliver messages over any path — including within a city without internet access.</p></div>
<div class="card"><h3>🛡️ Protection from abuse</h3><p>Blocking and reporting, verified official accounts, protection against impersonating the administrator.</p></div>
</div>
<h2>Project status</h2>
<div class="tbl"><table class="status">
<tr><th style="width:34%">Area</th><th>Status</th></tr>
<tr><td>iPhone app</td><td>Closed testing (TestFlight); App Store release in preparation</td></tr>
<tr><td>Android app</td><td>In development</td></tr>
<tr><td>Network nodes</td><td>Running, deployed with Docker</td></tr>
<tr><td>App languages</td><td>8: Ukrainian, English, Russian, German, Turkish, Spanish, Italian, French</td></tr>
</table></div>
</div></main>
"""

MANIFESTO = """
<main><div class="wrap">
<div class="eyebrow" style="color:#8A6A00">Manifesto</div>
<h1>Zero Knowledge Infrastructure</h1>
<p><b>The network you're looking at right now — Nevod — is the first full implementation of a single idea: the people who build communication infrastructure should be technically unable to see what travels through it.</b></p>
<p>I build tools.<br>I don't watch how they're used.<br>I have no access to the data.<br>And that is the architecture of the software!</p>
<p>This isn't a privacy policy. This isn't a marketing promise. This is a technical impossibility, built into the foundation.</p>
<h2>The knife principle</h2>
<p>A knife maker isn't responsible for how the knife gets used. A knife can cut bread or not. That's the choice of whoever holds it, not whoever made it.</p>
<p>The same logic applies to communication infrastructure.</p>
<p>I build the channel. What travels through it isn't my business.<br>Not because I don't care. Because it must not be my business.</p>
<p>The right to private communication is a basic human right. Communication infrastructure should not be a surveillance chokepoint.</p>
<h2>What this means, technically</h2>
<p>Encryption keys are generated on the user's device.<br>They never leave that device.<br>I have no servers holding keys.<br>I have no master key.<br>I have no backup.</p>
<p>If someone comes asking for a conversation, I have nothing to hand over. Not because I'm hiding it — because I don't have it.</p>
<p>This is an architectural guarantee, not a promise.</p>
<h2>What this means, as a position</h2>
<p>I don't want to profit from people's personal data. I don't want to know what they're talking about. I don't want to be a middleman someone can serve a subpoena to.</p>
<p>Monetization happens through the tool, not through the content. I sell the hammer, not what gets built with it.</p>
<h2>AI agents and the next frontier</h2>
<p>The world is moving toward autonomous AI agents. Agents will talk to each other — negotiate, hire each other, exchange data.</p>
<p>The question becomes: who sees these conversations?</p>
<p>Today's industry answer is the platform. OpenAI sees what agents do on OpenAI. Google sees what agents do on Google. The orchestrator operator sees everything.</p>
<p>My answer is no one.</p>
<p>If agents communicate through ZKI infrastructure, their exchange is end-to-end encrypted. The platform operator sees only routing. The content of the negotiation stays between the agents.</p>
<div class="tbl"><table>
<tr><th>Agent A</th><th style="width:30%">⇄ E2E encrypted ⇄</th><th>Agent B</th></tr>
<tr><td>Nevod node — sees only ciphertext</td><td></td><td>Nevod node — sees only ciphertext</td></tr>
<tr><td>Operator — sees nothing</td><td></td><td>Operator — sees nothing</td></tr>
</table></div>
<p><i>"I run a service that AI agents use. I don't know what they agreed with your agent."</i></p>
<p>This isn't a dodge of responsibility. It's an architecture for a world where agents are independent actors.</p>
<h2>Why this matters right now</h2>
<p>In 2025–2026:</p>
<ul><li>AI agents are starting to act autonomously</li><li>Agents from different companies are starting to interact</li><li>No one has decided who sees inter-agent negotiations</li><li>No one has decided who's accountable for what an agent "said"</li></ul>
<p>ZKI answers this:</p>
<ul><li>Negotiations are encrypted — the operator doesn't see them</li><li>Responsibility for an agent's actions belongs to whoever runs it</li><li>Communication infrastructure stays neutral — like a phone line</li></ul>
<h2>Precedents</h2>
<div class="tbl"><table>
<tr><th style="width:30%">Tool</th><th>Position</th></tr>
<tr><td>Tor Project</td><td>"We built an anonymity tool. We don't see the traffic."</td></tr>
<tr><td>Signal Foundation</td><td>"Keys live with users. We have nothing to hand over."</td></tr>
<tr><td>ProtonMail</td><td>"Zero-knowledge encryption. We can't read your mail."</td></tr>
<tr><td>VPN providers</td><td>"We provide the tunnel. The content isn't ours."</td></tr>
<tr><td>Hardware wallets</td><td>"Keys live on the device. We have no copy."</td></tr>
</table></div>
<p>All of these positions have held up to legal scrutiny in most democratic countries. ZKI is the same position, carried through to a design philosophy.</p>
<h2>What I'm building</h2>
<p><b>Nevod</b> is the first implementation of the ZKI principle as a full network. Not a product. A protocol.</p>
<p>It can be the foundation for:</p>
<ul><li>Messengers</li><li>File storage</li><li>Voting systems</li><li>Dead man's switches</li><li>Protocols for AI agents</li><li>Corporate infrastructure</li></ul>
<p>One principle, everywhere: <b>the infrastructure's creator is technically cut off from its content</b>.</p>
<p style="margin-top:2em"><i>April 2026</i></p>
<p><b>Kolpakov Andrey</b></p>
<p class="note">© 2026. When quoting or referencing this manifesto, please link back to <a href="https://nevod.network">nevod.network</a>. Original page: <a href="/manifesto/">nevod.network/manifesto</a>.</p>
</div></main>
"""

COMPARE = """
<main><div class="wrap">
<h1>Nevod and other messengers</h1>
<p>Most modern messengers encrypt messages. The difference isn't whether there's encryption, but <b>what stays in the company's hands</b>: servers, the user database, phone numbers, the address book, metadata — and what of it can be demanded.</p>
<p class="note">Nevod implements the principle of <a href="/en/manifesto/">Zero Knowledge Infrastructure</a>: the developer is cut off from users' data by <b>architecture</b>, not by encryption alone. Information about other messengers reflects their public descriptions as of 2026 and may change.</p>
<div class="tbl"><table>
<tr><th style="width:24%"></th><th>Nevod</th><th>Signal</th><th>Telegram</th><th>WhatsApp</th></tr>
<tr><td>Who can technically read a regular chat</td><td>Only the participants</td><td>Only the participants</td><td>Regular and group chats — Telegram's servers (end-to-end only in 1:1 "secret chats")</td><td>Only the participants</td></tr>
<tr><td>The company's central servers</td><td>None — independent nodes anyone can run</td><td>Yes</td><td>Yes</td><td>Yes, Meta's</td></tr>
<tr><td>Tied to a phone number</td><td>No — identity is a key</td><td>Yes (the number can be hidden behind a username)</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Address book upload</td><td>No — contacts are added by card or QR</td><td>Private contact discovery</td><td>Yes, if allowed</td><td>Yes, if allowed</td></tr>
<tr><td>User database held by the company</td><td>No central one — each node knows only its own</td><td>Minimal</td><td>Yes</td><td>Yes</td></tr>
<tr><td>What the company can hand over on request</td><td>The developer has nothing to hand over: no keys, no messages, no database</td><td>Per its reports — account creation and last connection dates</td><td>Per its policy — IP address and phone number in some cases</td><td>Account metadata per its policy</td></tr>
<tr><td>Cloud backups of chats</td><td>None — keys and history exist only on the device (lose the phone, lose the history)</td><td>Optional; encrypted with a key only the user holds</td><td>Not needed — regular chats are already stored on Telegram's servers</td><td>To iCloud / Google Drive; not end-to-end encrypted by default (must be turned on manually)</td></tr>
<tr><td>Single point of failure or blocking</td><td>None — nodes are independent</td><td>Yes</td><td>Yes</td><td>Yes</td></tr>
<tr><td>Works without internet within a city</td><td>Built into the architecture (city network, Wi-Fi mesh, radio)</td><td>No</td><td>No</td><td>No</td></tr>
<tr><td>Business model</td><td>Through the tool, not through data</td><td>Donations (non-profit)</td><td>Ads and Premium</td><td>Meta's business services</td></tr>
<tr><td>Open source</td><td>Not yet — closed until production release</td><td>Yes</td><td>Partly (clients)</td><td>No</td></tr>
</table></div>
<h2>Why "just encryption" isn't enough</h2>
<p>End-to-end encryption protects a message's content in transit. But if a company runs all the servers, keeps an account database keyed by phone numbers and sees who talks to whom and when, it keeps power over the system: it can be compelled, breached or blocked, and an app update can change the rules.</p>
<p>ZKI asks a different question: <b>what could the infrastructure's creator get, even in theory?</b> In Nevod the answer is built into the architecture: keys never leave the device, there's no master key and no backups, no central server and no register of people by phone number.</p>
<h2 id="low-load">Low-load distributed network: a comparison</h2>
<p>We rate networks against six traits of a low-load distributed network: each node's load is bounded by its own circle of people, not by the size of the whole network. The traits come from Nevod's own principles, so the comparison naturally favors it.</p>
<ol>
<li>Own circle: a node's load grows with its circle (family, home, team), not with the whole network.</li>
<li>Ordinary hardware: a home computer, mini-server or router; no data center needed.</li>
<li>Economy: text and signals first, heavy data on request.</li>
<li>Delay tolerance: with no connection, the message waits and goes later, including over a slow channel.</li>
<li>No center: no single point of failure, blocking or seizure.</li>
<li>Blind node: a node carries only ciphertext and cannot read it.</li>
</ol>
<p class="note">1: yes, ½: partly, 0: no. Year: first public release. Class: LL-0, a node's load is bounded by its circle; LL-1, plus bounded transit for others; LL-3, load grows with the whole network or depends on outside users. More: <a href="/en/publications/low-load-networks/">the article</a>.</p>
<div class="tbl"><table>
<tr><th>Network</th><th>Year</th><th>Own circle</th><th>Ordinary hardware</th><th>Economy</th><th>Delays</th><th>No center</th><th>Blind node</th><th>Class</th></tr>
<tr><td>Secure Scuttlebutt</td><td>2014</td><td>1</td><td>1</td><td>½</td><td>1</td><td>1</td><td>0</td><td>LL-0</td></tr>
<tr><td>Briar</td><td>2018</td><td>1</td><td>1</td><td>½</td><td>½</td><td>1</td><td>1</td><td>LL-0</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>1</td><td>1</td><td>½</td><td>½</td><td>1</td><td>1</td><td>LL-0</td></tr>
<tr><td>FidoNet</td><td>1984</td><td>1</td><td>1</td><td>1</td><td>1</td><td>0</td><td>0</td><td>LL-1</td></tr>
<tr><td>NNCP</td><td>2016</td><td>½</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>LL-1</td></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>½</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>LL-1</td></tr>
<tr><td>Meshtastic</td><td>2020</td><td>0</td><td>1</td><td>1</td><td>½</td><td>1</td><td>½</td><td>LL-1</td></tr>
<tr><td>Tor</td><td>2002</td><td>0</td><td>½</td><td>0</td><td>0</td><td>1</td><td>1</td><td>LL-3</td></tr>
<tr><td>WhatsApp</td><td>2009</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>½</td><td>LL-3</td></tr>
<tr><td>Telegram</td><td>2013</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>LL-3</td></tr>
<tr><td>Matrix</td><td>2014</td><td>0</td><td>½</td><td>0</td><td>0</td><td>½</td><td>½</td><td>LL-3</td></tr>
<tr><td>Signal</td><td>2014</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>½</td><td>LL-3</td></tr>
<tr><td>Mastodon</td><td>2016</td><td>0</td><td>½</td><td>0</td><td>0</td><td>½</td><td>0</td><td>LL-3</td></tr>
<tr><td>Nostr</td><td>2020</td><td>0</td><td>½</td><td>0</td><td>0</td><td>1</td><td>½</td><td>LL-3</td></tr>
<tr><td>Session</td><td>2020</td><td>0</td><td>½</td><td>0</td><td>½</td><td>1</td><td>1</td><td>LL-3</td></tr>
</table></div>
<p>Signal and WhatsApp get ½ for blindness: content is end-to-end encrypted, but the company sees metadata and runs the servers. In Reticulum and NNCP, intermediate nodes carry and store other people's packets. Nevod still sends media whole, keeps undelivered messages for 72 hours and works only over the internet.</p>
<h3>Reality check</h3>
<div class="tbl"><table>
<tr><th>Network</th><th>Year</th><th>For ordinary people</th><th>Maturity</th><th>Independent audit</th></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>no, for enthusiasts</td><td>active community</td><td>no</td></tr>
<tr><td>NNCP</td><td>2016</td><td>no, a command-line tool</td><td>niche</td><td>no</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>yes: iPhone/iPad, messages, media, calls</td><td>in testing, no real users yet</td><td>no</td></tr>
<tr><td>Briar</td><td>2018</td><td>yes, but no calls; Android and desktop</td><td>mature</td><td>yes (Cure53, 2017)</td></tr>
<tr><td>Signal</td><td>2014</td><td>yes</td><td>very mature</td><td>yes, repeatedly</td></tr>
</table></div>
<p>By the main trait, Nevod belongs to class LL-0 together with Briar and Secure Scuttlebutt; Reticulum and NNCP, close to them on the other traits, belong to LL-1. Nevod's difference lies elsewhere: of these networks it is the only one designed as a full messenger for ordinary people, with media, calls and an iPhone app. But it is young: no real users yet, no independent audit, iOS only. The path to six out of six: media on request and delivery without the internet over slow channels.</p>
<h2>What we acknowledge</h2>
<ul>
<li>A node technically processes only delivery data — which encrypted packet goes to whom — and never sees the content. Nothing stops you from running your own node: then even that delivery data stays with you.</li>
<li>Signal's protocol is open and thoroughly reviewed — a strength we acknowledge. Nevod's code is closed for now; opening it is planned.</li>
</ul>
</div></main>
"""

SECURITY = """
<main><div class="wrap">
<h1>Security and encryption</h1>
<p class="note">Encryption is only part of the protection. Nevod's foundation is the <a href="/en/manifesto/">Zero Knowledge Infrastructure</a> architecture, in which the developer has no access to users' keys or data.</p>
<h2>How your messages are protected</h2>
<p>Nevod uses end-to-end encryption: a message is encrypted on your device and decrypted only on the recipient's device. The node that carries the message sees only encrypted data and the service information needed for delivery — never the content.</p>
<div class="tbl"><table>
<tr><th style="width:38%">What</th><th>How it's done</th></tr>
<tr><td>Message encryption</td><td>CryptoKit — Apple's system cryptography library: X25519 key exchange, SHA-256, ChaCha20-Poly1305 cipher</td></tr>
<tr><td>Signatures</td><td>CryptoKit: Ed25519</td></tr>
<tr><td>Proving identity when connecting to a node</td><td>A zero-knowledge Schnorr protocol built on CryptoKit (Curve25519, SHA-256/512) plus one modular arithmetic operation implemented in Nevod itself</td></tr>
</table></div>
<p>For every message the sender creates a new one-time key. The recipient's key is long-term: if it were stolen from the recipient's device, previously intercepted messages to that recipient could be decrypted too. That's why protecting the device itself matters — a passcode and an up-to-date iOS.</p>
<p>The Schnorr protocol lets you prove to a node that you own your key without sending or revealing the key itself.</p>
<h2>If you lose your phone</h2>
<p>Your keys, contacts and message history are stored only on your device. They are not in iCloud or computer backups, on the nodes, or with the developer. So if your phone is lost, broken or reset, they cannot be restored. Deleting the app also erases your history.</p>
<p>Transfer to a new device is not available yet. On a new phone you create a new identity, and your contacts will need your new card. This follows from the architecture: a copy that could restore your conversations would also be a copy someone could get access to.</p>
<h2>Your node, your rules</h2>
<p>The developer sees nothing. A node processes only what delivery can't work without: participant identifiers, chosen names, notification tokens, and which encrypted packet goes to whom. A node never sees the content of messages, photos, voice messages or calls.</p>
<p>Nothing stops you from creating your own node — for yourself, your family, an organization or a community. Then even the delivery data stays with you. <a href="/en/node/">How to run your own node →</a></p>
<h2>Export control and the App Store</h2>
<p>When publishing to the App Store, a developer declares whether the app uses encryption subject to export control (US EAR, Category 5, Part 2). Nevod declares that it does not, and here's why:</p>
<ul>
<li><b>Everything that hides message content is Apple's system cryptography (CryptoKit).</b> Apps that use only the encryption built into Apple's operating system qualify for an exemption and need no export documentation.</li>
<li><b>Nevod's own implementation — one arithmetic operation in the Schnorr protocol — is used only to prove identity.</b> Export control covers cryptography for confidentiality. Cryptography used only for authentication, signatures and integrity is excluded from it.</li>
</ul>
<p>So Nevod needs no export documentation, including for distribution in France.</p>
<p><i>This is our reading of the applicable rules, not a legal opinion.</i></p>
</div></main>
"""

CITIES = """
<section class="hero"><div class="wrap">
<div class="eyebrow">For cities</div>
<h1>Communication for a city when there is no internet and no data centers</h1>
<p class="lead">Every modern city depends on data centers and backbone links. Nevod's architecture can deliver encrypted messages over any available path, so a backup city communication network can be built on it.</p>
</div></section>
<main><div class="wrap">
<h2>Four layers of communication</h2>
<div class="tbl"><table>
<tr><th style="width:24%">Layer</th><th>What it uses</th><th style="width:16%">Range</th><th style="width:20%">What it carries</th></tr>
<tr><td>1. City nodes</td><td>Provider networks without internet access</td><td>Whole city</td><td>Everything within the city</td></tr>
<tr><td>2. Wi-Fi mesh</td><td>Ordinary routers at "resilience points" — shelters, schools, help centers</td><td>Block–district</td><td>Everything, including calls</td></tr>
<tr><td>3. Radio links</td><td>Directional radio modems with line of sight</td><td>10–20 km</td><td>Everything, including calls</td></tr>
<tr><td>4. LoRa</td><td>Low-cost radio modules</td><td>1–10+ km</td><td>Short text only</td></tr>
</table></div>
<p>For people it's the same Nevod: the app picks whatever path is available.</p>
<h2>A resilience point</h2>
<p>A set of low-cost, off-the-shelf equipment: a few routers with open firmware, a small node server, backup power and, where needed, a radio link to other districts and a LoRa module for short texts. Nothing needs inventing.</p>
<h2>How to start</h2>
<p>We offer cities a pilot in one district: several interconnected resilience points, tested for messages and calls with no internet at all. The outcome is a report and a deployment plan. Contact: <a href="mailto:support@nevod.network">support@nevod.network</a>.</p>
<p class="note">Any transmitter can be direction-found, so installation sites are chosen with care, and message content is protected by end-to-end encryption on every layer. The ZKI architecture holds here too: the city network's operator has no access to the content.</p>
</div></main>
"""

DOWNLOAD = """
<main><div class="wrap">
<h1>Download Nevod</h1>
<div class="grid">
<div class="card"><h3>📱 iPhone and iPad</h3><p>Currently in closed testing via TestFlight; the App Store release is in preparation. To join the testing, write to <a href="mailto:support@nevod.network">support@nevod.network</a>.</p></div>
<div class="card"><h3>🤖 Android</h3><p>The app is in development. We'll announce it here as soon as it's ready for testing.</p></div>
<div class="card"><h3>🖥️ Network node</h3><p>A Nevod node runs on a server or an ordinary computer with Docker. See <a href="/en/node/">Run a node</a>.</p></div>
</div>
</div></main>
"""

NODE = """
<main><div class="wrap">
<h1>Run your own Nevod node</h1>
<p>A node is a small server through which phones exchange messages and calls. It only ever sees encrypted data. An organization, community, school or family can run its own — which is exactly why the network has no central point controlled by the developer.</p>
<h2>What you need</h2>
<ul>
<li>A computer or server with Linux or Windows and Docker installed</li>
<li>1 GB of RAM or more</li>
<li>For access from the internet — a public address or domain; for a city network or Wi-Fi, a local address is enough</li>
</ul>
<h2>How it works</h2>
<ol>
<li>The node runs in Docker and has a web admin panel.</li>
<li>In the panel you set the node's name and admission mode (open, by invitation, or with administrator approval), and optionally join the node to the Nevod network.</li>
<li>Phones connect to the node by its address or an invitation QR code.</li>
</ol>
<p class="note">A public release of the node software is in preparation. For now, access is on request at <a href="mailto:support@nevod.network">support@nevod.network</a>. Setting up a node with the help of an AI assistant is also in development.</p>
</div></main>
"""

ABOUT = """
<main><div class="wrap">
<h1>About the project</h1>
<p>Nevod is the first implementation of the <a href="/en/manifesto/">Zero Knowledge Infrastructure</a> principle: communication infrastructure whose creator is technically cut off from its content. The project doesn't depend on a single server, a single provider or a single country.</p>
<h2>Author</h2>
<p><b>Kolpakov Andrey</b> — author of the ZKI manifesto and developer of Nevod.</p>
<!--BIO-->
<h2>Contacts</h2>
<ul>
<li>General questions and support: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Reporting abuse: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Privacy and data: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
</div></main>
"""

SUPPORT = """
<main><div class="wrap">
<h1>Support</h1>
<p class="note"><b>Important.</b> The Nevod administration replies only inside the Nevod app — from the official <b>administrator</b> account with the ✓ badge. We never reply by e-mail and never ask for passwords, keys or codes. If "the administration" contacts you any other way, it's a scam.</p>
<h2>How to reach us</h2>
<ul>
<li>Questions and help: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Reporting a user or content: in the app — long-press a message → "Report", or Chat settings → "Report". Also: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Privacy and data: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
<h2>Blocking a user</h2>
<p>Chat settings → "Block". A blocked user can't message or call you; unblock in the same place or in Profile → Blocked.</p>
<h2>Deleting your account</h2>
<p>Profile → "Reset identity". This permanently deletes your identity, contacts and messages on the device, and your registration on the node. The people you chatted with will see that the identity was deleted.</p>
</div></main>
"""

PRIVACY = """
<main class="legal"><div class="wrap">
<h1>Privacy Policy</h1>
<p>Version of 17 October 2026. Nevod is developed by Kolpakov Andrey. Questions about data: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a>.</p>
<h2>1. The essentials</h2>
<p>Nevod is built on the principle of Zero Knowledge Infrastructure. The content of your messages, photos, videos, voice messages, files and calls is end-to-end encrypted, and keys never leave your device. Neither the network nodes nor the developer can read the content. The one exception is what you write to AI bots yourself, see section 5.</p>
<h2>2. What's stored on your device</h2>
<p>Your cryptographic identity (keys in the iOS secure storage), contacts, message history and media, settings, and a technical log for diagnostics. The log never leaves the device unless you send it yourself.</p>
<p>This data is not included in iCloud or computer backups and is not transferred to other devices. If the device is lost or reset, or the app is deleted, the history cannot be restored: neither the nodes nor the developer have a copy.</p>
<h2>3. What a node processes</h2>
<ul>
<li>Your identity's identifier (cell ID) and your public keys.</li>
<li>The display name you chose.</li>
<li>Device tokens for push notifications and calls.</li>
<li>Encrypted messages until they're delivered: undelivered messages are deleted after 72 hours.</li>
<li>Your notification settings and your list of blocked users.</li>
<li>Delivery metadata (who sends packets to whom and when) and technical logs for diagnostics, kept for a limited time.</li>
<li>Your messages to the administrator account (complaints and questions sent from the app). The node's operator reads them in order to reply: they are addressed to the operator. Your conversations with other people remain inaccessible to the operator.</li>
</ul>
<p>Nodes may belong to different independent operators. The operator of the node you connect to processes this data to run the network.</p>
<h2>4. Notifications</h2>
<p>Notifications on iPhone are delivered through the Apple Push Notification service. A notification carries the sender's name and the generic text "New message" — never the message content.</p>
<h2>5. AI bots</h2>
<p>A node may offer AI bots, for example an assistant or a translator. Such a bot answers through the AI provider you pick — Anthropic (Claude), OpenAI (ChatGPT) or Google (Gemini) — on your own API key. Nevod doesn't sell AI access and has no keys of its own. You don't need bots to use Nevod.</p>
<ul>
<li><b>Your key</b> is kept only on your device, in the iOS secure storage, and doesn't move to other devices. It travels to the bot end-to-end encrypted, together with each message. The bot uses it for that one request and doesn't save it.</li>
<li><b>Your messages to a bot.</b> A bot is a separate network participant run by the operator of the node where it's published. On the way, messages to it are end-to-end encrypted like all others; the bot decrypts them to answer and passes the text to the provider you picked. Only write to a bot what you're willing to share with that provider.</li>
<li><b>What the bot keeps:</b> only the last few messages of your conversation, in memory, so it can answer in context; they vanish when the bot restarts. The bot's log records that a request happened, its provider and its length — never the text or the key.</li>
<li><b>The provider</b> receives your messages, the recent conversation and your key, and processes them under its own terms and privacy policy (<a href="https://www.anthropic.com/legal/privacy">Anthropic</a>, <a href="https://openai.com/policies/privacy-policy">OpenAI</a>, <a href="https://policies.google.com/privacy">Google</a>). The requests come from the bot's server, not from your device.</li>
<li><b>Consent.</b> Before you add a key, the app asks you to agree that your messages to bots go to that provider. To withdraw: Profile → Security → AI keys → delete the key. "Reset identity" deletes all keys too.</li>
<li>Bots only receive text: photos, files, voice messages and calls are never passed to them.</li>
</ul>
<h2>6. Third parties</h2>
<p>We don't sell data or use it for advertising or tracking. We use: Apple (notifications, app distribution), node hosting, Cloudflare (DNS and domain e-mail). If you add an AI key: the provider you picked, for your messages to bots (section 5).</p>
<h2>7. Deletion</h2>
<p>Profile → "Reset identity" deletes your data on the device and your registration on the node.</p>
<h2>8. Children</h2>
<p>Nevod is not intended for children younger than the age at which your country allows consenting to data processing on one's own.</p>
<h2>9. Changes</h2>
<p>We'll announce significant changes to this policy on this page and in the app.</p>
</div></main>
"""

TERMS = """
<main class="legal"><div class="wrap">
<h1>Terms of Use</h1>
<p>Version of 28 September 2026. By using Nevod you agree to these terms.</p>
<h2>1. Zero tolerance for abuse</h2>
<p>It is forbidden to send or publish illegal, abusive or threatening content, harass others, spread spam or fraud, or impersonate others — including the Nevod administration. Violators are blocked.</p>
<h2>2. Reports and blocking</h2>
<p>You can block and report any user in the app or at <a href="mailto:abuse@nevod.network">abuse@nevod.network</a>. We review reports and act on them.</p>
<h2>3. Official accounts</h2>
<p>The administration replies only in the app, from the administrator account with the ✓ badge — never by e-mail — and never asks for passwords, keys or codes.</p>
<h2>4. Nodes</h2>
<p>The network consists of nodes that may be run by independent operators. A node's operator is responsible for running it in line with the laws of their country.</p>
<h2>5. No warranty</h2>
<p>Nevod is provided "as is". We do our best to keep communication reliable, but we don't guarantee uninterrupted message delivery.</p>
<h2>6. Contact</h2>
<p><a href="mailto:support@nevod.network">support@nevod.network</a></p>
</div></main>
"""

PAGES = {
    "index": ("Nevod", "Nevod — the first implementation of Zero Knowledge Infrastructure: a messenger whose developer is technically cut off from users' data.", INDEX),
    "manifesto": ("Zero Knowledge Infrastructure Manifesto", "The ZKI manifesto — the foundation of Nevod's development. By Kolpakov Andrey.", MANIFESTO),
    "compare": ("Compare", "Nevod compared with Signal, Telegram and WhatsApp: why encryption alone isn't ZKI.", COMPARE),
    "security": ("Security and encryption", "How Nevod encrypts messages, what a node processes, and why no export documentation is needed.", SECURITY),
    "cities": ("For cities", "A backup city communication network built on Nevod that works without the internet or data centers.", CITIES),
    "download": ("Download", "Nevod for iPhone, Android and the network node.", DOWNLOAD),
    "node": ("Run a node", "How to run your own Nevod network node.", NODE),
    "about": ("About", "Who is behind Nevod and how to reach us.", ABOUT),
    "support": ("Support", "Support, reporting, blocking and deleting your account in Nevod.", SUPPORT),
    "privacy": ("Privacy Policy", "What data Nevod processes and how it is protected.", PRIVACY),
    "terms": ("Terms of Use", "Nevod Terms of Use.", TERMS),
}
