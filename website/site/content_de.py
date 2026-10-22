# German content for nevod.network — same facts and structure as content_uk.py / content_en.py.

T = {
    "nav": {"index": "Start", "manifesto": "ZKI-Manifest", "compare": "Vergleich", "security": "Sicherheit",
            "cities": "Für Städte", "download": "Download", "about": "Über das Projekt"},
    "nav_support": "Support", "nav_privacy": "Datenschutz", "nav_terms": "Nutzungsbedingungen",
    "nav_node": "Eigener Node", "nav_source": "Quellcode",
    "footer_owner": "© 2026 Nevod · Kolpakov Andrey",
}

INDEX = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Zero Knowledge Infrastructure</div>
<h1>Nevod — ein Messenger, dessen Entwickler technisch von deinen Daten abgeschnitten ist</h1>
<p class="lead">Nicht durch ein Versprechen und nicht nur durch Verschlüsselung — durch die Architektur. Der Entwickler hat keinen deiner Schlüssel, keinen Generalschlüssel, keinen zentralen Server und keine Nutzerdatenbank. Selbst wenn jemand mit einer Forderung kommt, gibt es nichts herauszugeben.</p>
<div class="btns"><a class="btn primary" href="/de/manifesto/">ZKI-Manifest lesen</a><a class="btn ghost" href="/de/download/">Download</a></div>
</div></section>
<main><div class="wrap">
<h2>Verschlüsselung ist ein Schloss. ZKI heißt: Der Entwickler hat keinen Schlüssel</h2>
<p>Die meisten Messenger verschlüsseln Nachrichten, doch das Unternehmen betreibt weiterhin die Server, führt die Nutzerdatenbank, bindet Konten an Telefonnummern und sieht, wer mit wem wann kommuniziert. Verschlüsselung schützt den Inhalt auf dem Weg; alles andere bleibt in der Hand des Unternehmens.</p>
<p>Nevod folgt dem Prinzip der <b>Zero Knowledge Infrastructure</b>: Die Infrastruktur ist so gebaut, dass ihr Schöpfer nicht auf die Inhalte zugreifen kann — selbst wenn er wollte oder dazu gezwungen würde.</p>
<div class="grid">
<div class="card"><h3>🔑 Schlüssel nur bei dir</h3><p>Schlüssel entstehen auf deinem Gerät und verlassen es nie. Der Entwickler hat weder eine Kopie noch einen Generalschlüssel noch ein Backup.</p></div>
<div class="card"><h3>🌐 Ein eigener Node für jeden</h3><p>Kein zentraler Server: Das Netz besteht aus unabhängigen Nodes, und niemand hindert dich daran, deinen eigenen zu betreiben. Es gibt keinen Ort, an dem alles gesammelt wird.</p></div>
<div class="card"><h3>📵 Identität ist ein Schlüssel, keine Nummer</h3><p>Ohne Telefonnummer und E-Mail. Der Entwickler führt kein Register von Personen und weiß nicht, wer du bist.</p></div>
<div class="card"><h3>📭 Nichts herauszugeben</h3><p>Wird ein Chatverlauf angefordert, hat der Entwickler nichts herauszugeben. Nicht, weil er es versteckt — sondern weil er es nicht hat.</p></div>
</div>
<p class="note">ZKI ist die Grundlage der Entwicklung von Nevod. Jede technische Entscheidung wird an einer Frage gemessen: Erhält der Schöpfer der Infrastruktur Zugriff auf die Inhalte? <a href="/de/manifesto/">Das Manifest der Zero Knowledge Infrastructure →</a></p>
<h2>Gering belastetes verteiltes Netz</h2>
<p>Die Last jedes Nevod-Nodes ist durch seinen eigenen Kreis begrenzt (Familie, Zuhause, Team), nicht durch die Größe des ganzen Netzes: Eine Million neuer Nutzer anderswo fügt deinem Node kein einziges Byte hinzu. Ein Node läuft auf gewöhnlicher Heim-Hardware, das Netz hat kein Zentrum, und der Node selbst transportiert nur Chiffretext.</p>
<p><a href="/de/compare/#low-load">Ein Vergleich von Nevod mit 14 anderen Netzen, von FidoNet bis Signal →</a></p>
<h2>Was Nevod kann</h2>
<div class="grid">
<div class="card"><h3>🔒 Ende-zu-Ende-Verschlüsselung</h3><p>Jede Nachricht, jedes Foto, jede Sprachnachricht und jeder Anruf wird auf dem Telefon verschlüsselt. Nodes sehen nur verschlüsselte Daten.</p></div>
<div class="card"><h3>📞 Anrufe und Video</h3><p>Sprach- und Videoanrufe, Sprachnachrichten, Fotos, Videos und Dateien.</p></div>
<div class="card"><h3>🏙️ Kommunikation ohne Internet</h3><p>Die Architektur kann Nachrichten über jeden verfügbaren Weg zustellen — auch innerhalb einer Stadt ohne Internetzugang.</p></div>
<div class="card"><h3>🛡️ Schutz vor Missbrauch</h3><p>Blockieren und Melden, verifizierte offizielle Konten, Schutz vor dem Nachahmen des Administrators.</p></div>
</div>
<h2>Projektstatus</h2>
<div class="tbl"><table class="status">
<tr><th style="width:34%">Bereich</th><th>Status</th></tr>
<tr><td>iPhone-App</td><td>Geschlossener Test (TestFlight); Veröffentlichung im App Store in Vorbereitung</td></tr>
<tr><td>Android-App</td><td>In Entwicklung</td></tr>
<tr><td>Netz-Nodes</td><td>In Betrieb, laufen mit Docker</td></tr>
<tr><td>App-Sprachen</td><td>8: Ukrainisch, Englisch, Russisch, Deutsch, Türkisch, Spanisch, Italienisch, Französisch</td></tr>
</table></div>
</div></main>
"""

MANIFESTO = """
<main><div class="wrap">
<div class="eyebrow" style="color:#8A6A00">Manifest</div>
<h1>Zero Knowledge Infrastructure</h1>
<p><b>Das Netz, das du gerade siehst — Nevod — ist die erste vollständige Umsetzung einer einzigen Idee: Wer Kommunikationsinfrastruktur baut, soll technisch nicht in der Lage sein zu sehen, was durch sie fließt.</b></p>
<h2>Position</h2>
<p>Ich baue Werkzeuge.<br>Ich beobachte nicht, wie sie benutzt werden.<br>Ich habe keinen Zugriff auf die Daten.<br>Und das ist die Architektur der Software!</p>
<p>Das ist keine Datenschutzerklärung. Das ist kein Marketingversprechen. Das ist eine technische Unmöglichkeit, im Fundament verankert.</p>
<h2>Das Messer-Prinzip</h2>
<p>Ein Messerhersteller ist nicht dafür verantwortlich, wie das Messer benutzt wird. Mit einem Messer kann man Brot schneiden oder nicht. Das ist die Wahl dessen, der es hält, nicht dessen, der es gemacht hat.</p>
<p>Dieselbe Logik gilt für Kommunikationsinfrastruktur.</p>
<p>Ich baue den Kanal. Was durch ihn fließt, geht mich nichts an.<br>Nicht, weil es mir egal ist. Sondern weil es mich <b>nichts angehen darf</b>.</p>
<p>Das Recht auf private Kommunikation ist ein grundlegendes Menschenrecht. Kommunikationsinfrastruktur darf kein Überwachungsnadelöhr sein.</p>
<h2>Was das technisch bedeutet</h2>
<p>Die Verschlüsselungsschlüssel werden auf dem Gerät des Nutzers erzeugt.<br>Sie verlassen dieses Gerät nie.<br>Ich habe keine Server mit Schlüsseln.<br>Ich habe keinen Generalschlüssel.<br>Ich habe kein Backup.</p>
<p>Wenn jemand einen Chatverlauf verlangt, habe ich nichts herauszugeben. Nicht, weil ich ihn verstecke — sondern weil <b>ich ihn nicht habe</b>.</p>
<p>Das ist eine architektonische Garantie, kein Versprechen.</p>
<h2>Was das als Haltung bedeutet</h2>
<p>Ich will nicht an den persönlichen Daten von Menschen verdienen. Ich will nicht wissen, worüber sie sprechen. Ich will kein Mittelsmann sein, dem man eine Vorladung zustellen kann.</p>
<p>Geld wird mit dem Werkzeug verdient, nicht mit dem Inhalt. Ich verkaufe den Hammer, nicht das, was damit gebaut wird.</p>
<h2>KI-Agenten und die nächste Grenze</h2>
<p>Die Welt bewegt sich auf autonome KI-Agenten zu. Agenten werden miteinander sprechen — verhandeln, einander beauftragen, Daten austauschen.</p>
<p>Die Frage lautet: Wer sieht diese Gespräche?</p>
<p>Die heutige Antwort der Branche ist: die Plattform. OpenAI sieht, was Agenten auf OpenAI tun. Google sieht, was Agenten auf Google tun. Der Betreiber des Orchestrators sieht alles.</p>
<p>Meine Antwort: <b>niemand</b>.</p>
<p>Wenn Agenten über ZKI-Infrastruktur kommunizieren, ist ihr Austausch Ende-zu-Ende-verschlüsselt. Der Plattformbetreiber sieht nur das Routing. Der Inhalt der Verhandlung bleibt zwischen den Agenten.</p>
<div class="tbl"><table>
<tr><th>Agent A</th><th style="width:30%">⇄ Ende-zu-Ende verschlüsselt ⇄</th><th>Agent B</th></tr>
<tr><td>Nevod-Node — sieht nur Chiffretext</td><td></td><td>Nevod-Node — sieht nur Chiffretext</td></tr>
<tr><td>Betreiber — sieht nichts</td><td></td><td>Betreiber — sieht nichts</td></tr>
</table></div>
<p><i>„Ich betreibe einen Dienst, den KI-Agenten nutzen. Ich weiß nicht, was sie mit deinem Agenten vereinbart haben.“</i></p>
<p>Das ist keine Flucht vor Verantwortung. Es ist eine Architektur für eine Welt, in der Agenten eigenständige Akteure sind.</p>
<h2>Warum das gerade jetzt wichtig ist</h2>
<p>In den Jahren 2025–2026:</p>
<ul><li>KI-Agenten beginnen, autonom zu handeln</li><li>Agenten verschiedener Unternehmen beginnen zu interagieren</li><li>Niemand hat entschieden, wer Verhandlungen zwischen Agenten sieht</li><li>Niemand hat entschieden, wer dafür verantwortlich ist, was ein Agent „gesagt“ hat</li></ul>
<p>ZKI gibt die Antwort:</p>
<ul><li>Verhandlungen sind verschlüsselt — der Betreiber sieht sie nicht</li><li>Die Verantwortung für die Handlungen eines Agenten trägt, wer ihn betreibt</li><li>Kommunikationsinfrastruktur bleibt neutral — wie eine Telefonleitung</li></ul>
<h2>Präzedenzfälle</h2>
<div class="tbl"><table>
<tr><th style="width:30%">Werkzeug</th><th>Position</th></tr>
<tr><td>Tor Project</td><td>„Wir haben ein Anonymisierungswerkzeug gebaut. Wir sehen den Datenverkehr nicht.“</td></tr>
<tr><td>Signal Foundation</td><td>„Die Schlüssel liegen bei den Nutzern. Wir haben nichts herauszugeben.“</td></tr>
<tr><td>ProtonMail</td><td>„Zero-Knowledge-Verschlüsselung. Wir können deine E-Mails nicht lesen.“</td></tr>
<tr><td>VPN-Anbieter</td><td>„Wir stellen den Tunnel bereit. Der Inhalt gehört nicht uns.“</td></tr>
<tr><td>Hardware-Wallets</td><td>„Die Schlüssel liegen auf dem Gerät. Wir haben keine Kopie.“</td></tr>
</table></div>
<p>All diese Positionen haben in den meisten demokratischen Ländern der rechtlichen Prüfung standgehalten. ZKI ist dieselbe Position, konsequent zu einer Entwurfsphilosophie weitergedacht.</p>
<h2>Was ich baue</h2>
<p><b>Nevod</b> ist die erste Umsetzung des ZKI-Prinzips als vollständiges Netz. Kein Produkt. Ein Protokoll.</p>
<p>Es kann die Grundlage sein für:</p>
<ul><li>Messenger</li><li>Dateispeicher</li><li>Abstimmungssysteme</li><li>Totmannschalter</li><li>Protokolle für KI-Agenten</li><li>Unternehmensinfrastruktur</li></ul>
<p>Überall ein Prinzip: <b>Der Schöpfer der Infrastruktur ist technisch von ihrem Inhalt abgeschnitten</b>.</p>
<p style="margin-top:2em"><i>April 2026</i></p>
<p><b>Kolpakov Andrey</b></p>
<p class="note">© 2026. Beim Zitieren oder Verweisen auf dieses Manifest bitte auf <a href="https://nevod.network">nevod.network</a> verlinken. Original auf Englisch: <a href="/manifesto/">nevod.network/manifesto</a>.</p>
</div></main>
"""

COMPARE = """
<main><div class="wrap">
<h1>Nevod und andere Messenger</h1>
<p>Die meisten modernen Messenger verschlüsseln Nachrichten. Der Unterschied liegt nicht darin, ob verschlüsselt wird, sondern darin, <b>was in der Hand des Unternehmens bleibt</b>: Server, Nutzerdatenbank, Telefonnummern, Adressbuch, Metadaten — und was davon verlangt werden kann.</p>
<p class="note">Nevod setzt das Prinzip der <a href="/de/manifesto/">Zero Knowledge Infrastructure</a> um: Der Entwickler ist durch die <b>Architektur</b> von den Nutzerdaten abgeschnitten, nicht nur durch Verschlüsselung. Angaben zu anderen Messengern beruhen auf deren öffentlichen Beschreibungen (Stand 2026) und können sich ändern.</p>
<div class="tbl"><table>
<tr><th style="width:24%"></th><th>Nevod</th><th>Signal</th><th>Telegram</th><th>WhatsApp</th></tr>
<tr><td>Wer einen normalen Chat technisch lesen kann</td><td>Nur die Teilnehmer</td><td>Nur die Teilnehmer</td><td>Normale und Gruppenchats — die Server von Telegram (Ende-zu-Ende nur in 1:1-„geheimen Chats“)</td><td>Nur die Teilnehmer</td></tr>
<tr><td>Zentrale Server des Unternehmens</td><td>Keine — unabhängige Nodes, die jeder betreiben kann</td><td>Ja</td><td>Ja</td><td>Ja, von Meta</td></tr>
<tr><td>An eine Telefonnummer gebunden</td><td>Nein — die Identität ist ein Schlüssel</td><td>Ja (die Nummer lässt sich hinter einem Benutzernamen verbergen)</td><td>Ja</td><td>Ja</td></tr>
<tr><td>Hochladen des Adressbuchs</td><td>Nein — Kontakte werden per Karte oder QR hinzugefügt</td><td>Private Kontaktsuche</td><td>Ja, wenn erlaubt</td><td>Ja, wenn erlaubt</td></tr>
<tr><td>Nutzerdatenbank beim Unternehmen</td><td>Keine zentrale — jeder Node kennt nur seine eigenen</td><td>Minimal</td><td>Ja</td><td>Ja</td></tr>
<tr><td>Was das Unternehmen auf Anfrage herausgeben kann</td><td>Der Entwickler hat nichts herauszugeben: keine Schlüssel, keine Nachrichten, keine Datenbank</td><td>Laut eigenen Berichten — Registrierungsdatum und letzte Verbindung</td><td>Laut eigener Richtlinie — in manchen Fällen IP-Adresse und Telefonnummer</td><td>Kontometadaten laut eigener Richtlinie</td></tr>
<tr><td>Cloud-Backups der Chats</td><td>Keine — Schlüssel und Verlauf existieren nur auf dem Gerät (Telefon verloren, Verlauf verloren)</td><td>Optional; verschlüsselt mit einem Schlüssel, den nur der Nutzer hat</td><td>Nicht nötig — normale Chats liegen ohnehin auf den Telegram-Servern</td><td>In iCloud / Google Drive; standardmäßig ohne Ende-zu-Ende-Verschlüsselung (muss manuell aktiviert werden)</td></tr>
<tr><td>Single Point of Failure oder Sperrung</td><td>Keiner — Nodes sind unabhängig</td><td>Ja</td><td>Ja</td><td>Ja</td></tr>
<tr><td>Funktioniert ohne Internet innerhalb einer Stadt</td><td>In der Architektur angelegt (Stadtnetz, WLAN-Mesh, Funk)</td><td>Nein</td><td>Nein</td><td>Nein</td></tr>
<tr><td>Geschäftsmodell</td><td>Über das Werkzeug, nicht über Daten</td><td>Spenden (gemeinnützig)</td><td>Werbung und Premium</td><td>Business-Dienste von Meta</td></tr>
<tr><td>Open Source</td><td>Noch nicht — bis zum Produktivstart geschlossen</td><td>Ja</td><td>Teilweise (Clients)</td><td>Nein</td></tr>
</table></div>
<h2>Warum „nur Verschlüsselung“ nicht reicht</h2>
<p>Ende-zu-Ende-Verschlüsselung schützt den Inhalt einer Nachricht auf dem Weg. Betreibt ein Unternehmen aber alle Server, führt eine Kontodatenbank nach Telefonnummern und sieht, wer mit wem wann kommuniziert, behält es Macht über das System: Es kann gezwungen, gehackt oder gesperrt werden, und ein App-Update kann die Regeln ändern.</p>
<p>ZKI stellt eine andere Frage: <b>Was könnte der Schöpfer der Infrastruktur überhaupt bekommen, selbst theoretisch?</b> Bei Nevod steckt die Antwort in der Architektur: Schlüssel verlassen das Gerät nie, es gibt keinen Generalschlüssel und keine Backups, keinen zentralen Server und kein Register von Personen nach Telefonnummer.</p>
<h2 id="low-load">Gering belastetes verteiltes Netz: ein Vergleich</h2>
<p>Wir bewerten Netze nach sechs Merkmalen eines gering belasteten verteilten Netzes: Die Last jedes Nodes ist durch seinen eigenen Personenkreis begrenzt, nicht durch die Größe des ganzen Netzes. Die Merkmale stammen aus den Prinzipien von Nevod, der Vergleich begünstigt es also von vornherein.</p>
<ol>
<li>Eigener Kreis: Die Last eines Nodes wächst mit seinem Kreis (Familie, Zuhause, Team), nicht mit dem ganzen Netz.</li>
<li>Gewöhnliche Hardware: Heimcomputer, Mini-Server oder Router; kein Rechenzentrum nötig.</li>
<li>Sparsamkeit: zuerst Text und Signale, Schweres auf Anfrage.</li>
<li>Verzögerungstoleranz: Ohne Verbindung wartet die Nachricht und geht später raus, auch über einen langsamen Kanal.</li>
<li>Kein Zentrum: kein einzelner Ausfall-, Sperr- oder Beschlagnahmepunkt.</li>
<li>Blinder Node: Ein Node transportiert nur Chiffretext und kann ihn nicht lesen.</li>
</ol>
<p class="note">1: ja, ½: teilweise, 0: nein. Jahr: erste öffentliche Version. Klasse: LL-0, die Last eines Knotens ist durch seinen Kreis begrenzt; LL-1, dazu begrenzter fremder Transit; LL-3, die Last wächst mit dem ganzen Netz oder hängt von fremden Nutzern ab. Mehr: <a href="/de/publications/low-load-networks/">der Artikel</a>.</p>
<div class="tbl"><table>
<tr><th>Netz</th><th>Jahr</th><th>Eigener Kreis</th><th>Gewöhnliche Hardware</th><th>Sparsamkeit</th><th>Verzögerungen</th><th>Kein Zentrum</th><th>Blinder Node</th><th>Klasse</th></tr>
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
<p>Signal und WhatsApp bekommen ½ für Blindheit: Inhalte sind Ende-zu-Ende-verschlüsselt, aber das Unternehmen sieht Metadaten und betreibt die Server. Bei Reticulum und NNCP transportieren und speichern Zwischenknoten fremde Pakete. Nevod sendet Medien noch vollständig, speichert Unzugestelltes 72 Stunden und funktioniert nur über das Internet.</p>
<h3>Praxistest</h3>
<div class="tbl"><table>
<tr><th>Netz</th><th>Jahr</th><th>Für normale Menschen</th><th>Reife</th><th>Unabhängiges Audit</th></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>nein, für Enthusiasten</td><td>aktive Community</td><td>nein</td></tr>
<tr><td>NNCP</td><td>2016</td><td>nein, Kommandozeilen-Tool</td><td>Nische</td><td>nein</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>ja: iPhone/iPad, Nachrichten, Medien, Anrufe</td><td>im Test, noch keine echten Nutzer</td><td>nein</td></tr>
<tr><td>Briar</td><td>2018</td><td>ja, aber ohne Anrufe; Android und Desktop</td><td>ausgereift</td><td>ja (Cure53, 2017)</td></tr>
<tr><td>Signal</td><td>2014</td><td>ja</td><td>sehr ausgereift</td><td>ja, mehrfach</td></tr>
</table></div>
<p>Nach dem Hauptmerkmal gehört Nevod zusammen mit Briar und Secure Scuttlebutt zur Klasse LL-0; Reticulum und NNCP, die ihnen in den übrigen Merkmalen nahekommen, gehören zu LL-1. Der Unterschied liegt woanders: Von diesen Netzen ist Nevod als einziges als vollwertiger Messenger für normale Menschen gedacht, mit Medien, Anrufen und einer iPhone-App. Aber es ist jung: noch keine echten Nutzer, kein unabhängiges Audit, nur iOS. Der Weg zu sechs von sechs: Medien auf Anfrage und Zustellung ohne Internet über langsame Kanäle.</p>
<h2>Was wir anerkennen</h2>
<ul>
<li>Ein Node verarbeitet technisch nur Zustelldaten — welches verschlüsselte Paket an wen geht — und sieht nie den Inhalt. Niemand hindert dich daran, einen eigenen Node zu betreiben: Dann bleiben auch diese Zustelldaten bei dir.</li>
<li>Das Protokoll von Signal ist offen und gründlich geprüft — eine Stärke, die wir anerkennen. Der Code von Nevod ist vorerst geschlossen; seine Öffnung ist geplant.</li>
</ul>
</div></main>
"""

SECURITY = """
<main><div class="wrap">
<h1>Sicherheit und Verschlüsselung</h1>
<p class="note">Verschlüsselung ist nur ein Teil des Schutzes. Die Grundlage von Nevod ist die Architektur der <a href="/de/manifesto/">Zero Knowledge Infrastructure</a>, in der der Entwickler keinen Zugriff auf Schlüssel und Daten der Nutzer hat.</p>
<h2>Wie deine Nachrichten geschützt sind</h2>
<p>Nevod nutzt Ende-zu-Ende-Verschlüsselung: Eine Nachricht wird auf deinem Gerät verschlüsselt und nur auf dem Gerät des Empfängers entschlüsselt. Der Node, über den sie läuft, sieht nur verschlüsselte Daten und die für die Zustellung nötigen Dienstinformationen — nie den Inhalt.</p>
<div class="tbl"><table>
<tr><th style="width:38%">Was</th><th>Womit</th></tr>
<tr><td>Nachrichtenverschlüsselung</td><td>CryptoKit — Apples Systembibliothek für Kryptografie: X25519-Schlüsselaustausch, SHA-256, ChaCha20-Poly1305</td></tr>
<tr><td>Signaturen</td><td>CryptoKit: Ed25519</td></tr>
<tr><td>Identitätsnachweis beim Verbinden mit einem Node</td><td>Ein Zero-Knowledge-Schnorr-Protokoll auf Basis von CryptoKit (Curve25519, SHA-256/512) plus eine in Nevod selbst implementierte modulare Rechenoperation</td></tr>
</table></div>
<p>Für jede Nachricht erzeugt der Absender einen neuen Einmalschlüssel. Der Schlüssel des Empfängers ist langlebig: Würde er vom Gerät des Empfängers gestohlen, könnten auch früher abgefangene Nachrichten an diesen Empfänger entschlüsselt werden. Deshalb ist der Schutz des Geräts selbst wichtig — ein Code und ein aktuelles iOS.</p>
<p>Das Schnorr-Protokoll beweist einem Node, dass du deinen Schlüssel besitzt, ohne den Schlüssel selbst zu senden oder preiszugeben.</p>
<h2>Wenn du dein Telefon verlierst</h2>
<p>Deine Schlüssel, Kontakte und dein Nachrichtenverlauf werden nur auf deinem Gerät gespeichert. Sie liegen weder in iCloud- oder Computer-Backups noch auf den Nodes noch beim Entwickler. Geht das Telefon verloren oder kaputt oder wird es zurückgesetzt, lassen sie sich daher nicht wiederherstellen. Auch das Löschen der App löscht den Verlauf.</p>
<p>Eine Übertragung auf ein neues Gerät gibt es noch nicht. Auf einem neuen Telefon erstellst du eine neue Identität, und deine Kontakte brauchen deine neue Karte. Das folgt aus der Architektur: Eine Kopie, aus der sich deine Gespräche wiederherstellen ließen, wäre auch eine Kopie, auf die jemand zugreifen könnte.</p>
<h2>Dein Node, deine Regeln</h2>
<p>Der Entwickler sieht nichts. Ein Node verarbeitet nur, was für die Zustellung unerlässlich ist: Kennungen der Teilnehmer, gewählte Namen, Benachrichtigungs-Tokens und welches verschlüsselte Paket an wen geht. Den Inhalt von Nachrichten, Fotos, Sprachnachrichten und Anrufen sieht ein Node nie.</p>
<p>Niemand hindert dich daran, einen eigenen Node zu betreiben — für dich, deine Familie, eine Organisation oder eine Gemeinschaft. Dann bleiben selbst die Zustelldaten bei dir. <a href="/de/node/">Einen eigenen Node betreiben →</a></p>
<h2>Exportkontrolle und App Store</h2>
<p>Bei der Veröffentlichung im App Store gibt ein Entwickler an, ob die App Verschlüsselung verwendet, die der Exportkontrolle unterliegt (US-EAR, Kategorie 5, Teil 2). Nevod gibt an, dass dies nicht der Fall ist, und zwar aus folgenden Gründen:</p>
<ul>
<li><b>Alles, was den Inhalt von Nachrichten verbirgt, ist Apples Systemkryptografie (CryptoKit).</b> Apps, die nur die in Apples Betriebssystem eingebaute Verschlüsselung nutzen, fallen unter eine Ausnahme und benötigen keine Exportdokumentation.</li>
<li><b>Nevods eigene Implementierung — eine Rechenoperation im Schnorr-Protokoll — dient nur dem Identitätsnachweis.</b> Die Exportkontrolle betrifft Kryptografie zur Vertraulichkeit. Kryptografie ausschließlich für Authentifizierung, Signaturen und Integrität ist davon ausgenommen.</li>
</ul>
<p>Daher benötigt Nevod keine Exportdokumentation, auch nicht für den Vertrieb in Frankreich.</p>
<p><i>Das ist unsere Auslegung der geltenden Regeln, kein Rechtsgutachten.</i></p>
</div></main>
"""

CITIES = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Für Städte</div>
<h1>Kommunikation für eine Stadt, wenn es kein Internet und keine Rechenzentren gibt</h1>
<p class="lead">Jede moderne Stadt hängt von Rechenzentren und Backbone-Verbindungen ab. Die Architektur von Nevod kann verschlüsselte Nachrichten über jeden verfügbaren Weg zustellen — darauf lässt sich ein Ersatz-Kommunikationsnetz für die Stadt aufbauen.</p>
</div></section>
<main><div class="wrap">
<h2>Vier Kommunikationsebenen</h2>
<div class="tbl"><table>
<tr><th style="width:24%">Ebene</th><th>Was sie nutzt</th><th style="width:16%">Reichweite</th><th style="width:20%">Was sie überträgt</th></tr>
<tr><td>1. Städtische Nodes</td><td>Providernetze ohne Internetzugang</td><td>Ganze Stadt</td><td>Alles innerhalb der Stadt</td></tr>
<tr><td>2. WLAN-Mesh</td><td>Gewöhnliche Router an „Resilienzpunkten“ — Schutzräumen, Schulen, Hilfszentren</td><td>Block–Bezirk</td><td>Alles, auch Anrufe</td></tr>
<tr><td>3. Richtfunkstrecken</td><td>Richtfunkmodems mit Sichtverbindung</td><td>10–20 km</td><td>Alles, auch Anrufe</td></tr>
<tr><td>4. LoRa</td><td>Günstige Funkmodule</td><td>1–10+ km</td><td>Nur kurzer Text</td></tr>
</table></div>
<p>Für die Menschen ist es dasselbe Nevod: Die App wählt selbst den verfügbaren Weg.</p>
<h2>Ein Resilienzpunkt</h2>
<p>Ein Satz günstiger Serienhardware: einige Router mit offener Firmware, ein kleiner Node-Server, Notstrom und bei Bedarf eine Richtfunkstrecke zu anderen Bezirken sowie ein LoRa-Modul für kurze Texte. Nichts muss erfunden werden.</p>
<h2>Wie man beginnt</h2>
<p>Wir bieten Städten einen Pilotbetrieb in einem Bezirk an: mehrere verbundene Resilienzpunkte, getestet für Nachrichten und Anrufe ganz ohne Internet. Ergebnis sind ein Bericht und ein Ausbauplan. Kontakt: <a href="mailto:support@nevod.network">support@nevod.network</a>.</p>
<p class="note">Jeder Sender lässt sich anpeilen, daher werden Standorte sorgfältig gewählt, und der Inhalt der Nachrichten ist auf jeder Ebene Ende-zu-Ende-verschlüsselt. Die ZKI-Architektur gilt auch hier: Der Betreiber des Stadtnetzes hat keinen Zugriff auf Inhalte.</p>
</div></main>
"""

DOWNLOAD = """
<main><div class="wrap">
<h1>Nevod herunterladen</h1>
<div class="grid">
<div class="card"><h3>📱 iPhone und iPad</h3><p>Derzeit im geschlossenen Test über TestFlight; die Veröffentlichung im App Store wird vorbereitet. Um am Test teilzunehmen, schreib an <a href="mailto:support@nevod.network">support@nevod.network</a>.</p></div>
<div class="card"><h3>🤖 Android</h3><p>Die App ist in Entwicklung. Wir kündigen sie hier an, sobald sie bereit zum Testen ist.</p></div>
<div class="card"><h3>🖥️ Netz-Node</h3><p>Ein Nevod-Node läuft auf einem Server oder einem normalen Computer mit Docker. Siehe <a href="/de/node/">Eigener Node</a>.</p></div>
</div>
</div></main>
"""

NODE = """
<main><div class="wrap">
<h1>Einen eigenen Nevod-Node betreiben</h1>
<p>Ein Node ist ein kleiner Server, über den Telefone Nachrichten und Anrufe austauschen. Er sieht nur verschlüsselte Daten. Eine Organisation, Gemeinschaft, Schule oder Familie kann ihren eigenen betreiben — genau deshalb hat das Netz keinen zentralen, vom Entwickler kontrollierten Punkt.</p>
<h2>Was du brauchst</h2>
<ul>
<li>Einen Computer oder Server mit Linux oder Windows und installiertem Docker</li>
<li>Mindestens 1 GB Arbeitsspeicher</li>
<li>Für Zugriff aus dem Internet eine öffentliche Adresse oder Domain; für ein Stadtnetz oder WLAN genügt eine lokale Adresse</li>
</ul>
<h2>So funktioniert es</h2>
<ol>
<li>Der Node läuft in Docker und hat ein Web-Adminpanel.</li>
<li>Im Panel legst du den Namen des Nodes und den Zulassungsmodus fest (offen, per Einladung oder mit Freigabe durch den Administrator) und verbindest den Node auf Wunsch mit dem Nevod-Netz.</li>
<li>Telefone verbinden sich über die Adresse des Nodes oder einen Einladungs-QR-Code.</li>
</ol>
<p class="note">Die Node-Software ist Open Source: <a href="https://github.com/avk0978/nevod-messenger">github.com/avk0978/nevod-messenger</a> (GNU AGPL-3.0). Die Dateien zum Betrieb eines Nodes in Docker liegen im Ordner <code>installer/docker</code> des Repositorys. Auch die Einrichtung eines Nodes mithilfe eines KI-Assistenten ist in Entwicklung.</p>
</div></main>
"""

ABOUT = """
<main><div class="wrap">
<h1>Über das Projekt</h1>
<p>Nevod ist die erste Umsetzung des Prinzips der <a href="/de/manifesto/">Zero Knowledge Infrastructure</a>: einer Kommunikationsinfrastruktur, deren Schöpfer technisch von ihrem Inhalt abgeschnitten ist. Das Projekt hängt nicht von einem einzelnen Server, einem einzelnen Anbieter oder einem einzelnen Land ab.</p>
<h2>Autor</h2>
<p><b>Kolpakov Andrey</b> — Autor des ZKI-Manifests und Entwickler von Nevod.</p>
<!--BIO-->
<h2>Quellcode</h2>
<p>Der Quellcode von Nevod ist offen — der Node, die iOS-App und die Protokollspezifikationen: <a href="https://github.com/avk0978/nevod-messenger">github.com/avk0978/nevod-messenger</a>. Lizenz: GNU AGPL-3.0. Jeder kann prüfen, dass App und Node genau so arbeiten, wie es auf dieser Website beschrieben ist.</p>
<h2>Kontakt</h2>
<ul>
<li>Allgemeine Fragen und Support: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Missbrauch melden: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Datenschutz und Daten: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
</div></main>
"""

SUPPORT = """
<main><div class="wrap">
<h1>Support</h1>
<p class="note"><b>Wichtig.</b> Die Nevod-Administration antwortet nur innerhalb der Nevod-App — vom offiziellen Konto <b>administrator</b> mit dem ✓-Abzeichen. Wir antworten nie per E-Mail und fragen nie nach Passwörtern, Schlüsseln oder Codes. Meldet sich „die Administration“ auf anderem Weg, ist es Betrug.</p>
<h2>So erreichst du uns</h2>
<ul>
<li>Fragen und Hilfe: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Einen Nutzer oder Inhalt melden: in der App — Nachricht lange drücken → „Melden“ oder Chat-Einstellungen → „Melden“. Außerdem: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Datenschutz und Daten: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
<h2>Einen Nutzer blockieren</h2>
<p>Chat-Einstellungen → „Blockieren“. Ein blockierter Nutzer kann dir weder schreiben noch dich anrufen; die Blockierung hebst du an derselben Stelle oder unter Profil → Blockiert auf.</p>
<h2>Konto löschen</h2>
<p>Profil → „Identität zurücksetzen“. Dadurch werden deine Identität, Kontakte und Nachrichten auf dem Gerät sowie deine Registrierung auf dem Node dauerhaft gelöscht. Deine Gesprächspartner sehen, dass die Identität gelöscht wurde.</p>
</div></main>
"""

PRIVACY = """
<main class="legal"><div class="wrap">
<h1>Datenschutzerklärung</h1>
<p>Fassung vom 17. Oktober 2026. Nevod wird von Kolpakov Andrey entwickelt. Fragen zu Daten: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a>.</p>
<h2>1. Das Wichtigste</h2>
<p>Nevod folgt dem Prinzip der Zero Knowledge Infrastructure. Der Inhalt deiner Nachrichten, Fotos, Videos, Sprachnachrichten, Dateien und Anrufe ist Ende-zu-Ende-verschlüsselt, und die Schlüssel verlassen dein Gerät nie. Weder die Netz-Nodes noch der Entwickler können den Inhalt lesen. Die einzige Ausnahme ist, was du selbst an KI-Bots schreibst, siehe Abschnitt 5.</p>
<h2>2. Was auf deinem Gerät gespeichert wird</h2>
<p>Deine kryptografische Identität (Schlüssel im sicheren Speicher von iOS), Kontakte, Nachrichtenverlauf und Medien, Einstellungen sowie ein technisches Protokoll zur Diagnose. Das Protokoll verlässt das Gerät nur, wenn du es selbst sendest.</p>
<p>Diese Daten sind nicht in iCloud- oder Computer-Backups enthalten und werden nicht auf andere Geräte übertragen. Geht das Gerät verloren, wird es zurückgesetzt oder die App gelöscht, lässt sich der Verlauf nicht wiederherstellen: Weder die Nodes noch der Entwickler haben eine Kopie.</p>
<h2>3. Was ein Node verarbeitet</h2>
<ul>
<li>Die Kennung deiner Identität (Cell-ID) und deine öffentlichen Schlüssel.</li>
<li>Den von dir gewählten Anzeigenamen.</li>
<li>Geräte-Tokens für Push-Benachrichtigungen und Anrufe.</li>
<li>Verschlüsselte Nachrichten bis zur Zustellung: Nicht zugestellte Nachrichten werden nach 72 Stunden gelöscht.</li>
<li>Deine Benachrichtigungseinstellungen und deine Liste blockierter Nutzer.</li>
<li>Zustellmetadaten (wer wem wann Pakete sendet) und technische Protokolle zur Diagnose, die begrenzte Zeit aufbewahrt werden.</li>
<li>Deine Nachrichten an das Konto administrator (Beschwerden und Fragen aus der App). Der Betreiber des Nodes liest sie, um zu antworten: Sie sind an ihn gerichtet. Deine Unterhaltungen mit anderen Menschen bleiben für den Betreiber weiterhin unzugänglich.</li>
</ul>
<p>Nodes können verschiedenen unabhängigen Betreibern gehören. Der Betreiber des Nodes, mit dem du dich verbindest, verarbeitet diese Daten für den Netzbetrieb.</p>
<h2>4. Benachrichtigungen</h2>
<p>Benachrichtigungen auf dem iPhone werden über den Apple Push Notification Service zugestellt. Eine Benachrichtigung enthält den Namen des Absenders und den allgemeinen Text „Neue Nachricht“ — nie den Nachrichteninhalt.</p>
<h2>5. KI-Bots</h2>
<p>Ein Node kann KI-Bots anbieten, etwa einen Assistenten oder einen Übersetzer. Ein solcher Bot antwortet über den KI-Anbieter deiner Wahl — Anthropic (Claude), OpenAI (ChatGPT) oder Google (Gemini) — mit deinem eigenen API-Schlüssel. Nevod verkauft keinen KI-Zugang und hat keine eigenen Schlüssel. Nevod funktioniert auch ganz ohne Bots.</p>
<ul>
<li><b>Dein Schlüssel</b> liegt nur auf deinem Gerät, im sicheren Speicher von iOS, und wird nicht auf andere Geräte übertragen. Er gelangt Ende-zu-Ende-verschlüsselt zusammen mit jeder Nachricht zum Bot. Der Bot nutzt ihn für genau diese Anfrage und speichert ihn nicht.</li>
<li><b>Deine Nachrichten an einen Bot.</b> Ein Bot ist ein eigener Teilnehmer im Netz, betrieben vom Betreiber des Nodes, auf dem er veröffentlicht ist. Unterwegs sind Nachrichten an ihn wie alle anderen Ende-zu-Ende-verschlüsselt; der Bot entschlüsselt sie, um zu antworten, und gibt den Text an den von dir gewählten Anbieter weiter. Schreib einem Bot nur, was du mit diesem Anbieter teilen möchtest.</li>
<li><b>Was der Bot behält:</b> nur die letzten paar Nachrichten des Gesprächs, im Arbeitsspeicher, damit er im Zusammenhang antworten kann; beim Neustart des Bots sind sie weg. Im Protokoll des Bots steht nur, dass eine Anfrage kam, an welchen Anbieter und wie lang sie war — nie der Text oder der Schlüssel.</li>
<li><b>Der Anbieter</b> erhält deine Nachrichten, den jüngsten Gesprächsverlauf und deinen Schlüssel und verarbeitet sie nach seinen eigenen Bedingungen und seiner Datenschutzerklärung (<a href="https://www.anthropic.com/legal/privacy">Anthropic</a>, <a href="https://openai.com/policies/privacy-policy">OpenAI</a>, <a href="https://policies.google.com/privacy">Google</a>). Die Anfragen kommen vom Server des Bots, nicht von deinem Gerät.</li>
<li><b>Einwilligung.</b> Bevor du einen Schlüssel hinzufügst, bittet dich die App zuzustimmen, dass deine Nachrichten an Bots an diesen Anbieter gehen. Widerruf: Profil → Sicherheit → KI-Schlüssel → Schlüssel löschen. „Identität zurücksetzen“ löscht ebenfalls alle Schlüssel.</li>
<li>Bots erhalten nur Text: Fotos, Dateien, Sprachnachrichten und Anrufe werden nie an sie weitergegeben.</li>
</ul>
<h2>6. Dritte</h2>
<p>Wir verkaufen keine Daten und nutzen sie nicht für Werbung oder Tracking. Wir nutzen: Apple (Benachrichtigungen, App-Vertrieb), Hosting der Nodes, Cloudflare (DNS und E-Mail der Domain). Wenn du einen KI-Schlüssel hinzufügst: der von dir gewählte Anbieter, für deine Nachrichten an Bots (Abschnitt 5).</p>
<h2>7. Löschung</h2>
<p>Profil → „Identität zurücksetzen“ löscht deine Daten auf dem Gerät und deine Registrierung auf dem Node.</p>
<h2>8. Kinder</h2>
<p>Nevod ist nicht für Kinder unter dem Alter bestimmt, ab dem man in deinem Land selbst in die Datenverarbeitung einwilligen darf.</p>
<h2>9. Änderungen</h2>
<p>Über wesentliche Änderungen dieser Erklärung informieren wir auf dieser Seite und in der App.</p>
</div></main>
"""

TERMS = """
<main class="legal"><div class="wrap">
<h1>Nutzungsbedingungen</h1>
<p>Fassung vom 28. September 2026. Mit der Nutzung von Nevod stimmst du diesen Bedingungen zu.</p>
<h2>1. Null Toleranz für Missbrauch</h2>
<p>Verboten ist es, illegale, beleidigende oder bedrohliche Inhalte zu senden oder zu veröffentlichen, andere zu belästigen, Spam oder Betrug zu verbreiten oder sich als andere auszugeben — auch als die Nevod-Administration. Verstöße führen zur Blockierung.</p>
<h2>2. Meldungen und Blockieren</h2>
<p>Du kannst jeden Nutzer in der App oder unter <a href="mailto:abuse@nevod.network">abuse@nevod.network</a> blockieren und melden. Wir prüfen Meldungen und reagieren darauf.</p>
<h2>3. Offizielle Konten</h2>
<p>Die Administration antwortet nur in der App, vom Konto administrator mit dem ✓-Abzeichen — nie per E-Mail — und fragt nie nach Passwörtern, Schlüsseln oder Codes.</p>
<h2>4. Nodes</h2>
<p>Das Netz besteht aus Nodes, die von unabhängigen Betreibern betrieben werden können. Der Betreiber eines Nodes ist für dessen Betrieb gemäß den Gesetzen seines Landes verantwortlich.</p>
<h2>5. Keine Gewährleistung</h2>
<p>Nevod wird „wie besehen“ bereitgestellt. Wir tun alles für eine zuverlässige Kommunikation, garantieren aber keine unterbrechungsfreie Zustellung von Nachrichten.</p>
<h2>6. Kontakt</h2>
<p><a href="mailto:support@nevod.network">support@nevod.network</a></p>
</div></main>
"""

PAGES = {
    "index": ("Nevod", "Nevod — die erste Umsetzung der Zero Knowledge Infrastructure: ein Messenger, dessen Entwickler technisch von den Nutzerdaten abgeschnitten ist.", INDEX),
    "manifesto": ("Manifest der Zero Knowledge Infrastructure", "Das ZKI-Manifest — die Grundlage der Entwicklung von Nevod. Von Kolpakov Andrey.", MANIFESTO),
    "compare": ("Vergleich", "Nevod im Vergleich zu Signal, Telegram und WhatsApp: warum Verschlüsselung allein noch kein ZKI ist.", COMPARE),
    "security": ("Sicherheit und Verschlüsselung", "Wie Nevod Nachrichten verschlüsselt, was ein Node verarbeitet und warum keine Exportdokumentation nötig ist.", SECURITY),
    "cities": ("Für Städte", "Ein Ersatz-Kommunikationsnetz für Städte auf Basis von Nevod, das ohne Internet und Rechenzentren funktioniert.", CITIES),
    "download": ("Download", "Nevod für iPhone, Android und den Netz-Node.", DOWNLOAD),
    "node": ("Eigener Node", "Wie man einen eigenen Nevod-Node betreibt.", NODE),
    "about": ("Über das Projekt", "Wer hinter Nevod steht und wie man uns erreicht.", ABOUT),
    "support": ("Support", "Support, Meldungen, Blockieren und Löschen des Kontos in Nevod.", SUPPORT),
    "privacy": ("Datenschutzerklärung", "Welche Daten Nevod verarbeitet und wie sie geschützt sind.", PRIVACY),
    "terms": ("Nutzungsbedingungen", "Nutzungsbedingungen von Nevod.", TERMS),
}
