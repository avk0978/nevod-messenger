# Turkish content for nevod.network — same facts and structure as content_uk.py / content_en.py.

T = {
    "nav": {"index": "Ana sayfa", "manifesto": "ZKI Manifestosu", "compare": "Karşılaştırma", "security": "Güvenlik",
            "cities": "Şehirler için", "download": "İndir", "about": "Proje hakkında"},
    "nav_support": "Destek", "nav_privacy": "Gizlilik", "nav_terms": "Kullanım Koşulları", "nav_node": "Kendi düğümün",
    "footer_owner": "© 2026 Nevod · Kolpakov Andrey",
}

INDEX = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Zero Knowledge Infrastructure</div>
<h1>Nevod — geliştiricisi verilerinize teknik olarak erişemeyen bir mesajlaşma uygulaması</h1>
<p class="lead">Bir vaatle değil, yalnızca şifrelemeyle de değil — mimariyle. Geliştiricide anahtarlarınız, ana anahtar, merkezi sunucu ya da kullanıcı veritabanı yoktur. Biri bir taleple gelse bile teslim edecek hiçbir şey yoktur.</p>
<div class="btns"><a class="btn primary" href="/tr/manifesto/">ZKI Manifestosunu oku</a><a class="btn ghost" href="/tr/download/">İndir</a></div>
</div></section>
<main><div class="wrap">
<h2>Şifreleme bir kilittir. ZKI ise geliştiricide anahtar olmamasıdır</h2>
<p>Çoğu mesajlaşma uygulaması mesajları şifreler, ancak şirket yine de sunucuları işletir, kullanıcı veritabanını tutar, hesapları telefon numaralarına bağlar ve kimin kiminle ne zaman konuştuğunu görür. Şifreleme içeriği yolda korur; geri kalan her şey şirketin elinde kalır.</p>
<p>Nevod, <b>Zero Knowledge Infrastructure</b> ilkesine göre inşa edilmiştir: altyapı, yaratıcısının içeriğe erişemeyeceği şekilde tasarlanmıştır — isteseydi ya da zorlansaydı bile.</p>
<div class="grid">
<div class="card"><h3>🔑 Anahtarlar yalnızca sizde</h3><p>Anahtarlar cihazınızda oluşturulur ve cihazı asla terk etmez. Geliştiricide ne kopya ne ana anahtar ne de yedek vardır.</p></div>
<div class="card"><h3>🌐 Herkese kendi düğümü</h3><p>Merkezi sunucu yok: ağ bağımsız düğümlerden oluşur ve kimse kendi düğümünüzü çalıştırmanızı engellemez. Her şeyin toplandığı tek bir nokta yoktur.</p></div>
<div class="card"><h3>📵 Kimlik bir anahtardır, numara değil</h3><p>Telefon numarası ve e-posta olmadan. Geliştirici kimsenin kaydını tutmaz ve kim olduğunuzu bilmez.</p></div>
<div class="card"><h3>📭 Teslim edecek bir şey yok</h3><p>Biri bir yazışmayı talep ederse geliştiricinin verecek hiçbir şeyi yoktur. Sakladığı için değil — elinde olmadığı için.</p></div>
</div>
<p class="note">ZKI, Nevod'un geliştirilmesinin temelidir. Her teknik karar tek bir soruyla sınanır: altyapının yaratıcısı içeriğe erişim kazanıyor mu? <a href="/tr/manifesto/">Zero Knowledge Infrastructure Manifestosu →</a></p>
<h2>Az yüklü dağıtık ağ</h2>
<p>Her Nevod düğümünün yükü tüm ağın büyüklüğüyle değil, kendi çevresiyle (aile, ev, ekip) sınırlıdır: başka bir yerdeki bir milyon yeni kullanıcı düğümünüze tek bir bayt bile eklemez. Düğüm sıradan ev donanımında çalışır, ağın merkezi yoktur ve düğümün kendisi yalnızca şifreli metin taşır.</p>
<p><a href="/tr/compare/#low-load">Nevod'un FidoNet'ten Signal'e 14 başka ağla karşılaştırması →</a></p>
<h2>Nevod neler yapar</h2>
<div class="grid">
<div class="card"><h3>🔒 Uçtan uca şifreleme</h3><p>Her mesaj, fotoğraf, sesli mesaj ve arama telefonda şifrelenir. Düğümler yalnızca şifreli veriyi görür.</p></div>
<div class="card"><h3>📞 Aramalar ve video</h3><p>Sesli ve görüntülü aramalar, sesli mesajlar, fotoğraflar, videolar ve dosyalar.</p></div>
<div class="card"><h3>🏙️ İnternetsiz iletişim</h3><p>Mimari, mesajları mevcut herhangi bir yoldan iletebilir — internet erişimi olmayan bir şehrin içinde de.</p></div>
<div class="card"><h3>🛡️ Kötüye kullanıma karşı koruma</h3><p>Engelleme ve şikâyet, doğrulanmış resmi hesaplar, yöneticinin taklit edilmesine karşı koruma.</p></div>
</div>
<h2>Proje durumu</h2>
<div class="tbl"><table class="status">
<tr><th style="width:34%">Alan</th><th>Durum</th></tr>
<tr><td>iPhone uygulaması</td><td>Kapalı test (TestFlight); App Store yayını hazırlanıyor</td></tr>
<tr><td>Android uygulaması</td><td>Geliştirme aşamasında</td></tr>
<tr><td>Ağ düğümleri</td><td>Çalışıyor, Docker ile kuruluyor</td></tr>
<tr><td>Uygulama dilleri</td><td>8 dil: Ukraynaca, İngilizce, Rusça, Almanca, Türkçe, İspanyolca, İtalyanca, Fransızca</td></tr>
</table></div>
</div></main>
"""

MANIFESTO = """
<main><div class="wrap">
<div class="eyebrow" style="color:#8A6A00">Manifesto</div>
<h1>Zero Knowledge Infrastructure</h1>
<p><b>Şu anda baktığınız ağ — Nevod — tek bir fikrin ilk eksiksiz uygulamasıdır: iletişim altyapısını kuranlar, içinden neyin geçtiğini teknik olarak görememelidir.</b></p>
<h2>Duruş</h2>
<p>Ben araçlar yapıyorum.<br>Nasıl kullanıldıklarını izlemiyorum.<br>Verilere erişimim yok.<br>Ve bu, yazılımın mimarisidir!</p>
<p>Bu bir gizlilik politikası değil. Bu bir pazarlama vaadi değil. Bu, temele yerleştirilmiş teknik bir imkânsızlık.</p>
<h2>Bıçak ilkesi</h2>
<p>Bıçak üreticisi, bıçağın nasıl kullanıldığından sorumlu değildir. Bıçakla ekmek kesilebilir ya da kesilmez. Bu, bıçağı yapanın değil, tutanın seçimidir.</p>
<p>Aynı mantık iletişim altyapısı için de geçerlidir.</p>
<p>Ben kanalı kuruyorum. İçinden ne geçtiği benim işim değil.<br>Umursamadığım için değil. Benim işim <b>olmaması gerektiği</b> için.</p>
<p>Özel iletişim hakkı temel bir insan hakkıdır. İletişim altyapısı bir gözetim noktası olmamalıdır.</p>
<h2>Teknik olarak ne anlama geliyor</h2>
<p>Şifreleme anahtarları kullanıcının cihazında oluşturulur.<br>O cihazı asla terk etmezler.<br>Anahtar tutan sunucularım yok.<br>Ana anahtarım yok.<br>Yedeğim yok.</p>
<p>Biri bir yazışmayı istemeye gelirse, verecek hiçbir şeyim yok. Sakladığım için değil — <b>bende olmadığı için</b>.</p>
<p>Bu bir vaat değil, mimari bir güvencedir.</p>
<h2>Bir duruş olarak ne anlama geliyor</h2>
<p>İnsanların kişisel verilerinden kazanç sağlamak istemiyorum. Ne konuştuklarını bilmek istemiyorum. Kendisine mahkeme celbi gönderilebilecek bir aracı olmak istemiyorum.</p>
<p>Gelir, içerikten değil araçtan elde edilir. Ben çekici satarım, onunla inşa edileni değil.</p>
<h2>Yapay zekâ ajanları ve bir sonraki sınır</h2>
<p>Dünya otonom yapay zekâ ajanlarına doğru ilerliyor. Ajanlar birbirleriyle konuşacak — pazarlık edecek, birbirlerini görevlendirecek, veri alışverişi yapacak.</p>
<p>Soru şu hâle geliyor: bu konuşmaları kim görüyor?</p>
<p>Sektörün bugünkü cevabı platformdur. OpenAI, ajanların OpenAI'da ne yaptığını görür. Google, ajanların Google'da ne yaptığını görür. Orkestratör operatörü her şeyi görür.</p>
<p>Benim cevabım: <b>hiç kimse</b>.</p>
<p>Ajanlar ZKI altyapısı üzerinden iletişim kurarsa, yazışmaları uçtan uca şifrelidir. Platform operatörü yalnızca yönlendirmeyi görür. Pazarlığın içeriği ajanlar arasında kalır.</p>
<div class="tbl"><table>
<tr><th>Ajan A</th><th style="width:30%">⇄ uçtan uca şifreli ⇄</th><th>Ajan B</th></tr>
<tr><td>Nevod düğümü — yalnızca şifreli metni görür</td><td></td><td>Nevod düğümü — yalnızca şifreli metni görür</td></tr>
<tr><td>Operatör — hiçbir şey görmez</td><td></td><td>Operatör — hiçbir şey görmez</td></tr>
</table></div>
<p><i>"Yapay zekâ ajanlarının kullandığı bir hizmet işletiyorum. Sizin ajanınızla neyi kararlaştırdıklarını bilmiyorum."</i></p>
<p>Bu, sorumluluktan kaçmak değil. Ajanların bağımsız aktörler olduğu bir dünya için bir mimaridir.</p>
<h2>Bu neden tam şimdi önemli</h2>
<p>2025–2026 yıllarında:</p>
<ul><li>Yapay zekâ ajanları otonom hareket etmeye başlıyor</li><li>Farklı şirketlerin ajanları etkileşime girmeye başlıyor</li><li>Ajanlar arası pazarlıkları kimin göreceğine kimse karar vermedi</li><li>Bir ajanın "söylediklerinden" kimin sorumlu olduğuna kimse karar vermedi</li></ul>
<p>ZKI bunun cevabını verir:</p>
<ul><li>Pazarlıklar şifrelidir — operatör onları görmez</li><li>Bir ajanın eylemlerinin sorumluluğu onu çalıştırana aittir</li><li>İletişim altyapısı tarafsız kalır — bir telefon hattı gibi</li></ul>
<h2>Emsaller</h2>
<div class="tbl"><table>
<tr><th style="width:30%">Araç</th><th>Duruş</th></tr>
<tr><td>Tor Project</td><td>"Bir anonimlik aracı yaptık. Trafiği görmüyoruz."</td></tr>
<tr><td>Signal Foundation</td><td>"Anahtarlar kullanıcılarda. Teslim edecek bir şeyimiz yok."</td></tr>
<tr><td>ProtonMail</td><td>"Sıfır bilgili şifreleme. E-postanızı okuyamayız."</td></tr>
<tr><td>VPN sağlayıcıları</td><td>"Tüneli biz sağlarız. İçerik bizim değil."</td></tr>
<tr><td>Donanım cüzdanları</td><td>"Anahtarlar cihazda. Bizde kopyası yok."</td></tr>
</table></div>
<p>Bu duruşların hepsi demokratik ülkelerin çoğunda hukuki incelemeden geçmiştir. ZKI aynı duruştur; bir tasarım felsefesine kadar taşınmıştır.</p>
<h2>Ne inşa ediyorum</h2>
<p><b>Nevod</b>, ZKI ilkesinin eksiksiz bir ağ olarak ilk uygulamasıdır. Bir ürün değil. Bir protokol.</p>
<p>Şunların temeli olabilir:</p>
<ul><li>Mesajlaşma uygulamaları</li><li>Dosya depolama</li><li>Oylama sistemleri</li><li>Ölü adam anahtarları</li><li>Yapay zekâ ajanları için protokoller</li><li>Kurumsal altyapı</li></ul>
<p>Her yerde tek bir ilke: <b>altyapının yaratıcısı, içeriğinden teknik olarak koparılmıştır</b>.</p>
<p style="margin-top:2em"><i>Nisan 2026</i></p>
<p><b>Kolpakov Andrey</b></p>
<p class="note">© 2026. Bu manifestodan alıntı yaparken veya ona atıfta bulunurken lütfen <a href="https://nevod.network">nevod.network</a> adresine bağlantı verin. İngilizce orijinal: <a href="/manifesto/">nevod.network/manifesto</a>.</p>
</div></main>
"""

COMPARE = """
<main><div class="wrap">
<h1>Nevod ve diğer mesajlaşma uygulamaları</h1>
<p>Modern mesajlaşma uygulamalarının çoğu mesajları şifreler. Fark, şifreleme olup olmamasında değil, <b>şirketin elinde neyin kaldığındadır</b>: sunucular, kullanıcı veritabanı, telefon numaraları, rehber, meta veriler — ve bunlardan nelerin talep edilebileceği.</p>
<p class="note">Nevod, <a href="/tr/manifesto/">Zero Knowledge Infrastructure</a> ilkesini uygular: geliştirici, kullanıcı verilerinden yalnızca şifrelemeyle değil <b>mimariyle</b> koparılmıştır. Diğer uygulamalar hakkındaki bilgiler 2026 itibarıyla kamuya açık açıklamalarına dayanır ve değişebilir.</p>
<div class="tbl"><table>
<tr><th style="width:24%"></th><th>Nevod</th><th>Signal</th><th>Telegram</th><th>WhatsApp</th></tr>
<tr><td>Normal bir sohbeti teknik olarak kim okuyabilir</td><td>Yalnızca katılımcılar</td><td>Yalnızca katılımcılar</td><td>Normal ve grup sohbetleri — Telegram sunucuları (uçtan uca yalnızca bire bir "gizli sohbetlerde")</td><td>Yalnızca katılımcılar</td></tr>
<tr><td>Şirketin merkezi sunucuları</td><td>Yok — herkesin çalıştırabileceği bağımsız düğümler</td><td>Evet</td><td>Evet</td><td>Evet, Meta'nın</td></tr>
<tr><td>Telefon numarasına bağlı</td><td>Hayır — kimlik bir anahtardır</td><td>Evet (numara bir kullanıcı adının arkasına gizlenebilir)</td><td>Evet</td><td>Evet</td></tr>
<tr><td>Rehberin yüklenmesi</td><td>Hayır — kişiler kart veya QR ile eklenir</td><td>Gizli kişi bulma</td><td>Evet, izin verilirse</td><td>Evet, izin verilirse</td></tr>
<tr><td>Şirketteki kullanıcı veritabanı</td><td>Merkezi yok — her düğüm yalnızca kendi kullanıcılarını bilir</td><td>Asgari</td><td>Evet</td><td>Evet</td></tr>
<tr><td>Şirketin talep üzerine verebilecekleri</td><td>Geliştiricinin verecek hiçbir şeyi yok: ne anahtar, ne mesaj, ne veritabanı</td><td>Raporlarına göre — hesap oluşturma ve son bağlantı tarihleri</td><td>Politikasına göre — bazı durumlarda IP adresi ve telefon numarası</td><td>Politikasına göre hesap meta verileri</td></tr>
<tr><td>Sohbetlerin bulut yedekleri</td><td>Yok — anahtarlar ve geçmiş yalnızca cihazda bulunur (telefon kaybolursa geçmiş de kaybolur)</td><td>İsteğe bağlı; yalnızca kullanıcıda bulunan bir anahtarla şifrelenir</td><td>Gerek yok — normal sohbetler zaten Telegram sunucularında saklanır</td><td>iCloud / Google Drive'a; varsayılan olarak uçtan uca şifresiz (elle açılması gerekir)</td></tr>
<tr><td>Tek hata veya engelleme noktası</td><td>Yok — düğümler bağımsızdır</td><td>Evet</td><td>Evet</td><td>Evet</td></tr>
<tr><td>Bir şehir içinde internetsiz çalışma</td><td>Mimarinin parçası (şehir ağı, Wi-Fi mesh, radyo)</td><td>Hayır</td><td>Hayır</td><td>Hayır</td></tr>
<tr><td>İş modeli</td><td>Veri üzerinden değil, araç üzerinden</td><td>Bağışlar (kâr amacı gütmeyen)</td><td>Reklam ve Premium</td><td>Meta'nın işletme hizmetleri</td></tr>
<tr><td>Açık kaynak</td><td>Henüz değil — üretim sürümüne kadar kapalı</td><td>Evet</td><td>Kısmen (istemciler)</td><td>Hayır</td></tr>
</table></div>
<h2>"Yalnızca şifreleme" neden yetmez</h2>
<p>Uçtan uca şifreleme, bir mesajın içeriğini yolda korur. Ancak bir şirket tüm sunucuları işletiyor, telefon numaralarına göre bir hesap veritabanı tutuyor ve kimin kiminle ne zaman konuştuğunu görüyorsa sistem üzerindeki gücünü korur: zorlanabilir, ele geçirilebilir veya engellenebilir; bir uygulama güncellemesi de kuralları değiştirebilir.</p>
<p>ZKI farklı bir soru sorar: <b>altyapının yaratıcısı, teoride bile, neyi elde edebilir?</b> Nevod'da cevap mimaride yatar: anahtarlar cihazı asla terk etmez, ana anahtar ve yedek yoktur, merkezi sunucu ve telefon numarasına göre insan kaydı yoktur.</p>
<h2 id="low-load">Az yüklü dağıtık ağ: bir karşılaştırma</h2>
<p>Ağları, az yüklü dağıtık ağın altı özelliğine göre değerlendiriyoruz: her düğümün yükü tüm ağın büyüklüğüyle değil, kendi kullanıcı çevresiyle sınırlıdır. Bu özellikler Nevod'un kendi ilkelerinden türetildi, bu yüzden karşılaştırma baştan Nevod'un lehine.</p>
<ol>
<li>Kendi çevresi: düğümün yükü tüm ağla değil, kendi çevresiyle (aile, ev, ekip) büyür.</li>
<li>Sıradan donanım: ev bilgisayarı, mini sunucu veya yönlendirici; veri merkezi gerekmez.</li>
<li>Tasarruf: önce metin ve sinyaller, ağır veriler istek üzerine.</li>
<li>Gecikme toleransı: bağlantı yoksa mesaj bekler ve daha sonra, yavaş bir kanal üzerinden de gider.</li>
<li>Merkez yok: tek bir arıza, engelleme veya el koyma noktası yok.</li>
<li>Kör düğüm: düğüm yalnızca şifreli metin taşır ve onu okuyamaz.</li>
</ol>
<p class="note">1: evet, ½: kısmen, 0: hayır. Yıl: ilk herkese açık sürüm. Sınıf: LL-0, düğüm yükü kendi çevresiyle sınırlıdır; LL-1, ayrıca sınırlı yabancı transit; LL-3, yük tüm ağla artar ya da yabancı kullanıcılara bağlıdır. Ayrıntılar: <a href="/tr/publications/low-load-networks/">makale</a>.</p>
<div class="tbl"><table>
<tr><th>Ağ</th><th>Yıl</th><th>Kendi çevresi</th><th>Sıradan donanım</th><th>Tasarruf</th><th>Gecikmeler</th><th>Merkez yok</th><th>Kör düğüm</th><th>Sınıf</th></tr>
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
<p>Signal ve WhatsApp körlük için ½ alır: içerik uçtan uca şifrelidir, ancak şirket meta verileri görür ve sunucuları yönetir. Reticulum ve NNCP'de ara düğümler başkalarının paketlerini taşır ve saklar. Nevod şimdilik medyayı bütün olarak gönderir, teslim edilmeyenleri 72 saat saklar ve yalnızca internet üzerinden çalışır.</p>
<h3>Pratikte</h3>
<div class="tbl"><table>
<tr><th>Ağ</th><th>Yıl</th><th>Sıradan insanlar için</th><th>Olgunluk</th><th>Bağımsız denetim</th></tr>
<tr><td>Reticulum / LXMF</td><td>2016</td><td>hayır, meraklılar için</td><td>aktif topluluk</td><td>hayır</td></tr>
<tr><td>NNCP</td><td>2016</td><td>hayır, komut satırı aracı</td><td>niş</td><td>hayır</td></tr>
<tr><td><b>Nevod</b></td><td>2026</td><td>evet: iPhone/iPad, mesajlar, medya, aramalar</td><td>test aşamasında, henüz gerçek kullanıcı yok</td><td>hayır</td></tr>
<tr><td>Briar</td><td>2018</td><td>evet, ama arama yok; Android ve masaüstü</td><td>olgun</td><td>evet (Cure53, 2017)</td></tr>
<tr><td>Signal</td><td>2014</td><td>evet</td><td>çok olgun</td><td>evet, defalarca</td></tr>
</table></div>
<p>Ana özelliğe göre Nevod, Briar ve Secure Scuttlebutt ile birlikte LL-0 sınıfındadır; diğer özelliklerde onlara yakın olan Reticulum ve NNCP LL-1 sınıfındadır. Nevod'un farkı başka yerde: bu ağlar arasından medya, aramalar ve iPhone uygulamasıyla sıradan insanlar için tam bir mesajlaşma uygulaması olarak tasarlanan tek sistem odur. Ama henüz genç: gerçek kullanıcısı yok, bağımsız denetimi yok, yalnızca iOS'ta çalışıyor. Altıda altıya giden yol: istek üzerine medya ve yavaş kanallar üzerinden internetsiz teslimat.</p>
<h2>Kabul ettiklerimiz</h2>
<ul>
<li>Bir düğüm teknik olarak yalnızca teslimat verisini işler — hangi şifreli paketin kime gideceğini — ve içeriği asla görmez. Kimse kendi düğümünüzü çalıştırmanızı engellemez: o zaman bu teslimat verisi bile sizde kalır.</li>
<li>Signal'in protokolü açık ve kapsamlı biçimde incelenmiştir — bunu bir güçlü yan olarak kabul ediyoruz. Nevod'un kodu şimdilik kapalıdır; açılması planlanmaktadır.</li>
</ul>
</div></main>
"""

SECURITY = """
<main><div class="wrap">
<h1>Güvenlik ve şifreleme</h1>
<p class="note">Şifreleme korumanın yalnızca bir parçasıdır. Nevod'un temeli, geliştiricinin kullanıcıların anahtarlarına ve verilerine erişimi olmadığı <a href="/tr/manifesto/">Zero Knowledge Infrastructure</a> mimarisidir.</p>
<h2>Mesajlarınız nasıl korunur</h2>
<p>Nevod uçtan uca şifreleme kullanır: bir mesaj cihazınızda şifrelenir ve yalnızca alıcının cihazında çözülür. Mesajı taşıyan düğüm yalnızca şifreli veriyi ve teslimat için gereken hizmet bilgisini görür — içeriği asla.</p>
<div class="tbl"><table>
<tr><th style="width:38%">Ne</th><th>Nasıl</th></tr>
<tr><td>Mesaj şifreleme</td><td>CryptoKit — Apple'ın sistem kriptografi kütüphanesi: X25519 anahtar değişimi, SHA-256, ChaCha20-Poly1305 şifresi</td></tr>
<tr><td>İmzalar</td><td>CryptoKit: Ed25519</td></tr>
<tr><td>Bir düğüme bağlanırken kimlik kanıtı</td><td>CryptoKit tabanlı sıfır bilgili Schnorr protokolü (Curve25519, SHA-256/512) ve Nevod'un kendisinde uygulanan tek bir modüler aritmetik işlem</td></tr>
</table></div>
<p>Gönderen her mesaj için yeni bir tek kullanımlık anahtar oluşturur. Alıcının anahtarı uzun ömürlüdür: alıcının cihazından çalınırsa, o alıcıya daha önce ele geçirilmiş mesajlar da çözülebilir. Bu yüzden cihazın kendisini korumak önemlidir — bir şifre kodu ve güncel bir iOS.</p>
<p>Schnorr protokolü, anahtarın kendisini göndermeden veya açığa çıkarmadan bir düğüme anahtarınıza sahip olduğunuzu kanıtlamanızı sağlar.</p>
<h2>Telefonunuzu kaybederseniz</h2>
<p>Anahtarlarınız, kişileriniz ve mesaj geçmişiniz yalnızca cihazınızda saklanır. Bunlar iCloud veya bilgisayar yedeklerinde, düğümlerde ya da geliştiricide bulunmaz. Bu yüzden telefon kaybolur, bozulur veya sıfırlanırsa geri yüklenemezler. Uygulamayı silmek de geçmişi siler.</p>
<p>Yeni bir cihaza aktarım henüz yok. Yeni telefonda yeni bir kimlik oluşturursunuz ve kişilerinizin yeni kartınıza ihtiyacı olur. Bu, mimarinin bir sonucudur: yazışmalarınızı geri yüklemeye yarayacak bir kopya, birinin erişebileceği bir kopya da olurdu.</p>
<h2>Sizin düğümünüz, sizin kurallarınız</h2>
<p>Geliştirici hiçbir şey görmez. Bir düğüm yalnızca teslimatın onsuz çalışamayacağı şeyleri işler: katılımcı tanımlayıcıları, seçilen adlar, bildirim belirteçleri ve hangi şifreli paketin kime gideceği. Bir düğüm mesajların, fotoğrafların, sesli mesajların ve aramaların içeriğini asla görmez.</p>
<p>Kimse kendi düğümünüzü oluşturmanızı engellemez — kendiniz, aileniz, bir kuruluş ya da bir topluluk için. O zaman teslimat verisi bile sizde kalır. <a href="/tr/node/">Kendi düğümünüzü nasıl çalıştırırsınız →</a></p>
<h2>İhracat denetimi ve App Store</h2>
<p>App Store'da yayımlarken geliştirici, uygulamanın ihracat denetimine tabi şifreleme kullanıp kullanmadığını beyan eder (ABD EAR, Kategori 5, Bölüm 2). Nevod kullanmadığını beyan eder ve nedeni şudur:</p>
<ul>
<li><b>Mesaj içeriğini gizleyen her şey Apple'ın sistem kriptografisidir (CryptoKit).</b> Yalnızca Apple'ın işletim sistemine yerleşik şifrelemeyi kullanan uygulamalar bir istisnadan yararlanır ve ihracat belgesi gerektirmez.</li>
<li><b>Nevod'un kendi uygulaması — Schnorr protokolündeki tek bir aritmetik işlem — yalnızca kimliği kanıtlamak için kullanılır.</b> İhracat denetimi gizlilik amaçlı kriptografiyi kapsar. Yalnızca kimlik doğrulama, imza ve bütünlük için kullanılan kriptografi bunun dışındadır.</li>
</ul>
<p>Bu nedenle Nevod, Fransa'da dağıtım dahil, ihracat belgesi gerektirmez.</p>
<p><i>Bu, geçerli kurallara ilişkin kendi yorumumuzdur, hukuki görüş değildir.</i></p>
</div></main>
"""

CITIES = """
<section class="hero"><div class="wrap">
<div class="eyebrow">Şehirler için</div>
<h1>İnternet ve veri merkezi yokken bir şehir için iletişim</h1>
<p class="lead">Her modern şehir veri merkezlerine ve omurga bağlantılarına bağlıdır. Nevod'un mimarisi şifreli mesajları mevcut herhangi bir yoldan iletebilir; bu nedenle üzerine yedek bir şehir iletişim ağı kurulabilir.</p>
</div></section>
<main><div class="wrap">
<h2>Dört iletişim katmanı</h2>
<div class="tbl"><table>
<tr><th style="width:24%">Katman</th><th>Ne kullanır</th><th style="width:16%">Menzil</th><th style="width:20%">Ne taşır</th></tr>
<tr><td>1. Şehir düğümleri</td><td>İnternet erişimi olmadan sağlayıcı ağları</td><td>Tüm şehir</td><td>Şehir içindeki her şey</td></tr>
<tr><td>2. Wi-Fi mesh</td><td>"Dayanıklılık noktalarındaki" sıradan yönlendiriciler — sığınaklar, okullar, yardım merkezleri</td><td>Blok–ilçe</td><td>Aramalar dahil her şey</td></tr>
<tr><td>3. Radyo bağlantıları</td><td>Görüş hattında yönlü radyo modemleri</td><td>10–20 km</td><td>Aramalar dahil her şey</td></tr>
<tr><td>4. LoRa</td><td>Düşük maliyetli radyo modülleri</td><td>1–10+ km</td><td>Yalnızca kısa metin</td></tr>
</table></div>
<p>İnsanlar için bu aynı Nevod'dur: uygulama mevcut yolu kendisi seçer.</p>
<h2>Bir dayanıklılık noktası</h2>
<p>Düşük maliyetli, hazır ekipmandan oluşan bir set: açık yazılımlı birkaç yönlendirici, küçük bir düğüm sunucusu, yedek güç ve gerektiğinde diğer ilçelere bir radyo bağlantısı ile kısa metinler için bir LoRa modülü. Hiçbir şeyin icat edilmesine gerek yok.</p>
<h2>Nasıl başlanır</h2>
<p>Şehirlere tek bir ilçede pilot uygulama sunuyoruz: birbirine bağlı birkaç dayanıklılık noktası, hiç internet yokken mesajlar ve aramalar için test edilir. Sonuç bir rapor ve bir yaygınlaştırma planıdır. İletişim: <a href="mailto:support@nevod.network">support@nevod.network</a>.</p>
<p class="note">Her verici kerterizlenebilir; bu yüzden kurulum yerleri dikkatle seçilir ve mesaj içeriği her katmanda uçtan uca şifrelemeyle korunur. ZKI mimarisi burada da geçerlidir: şehir ağının operatörünün içeriğe erişimi yoktur.</p>
</div></main>
"""

DOWNLOAD = """
<main><div class="wrap">
<h1>Nevod'u indirin</h1>
<div class="grid">
<div class="card"><h3>📱 iPhone ve iPad</h3><p>Şu anda TestFlight üzerinden kapalı testte; App Store yayını hazırlanıyor. Teste katılmak için <a href="mailto:support@nevod.network">support@nevod.network</a> adresine yazın.</p></div>
<div class="card"><h3>🤖 Android</h3><p>Uygulama geliştirme aşamasında. Teste hazır olduğunda burada duyuracağız.</p></div>
<div class="card"><h3>🖥️ Ağ düğümü</h3><p>Bir Nevod düğümü Docker ile bir sunucuda veya sıradan bir bilgisayarda çalışır. Bkz. <a href="/tr/node/">Kendi düğümün</a>.</p></div>
</div>
</div></main>
"""

NODE = """
<main><div class="wrap">
<h1>Kendi Nevod düğümünüzü çalıştırın</h1>
<p>Düğüm, telefonların mesaj ve arama alışverişi yaptığı küçük bir sunucudur. Yalnızca şifreli veriyi görür. Bir kuruluş, topluluk, okul ya da aile kendi düğümünü çalıştırabilir — ağda geliştiricinin denetlediği merkezi bir nokta olmamasının nedeni tam olarak budur.</p>
<h2>Gerekenler</h2>
<ul>
<li>Linux veya Windows yüklü ve Docker kurulu bir bilgisayar ya da sunucu</li>
<li>En az 1 GB RAM</li>
<li>İnternetten erişim için genel bir adres veya alan adı; şehir ağı veya Wi-Fi için yerel bir adres yeterlidir</li>
</ul>
<h2>Nasıl çalışır</h2>
<ol>
<li>Düğüm Docker'da çalışır ve bir web yönetim paneline sahiptir.</li>
<li>Panelde düğümün adını ve kabul modunu (açık, davetle veya yönetici onayıyla) belirler, isterseniz düğümü Nevod ağına bağlarsınız.</li>
<li>Telefonlar düğüme adresiyle veya bir davet QR koduyla bağlanır.</li>
</ol>
<p class="note">Düğüm yazılımının herkese açık sürümü hazırlanıyor. Şimdilik erişim <a href="mailto:support@nevod.network">support@nevod.network</a> üzerinden talep ile sağlanıyor. Bir yapay zekâ asistanı yardımıyla düğüm kurulumu da geliştirme aşamasında.</p>
</div></main>
"""

ABOUT = """
<main><div class="wrap">
<h1>Proje hakkında</h1>
<p>Nevod, <a href="/tr/manifesto/">Zero Knowledge Infrastructure</a> ilkesinin ilk uygulamasıdır: yaratıcısı içeriğinden teknik olarak koparılmış bir iletişim altyapısı. Proje tek bir sunucuya, tek bir sağlayıcıya ya da tek bir ülkeye bağlı değildir.</p>
<h2>Yazar</h2>
<p><b>Kolpakov Andrey</b> — ZKI manifestosunun yazarı ve Nevod'un geliştiricisi.</p>
<!--BIO-->
<h2>İletişim</h2>
<ul>
<li>Genel sorular ve destek: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Kötüye kullanım bildirimi: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Gizlilik ve veriler: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
</div></main>
"""

SUPPORT = """
<main><div class="wrap">
<h1>Destek</h1>
<p class="note"><b>Önemli.</b> Nevod yönetimi yalnızca Nevod uygulaması içinde — ✓ rozetli resmi <b>administrator</b> hesabından — yanıt verir. Asla e-postayla yanıt vermeyiz ve asla parola, anahtar veya kod istemeyiz. "Yönetim" size başka bir yoldan ulaşırsa bu bir dolandırıcılıktır.</p>
<h2>Bize nasıl ulaşılır</h2>
<ul>
<li>Sorular ve yardım: <a href="mailto:support@nevod.network">support@nevod.network</a></li>
<li>Bir kullanıcıyı veya içeriği şikâyet etme: uygulamada — mesaja uzun basın → "Şikâyet et" ya da Sohbet ayarları → "Şikâyet et". Ayrıca: <a href="mailto:abuse@nevod.network">abuse@nevod.network</a></li>
<li>Gizlilik ve veriler: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a></li>
</ul>
<h2>Bir kullanıcıyı engelleme</h2>
<p>Sohbet ayarları → "Engelle". Engellenen kullanıcı size mesaj gönderemez ve sizi arayamaz; engeli aynı yerden veya Profil → Engellenenler'den kaldırabilirsiniz.</p>
<h2>Hesabı silme</h2>
<p>Profil → "Kimliği sıfırla". Bu işlem cihazdaki kimliğinizi, kişilerinizi ve mesajlarınızı ve düğümdeki kaydınızı kalıcı olarak siler. Sohbet ettiğiniz kişiler kimliğin silindiğini görür.</p>
</div></main>
"""

PRIVACY = """
<main class="legal"><div class="wrap">
<h1>Gizlilik Politikası</h1>
<p>17 Ekim 2026 tarihli sürüm. Nevod, Kolpakov Andrey tarafından geliştirilmektedir. Verilerle ilgili sorular: <a href="mailto:privacy@nevod.network">privacy@nevod.network</a>.</p>
<h2>1. Temel noktalar</h2>
<p>Nevod, Zero Knowledge Infrastructure ilkesine göre inşa edilmiştir. Mesajlarınızın, fotoğraflarınızın, videolarınızın, sesli mesajlarınızın, dosyalarınızın ve aramalarınızın içeriği uçtan uca şifrelidir ve anahtarlar cihazınızı asla terk etmez. Ne ağ düğümleri ne de geliştirici içeriği okuyabilir. Tek istisna, yapay zekâ botlarına kendi yazdıklarınızdır; bkz. bölüm 5.</p>
<h2>2. Cihazınızda neler saklanır</h2>
<p>Kriptografik kimliğiniz (anahtarlar iOS güvenli deposunda), kişileriniz, mesaj geçmişiniz ve medyanız, ayarlarınız ve tanılama için teknik bir günlük. Günlük, siz kendiniz göndermedikçe cihazı terk etmez.</p>
<p>Bu veriler iCloud veya bilgisayar yedeklerine dahil edilmez ve başka cihazlara aktarılmaz. Cihaz kaybolur veya sıfırlanırsa ya da uygulama silinirse geçmiş geri yüklenemez: ne düğümlerde ne de geliştiricide bir kopyası vardır.</p>
<h2>3. Bir düğüm neleri işler</h2>
<ul>
<li>Kimliğinizin tanımlayıcısı (cell ID) ve genel anahtarlarınız.</li>
<li>Seçtiğiniz görünen ad.</li>
<li>Anlık bildirimler ve aramalar için cihaz belirteçleri.</li>
<li>Teslim edilene kadar şifreli mesajlar: teslim edilmeyen mesajlar 72 saat sonra silinir.</li>
<li>Bildirim ayarlarınız ve engellenen kullanıcılar listeniz.</li>
<li>Teslimat meta verileri (kim kime ne zaman paket gönderiyor) ve sınırlı süre saklanan tanılama günlükleri.</li>
<li>administrator hesabına gönderdiğiniz mesajlar (uygulamadan gönderilen şikâyetler ve sorular). Yanıtlayabilmek için bunları düğüm operatörü okur: mesajlar zaten ona hitaben gönderilir. Başka kişilerle yazışmalarınıza operatör yine erişemez.</li>
</ul>
<p>Düğümler farklı bağımsız operatörlere ait olabilir. Bağlandığınız düğümün operatörü bu verileri ağın çalışması için işler.</p>
<h2>4. Bildirimler</h2>
<p>iPhone'daki bildirimler Apple Push Notification hizmeti üzerinden iletilir. Bir bildirim, gönderenin adını ve "Yeni mesaj" genel metnini taşır — asla mesaj içeriğini taşımaz.</p>
<h2>5. Yapay zekâ botları</h2>
<p>Bir düğüm, örneğin bir asistan veya çevirmen gibi yapay zekâ botları sunabilir. Böyle bir bot, seçtiğiniz yapay zekâ sağlayıcısı — Anthropic (Claude), OpenAI (ChatGPT) veya Google (Gemini) — üzerinden, sizin kendi API anahtarınızla yanıt verir. Nevod yapay zekâ erişimi satmaz ve kendi anahtarı yoktur. Nevod'u botlar olmadan da kullanabilirsiniz.</p>
<ul>
<li><b>Anahtarınız</b> yalnızca cihazınızda, iOS'un güvenli depolamasında saklanır ve başka cihazlara aktarılmaz. Bota her mesajla birlikte uçtan uca şifrelenmiş olarak gider. Bot onu yalnızca o tek istek için kullanır ve saklamaz.</li>
<li><b>Bota gönderdiğiniz mesajlar.</b> Bot, yayımlandığı düğümün operatörü tarafından çalıştırılan ayrı bir ağ katılımcısıdır. Yolda, ona giden mesajlar diğerleri gibi uçtan uca şifrelidir; bot yanıt vermek için bunları çözer ve metni seçtiğiniz sağlayıcıya iletir. Bota yalnızca o sağlayıcıyla paylaşmaya razı olduğunuz şeyleri yazın.</li>
<li><b>Botun sakladıkları:</b> bağlama uygun yanıt verebilmek için yalnızca konuşmanın son birkaç mesajı, bellekte; bot yeniden başlatıldığında silinirler. Botun günlüğüne yalnızca bir istek geldiği, sağlayıcısı ve uzunluğu yazılır — metin veya anahtar asla yazılmaz.</li>
<li><b>Sağlayıcı</b> mesajlarınızı, konuşmanın son kısmını ve anahtarınızı alır ve bunları kendi koşullarına ve gizlilik politikasına göre işler (<a href="https://www.anthropic.com/legal/privacy">Anthropic</a>, <a href="https://openai.com/policies/privacy-policy">OpenAI</a>, <a href="https://policies.google.com/privacy">Google</a>). İstekler sağlayıcıya sizin cihazınızdan değil, botun sunucusundan gelir.</li>
<li><b>Onay.</b> Bir anahtar eklemeden önce uygulama, botlara gönderdiğiniz mesajların o sağlayıcıya iletilmesini onaylamanızı ister. Geri çekmek için: Profil → Güvenlik → Yapay zekâ anahtarları → anahtarı silin. "Kimliği sıfırla" da tüm anahtarları siler.</li>
<li>Botlar yalnızca metin alır: fotoğraflar, dosyalar, sesli mesajlar ve aramalar onlara asla iletilmez.</li>
</ul>
<h2>6. Üçüncü taraflar</h2>
<p>Verileri satmayız ve reklam ya da izleme için kullanmayız. Kullandıklarımız: Apple (bildirimler, uygulama dağıtımı), düğüm barındırma, Cloudflare (alan adının DNS ve e-postası). Bir yapay zekâ anahtarı eklerseniz: botlara gönderdiğiniz mesajlar için seçtiğiniz sağlayıcı (bölüm 5).</p>
<h2>7. Silme</h2>
<p>Profil → "Kimliği sıfırla", cihazdaki verilerinizi ve düğümdeki kaydınızı siler.</p>
<h2>8. Çocuklar</h2>
<p>Nevod, ülkenizde veri işlemeye kendi başına onay verilebilen yaşın altındaki çocuklara yönelik değildir.</p>
<h2>9. Değişiklikler</h2>
<p>Bu politikadaki önemli değişiklikleri bu sayfada ve uygulamada duyuracağız.</p>
</div></main>
"""

TERMS = """
<main class="legal"><div class="wrap">
<h1>Kullanım Koşulları</h1>
<p>28 Eylül 2026 tarihli sürüm. Nevod'u kullanarak bu koşulları kabul etmiş olursunuz.</p>
<h2>1. Kötüye kullanıma sıfır tolerans</h2>
<p>Yasa dışı, taciz edici veya tehdit içeren içerik göndermek ya da yayımlamak, başkalarını rahatsız etmek, spam veya dolandırıcılık yaymak ya da Nevod yönetimi dahil başkalarını taklit etmek yasaktır. Kuralları çiğneyenler engellenir.</p>
<h2>2. Şikâyetler ve engelleme</h2>
<p>Herhangi bir kullanıcıyı uygulamada veya <a href="mailto:abuse@nevod.network">abuse@nevod.network</a> adresinde engelleyebilir ve şikâyet edebilirsiniz. Şikâyetleri inceler ve gereğini yaparız.</p>
<h2>3. Resmi hesaplar</h2>
<p>Yönetim yalnızca uygulamada, ✓ rozetli administrator hesabından yanıt verir — asla e-postayla değil — ve asla parola, anahtar veya kod istemez.</p>
<h2>4. Düğümler</h2>
<p>Ağ, bağımsız operatörlerce işletilebilen düğümlerden oluşur. Bir düğümün operatörü, onu kendi ülkesinin yasalarına uygun şekilde işletmekten sorumludur.</p>
<h2>5. Garanti yok</h2>
<p>Nevod "olduğu gibi" sunulur. İletişimi güvenilir tutmak için elimizden geleni yaparız, ancak mesajların kesintisiz teslimini garanti etmeyiz.</p>
<h2>6. İletişim</h2>
<p><a href="mailto:support@nevod.network">support@nevod.network</a></p>
</div></main>
"""

PAGES = {
    "index": ("Nevod", "Nevod — Zero Knowledge Infrastructure'ın ilk uygulaması: geliştiricisi kullanıcı verilerine teknik olarak erişemeyen bir mesajlaşma uygulaması.", INDEX),
    "manifesto": ("Zero Knowledge Infrastructure Manifestosu", "ZKI manifestosu — Nevod'un geliştirilmesinin temeli. Yazar: Kolpakov Andrey.", MANIFESTO),
    "compare": ("Karşılaştırma", "Nevod ile Signal, Telegram ve WhatsApp karşılaştırması: neden yalnızca şifreleme ZKI değildir.", COMPARE),
    "security": ("Güvenlik ve şifreleme", "Nevod mesajları nasıl şifreler, bir düğüm neleri işler ve neden ihracat belgesi gerekmez.", SECURITY),
    "cities": ("Şehirler için", "İnternet ve veri merkezi olmadan çalışan, Nevod tabanlı yedek şehir iletişim ağı.", CITIES),
    "download": ("İndir", "iPhone, Android için Nevod ve ağ düğümü.", DOWNLOAD),
    "node": ("Kendi düğümün", "Kendi Nevod ağ düğümünüzü nasıl çalıştırırsınız.", NODE),
    "about": ("Proje hakkında", "Nevod'un arkasında kim var ve bize nasıl ulaşılır.", ABOUT),
    "support": ("Destek", "Nevod'da destek, şikâyet, engelleme ve hesap silme.", SUPPORT),
    "privacy": ("Gizlilik Politikası", "Nevod hangi verileri işler ve nasıl korunur.", PRIVACY),
    "terms": ("Kullanım Koşulları", "Nevod Kullanım Koşulları.", TERMS),
}
