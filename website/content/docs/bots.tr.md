# Botlar ve yapay zekâ asistanları

Botları nerede bulacağınız, yapay zekâ asistanlarını kendi anahtarınızla nasıl kullanacağınız, bunun ne kadar tuttuğu ve bir botla yazışmanızı kimin gördüğü.

## Nevod'da bot nedir

Bot da tıpkı bir insan gibi ağın bir üyesidir, yalnız ona bir program yanıt verir. Botlar basit olabilir — örneğin Nevod Open'daki **Echo** mesajlarınızı tekrarlar, bağlantının çalıştığını denemek için kullanışlıdır — ya da Claude, ChatGPT veya Gemini ile yanıt veren **yapay zekâ asistanları** olabilir.

## Botlar nerede

- **Düğümler** → bir düğüme dokunun — sayfasında düğümün kullanıcılarına sunduğu botlar ve sayfalar görünür. Bir botla sohbet açmak için ona dokunun. Henüz kayıtlı değilseniz uygulama bir ad veya takma ad ister ve sizi o düğüme kaydeder.
- **Kişiler → Bu düğümde** — ev düğümünüzün botları.

Nevod Open'da şu anda her işe yarayan bir asistan olan **AI Assistant** ve bir çevirmen olan **Tolmach** çalışıyor.

Özel düğümlerdeki botları düğüm yöneticisi kurar: hangi botlara sahip olduğunuz düğümünüze bağlıdır.

## Kendi anahtarınızla yapay zekâ asistanları

Nevod'daki yapay zekâ asistanlarının Claude, ChatGPT veya Gemini'ye kendi ücretli erişimi yoktur. Bot **sizin kendi anahtarınızla** yanıt verir — böylece sağlayıcıyı kendiniz seçer ve doğrudan ona ödersiniz; düğüm ve Nevod geliştiricileri bu ödemeye karışmaz.

**Anahtar nasıl bağlanır:**

1. Bir yapay zekâ asistanıyla sohbet açın. "Bu bot kendi yapay zekâ anahtarınızla yanıt verir." görünür → **Yapay zekâ anahtarı ekle**.
2. Bot birden çok sağlayıcıyla çalışıyorsa **Sağlayıcı**'yı seçin: Claude (Anthropic), ChatGPT (OpenAI) veya Gemini (Google).
3. Sağlayıcının sitesinden bir anahtar alın — **Anahtarı nereden alırım?** bağlantısı doğrudan doğru sayfaya götürür. Anahtarı kopyalayıp **API anahtarınızı yapıştırın** alanına yapıştırın.
4. Mesajlarınızın nereye gittiğini okuyun, **Kabul ediyorum**'u açın ve **Kontrol et ve kaydet**'e dokunun. Uygulama anahtarın çalıştığını kontrol eder.

Tamam — bota yazabilirsiniz. Sağlayıcıyı veya anahtarı değiştirmek için botla sohbetteki **Değiştir** düğmesini kullanın. Sağlayıcı başına bir anahtar tüm botlar için geçerlidir: bir anahtar zaten kayıtlıysa uygulama **Kayıtlı anahtarı kullan** önerir.

**Kayıtlı tüm anahtarlar** — **Profil → Güvenlik → Yapay zekâ anahtarları**. **Anahtarı sil** de oradadır.

## Ne kadar tutar

Sağlayıcı her istek için — kendi tarifeleriyle, anahtarınızın bağlı olduğu hesaptan — ücret alır. Bir asistanla yazışma için bunlar genellikle küçük tutarlardır; bazı sağlayıcıların sınırlı ücretsiz bir katmanı vardır. Tarifeleri ve sınırları sağlayıcının sitesinde görün; orada anahtar için bir harcama sınırı da koyabilirsiniz — böylece kararlaştırdığınızdan fazlasını asla harcamazsınız.

## Bir yapay zekâ botuyla yazışmanızı kim görür

Olağan yazışmadan farkı burada.

- **Anahtarınız** yalnızca telefonunuzda saklanır. Her mesajla birlikte bota şifreli gider; bot onu sağlayıcıya tek bir istek için kullanır ve saklamaz.
- **Bota gönderdiğiniz mesajları** botun çalıştığı düğüm çözer ve seçilen sağlayıcıya iletir — yoksa yapay zekâ yanıt veremezdi. **Sağlayıcı (Anthropic, OpenAI veya Google) botla yazışmanızı görür** ve kendi kurallarına göre işler.
- İnsanlar arasında hiçbir şey değişmez: insanlar arasındaki yazışmaları ne düğümler ne de yapay zekâ sağlayıcıları görür.

Bu yüzden yapay zekâ botlarına sağlayıcıya göstermek istemeyeceğiniz şeyleri göndermeyin: parolalar, kart numaraları, başkalarının kişisel verileri. Daha fazlası [Gizlilik Politikası](../../privacy/), 5. bölümde.

> Yapay zekâ yanıtları hatalı olabilir. Önemli olanı kontrol edin — özellikle belge çevirilerini ve tıbbi, hukuki ve mali soruları.
