# Güvenlik ve yedekler

Nevod'un kendiliğinden neyi koruduğu, sizi dolandırıcılara ve saldırılara karşı nasıl koruduğu, sizin ne yapmanız gerektiği, yabancılardan nasıl korunacağınız, bir sohbeti parolayla nasıl kilitleyeceğiniz, nasıl engelleyip şikâyet edeceğiniz — ve Nevod'da neden yazışma yedeği olmadığı.

## Sizin müdahaleniz olmadan korunanlar

- **Yazışmalar ve aramalar** telefonunuzda, karşınızdakinin anahtarıyla **şifrelenir**. Düğümler, Nevod geliştiricileri ve Apple onları göremez.
- **Anahtarlar, kişiler ve mesaj geçmişi yalnızca telefonunuzda saklanır.** iCloud ve bilgisayar yedeklerinde, düğümlerde ya da geliştiricide bulunmazlar.
- **Düğüm yalnızca mesajı teslim etmek için gerekeni bilir:** kimin kayıtlı olduğunu, kime ve ne zaman yazdığınızı — ama ne yazdığınızı değil.

Bunun nasıl işlediği ayrıntılı olarak [Güvenlik](../../security/) sayfasında.

## Dolandırıcılara ve saldırılara karşı koruma

- **Kimse sizi telefon numaranızla bulamaz.** Nevod'da telefon numarası ve e-posta yoktur; bu yüzden sızdırılmış bir veritabanından alınıp toplu mesaj veya dolandırıcı aramaları için kullanılamazlar. Size yalnızca kartınız olan biri ya da düğümünüzün bir üyesi yazabilir.
- **Hesap parolası yok — çalınacak bir şey yok.** Gözetlenemez, tahmin edilemez, sizden koparılamaz. Bağlanırken telefon düğüme anahtara sahip olduğunu kanıtlar, ama anahtarın kendisi telefondan asla çıkmaz.
- **Kimse kendini yönetim gibi gösteremez.** Hizmet adları — administrator, support, Nevod ve benzerleri — kaydedilemez. Gerçek yönetimde mavi ✓ rozeti, özel bir düğümün yöneticisinde **Düğüm yöneticisi** işareti vardır. Rozeti ve işareti olmayan hizmet adlı bir hesabı uygulama turuncu ⚠ ve sohbette bir uyarıyla işaretler.
- **Sahte bildirimler geçmez.** Yeni mesaj bildiriminde bir yabancının belirleyebileceği bir metin yoktur: yalnızca "Yeni mesaj" ve gönderenin adı vardır ve içindeki hizmet adları "Nevod" ile değiştirilir. Sizden kod girmenizi veya bir bağlantıyı açmanızı isteyen "Nevod'dan" bir bildirim dolandırıcılıktır.
- **Düğümünüzün yerine geçilemez.** Düğümden gelen her şey onun anahtarıyla imzalıdır ve uygulama imzayı kontrol eder. Başkasının Wi-Fi ağında bile aradaki kimse düğümünüz gibi davranamaz veya onun adına sahte mesaj sokuşturamaz.
- **Tehlikeli dosyalar ve resimler ayıklanır.** Telefonlara yönelik en tehlikeli saldırılar — Pegasus casus yazılımı gibi — özel hazırlanmış bir resim veya dosya olarak gelir ve tek bir dokunuş olmadan çalışır. Bu yüzden Nevod başkalarından aldığı her şeyi kontrol eder: dosya boyutu sınırlıdır ve türü içerikle eşleşmelidir — aksi hâlde dosya resim veya video olarak gösterilmez ve kendiliğinden açılmaz. Avatarlar yalnızca kişilerinizden ve düğümünüzün üyelerinden kabul edilir ve uygulama gönderilen resmi asla göstermez, kendisi yeniden çizer.
- **Telefon kilitliyken dosyalar kapalıdır.** Sohbetlerdeki fotoğraflar, videolar ve dosyalar iOS tarafından şifrelenir ve telefon kilitlendikten birkaç saniye sonra erişilemez hâle gelir — telefonun belleğine erişim elde eden biri için bile. Uygulama değiştiricide yazışmanız yerine bir Nevod kapağı görünür.
- **Bir düğümün ele geçirilmesi yazışmalarınızı açığa çıkarmaz.** Düğümde ne mesaj metni ne de anahtarlarınız vardır: düğüme erişse bile saldırgan yazışmalarınızı okuyamaz.
- **Doğrulanmış düğümler işaretlidir.** **Ağı keşfet**'teki Nevod projesi düğümlerinde altın bir halka vardır — projenin imzasıyla doğrulanır ve sahte bir düğüm onu alamaz.

## Sizin yapmanız gerekenler

En savunmasız nokta telefonun kendisidir: telefonunuzun kilidini açan, yazışmalarınızı da görür. Ve iOS'un kendisini kırmış bir casus yazılım telefona zaten girmişse, ekranda gördüğünüz her şeyi görür — Nevod dahil hiçbir uygulama sizi bundan koruyamaz. Bu yüzden oraya girmemesi önemlidir.

- **iPhone'da bir parola** — şart, ve 000000 gibi basit olmasın.
- **iOS'u güncel tutun** — güncellemeler casus yazılımların kullandığı açıkları kapatır.
- **Telefonunuzu ara sıra yeniden başlatın.** Birçok casus yazılım yeniden başlatmadan sağ çıkmaz.
- **Gazeteci, insan hakları savunucusu iseniz ya da başka bir nedenle hedef olabilirseniz** — iPhone **Kilitlenme Modu**'nu açın: **Ayarlar → Gizlilik ve Güvenlik → Kilitlenme Modu**. Pegasus gibi saldırıların kullandığı birçok yolu kapatır.
- **Önemli sohbetlere parola** — aşağıya bakın.
- **Kimseye kod veya anahtar vermeyin.** Nevod yönetimi yalnızca uygulamada, ✓ rozetli **administrator** hesabından (özel bir düğümde — **Düğüm yöneticisi** işaretiyle) yazar; asla e-postayla yazmaz ve asla parola, anahtar veya kod istemez. İsteyen dolandırıcıdır.

## Sohbet parolası

Tek bir sohbeti parolayla kilitleyebilirsiniz — o zaman kilidi açık telefonunuzu elinde tutan biri bile o sohbeti açamaz.

1. Sohbeti açın → sağ üstteki dişli simgesi → **Parola koruması**'nı açın.
2. İki parola belirleyin:
   - **Kilit açma parolası** — sohbeti bununla açarsınız;
   - **Baskı altı parolası** — sohbeti açmaya zorlandığınız durumlar için. Gerçeğinin yerine bunu girerseniz bu sohbetteki yazışma telefonunuzdan **sessizce silinir** ve ekranda olağan "Yanlış parola" görünür — dışarıdan bakan için bir yazım hatası gibidir.
3. Parolalar farklı olmalıdır. Değiştirmek için aynı yerde **Parolaları değiştir**.

> Sohbet parolası yalnızca bu telefonda saklanır, üstelik parolanın kendisi değil, özeti (hash). **Unutulan parola kurtarılamaz** — ne sizin ne de geliştiricilerin elinden gelir. Parolayı unuttuysanız giriş ekranında **Parolayı mı unuttunuz?** düğmesine dokunun: bu sohbetteki yazışma telefondan silinir, parola kilidi kaldırılır ve sohbet yeniden — boş olarak — açılır. Unutmayacağınız bir parola seçin. Baskı altı parolası yazışmayı yalnızca sizde siler: karşınızdakinde kalır.

## Yabancılara karşı koruma

Size yalnızca kartınızı verdiğiniz kişiler yazamaz ve sizi arayamaz. Nevod Open gibi açık bir düğümde herkes kaydolabilir ve düğümün üyeleri birbirini **Kişiler → Bu düğümde** içinde görür. Ayrıca yazıştığınız biri kartınızı başkasına iletebilir. Burada yabancı, kişileriniz arasında olmayan kişidir. Resmî Nevod hesapları ve düğümünüzün yöneticisi yabancı sayılmaz.

**Profil → Güvenlik** içinde iki ayar vardır. Açıp açmamaya siz karar verirsiniz; başlangıçta ikisi de kapalıdır:

- **Yalnızca kişilerden aramalar** — kişileriniz arasında olmayan birinden gelen arama sessizce reddedilir, telefon çalmaz. Arayan için arama hemen sona erer; sizin arama geçmişinizde **Reddedildi: kişilerde yok** olarak görünür.
- **Yabancılardan resimler — dokununca** — kişileriniz arasında olmayan birinden gelen fotoğraf ve videolar hemen gösterilmez: sohbette **Fotoğraf — göster** veya **Video — göster** yer tutucusu görünür ve uygulama dosyayı ancak siz dokunduktan sonra açar. Böylece özel hazırlanmış bir resim bile kendiliğinden çalışamaz.

Yöneticinin tüm üyeleri tanıdığı kapalı bir düğümde bu ayarlara genellikle gerek yoktur. Açık bir düğümde açmaya değer.

## Engelleme ve şikâyet

- Birini **engellemek** — sohbet ayarları (dişli) → **Engelle**. Size yazamaz ve sizi arayamaz, bundan haberi de olmaz. Engellenenlerin listesi — **Profil → Güvenlik → Engellenenler**.
- **Bir mesajı şikâyet etmek** — üzerine basılı tutun → **Şikâyet et**. Bir kişiyi şikâyet etmek — sohbet ayarları → **Şikâyet et**.
- Belirli bir sohbet olmadan **kötüye kullanımı bildirmek** — **Profil → Güvenlik → Kötüye kullanımı bildir**.

Şikâyet, düğümünüzün yönetimine gider — uygulama içinden administrator hesabına bir mesaj olarak (veya abuse@nevod.network adresine e-postayla). Nevod'daki mesajlar şifrelidir ve yönetim onları göremez; bu yüzden uygulama şikâyet ettiğiniz mesajın metnini şikâyete ekler. Yanıt administrator ile sohbete gelir. Şikâyetle birlikte kişiyi hemen engelleyebilirsiniz — **Ayrıca engelle**.

## Yedek yok — bilerek

Anahtarlar, kişiler ve mesaj geçmişi yalnızca telefonunuzda bulunur. Bu yüzden:

- **telefon kaybolur, bozulur veya sıfırlanırsa yazışmalar kurtarılamaz;**
- **uygulamayı silmek de geçmişi siler;**
- **yeni telefona aktarma henüz yok.** Yeni telefonda yeni bir kimlik oluşturursunuz ve kişilerinizin yeni kartınıza ihtiyacı olur.

Bu, Nevod'un yapısından kaynaklanır: yazışmalarınızın geri yüklenebileceği bir kopya, başka birinin de erişebileceği bir kopya olurdu. Bir yazışmadan bir şeyi uzun süre saklamanız gerekiyorsa ayrıca kaydedin: fotoğraf ve dosyaları — **Paylaş** ile.

## Kimliği sıfırlama

**Profil → Kimliği sıfırla…** kimliğinizi, kişilerinizi, telefondaki yazışmaları ve düğümdeki kaydınızı kalıcı olarak siler. Uygulama, sıfırlamanın yanlışlıkla yapılamaması için bir onay kelimesi yazmanızı ister.

Sıfırlama, sıfırdan başlamak veya başka bir düğüme geçmek istediğinizde gerekir. Kişileriniz sohbetinizde **Kimlik silindi** görür; size yeniden yazmak için yeni kartınıza ihtiyaçları olur.
