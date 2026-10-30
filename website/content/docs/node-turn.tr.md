# Kendi düğümünüz üzerinden aramalar

Nevod'un aramaları nasıl bağladığı, bir düğümün ne zaman kendi arama aktarıcısına (TURN) ihtiyaç duyduğu ve onu aynı sunucuya nasıl kuracağınız. Yeni başlıyorsanız bu bölümü atlayabilirsiniz: ağa bağlı bir düğüm, aktarıcıyı proje düğümlerinden alır.

## Arama nasıl bağlanır

Ses ve görüntü **doğrudan telefonlar arasında** gider; düğüm yalnızca bağlantı üzerinde anlaşmalarına yardım eder. Ama doğrudan bağlantı her zaman mümkün değildir: mobil operatörler ve birçok yönlendirici telefonları ortak adreslerin (NAT) arkasına gizler ve böyle iki telefon birbirine ulaşamaz. O zaman arama bir **aktarıcı (TURN)** üzerinden gider — telefonlar arasında paketleri ileten bir sunucu.

Arama telefondan telefona şifrelidir (DTLS-SRTP). Aktarıcı yalnızca şifreli paketleri, telefonların adreslerini, aramanın zamanını ve hacmini görür — konuşmayı duyamaz veya göremez.

## Kendi aktarıcınıza ihtiyacınız var mı

**Kendi aktarıcınız olmadan**, [ağa bağlı](../node-network/) bir düğüm, oturum açan her kullanıcı için, aktarıcısı olan ağ düğümlerinden birinin — rastgele seçilen — aktarıcısına erişim ister. Aramalar çalışır ve ayarlanacak bir şey yoktur. Ağa bağlı olmayan bir düğüm aktarıcı alamaz: kullanıcıları arasında NAT arkasındaki telefonlar arası aramalar bağlanmayabilir.

**Kendi aktarıcınızı** kurmaya değer, eğer:

- kullanıcılarınızın aramalarının proje düğümlerine bağlı olmamasını istiyorsanız;
- kullanıcılarınız proje sunucularından uzaksa ve onlar üzerinden aramalar gecikmeliyse;
- çok sayıda kullanıcınız ve aramanız varsa.

Dikkate alınacaklar:

- **trafik.** Aramanın tamamı aktarıcıdan geçer: ses — her yönde yaklaşık 100 kbit/s, görüntü — 1–2 Mbit/s. Çoğu VPS ayda birkaç terabayt trafik içerir — onlarca kullanıcılı bir düğüm için fazlasıyla yeterli;
- **aktarıcınız ağın diğer düğümlerine de yardım eder.** Düğüm ağa bir aktarıcısı olduğunu bildirir ve kendi aktarıcısı olmayan düğümler onu rastgele kendi kullanıcılarına verir. Aşağıdaki yapılandırmada, bunun sunucunun tüm bant genişliğini yememesi için sınırlar vardır.

## coturn kurulumu

En yaygın aktarıcı olan coturn'ü doğrudan düğümün sunucusuna kuruyoruz. Tüm komutlar sunucuda çalıştırılır.

**1. coturn'ü kurun ve bir sır oluşturun:**

```
apt install -y coturn
openssl rand -hex 32
```

İkinci komutun çıktısını saklayın — aktarıcı ile düğümün ortak sırrı budur.

**2. Sunucunun dış IP adresini öğrenin:**

```
curl -4 ifconfig.me
```

**3. Yapılandırmayı yazın.** Dosyayı açın:

```
nano /etc/turnserver.conf
```

içindeki her şeyi silin ve kendi IP adresiniz ile sırrınızı koyarak şunu yapıştırın:

```
listening-port=3478
external-ip=SUNUCU-IP-ADRESI
realm=nevod
use-auth-secret
static-auth-secret=SIR
min-port=49152
max-port=65535
no-tls
no-dtls
fingerprint
no-loopback-peers
no-multicast-peers
denied-peer-ip=0.0.0.0-0.255.255.255
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=100.64.0.0-100.127.255.255
denied-peer-ip=127.0.0.0-127.255.255.255
denied-peer-ip=169.254.0.0-169.254.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
total-quota=200
user-quota=10
max-bps=4000000
```

Kaydedin: **Ctrl+O**, **Enter**, **Ctrl+X**.

`denied-peer-ip` satırları, aktarıcının iç adreslere — aynı sunucudaki Docker'ın içi dahil — herhangi bir şey iletmesini yasaklar. Bunları silmeyin. `total-quota`, `user-quota` ve `max-bps` eşzamanlı bağlantı sayısını ve tek bir bağlantının hızını (4 Mbit/s) sınırlar.

**4. coturn'ü başlatın:**

```
systemctl enable --now coturn
systemctl status coturn
```

Çıktıda `active (running)` görünmelidir. coturn başlamazsa `/etc/default/coturn` dosyasını açın ve `TURNSERVER_ENABLED=1` satırının başındaki yorum işaretini kaldırın — paketin bazı sürümlerinde bu gereklidir.

**5. Portları açın:**

```
ufw allow 3478/tcp
ufw allow 3478/udp
ufw allow 49152:65535/udp
```

Varsa aynı portları sağlayıcının güvenlik duvarında da açın.

**6. Sırrı düğüme verin.** `/opt/nevod/installer/docker` klasöründe:

```
nano .env
```

aynı sırrı `TURN_SECRET=` satırına yazın ve uygulayın:

```
docker compose up -d
```

## Kontrol

- **Tanılama → Kontrol et → Bağımlılıklar ve yapılandırma** — TURN ile ilgili uyarı olmamalıdır.
- Düğüm telefonlara `turn:alanadiniz:3478` aktarıcı adresini verir — alan adı bu sunucuyu göstermelidir (düğüm çalışıyorsa zaten gösterir).
- Mobil veriye bağlı bir telefondan Wi-Fi'ye bağlı bir telefonu arayın. Arama bağlanır ve ikiniz de duyuluyorsanız aktarıcı çalışıyordur. coturn günlüğü: `journalctl -u coturn -n 50`.

> Aktarıcı, 3478 portunda UDP ve TCP üzerinden, aktarıcıya giden kanal şifrelenmeden çalışır (aramanın kendisi her zaman şifrelidir). Bazı kurumsal ağlarda bu portlar kapalıdır — o zaman bu ağlardan gelen aramalar aktarıcı üzerinden geçemez.
