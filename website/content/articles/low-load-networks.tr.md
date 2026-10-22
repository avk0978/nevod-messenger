# Az Yüklü Dağıtık Veri Ağları: Kavram, Sınıflandırma ve Karşılaştırmalı Analiz

**Kavramın yazarı:** Kolpakov Andrey

**Sürüm:** 30 Eylül 2026

**İlgili içerikler:** [Zero Knowledge Infrastructure manifestosu](/tr/manifesto/), [ağların karşılaştırması](/tr/compare/#low-load).

---

## Özet

Bu makale *az yüklü dağıtık veri ağı* kavramını tanıtır: her düğümün yükünün (trafik, depolama,
hizmet durumu) o düğümün kendi katılımcı çevresiyle sınırlı olduğu ve ağın bütünü büyüdükçe
artmadığı bir ağ. İletişim kuramında kullanılan yük sınıflandırmalarının (kullanım oranı,
erlang, verim-yük eğrisindeki "diz" (knee) ve "uçurum" (cliff) noktaları, hizmet kalitesi sınıfları) bir ağın mimarisinin bir
özelliğini değil, belirli bir andaki *durumunu* tanımladığı ve bu nedenle ağları bu özelliğe göre
ayırt edemediği gösterilmektedir. Az yüklü bir ağın altı özelliği ve düğüm başına yükün asimptotik
davranışına göre LL-0…LL-3 sınıflandırması önerilmektedir. FidoNet'ten (1984) Nevod'a (2026) on
beş ağ karşılaştırılmakta ve literatürdeki öncülleri belirtilmektedir: arkadaştan arkadaşa (F2F)
ağlar, gecikmeye dayanıklı ağlar (DTN), dağıtık özet tabloları, yerel öncelikli yazılım
(local-first) ve topluluk ağları (community networks).

**Anahtar kelimeler:** dağıtık ağlar, merkeziyetsizleşme, düğüm başına yük, ölçeklenebilirlik,
F2F, DTN, eşler arası ağlar, mesajlaşma uygulamaları, Zero Knowledge Infrastructure.

---

## 1. Giriş

Günümüzdeki mesajlaşma hizmetlerinin çoğu merkezidir: tüm ağ tek bir şirketin sunucuları
tarafından hizmet görür ve bu sunucuların yükü kullanıcı sayısıyla birlikte büyür. Merkeziyetsiz
alternatifler (federe ağlar, eşler arası katmanlar, anonimleştirici ağlar) altyapının *sahipliğini*
dağıtır, ancak aşağıda gösterileceği gibi genellikle *yükü* dağıtmaz: bir federasyon sunucusu ya
da katman düğümü başkalarının kullanıcılarının ürettiği trafiği, geçmişi ve hizmet durumunu taşır
ve yükü yine ağın ya da ağın popüler kısmının büyüklüğüyle artar.

Çalışmanın amacı, düğüm yükünün yalnızca kendi çevresiyle, yani düğümün ev düğümü olduğu kullanıcılar ve yazılım ajanlarıyla (botlar, yapay zekâ ajanları, hizmetler) belirlendiği ağ sınıfını ayırmak, onu tanımlamak, ölçülebilir bir sınıflandırma önermek ve mevcut ağları bu özelliğe göre karşılaştırmaktır.

## 2. Veri ağlarında yük: mevcut kavramlar

### 2.1 Kullanım oranı

Kuyruk kuramında bir kanalın ya da düğümün yükü, geliş hızının hizmet hızına oranı olan kullanım
oranı ρ = λ/μ ile tanımlanır [1]. ρ → 1 olduğunda kuyruk uzunluğu ve gecikme sınırsız büyür;
ρ > 1 olduğunda sistem aşırı yüklenmiştir. Uygulamada kaba düzeyler kullanılır: düşük kullanım
(ρ < ~0,3), orta (0,3–0,7), yüksek (0,7–0,9), doygunluk ve aşırı yük; operatörler hatları
genellikle yoğun saatte ~%70–80'e kadar pay bırakarak planlar. Bu eşikler tek bir standart değil,
mühendislik ölçütleridir.

### 2.2 Teletrafik: erlang ve en yoğun saat

Telefonide trafik yoğunluğu erlang ile ölçülür (1 Erl, kesintisiz meşgul bir kanaldır) [2];
boyutlandırma en yoğun saate göre yapılır; sunulan, taşınan ve kaybedilen trafik ayırt edilir ve
hizmet derecesi kabul edilebilir bir engellenme olasılığı olarak belirlenir (Erlang B ve C
formülleri) [1, 2].

### 2.3 Ağın artan yüke tepkisi: "diz" ve "uçurum"

Jain, Ramakrishnan ve Chiu [3] bir ağın üç çalışma bölgesini tanımladı: "dizden" önce iş
hacmi düşük gecikmeyle yükle birlikte artar; "diz" ile "uçurum" arasında iş hacmi neredeyse artmaz,
gecikme ise hızla yükselir; "uçurumun" ötesinde tıkanıklık ve çöküş başlar. "Diz" noktasında verimin gecikmeye oranı (ağın "gücü") en yüksek değerine ulaşır; tıkanıklıktan kaçınma (congestion avoidance: çalışmayı "diz" yakınında tutmak) ve tıkanıklık denetimi (congestion control: "uçurumdan" düşmeyi önlemek) bu ayrıma dayanır. TCP tıkanıklık
denetimi bu fikirler üzerine kuruludur [4].

### 2.4 Trafik ve hizmet kalitesi sınıfları

Differentiated Services mimarisi [5] iletim sınıfları getirir (hızlandırılmış iletim EF,
güvenceli iletim AF, en iyi çaba BE); ITU-T Y.1541 tavsiyesi [6] IP ağları için gecikme,
titreşim ve kayba göre 0–5 hizmet kalitesi sınıflarını tanımlar. Bunlar yükün değil, teslimata
yönelik *gereksinimlerin* sınıflandırmalarıdır.

### 2.5 Yük rejimleri: düşük yükten çöküşe

Ağın yüke göre çalışma rejimleri standartlarda ve klasik çalışmalarda tanımlanmıştır:

| Rejim | Nerede tanımlı | Anlamı |
|---|---|---|
| Düşük yük (underutilization) | betimsel, standartlarda tanımlı değil | hatlar belirgin biçimde boşta; çoğu zaman bilinçli bir kapasite yedeği (overprovisioning) |
| Normal yük | ITU-T E.500 [36] | kullanıcı beklentilerinin karşılanması gereken sık yoğun dönemler; hizmet kalitesi hedef değerleri buna göre belirlenir |
| Yüksek yük | ITU-T E.500 [36] | seyrek zirve dönemleri: beklentiler karşılanmayabilir, ancak tıkanıklığın ağa yayılmasını önleyecek kadar yüksek performans korunmalıdır |
| Aşırı yük | ITU-T E.412 [37]; iletişim ağlarına ilişkin GOST standartlarında dikkate alınır [39] | trafik ağın kapasitesini aşar; yönetim önlemleri devreye girer: otomatik tıkanıklık denetimi, hat ayırma, yeniden yönlendirme |
| Tıkanıklık çöküşü (congestion collapse) | RFC 896, J. Nagle, 1984 [38] | her paket defalarca gönderilir, faydalı iş hacmi neredeyse sıfıra düşer; ilk kez Ekim 1986'da, NSFnet omurgası 32 kbit/s'den 40 bit/s'ye düştüğünde gözlemlendi |

"Tam yüklü ağ" için yerleşik bir terim yoktur; ağın tasarlandığı düzey E.500'deki "normal yük"e
karşılık gelir.

Bu rejimlerin hepsi bir ağın belirli bir andaki **durumlarıdır**: aynı ağ sabah düşük yüklü,
akşam normal yükte, bir arıza sırasında aşırı yüklüdür. Rejimler ekseni ile aşağıda tanıtılan
mimari sınıflar ekseni bağımsızdır: LL-0 sınıfı bir ağ da aşırı yüklenebilir, örneğin bir düğüm
zayıf bir hat üzerinde çalışıyorsa.

### 2.6 Düğüm başına yükün ölçeklenmesi

Dağıtık sistemler literatüründe bir düğümün maliyeti, katılımcı sayısı N'ye bağlı olarak asimptotik
biçimde değerlendirilir: tüm düğümlere yayın mesaj başına O(N); dağıtık özet tabloları (Chord [7],
Kademlia [8]) yönlendirme ve komşu tablosu için O(log N). Eşler arası sistemlerde düğüm başına
azami yükün düğüm sayısıyla artmadığı, çünkü yeni düğümlerin tükettiğinden fazla kaynak getirdiği
iddiası da vardır [9]; ancak bu, başkalarının isteklerinden oluşan bir yükün *istatistiksel
dengelenmesidir*.

### 2.7 Sonuç

2.1–2.5 sınıflandırmaları "ağ *şu anda* ne kadar yüklü" sorusunu yanıtlar; bunlara göre aynı ağ
bazen az, bazen çok yüklüdür. Rusça "az yüklü ağ" (малонагруженная сеть) ifadesi uygulamada tam
bu betimsel anlamda kullanılır (düşük kullanımlı bir ağ ya da makine) ve bir mimari sınıfı
belirten bir terim değildir. Kablolu telefonide "yükleme" sözcüğünün üçüncü bir anlamı bile vardır:
endüktans bobinli "yüklenmiş hat" (Pupin yüklemesi). Yalnızca 2.6 ekseni *mimarinin bir
özelliğiyle* ilgilidir ve buna göre ağların standart bir sınıflandırması yoktur.

## 3. Dağıtık ağlar: yaklaşımlara genel bakış

**Merkezi hizmetler** (WhatsApp, 2009; Telegram, 2013; Signal, 2014 [10]): içeriğin uçtan uca
şifrelenmesi güçlü olabilir, ancak sunucular, hesaplar ve meta veriler tek bir kuruluştadır;
sunucu yükü tüm kitleyle birlikte büyür.

**Federe ağlar**: e-posta, Matrix (2014) [11], ActivityPub/Mastodon (2016; W3C tavsiyesi 2018)
[12]. Sahiplik sunuculara dağıtılmıştır, ancak bir sunucunun yükü dış bağlantılarıyla artar:
Matrix'te büyük bir odanın geçmişi her katılımcı sunucuya çoğaltılır, ActivityPub'da dağıtım
takipçi sayısıyla artar.

**Eşler arası katmanlar ve dağıtık özet tabloları**: Freenet (2001) [13], Chord [7], Kademlia [8].
Düğümler eşittir, yük O(log N)'dir, ancak bir düğüm yabancı katılımcıların verilerini saklar ve
yönlendirir.

**Arkadaştan arkadaşa (F2F) ağlar.** Terim 2000 yılında D. Bricklin tarafından önerildi [14]: bir
düğüm yalnızca tanıdıklarının düğümleriyle bağlantı kurar. Örnekler: Turtle (Popescu, Crispo,
Tanenbaum, 2004) [15], OneSwarm [16], Freenet'in "karanlık ağ" kipi, RetroShare, GNUnet; güvenilir
düğümlerde depolama da buraya girer [17]. Bir düğümün bağlantı sayısı arkadaş sayısıyla
sınırlıdır [18, 19], ancak mesajlar arkadaş zincirleri boyunca ilgisiz düğümlerden geçer ve bu tür
ağlarda yönlendirme zor bir sorun olarak kalır [18, 19, 20]. **F2F ağlar önerilen kavramın en yakın
öncülüdür**: bir düğümü tanıdık çevresiyle ilk sınırlayanlar onlardır, ancak yüke göre değil,
bağlantı sayısına göre.

**Anonimleştirici katman ağları** (soğan yönlendirme): D. Chaum'un karıştırma ağları (1981) [40] ile D. Goldschlag, M. Reed ve P. Syverson'un soğan yönlendirmesinin (1996) [41] geliştirilmiş hâli; uygulamaları Tor (2002–2004) [21] ve Session'dır (2020) [22]. Gönüllülerin ya da operatörlerin işlettiği aktarma düğümleri, kendi bant genişlikleriyle orantılı olarak başkalarının transit trafiğini taşır.

**Gecikmeye dayanıklı ağlar (DTN)**: Fall'un mimarisi (2003) [23], RFC 4838 [24], Bundle Protocol
v7, RFC 9171 [25]: bağlantı kopmalarında "sakla ve ilet". Aynı ilkenin tarihsel bir uygulaması
FidoNet (1984) [26], modern bir uygulaması NNCP'dir (2016) [27].

**Her ortam için yığınlar ve radyo ağları**: Reticulum (protokol 2016'da yayımlandı) ve LXMF
mesajlaşma sistemi [28]: saniyede birkaç bitten (LoRa, paket radyo) internete kadar çalışma,
varsayılan olarak şifreleme; Meshtastic (2020) [29]: LoRa radyo modülleri üzerinden metin iletişimi.

**Topluluk ağları** (community networks): Freifunk, Guifi.net [30]: kullanıcıların kendilerinin oluşturup işlettiği ağlar.

**Yerel öncelikli yazılım** (local-first) [31] ve **Secure Scuttlebutt** (2014) [32]: veriler
kullanıcıda yaşar; SSB'de bir düğüm arkadaşlarının ve arkadaşlarının arkadaşlarının akışlarını
saklar, eşitleme düğümler karşılaştığında gerçekleşir.

**Aktarıcılar (relay)**: Nostr (2020) [33]: basit aktarıcı sunucular; popüler olanlar tüm kitle
tarafından yüklenir.

## 4. Az yüklü dağıtık ağ kavramı

### 4.1 Tanım

**Az yüklü dağıtık veri ağı**, her düğümün küçük, doğal olarak sınırlı bir katılımcı çevresine
hizmet ettiği ve çoğunlukla onların kendi trafiğini taşıdığı bir ağdır. Düğümler eşittir ve
sıradan donanımda çalışır. Ağ yalnızca gerekli olanı iletir, gecikmelere ve bağlantı kopmalarına
dayanır ve kapatılması ya da el konulması çalışmasını durduracak bir merkeze sahip değildir.

Kavram bir ağın belirli bir andaki yükünü değil, *yapısını* ilgilendirir (bölüm 2.5, 2.7).

### 4.2 Özellikler

1. **Kendi çevresi**: bir düğümün yükü tüm ağın büyüklüğüyle değil, hizmet ettiği insanlar ve yazılım ajanlarından oluşan kendi çevresiyle büyür. Ana özellik.
2. **Sıradan donanım**: ev bilgisayarı, mini sunucu ya da yönlendirici; veri merkezi gerekmez.
3. **İletim tasarrufu**: önce metin ve sinyaller, hacimli veriler istek üzerine.
4. **Gecikme toleransı**: bağlantı yoksa mesaj bekler ve daha sonra, yavaş bir kanal üzerinden de
   iletilir.
5. **Merkez yok**: tek bir arıza, engelleme ya da el koyma noktası yok.
6. **Düğüm körlüğü**: bir düğüm yalnızca şifreli metin taşır ve onu okuyamaz (Zero Knowledge
   Infrastructure ilkesi).

### 4.3 Öncüllerden farkı

| Kavram | Ne sınırlı | Farkı |
|---|---|---|
| F2F [14–20] | düğümün bağlantı sayısı, tanıdık çevresiyle | tanıdık zincirleri boyunca transit sürer; yük sınırlı değil |
| DHT [7, 8] | yük artışı, logaritmik | düğüm yabancıların verilerini taşır |
| DTN [23–25] | yükle ilgili bir şey yok | gecikmeler ve kopmalar hakkında, yük dağılımı hakkında değil |
| Local-first [31] | verinin saklandığı yer: kullanıcıda | veri sahipliği hakkında, ağ hakkında değil |
| **Az yüklü ağ** | **düğümün tüm yükü, kendi çevresiyle** | 1–6 özelliklerinin birleşimi; belirleyici olan 1. özellik |

## 5. Sınıflandırma: LL sınıfları

**Düğümün yük sınıfı**, yükün üç bileşeninden en hızlı büyüyenine göre belirlenir: taşınan trafik, saklanan veriler, sürdürülen hizmet durumu. N ağdaki katılımcı sayısı, k düğüm çevresinin büyüklüğüdür: kullanıcılarının ve yazılım ajanlarının sayısı. O(x) gösterimi ("x'in büyük O'su"; 1894'te P. Bachmann tarafından tanıtılmış [42], 1909'da E. Landau tarafından yaygınlaştırılmıştır [43]), bir büyüklüğün x'in bir sabitle çarpımından daha hızlı büyümediği anlamına gelir; LL-0 sınıfı için yük tahmininde N yoktur, yalnızca k vardır.

| Sınıf | Düğüm yükü | Tanım |
|---|---|---|
| **LL-0** | O(k) | düğüm yalnızca kendi çevresiyle ilgili olanı taşır, saklar ve hatırlar; başkaları için transit yok |
| **LL-1** | O(k) + sınırlı yabancı | ayrıca başkaları için N'den bağımsız olarak sınırlandırılmış transit ya da depolama (iletim sınırı, kotalar, komşuların düğümün kendisince seçilmesi) |
| **LL-2** | O(log N) | yük yavaş artar (dağıtık özet tabloları) |
| **LL-3** | O(N) ya da kendi çevresiyle sınırlı değil | yük tüm ağla birlikte artar ya da düğüme kaç yabancı kullanıcının eriştiğine bağlıdır (popüler bir sunucu, bir aktarıcı) |

Katı anlamda az yüklü ağ **LL-0** sınıfı bir ağdır; LL-1 neredeyse az yüklüdür.

## 6. Karşılaştırmalı analiz

### 6.1 Özellikler (1 = karşılanıyor, ½ = kısmen, 0 = karşılanmıyor) ve sınıflar

| Ağ | Yıl | Kendi çevresi | Donanım | Tasarruf | Gecikmeler | Merkez yok | Kör düğüm | Sınıf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Secure Scuttlebutt [32] | 2014 | 1 | 1 | ½ | 1 | 1 | 0 | LL-0 |
| Briar [35] | 2018 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| Nevod [34] | 2026 | 1 | 1 | ½ | ½ | 1 | 1 | LL-0 |
| FidoNet [26] | 1984 | 1 | 1 | 1 | 1 | 0 | 0 | LL-1 |
| NNCP [27] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Reticulum / LXMF [28] | 2016 | ½ | 1 | 1 | 1 | 1 | 1 | LL-1 |
| Meshtastic [29] | 2020 | 0 | 1 | 1 | ½ | 1 | ½ | LL-1 |
| Tor [21] | 2002 | 0 | ½ | 0 | 0 | 1 | 1 | LL-3 |
| WhatsApp | 2009 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Telegram | 2013 | 0 | 0 | 0 | 0 | 0 | 0 | LL-3 |
| Matrix [11] | 2014 | 0 | ½ | 0 | 0 | ½ | ½ | LL-3 |
| Signal [10] | 2014 | 0 | 0 | 0 | 0 | 0 | ½ | LL-3 |
| Mastodon [12] | 2016 | 0 | ½ | 0 | 0 | ½ | 0 | LL-3 |
| Nostr [33] | 2020 | 0 | ½ | 0 | 0 | 1 | ½ | LL-3 |
| Session [22] | 2020 | 0 | ½ | 0 | ½ | 1 | 1 | LL-3 |

Notlar. Signal ve WhatsApp 6. özellikte ½ alır: içerik uçtan uca şifrelidir, ancak kuruluş meta
verileri görür ve sunucuları yönetir. Reticulum ve NNCP'de ara düğümler başkalarının paketlerini
taşır ve saklar (1. özellik = ½, sınıf LL-1). Yıl, ilk herkese açık sürümdür (Reticulum: 2014'ten
beri geliştiriliyor; Signal: öncülleri TextSecure/RedPhone, 2010; Briar: 2011'den beri
geliştiriliyor).

### 6.2 Gözlemler

- Ana özelliğe (LL sınıfı) göre en katı olanlar Nevod, Briar ve Secure Scuttlebutt'tır (LL-0);
  Reticulum ve NNCP LL-1'e aittir.
- Tüm merkezi ve federe ağlar ile anonimleştirici katman ağları LL-3'tür: sahipliğin merkeziyetsizleşmesi,
  yükün merkeziyetsizleşmesi anlamına gelmez.

## 7. LL-0 sınıfına örnek olarak Nevod ve sınırlamaları

Nevod [34], Zero Knowledge Infrastructure ilkesine göre kurulmuş bir mesajlaşma ağıdır: bir düğüm
("node") yalnızca kendi katılımcılarına hizmet eder ve içeriğe erişimi olmadan şifreli mesajları
taşır; merkez yoktur; düğümler ev donanımında ya da kiralık sunucularda çalışır. Düğümlerin hizmet
tablosu kullanıcı sayısıyla değil, *düğüm* sayısıyla artar ve küçüktür.

Eylül 2026 itibarıyla sınırlamalar (özellikler tam karşılanmıyor, uygulamada kanıtlanmadı):

- 3. özellik: medya önizleme ve istek üzerine indirme olmadan bütün olarak iletilir;
- 4. özellik: teslim edilmeyen mesajlar 72 saat saklanır; yalnızca internet üzerinden çalışır;
- ileri gizlilik (forward secrecy) yok: mesajlar alıcının uzun ömürlü anahtarıyla şifrelenir;
- bir düğüm teslimat meta verilerini görür (kim, kime, ne zaman);
- gerçek kullanıcısı ve bağımsız denetimi olmayan çalışan bir prototip; kapalı kaynak; yalnızca
  iOS uygulaması.

Özellikler Nevod'un ilkelerinden türetildi, bu yüzden karşılaştırma baştan onun lehinedir;
Nevod'un puanı ürünün olgunluğunu değil, mimarisini yansıtır.

## 8. Açık sorular

1. Uzun süre çevrim dışı kalan bir alıcı için depolama: LL-0 sınıfını bozmadan kim ve ne kadar
   saklar.
2. Merkezi bir dizin olmadan çok sayıda düğüm arasında yol bulma.
3. Yavaş kanallar üzerinden teslimat için sınırlı transit (LL-1) kabul edilebilir mi ve karşılıklılık
   gerekli mi ("başkalarınınkini ilet, seninkini iletsinler")?
4. Hangi bileşenler yük sayılır: trafik, depolama, durum, enerji tüketimi, yönetici zamanı.
5. Düğüm çevresi k için biçimsel bir ölçüt ve gerçek ağlarda ölçümü.

## 9. Sonuç

İletişim kuramının yük kavramları bir ağın mimarisinin bir özelliğini değil, durumunu tanımlar.
Önerilen az yüklü dağıtık ağ kavramı, düğüm yükünün kendi çevresiyle sınırlandığı bir mimari sınıfı
ayırır ve bilinen yaklaşımları (F2F, DTN, dağıtık özet tabloları, local-first, topluluk ağları) altı
özelliğin birleşimiyle tamamlar. LL-0…LL-3 sınıflandırması kavramı ölçülebilir kılar ve her ağın
bir sınıfa atanmasını sağlar. Uygulamada doğrulama ve kapalı veri tabanlarında (IEEE, ACM, eLibrary)
tam bir literatür taraması sonraki adımlardır.

---

## Kaynaklar

{{REFS}}

---

*Yöntem notu.* İnceleme açık kaynaklar üzerinden yapılmıştır; ücretli veri tabanları (IEEE Xplore,
ACM Digital Library tam metinleri, Springer, eLibrary) sistematik olarak taranmamıştır. Özellik ve
sınıf değerlendirmeleri, ağların Eylül 2026 itibarıyla kamuya açık tanımlarına dayanan uzman
görüşleridir.
