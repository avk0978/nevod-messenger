# Düğüm nasıl çalışır

Düğüm, telefonların mesaj alışverişi yaptığı ve arama kurduğu, bir sunucuda çalışan bir programdır. Burada kısaca bir düğümün ne yaptığı, neyi sakladığı ve neyi göremediği anlatılıyor — kurulumdan önce neyi üstlendiğinizi bilmeniz için.

## Düğüm, hücre ve ev düğümü

Her Nevod kullanıcısı bir **hücredir**: telefonda oluşturulan ve telefondan asla çıkmayan bir çift şifreleme anahtarı. Hücre tek bir düğüme kaydolur — bu onun **ev düğümüdür**. Telefon kapalıyken gönderilen mesajları telefon bu düğüm üzerinden alır.

Düğümler ortak bir ağda birbirine bağlıdır. Başka bir düğümdeki birine yazdığınızda, düğümünüz şifreli mesajı onun düğümüne iletir. Merkezi bir sunucu yoktur: ağ, düğümlerin kendisidir.

Bir düğümün yükü tüm ağın büyüklüğüne değil, yalnızca kendi çevresine — kendi kullanıcılarına ve botlarına — bağlıdır: düğüm başka düğümlerin mesajlarını ne iletir ne de saklar. Bu yüzden bir düğüme sıradan bir bilgisayar yeter ve başka düğümlerde Nevod'a ne kadar çok insan gelirse gelsin yükü artmaz. Bu tür ağlara **düşük yüklü** ağlar denir (LL-0 sınıfı) — ayrıntılar ["Low-Load Distributed Data Networks"](../../publications/low-load-networks/) makalesinde (DOI 10.5281/zenodo.23621073).

## Düğüm türleri

Tüm düğümler aynı programı çalıştırır. Bir düğümün ne olacağına — kapalı bir aile düğümü, açık bir topluluk düğümü ya da bir kuruluşun düğümü — [yönetim panelindeki](../node-admin/) üç ayar karar verir:

- **kimi kabul edeceği** — hücre kabul modu: yalnızca davet koduyla, kodla ya da sizin onayınızla başvuruyla, veya herkes (ayrıntılar [İlk ayarlar](../node-panel/) bölümündeki tabloda, 2. adım);
- **düğümün diğer düğümlerin kullanıcılarına "Ağı keşfet"te görünüp görünmediği**;
- **düğümün kullanıcılarına ne gösterdiği** — üzerinde yayınlanan botlar ve sayfalar.

| Hangi düğüm | Kimi kabul etmeli | "Ağı keşfet"te görünür | Örnek |
|---|---|---|---|
| Kapalı: aile, arkadaşlar, kuruluş | davet koduyla | hayır | yöneticinin her çalışanı davet ettiği bir şirket düğümü |
| Seçimli topluluk | kodla veya onaylı başvuruyla | evet | bir kulüp düğümü: herkes bulabilir ama üyeleri yönetici onaylar |
| Açık topluluk | herkes | evet | Nevod Open gibi herkese açık bir düğüm |

**Düğümün nerede çalıştığı** — alan adlı kiralık bir sunucuda ya da evde kendi bilgisayarınızda — yeteneklerini değiştirmez. Ev düğümünün internetten erişilebilir olması gerekir: yönlendiricide port yönlendirme ve bir alan adı. Bu yüzden kiralık bir sunucuyla başlamak daha kolaydır — tüm belgeler onun için yazılmıştır.

**Ev düğümü için önemli: ev ağınızdan ona başka kurallarla bağlanılır.** Telefonlar düğüme alan adıyla bağlanır ve alan adı yönlendiricinizin dış adresini gösterir. Ev Wi-Fi'sindeki bir telefon bu dış adrese ağın içinden ulaşır ve birçok yönlendirici bu tür bağlantıları geçirmez. O zaman düğüm mobil veriyle çalışır, ama ev Wi-Fi'sinde uygulama "Bağlantı yok" der. Sunucunun yerel adresiyle (örneğin `192.168.1.10`) bağlanmak da işe yaramaz: sertifika adrese değil alan adına verilmiştir. Bu, yönlendiricide iki yoldan biriyle çözülür:

- yönlendirici destekliyorsa **NAT loopback**'i açın (NAT hairpinning veya NAT reflection da denir);
- ya da yönlendiricinin DNS'ine yerel bir kayıt ekleyin: alan adınız → sunucunun yerel adresi.

Bunu kurulumdan hemen sonra kontrol edin: düğüme bir telefondan hem ev Wi-Fi'siyle hem mobil veriyle bağlanın.

**Nevod projesinin düğümleri** — Nevod Open, Dev Planet ve birkaç diğeri — ötekilerden programlarıyla değil, üç şeyle ayrılır:

- push bildirimleri için bir Apple anahtarları ve bir arama aktarıcıları vardır ve bunları ağın düğümleriyle paylaşırlar (aşağıya bakın);
- "Ağı keşfet"te doğrulanmış bir düğümün **altın halkası** ve bir amaç etiketiyle işaretlidirler — "Topluluk", "Bilgilendirme", "Yapay zekâ ajanı". Halka proje küratörünün imzasıyla doğrulanır ve şu anda yalnızca proje düğümlerinde bulunur;
- **Nevod Open**, uygulamanın kullanıcıları varsayılan olarak kaydettiği düğüm ve yeni düğümler için ağa giriş noktasıdır: ona davetsiz bağlanılabilir.

> Panel ayarlarında ayrıca "Düğüm türü" — `permanent` veya `temporary` — ve "Üst düğüm kimliği" vardır. Bunlar **geliştirme aşamasında**: geçici düğümler (örneğin bir etkinlik süresince). Uygulama bunları henüz kullanmıyor — `permanent` bırakın ve üst düğüm kimliğini boş bırakın.

## Düğüm neyi saklar

- **Hücre kayıtları**: kimlik, açık anahtarlar ve kullanıcının seçtiği görünen ad.
- **Teslim edilmemiş mesajlar** — şifreli olarak, alıcı çevrimiçi olana kadar, ama en fazla 72 saat. Teslimden sonra mesaj silinir.
- Telefonların **bildirim belirteçleri** — bir mesaj veya arama geldiğinde telefonu "uyandırmak" için.
- **Davet kodları**, katılım istekleri, kullanıcıların düğüm yöneticisine mesajları.
- **Ağdaki diğer düğümlerin listesi** ve kendi ayarları.
- **Teknik günlükler** — boyutu sınırlıdır (konteyner başına 10'ar MB'lık 3 dosya); eski kayıtların üzerine yazılır.

## Düğüm neyi göremez

- **Mesajların, fotoğrafların, videoların, sesli mesajların ve dosyaların içeriği.** Bunlar gönderenin telefonunda alıcının anahtarıyla şifrelenir. Düğüm onları açabilecek anahtara sahip olmadan iletir.
- **Aramaların içeriği.** Ses ve görüntü telefonlar arasında doğrudan ya da bir aktarıcı (TURN) üzerinden şifreli gider.
- **Telefondaki kişiler ve yazışmalar.** Yalnızca cihazda saklanırlar.

Düğümün gördükleri ise şunlardır: üzerinde hangi hücrelerin hangi adlarla kayıtlı olduğu, kimin kime ne zaman yazdığı, mesajların boyutu, bağlantıların IP adresleri. Bunlar teslim verileridir — onlar olmadan düğüm çalışamazdı. Daha fazlası [Gizlilik Politikası](../../privacy/)'nda.

> Düğüm sahibi, düğümün çalışmasından ve verilerinin yedeğinden sorumludur. Kullanıcıların yazışmalarını okuyamaz — bu bir sözden değil, ağın yapısından kaynaklanır.

## Proje düğümleri üzerinden bildirimler ve aramalar

App Store'daki Nevod uygulamasına push bildirimi yalnızca Apple anahtarı olan bir düğüm gönderebilir ve bu anahtar yalnızca proje düğümlerinde vardır. Bu yüzden ağa bağlı bir düğüm, bildirimi kendi yerine göndermesini bir proje düğümünden ister. Proje düğümü bu sırada telefonun belirtecini ve bildirim başlığı için gönderenin adını görür; metin ise her zaman aynıdır — "Yeni mesaj". Gönderen alıcının kişileri arasındaysa, telefon kayıtlı olduğu adı kendisi koyar.

**Bildirimleri doğrudan kendi düğümümden gönderebilir miyim?** Hayır. App Store'daki bir uygulamaya bildirimler yalnızca uygulamanın yayınlandığı Apple geliştirici hesabının anahtarıyla kabul edilir — Nevod'u ise proje yayınlar. Bu anahtar düğüm sahiplerine verilemez: tek bir düğümle sınırlandırılamaz ve herhangi bir Nevod kullanıcısına herhangi bir metinle bildirim gönderme olanağı verir. Bu yüzden bildirimler proje düğümleri üzerinden gider ve metinleri her zaman "Yeni mesaj"dır.

Aynı şekilde, kendi arama aktarıcısı (TURN) olmayan bir düğüm de ağın düğümlerinden bir aktarıcı alır — daha fazlası [Kendi düğümünüz üzerinden aramalar](../node-turn/) bölümünde.

Buradan önemli bir sonuç çıkar: **ağa bağlı olmayan bir düğüm mesajları teslim eder, ama uygulama kapalıyken telefonlara bildirim gelmez.** Nasıl bağlanacağınız — [Nevod ağına katılmak](../node-network/) bölümünde.

## Kurulum nelerden oluşur

Hazır sunucu paketi ([kaynak kodundaki](https://github.com/avk0978/nevod-messenger) `installer/docker` klasörü) iki Docker konteynerinden oluşur:

| Konteyner | Ne yapar | Portlar |
|---|---|---|
| `nevod_node` | düğümün kendisi | 8765 — diğer düğümler için; 8766 — yönetim paneli, yalnızca sunucunun kendisinden erişilebilir |
| `nevod_caddy` | Caddy web sunucusu: alan adınız için HTTPS sertifikasını kendisi alır ve telefon ile panel bağlantılarını düğüme iletir | 80 ve 443 |

Düğümün tüm verileri ayar dosyasının yanındaki `data/` klasöründedir:

- `node.json` — **düğümün kimliği**: anahtarları. Bu dosyayı kaybederseniz düğümü kaybedersiniz: aynı kimlikle bir düğüm yeniden oluşturulamaz ve tüm kullanıcıların yeni bir düğüme kaydolması gerekir. Yedeğini alın.
- `node.db` — veritabanı: kayıtlar, davetler, mesaj arabelleği.

## Neye ihtiyacınız var

- **Bir Linux sunucusu** — en ucuz kiralık VPS yeter: 1 işlemci, 1 GB bellek, 10 GB disk. Onlarca ve yüzlerce kullanıcı için bu yeterlidir.
- Sunucuya yönlendirebileceğiniz **bir alan adı** (veya alt alan adı) — örneğin `node.example.org`. Alan adı olmadan telefonlar HTTPS sertifikasını doğrulayamaz.
- **Yaklaşık yarım saat** ve sunucuya SSH ile bağlanabilme becerisi. Tüm komutlar [Adım adım kurulum](../node-install/) bölümünde — olduğu gibi kopyalayabilirsiniz.
