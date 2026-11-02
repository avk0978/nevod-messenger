# Sorular ve sorunlar

Sık sorulan sorulara kısa yanıtlar ve bir şey çalışmazsa ne yapılacağı. Sorunuz burada yoksa bize yazın (bu bölümün sonunda).

## Genel sorular

**Nevod ücretli mi?**
Hayır. Uygulama ücretsizdir; abonelik ve reklam yoktur. Yalnızca yapay zekâ asistanlarını kendi anahtarınızla kullanırsanız yapay zekâ sağlayıcısına ödeme yapmanız gerekebilir — bkz. [Botlar ve yapay zekâ asistanları](../bots/).

**Telefon numarası gerekir mi?**
Hayır. Nevod telefon numarasına veya e-posta adresine ihtiyaç duymaz ve bunları sormaz. Sizi yalnızca kart alışverişi yaptığınız kişiler tanır.

**Nevod Android veya bilgisayar için var mı?**
Şu anda yalnızca iPhone ve iPad için. Android sürümü geliştirme aşamasında.

**Nevod'u aynı anda iki cihazda kullanabilir miyim?**
Henüz değil: bir kimlik tek bir cihazda yaşar. İkinci bir iPhone veya iPad'de kendi kişileri olan ayrı bir kimliğiniz olur.

**Telefonumu değiştirdim. Yazışmalarımı nasıl taşırım?**
Şimdilik taşınamaz: yeni cihaza aktarma yoktur ve Nevod bilerek yazışma yedeği almaz. Yeni telefonda yeni bir kimlik oluşturun ve kişilerinize yeni kartınızı gönderin. Daha fazlası [Güvenlik ve yedekler](../security/) bölümünde.

**Başka bir düğüme nasıl geçerim?**
Yalnızca kimliği sıfırlayarak: **Profil → Kimliği sıfırla…**, ardından yeni düğümün davetini açın. Sıfırlama; kimliğinizi, kişilerinizi, telefondaki yazışmaları ve önceki düğümdeki kaydınızı kalıcı olarak siler. Başka bir düğümdeki biriyle sadece yazışmak için geçmenize gerek yoktur — onun kartı yeterlidir.

## Kayıt

| Ne görüyorsunuz | Ne yapmalı |
|---|---|
| "Bu ad zaten alınmış, başka bir ad seçin" | bu ad düğümde zaten var ya da bir hizmet adı (administrator, support, Nevod…). Başka bir ad seçin. |
| "Davet kodu gerekli" | düğüm yalnızca davetle kabul ediyor. Düğüm yöneticisinden davet isteyin veya başka bir düğüm seçin. |
| "Geçersiz veya süresi dolmuş kod — yeni bir kod alın" | kod zaten kullanılmış veya süresi dolmuş. Yenisini isteyin. |
| "Onay bekleniyor" | düğüm başvuruyla kabul ediyor — yöneticinin kararını bekleyin; bildirim gelecek. |
| "Talep reddedildi" | düğüm yöneticisi başvurunuzu reddetti. Nevod Open gibi başka bir düğüm seçebilirsiniz. |
| bir davet açtınız ve uygulama "Başka bir düğüme davet" diyor | zaten bir düğüme kayıtlısınız. Yukarıdaki "Başka bir düğüme nasıl geçerim?" sorusuna bakın. |
| bir davet açtınız ve uygulama "Bu düğüme zaten kayıtlısınız" diyor | davet kendi düğümünüze — bir şey yapmanıza gerek yok. |

## Bağlantı

**Sohbette giriş alanının üstünde "Bağlantı yok" ya da uzun süre "Bağlanıyor…" yazıyor ve mesaj gönderilemiyor.**
İnternetinizi kontrol edin: herhangi bir siteyi açın. VPN kullanıyorsanız kapatmayı veya sunucuyu değiştirmeyi deneyin. Wi-Fi ile mobil veri arasında geçiş yapın. İşe yaramazsa düğümünüz geçici olarak erişilemez olabilir — birkaç dakika bekleyin; özel bir düğümdeyseniz yöneticisine haber verin.

**Nevod kapalıyken bildirim gelmiyor.**
- **iPhone Ayarları → Nevod → Bildirimler** — izinli olmalı.
- Rahatsız Etme veya başka bir Odak modunun açık olmadığını kontrol edin.
- Bu sohbet için bildirimlerin kapatılmadığını kontrol edin: sohbet ayarları (dişli) → **Bildirimler**.
- Özel bir düğümde: yöneticiden düğümün [Nevod ağına bağlı](../node-network/) olduğunu kontrol etmesini isteyin — aksi hâlde bildirimler gelmez.

**Arama bağlanmıyor.** Bkz. [Aramalar](../calls/), "Arama bağlanmazsa".

## Mesajlar ve dosyalar

**Bir mesajın yanında turuncu bir saat var.**
Karşınızdaki çevrimdışı: mesaj düğümde onu bekliyor ve bağlandığında teslim edilecek. Düğüm bu tür mesajları 72 saate kadar saklar — kişi bu sürede çevrimiçi olmazsa mesaj ulaşmaz.

**"Mesaj gönderilmedi. Tekrar gönderilsin mi?"**
Gönderdiğiniz anda bağlantı yoktu. Bağlantı geri geldiğinde bu satıra dokunun.

**Dosya gönderilmiyor.**
- 50 MB'tan büyük — uygulama bunu söyler. Videoları **Fotoğraf veya video** ile seçin: sıkıştırılırlar.
- "Video yüklenemedi" — klip iCloud'da saklanıyorsa telefonda yalnızca küçültülmüş bir kopyası olabilir. Videoyu Fotoğraflar uygulamasında açın, tamamen inmesini bekleyin ve yeniden deneyin. Hata tekrarlanırsa bize bildirin (aşağıdaki "Sorun bildirme"ye bakın).
- "Video sıkıştırılamadı" — daha kısa bir klip deneyin veya 50 MB'tan küçükse **Dosya** ile gönderin.

**"Dosya kaydedilemedi: depolama dolu".**
Alınan dosyalar telefonda Nevod kotası dahilinde yer kaplar. Kotayı artırın: **Profil → Depolama → Kota** — ya da gereksiz sohbetleri silin (sohbet listesinde sola kaydırın → **Sil**).

## Yapay zekâ asistanları

**Bot anahtar gerektiğini yazıyor veya anahtar kabul edilmiyor.**
Anahtarın eksiksiz kopyalandığını ve sağlayıcının sitesinde iptal edilmediğini, sağlayıcıdaki hesabınızda bakiye olduğunu ya da ücretsiz sınırın dolmadığını kontrol edin. Anahtarı botla sohbette değiştirebilirsiniz — **Değiştir**. Daha fazlası [Botlar ve yapay zekâ asistanları](../bots/) bölümünde.

## Sorun bildirme

**Profil → Tanılama** — ne olduğunu ve yaklaşık ne zaman olduğunu yazın (örneğin, "3 fotoğraftan 2'si gelmedi, saat 21:00 civarı") ve **Geliştiricilere gönder**'e dokunun. Açıklamanızla birlikte uygulamanın teknik günlüğü de gider: yalnızca telefonda saklanır ve mesaj metni içermez. Günlük e-postayla support@nevod.network adresine gider; telefonda e-posta hesabı kurulu değilse Nevod'da düğümünüzün yöneticisine gider; yanıt onunla sohbete gelir.

Bir kişiyi veya mesajı şikâyet etmek için — bkz. [Güvenlik](../security/), "Engelleme ve şikâyet".
