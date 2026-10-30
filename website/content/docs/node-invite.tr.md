# İnsanları davet etmek

İnsanlar düğümünüze nasıl gelir — davetle, başvuruyla veya serbestçe — ve sonra birbirlerini, başka düğümlerdeki insanlar dahil, nasıl bulur. Hangi modun kullanılacağı panelde belirlenir: **Ayarlar → Hücre kabul modu** (bkz. [İlk ayarlar](../node-panel/), 2. adım).

## Yöneticiden davet

Ana yol — ve düğüm varsayılan modda (`delegated`) çalıştığı sürece tek yol.

1. Panel → **Davetler** → geçerlilik süresini seçin: 1 saat, 24 saat veya 7 gün → **+ Kod oluştur**.
2. Daveti kişiye şu yollardan biriyle verin:
   - ekranda **QR kodunu gösterin** — kişi onu telefonun normal kamerasıyla tarar;
   - **Bağlantıyı kopyala** — ve herhangi bir mesajlaşma uygulaması veya e-postayla gönderin;
   - `ABCD-EFGH` gibi **kısa kodu söyleyin** — yalnızca kişinin uygulamasında düğümünüz zaten ayarlıysa işe yarar.
3. Kişi Nevod'u App Store'dan kurar, bağlantıyı açar (davet sayfasında **Nevod'da aç** düğmesi vardır), bir ad yazar ve **Başlayın**'a dokunur.

Kodlar hakkında bilinmesi gerekenler:

- **Her kod bir kez kullanılır.** Her kişiye ayrı kod. Kullanılmış bir kod listede "kullanıldı" olarak işaretlenir, yanında onunla kimin girdiği yazar.
- **Geçerlilik süresi.** Bir grup sohbetine attığınız kod için bir hafta seçmeyin: kod kullanılana kadar eline geçen herkes onu kullanabilir. 1 saat, birine yüz yüze gösterdiğiniz kod içindir.
- **Bağlantı gereksiz hiçbir şey açığa çıkarmaz.** İçinde yalnızca düğüm adresi ve kod vardır. nevod.network'teki davet sayfası ne kodu ne de adresi görür: bunlar bağlantının `#` işaretinden sonraki, tarayıcının sunucuya göndermediği kısmında kalır.

Kişi Nevod'u zaten başka bir düğümde kullanıyorsa davet onu kendiliğinden taşımaz: uygulama önce kimliğini sıfırlaması gerektiği konusunda uyarır (**Profil → Kimliği sıfırla…**). Sıfırlama; kimliğini, kişilerini, telefondaki yazışmaları ve önceki düğümdeki kaydını kalıcı olarak siler. Sadece yazışmak için geçmesine gerek yoktur: kişi alışverişi yeterlidir (aşağıya bakın).

## Üyeler kendileri davet eder

`delegated` modunda davetleri güvendiğiniz kişilere bırakabilirsiniz: panel → **Davetler** → **Kabul edilen hücreler** → ilgili kişide **Davet edebilir**'i açın. O zaman onun uygulamasında **Profil → Birini davet et** bir kod oluşturur ve uygulama taranacak bir QR kodu gösterir.

`open` modunda her üye davet edebilir — ama bu modda zaten kod gerekmez.

## Onaylı başvurular

`admin` modu, düğümün bulunabilmesini ve insanların katılmak için başvurabilmesini, ama kararı sizin vermenizi istiyorsanız uygundur.

1. Kişi düğümünüzü "Ağı keşfet"te bulur ve **Bu düğüme katıl**'a dokunur (düğüm orada görünüyorsa, bkz. [İlk ayarlar](../node-panel/), 4. adım) — ya da uygulamanın ilk açılışında **Sunucuyu değiştir…**'e dokunur ve düğüm adresini `node.example.org/nevod-ws` girer.
2. Uygulama kendisi bir istek gönderir ve "Onay bekleniyor" gösterir.
3. İstek panelde **Katılım istekleri** sayfasında görünür. **Ayarlar → Yöneticiler** içine `cell_id`'niz yazılıysa ayrıca Nevod'da bir mesaj alırsınız.
4. **Onayla** — kişi bir bildirim alır ve hemen girer. **Reddet** — uygulama ona isteğin reddedildiğini gösterir.

Davet kodları `admin` modunda da çalışır — kodla kişi isteğe gerek kalmadan hemen girer.

## Serbest kayıt

`open` modunda düğümün adresini bilen herkes kaydolabilir. Açık bir topluluğa uygundur. Unutmayın:

- düğüm kayıtları asla kendiliğinden silmez ve adları serbest bırakmaz — fazlalıkları **Genel bakış** sayfasında (✕ düğmesi) elle temizlemeniz gerekir;
- hizmet adları (Nevod, administrator, support ve benzerleri) hiçbir modda alınamaz.

## Üyeler birbirini nasıl bulur

Aynı düğüme kaydolmak insanları birbirinin kişisi yapmaz. Yazışmak için kişi alışverişi yapmaları gerekir:

- **Profil → Kartımı paylaş** — bir QR kodu ve kart metni gösterir; diğer kişi: **Kişiler → Kişi ekle**, ardından QR kodunu tarar veya metni yapıştırır;
- kart her yoldan gönderilebilir — içinde gizli bir şey yoktur, yalnızca bir kimlik ve açık anahtarlar.

**Başka düğümlerdeki** insanlar da aynı şekilde eklenir — kart, ev düğümlerinin adresini içerir. Bu tür yazışmaların çalışması için düğümünüzün [Nevod ağına bağlı](../node-network/) olması gerekir.

> Bir kullanıcıyı silmek (panel → **Genel bakış** → ✕) kabulünü tamamen iptal eder: kayıt, teslim edilmemiş mesajlar ve bildirim belirteçleri silinir. Geri dönmek için kişinin yeni bir davete ihtiyacı olur.
