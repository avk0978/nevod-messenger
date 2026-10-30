# Yönetim paneli: tüm sayfalar ve ayarlar

Düğümün yönetim paneli için bir başvuru kaynağı: her sayfada ne olduğu ve her ayarın ne yaptığı. Düğümü yeni kurduysanız [Yönetim panelinde ilk ayarlar](../node-panel/) bölümüyle başlayın — orada en gerekli olanlar adım adım anlatılıyor.

Panel `https://alanadiniz/nevod-admin` adresinde açılır (ya da kapattıysanız bir SSH tüneli üzerinden — bkz. [kurulum](../node-install/), 10. adım). Kullanıcı adı herhangi bir şey olabilir; parola `.env`'deki `NEVOD_ADMIN_PASSWORD` ya da "Güvenlik" sayfasında oluşturulmuş kişisel bir paroladır. Dil üst kısımdan değiştirilir.

## Üst kısım

Her sayfanın üstünde — düğümün adı, kimliği (`node_id`) ve mevcut durumu gösteren etiketler: düğümün "Ağı keşfet"te görünür olup olmadığı, hücre kabul modu, yayınlanan hücreleri kimin gördüğü.

## Genel bakış

Düğüme kayıtlı tüm hücrelerin (kullanıcılar ve botlar) listesi.

| Sütun | Ne gösterir |
|---|---|
| Ad | Bu hücre için kendi notunuz — yalnızca siz, panelde görürsünüz. Yazın ve ✓ ya da Enter'a basın. Kullanıcının kendi seçtiği adı değiştirmez. |
| `cell_id` | Hücrenin kimliği. Tamamı ipucu balonunda. |
| Durum | Çevrimiçi veya çevrimdışı — uygulamanın şu anda bağlı olup olmadığı. |
| Arabellek | Kullanıcının çevrimiçi olmasını bekleyen mesaj sayısı (72 saate kadar saklanır). |
| Kayıt | Hücrenin ne zaman kaydolduğu. |

Düğmeler:

- Satırdaki **✕** — hücreyi silmek. Bu, kabulünü tamamen iptal eder: kayıt, teslim edilmemiş mesajlar ve bildirim belirteçleri silinir, ad serbest kalır. Geri dönmek için kişinin yeni bir davet koduna veya yeni bir isteğe ihtiyacı olur. Düğüm hücreleri asla kendiliğinden silmez — yalnızca siz silersiniz.
- **Kayıtları sıfırla** — tüm hücreler bir sonraki bağlantıda yeniden kaydolur; kodu yeniden girmek gerekmez.
- **Tam sıfırlama** — geri alınamaz: tüm üyelerin bir davet koduyla yeniden giriş yapması gerekir. Uygulamada yalnızca taşınırken veya düğümün üyeleri tamamen değişirken gerekir.

## Ayarlar

| Ayar | Ne yapar | Ne zaman geçerli olur |
|---|---|---|
| **Düğüm adı** | Kullanıcıların gördüğü düğüm adı. Hizmet sözcükleri (Nevod, admin, support, official ve benzerleri) kullanılamaz. | Panelde — hemen; diğer düğümler için — yeniden başlatmadan sonra. |
| **Düğüm türü** *(geliştirme aşamasında)* | `permanent` — olağan düğüm. `temporary` — örneğin bir etkinlik süresince kullanılan geçici düğüm; uygulama bu tür düğümleri henüz kullanmıyor. `permanent` bırakın. | Yeniden başlatmadan sonra. |
| **Üst düğüm kimliği** *(geliştirme aşamasında)* | Yalnızca geçici bir düğüm için gerekir: hangi kalıcı düğüme ait olduğu. Boş bırakın. | Hemen. |
| **"Ağı keşfet" listesinde görünürlük** | `closed` — düğüm diğer düğümlerin kullanıcılarına gösterilmez. `open` — düğüm onların "Ağı keşfet" listesinde görünür. Bu, kaydı açmaz. | Yeniden başlatmadan sonra. |
| **Yayınlanan hücrelerin görünürlüğü** | "Yayınlama" sayfasındaki bot ve sayfa listesini kimin gördüğü: `off` — kimse, `members` — yalnızca bu düğümün kullanıcıları, `public` — herkes. | Hemen. |
| **Hücre kabul modu** | `delegated` — yalnızca davet koduyla; `admin` — kodla veya sizin onayınızla başvuruyla; `open` — adresi bilen herkes. | Hemen. |
| **Yöneticiler** | Kendi hücrelerinizin kimlikleri (`cell_id`), virgülle ayrılmış. `admin` modunda her yeni istek hakkında Nevod'da mesaj alırlar. Kendi `cell_id`'nizi "Genel bakış" sayfasında bulabilirsiniz. | Hemen. |

Düğümü yeniden başlatmak — sunucuda, `/opt/nevod/installer/docker` klasöründe:

```
docker compose restart nevod_node
```

## Katılım istekleri

`admin` kabul modunda çalışır. Kodu olmayan biri kaydolmaya çalıştığında uygulama kendisi bir istek gönderir — burada ad ve notla birlikte görünür. **Onayla** — kişi hemen erişim ve telefonunda bir bildirim alır. **Reddet** — uygulama ona isteğin reddedildiğini gösterir.

## Gelen kutusu

Düğümün kullanıcılarının uygulamadan düğümün **administrator** hesabına gönderdiği mesajlar: mesajlarla ilgili şikâyetler, sorular. Her düğümün bir administrator hesabı vardır; ilk başlatmada kendiliğinden oluşturulur.

Bir yazışmayı açın, bir yanıt yazın ve **Yanıtla**'ya tıklayın — yanıt, administrator adına, şifreli olarak kullanıcıya Nevod'da gider. Kullanıcıların mesajları yalnızca bu şekilde, uygulamada yanıtlanır, e-postayla değil.

Kullanıcı mesajına uygulama günlüğünü eklediyse (bir sorunu incelemek için), yazışmada **nevod.log dosyasını indir** bağlantısı görünür.

Kullanıcılar düğümünüzün administrator hesabını **Düğüm yöneticisi** işareti ve düğümün adıyla görür. İşareti düğümünüzün anahtarı doğrular, bu yüzden başka kimse kendini düğümünüzün yöneticisi gibi gösteremez. Mavi ✓ rozeti Nevod projesi yönetiminin işaretidir: proje küratörünün imzasıyla doğrulanır ve yalnızca proje düğümlerinde bulunur.

## Davetler

**Kod oluşturmak:** süreyi seçin (1 saat, 24 saat, 7 gün) → **+ Kod oluştur**. Bir QR kodu ve bir bağlantı görünür — ekranda gösterebilir, iletebilir veya **Bağlantıyı kopyala**'ya tıklayabilirsiniz. Bağlantı Nevod'u düğüm adresi ve kod önceden doldurulmuş olarak açar. `ABCD-EFGH` gibi kısa kod yalnızca kişinin uygulamasında düğümünüz zaten ayarlıysa işe yarar.

Her kod bir kez kullanılır. Aşağıda tüm kodlar süreleri ve durumlarıyla listelenir: etkin, kullanıldı, kim tarafından.

**Kabul edilen hücreler** — kimin, kimin davetiyle girdiği. **Davet edebilir** anahtarı bu kişinin uygulamadan kod oluşturmasına izin verir (Profil → Birini davet et) — `delegated` modunda davetleri güvendiğiniz kişilere böyle bırakırsınız.

Daha fazlası [İnsanları davet etmek](../node-invite/) bölümünde.

## Düğümler

**Nevod ağına katılmak.** Durum ("bağlı · çevrimiçi düğümler" veya "bağlı değil") ve **Nevod ağına bağlan** düğmesi. Bağlı bir düğüm, proje düğümlerinden telefonlar için push bildirimleri ve bir arama aktarıcısı alır. **Başka bir düğümün yöneticisinden alınan belirteç** alanı, Nevod Open yerine başka bir düğüm üzerinden katılmak içindir. Daha fazlası [Nevod ağına katılmak](../node-network/) bölümünde.

**Bilinen düğümler** — düğümünüzün bildiği tüm ağ düğümleri: ad, adres, çevrimiçi olup olmadığı, en son ne zaman iletişimde olduğu. 72 saat iletişim kurmayan bir düğüm listeden çıkarılır ve ağda yeniden göründüğünde kendiliğinden geri döner.

**Düğüm davetleri** — başka bir düğümün sizinki üzerinden ağa katılabileceği bir belirteç. 10 dakika geçerlidir; diğer düğümün yöneticisine herkese açık değil, yüz yüze verin.

## Yayınlama

Düğümünüzün uygulamada kullanıcılara gösterdiği botlar ve sayfalar — "Ağı keşfet"teki düğüm "gezegeninde". Bir hücre seçin, bir başlık, tür (`bot` — bot, `page` — metin içeren sayfa) ve açıklama belirleyin → **Yayınla**. Yayından kaldırmak onu listeden çıkarır; hücrenin kendisi kalır.

Claude, ChatGPT, Gemini onay kutuları, kullanıcının anahtarıyla çalışan harici bir yapay zekâ botu içindir: hangi sağlayıcıları kabul ettiği. Olağan bir bot için hiçbirini işaretlemeyin.

Bu listeyi kimin göreceği "Ayarlar" → "Yayınlanan hücrelerin görünürlüğü" içinde belirlenir.

## Yapay zekâ botları

Doğrudan düğümün içinde çalışan ve Claude, ChatGPT veya Gemini aracılığıyla **kullanıcının anahtarıyla** yanıt veren yapay zekâ botları: kişi anahtarını botla sohbette ekler, anahtar her mesajla gelir ve bot tarafından saklanmaz. Düğümün kendi anahtarları yoktur ve yapay zekâ için ödeme yapmaz.

**Bot ekle** — bir ad, açıklama, model için bir talimat ve sağlayıcıları belirleyin ya da hazır bir şablon alın (AI Assistant, çevirmen Tolmach) ve düzenleyin. Etkin bir bot, düğümün kullanıcılarına "Bu düğümde" listesinde görünür. Devre dışı bırakılan bot durdurulur ve gizlenir, adını korur. Silme kalıcıdır: botun anahtarları ve adı silinir, yazışmalar kullanıcılarda kalır.

> Bir yapay zekâ botuyla yazışmaları düğümünüzdeki kod çözer ve seçilen sağlayıcıya iletir. Kullanıcılar bu konuda [Gizlilik Politikası](../../privacy/) (5. bölüm) ile uyarılır. Yapay zekâ botlarını açarsanız, düğüm sahibi olarak bu aktarıma siz de katılırsınız.

## Güvenlik

Kişisel yönetici hesapları: **Ekle / parolayı değiştir** — bir kullanıcı adı ve parola (özet olarak saklanır). Her yöneticiye bir hesap; biri ayrılırsa ana parolayı değiştirmeden onun hesabını silin. `.env`'deki ana parola her zaman yedek giriş olarak çalışır.

Aynı adresten art arda beş yanlış parola, o adres için girişi 15 dakika kilitler.

## Tanılama

**Kontrol et** — düğümün öz denetimi (10 saniyeye kadar):

| Kontrol | Anlamı |
|---|---|
| Kodun güncelliği | Kurulu düğüm yapısının protokolün gerisinde kalıp kalmadığı — kaldıysa düğümü güncelleyin (bkz. [Bakım](../node-maintenance/)). |
| identity/DB tutarlılığı | `node.json`'daki ayarların veritabanıyla uyuşup uyuşmadığı. |
| Bağımlılıklar ve yapılandırma | Ayarlarda hata olup olmadığı (örneğin `TURN_SECRET` olmadan bir arama aktarıcısı). |
| Dış erişilebilirlik | Ağın başka bir düğümünün sizinkine dışarıdan ulaşıp ulaşamadığı. Düğüm ağa bağlı değilken "Kontrol için bilinen eş yok" gösterir — bu beklenen bir durumdur. |

**Günlükler** — düğüm günlüğünün son kayıtları. Mesaj metinleri günlüğe asla girmez.
