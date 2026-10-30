# Yönetim panelinde ilk ayarlar

Düğüm çalışıyor — şimdi ona bir ad vermeniz, kimi kabul edeceğinize karar vermeniz ve kendiniz kaydolmanız gerekiyor. Bunların hepsi `https://node.example.org/nevod-admin` adresindeki yönetim panelinde yapılır (nasıl açılacağı — [kurulumun](../node-install/) 9. adımında).

Panelin dili üst kısmından değiştirilir. Her sayfanın ve ayarın ayrıntılı açıklaması — [Yönetim paneli: tüm sayfalar ve ayarlar](../node-admin/) bölümünde.

## Panelde ne nerede

| Sayfa | Ne için |
|---|---|
| **Genel bakış** | Düğüme kayıtlı hücreler (kullanıcılar). |
| **Ayarlar** | Düğüm adı, kabul modu, görünürlük. |
| **Katılım istekleri** | Düğüm onay modunda çalışıyorsa kullanıcıların istekleri. |
| **Gelen kutusu** | Kullanıcıların düğüm yöneticisine mesajları — şikâyetler, sorular. Doğrudan buradan yanıt verebilirsiniz. |
| **Davetler** | Kullanıcılar için davet kodları. |
| **Düğümler** | Nevod ağına katılmak ve düğümünüzün bildiği diğer düğümler. |
| **Yayınlama**, **Yapay zekâ botları** | Düğümün kullanıcılarına gösterdiği botlar ve kanallar. |
| **Güvenlik** | Ek yönetici hesapları. |
| **Tanılama** | Düğümün öz denetimi ve günlüğü. |

## 1. Düğüme ad verin

**Ayarlar → Düğüm adı** → örneğin "Yılmaz ailesi" veya "5 Nolu Okul" gibi bir ad girin → **Kaydet**.

Adı kullanıcılar uygulamada görür. Ağdaki diğer düğümler yeni adı düğüm yeniden başlatıldıktan sonra öğrenir (aşağıya bakın). Düğümü bir proje düğümü gibi gösteren adlar kullanılamaz: Nevod, admin, support, official ve benzeri sözcükleri içeren adlar.

## 2. Kimi kabul edeceğinize karar verin

**Ayarlar → Hücre kabul modu.** Yeni bir düğüm varsayılan olarak **davetle** çalışır: yalnızca sizin verdiğiniz bir kodla kaydolunabilir. Genellikle tam da gereken budur.

| Paneldeki mod | Kim kaydolabilir | Davet kodlarını kim oluşturur |
|---|---|---|
| `delegated` — yalnızca davet koduyla (varsayılan) | Yalnızca davet koduyla. Kod olmadan düğüm kaydı kabul etmez. | Siz panelde, ayrıca **Davet edebilir** hakkı verdiğiniz kullanıcılar. |
| `admin` — istek + sizin onayınız | Kodla — hemen. Kod olmadan uygulama kendisi bir istek gönderir ve "Onay bekleniyor" gösterir; siz onu **Katılım istekleri** sayfasında onaylar veya reddedersiniz. | Yalnızca siz, panelde. |
| `open` — kodsuz | Düğümün adresini bilen herkes. Açık bir topluluğa uygundur; kayıtları ve alınmış adları daha sonra elle düzenlemeniz gerekeceğini unutmayın. | Kod gerekmez. |

Mod hemen geçerli olur.

## 3. Kendi düğümünüze kaydolun

1. Panelde: **Davetler** → geçerlilik süresini seçin (1 saat, 24 saat veya 7 gün) → **+ Kod oluştur**. Bir QR kodu ve `ABCD-EFGH` gibi kısa bir kod görünür.
2. Telefonunuza App Store'dan Nevod'u kurun.
3. QR kodunu telefonun normal kamerasıyla tarayın. Bu bir bağlantıdır: davet sayfası açılır — orada **Nevod'da aç**'a dokunun. Uygulama, düğümünüzün adresi ve kod önceden doldurulmuş olarak açılır.
4. Adınızı yazın ve **Başlayın**'a dokunun.

Taramak zahmetliyse panelde **Bağlantıyı kopyala**'ya tıklayın ve bağlantıyı kendinize gönderin. "Nevod'da aç" çalışmadıysa: uygulamada **Mesajlaşmaya başla**'ya dokunun, adınızı yazın, **Davet kodunuz var mı?**'ya dokunun ve bağlantıyı kod alanına yapıştırın. Bağlantı yerine kısa kod yalnızca uygulamada düğümünüz zaten ayarlıysa işe yarar.

> Bu telefondaki Nevod zaten başka bir düğüme (örneğin Nevod Open'a) kayıtlıysa davet sizi kendiliğinden düğümünüze taşımaz — uygulama önce kimliğinizi sıfırlamanız gerektiği konusunda uyarır: **Profil → Kimliği sıfırla…**. Sıfırlama; kimliğinizi, kişilerinizi, telefondaki yazışmaları ve önceki düğümdeki kaydınızı kalıcı olarak siler. Sıfırladıktan sonra davet bağlantısını yeniden açın.

Her kod bir kez kullanılır. Her kişi için ayrı bir kod oluşturun — daha fazlası [İnsanları davet etmek](../node-invite/) bölümünde.

## 4. Düğümün ağda görünüp görünmeyeceğine karar verin

**Ayarlar → "Ağı keşfet" listesinde görünürlük**:

- `closed` (varsayılan) — düğüm diğer düğümlerin kullanıcılarına "Ağı keşfet"te gösterilmez. Aile, kuruluş, her türlü kapalı grup için uygundur.
- `open` — düğüm "Ağı keşfet"te görünür ve diğer düğümlerin kullanıcıları onu bulabilir. Açık bir topluluk için uygundur.

Bu seçim kaydı açmaz: kimin kabul edileceğine yine hücre kabul modu karar verir (2. adım). "Ağı keşfet"teki doğrulanmış düğüm altın halkası şu anda yalnızca Nevod projesinin düğümlerinde bulunur.

Bu ayar, düğüm adının diğer düğümlere yansıması gibi, düğüm yeniden başlatıldıktan sonra geçerli olur. Sunucuda, `/opt/nevod/installer/docker` klasöründe:

```
docker compose restart nevod_node
```

## 5. Düğümü kontrol edin

**Tanılama → Kontrol et.** Birkaç saniye içinde düğüm her şeyin yolunda olup olmadığını gösterir: kodunun güncel olup olmadığı, ayarlarının veritabanıyla uyuşup uyuşmadığı, yapılandırma sorunu olup olmadığı, düğüme dışarıdan erişilip erişilemediği.

Dışarıdan erişilebilirliği düğüm, ağın diğer düğümleri üzerinden kontrol eder. Düğümünüz kimseye bağlı değilken bu satır "Kontrol için bilinen eş yok" gösterir — bu beklenen bir durumdur. Ağa katılmak bir sonraki adımdır ve önemlidir: o olmadan uygulama kapalıyken telefonlara bildirim gelmez. Bkz. [Nevod ağına katılmak](../node-network/).

## 6. İsteğe bağlı: başka yöneticiler

**Güvenlik → Ekle / parolayı değiştir** — her yöneticinin kendi kullanıcı adı ve parolası olur ve bunları `.env`'deki ana parolayı değiştirmeden iptal edebilirsiniz. Ana parola, diğerleri kaybolursa diye yedek giriş olarak kalır.
