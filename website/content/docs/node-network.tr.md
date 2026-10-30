# Nevod ağına katılmak

Bir düğümün ağa neden ihtiyacı olduğu, tek bir düğmeyle nasıl katılacağı ve sonrasında diğer düğümlerin neleri gördüğü.

## Neden katılmalı

Kimseye bağlı olmayan bir düğüm bir adadır. Çalışır, ama:

- **kullanıcıları yalnızca birbirine yazabilir ve birbirini arayabilir.** Başka bir düğümdeki birine yazmak ya da ondan mesaj almak imkânsızdır — düğüm mesajı nereye göndereceğini bilmez;
- uygulama kapalıyken **telefonlara bildirim gelmez:** App Store'daki Nevod'a push bildirimi yalnızca Apple anahtarı olan proje düğümleri gönderebilir ve bunu ağın düğümleri için yaparlar;
- **zorlu ağlar üzerinden aramalar bağlanmayabilir:** kendi arama aktarıcısı (TURN) olmayan bir düğüm, aktarıcıyı ağın düğümlerinden alır — daha fazlası [Kendi düğümünüz üzerinden aramalar](../node-turn/) bölümünde.

Bu yüzden düğümü ağa bağlamak neredeyse her zaman değerlidir — kapalı bir aile veya kuruluş düğümü bile olsa. Ağa katılmak **kaydı açmaz** ve **düğümü "Ağı keşfet"te göstermez**: kimi kabul edeceğinize ve düğümün görünüp görünmeyeceğine yine ayarlarda siz karar verirsiniz.

## Nasıl katılınır

1. Sunucudaki **8765** portunun dışarıdan açık olduğundan emin olun — hem `ufw`'de hem sağlayıcının güvenlik duvarında (bkz. [kurulum](../node-install/), 1. ve 5. adımlar). Düğümler birbirleriyle bu port üzerinden konuşur.
2. Panel → **Düğümler** → **Nevod ağına bağlan**.
3. Birkaç saniye içinde bağlantının kurulduğunu söyleyen bir mesaj görünür. Bloğun üstündeki durum "bağlı · çevrimiçi düğümler: N" olarak değişir ve **Bilinen düğümler** listesinde ağın düğümleri belirir.

Düğüm, ağa davetsiz düğüm kabul eden bir proje düğümü olan Nevod Open üzerinden katılır. Open'ın gerçekliği, düğüm programına gömülü sertifika parmak iziyle doğrulanır: yolda değiştirilemez.

Panel, **ağ düğümünün düğümünüze dışarıdan ulaşamadığını** söylüyorsa bağlantı kurulmuştur, ama kimse size geri bağlanamaz. Neredeyse her zaman sebep 8765 portunun kapalı olmasıdır. Açın ve düğmeye tekrar basın. Daha sonra da kontrol edebilirsiniz: **Tanılama → Kontrol et → Dış erişilebilirlik**.

Bağlantı korunur: yeniden başlattıktan sonra düğüm bildiği tüm düğümlerle kendiliğinden yeniden iletişim kurar.

## Başka bir düğüm üzerinden katılmak

Başka bir düğümün yöneticisini tanıyorsanız Open yerine onun düğümü üzerinden katılabilirsiniz:

1. O, kendi panelinde: **Düğümler → Düğüm davetleri → + Düğüm daveti oluştur** — ve belirteci size yüz yüze verir (belirteç 10 dakika geçerlidir).
2. Siz: **Düğümler** → belirteci **Başka bir düğümün yöneticisinden alınan belirteç** alanına yapıştırın → **Belirteçle bağlan**.

Sonuç aynıdır: düğümünüz ağın bir parçası olur. Aynı şekilde tanıdığınız bir düğümü de kendi düğümünüz üzerinden ağa alabilirsiniz — onun için bir belirteç oluşturun.

## Diğer düğümler neyi görür

Ağın düğümleri bir düğüm listesi paylaşır. Bu listede düğümünüz hakkında şunlar bulunur:

- düğüm kimliği (`node_id`), adı ve düğümler arası bağlantı adresi (`alanadi:8765`);
- düğümün sertifika parmak izi;
- düğümün "Ağı keşfet"te görünür olup olmadığı, kendi arama aktarıcısı ve bildirim anahtarı olup olmadığı.

Düğüm "Ağı keşfet"te görünürse (`open` ayarı), ağın düğümleri üzerinde hangi hücrelerin kayıtlı olduğunu da öğrenir — adlar olmadan, kimliklerle. Kapalı bir düğüm bunu bildirmez: kullanıcısına giden bir mesaj, ev düğümünü belirten kişi kartındaki adrese ulaşır.

Ağın düğümlerinin asla almadıkları: mesaj metinleri, dosyalar, aramalar, kullanıcıların kişileri, kapalı bir düğümün hücrelerinin adları ve anahtarları.

## Ağdan ayrılmak

Ayrı bir "ağdan ayrıl" düğmesi henüz yok. 72 saat boyunca iletişim kurmayan bir düğümü diğer düğümler listelerinden kendiliğinden kaldırır. Düğümün ağla bağlantısını kalıcı olarak kesmek istiyorsanız onu durdurun veya 8765 portunu kapatın.
