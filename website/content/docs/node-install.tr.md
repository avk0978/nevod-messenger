# Adım adım kurulum

Kiralık bir sunucuya sıfırdan Nevod düğümü kurmak: sunucuyu satın almaktan yönetim paneline ilk girişe kadar. Örnekte Ubuntu 26.04 yüklü bir sunucu ve `node.example.org` alan adı kullanılıyor; her yerde kendi alan adınızı yazın.

Aşağıdaki tüm komutlar sunucunun terminaline girilir; tamamını kopyalayabilirsiniz. Düğümün ne olduğu ve neyi sakladığı — [Düğüm nasıl çalışır](../node-how/) bölümünde.

## 1. Bir sunucu kiralayın

Herhangi bir sağlayıcıdan herhangi bir VPS olur: 1 işlemci, 1 GB bellek, 10 GB disk, **Ubuntu 24.04** veya **26.04**. Sipariş verdiğinizde sağlayıcı size sunucunun **IP adresini** ve `root` kullanıcısının parolasını verir (veya bir SSH anahtarı yüklemenizi ister).

Sağlayıcının kontrol panelinde kendi ağ güvenlik duvarı varsa (örneğin Hetzner'de Firewalls, başkalarında Security groups), orada gelen **22, 80, 443 ve 8765** (TCP) portlarını açın.

## 2. Alan adını sunucuya yönlendirin

Düğümün kendine ait bir alan adı veya alt alan adı olmalıdır, örneğin `node.example.org`. İki nedenle onsuz olmaz:

- **Telefonlar düğüme `https://alanadı/nevod-ws` adresinden bağlanır.** iPhone'un hiçbir ayar gerektirmeden güvendiği HTTPS sertifikasını Caddy, Let's Encrypt'ten bir alan adı için alır.
- **Düğümün adresi her yerde kayıtlıdır:** kullanıcıların telefonlarında, kişi kartlarında, ağdaki diğer düğümlerde. Başka bir sunucuya taşınırsanız veya sağlayıcınız IP adresini değiştirirse tek bir DNS kaydını düzeltmeniz yeterlidir; kullanıcılar hiçbir şey fark etmez. Çıplak bir IP adresiyle taşınma herkesin bağlantısını keser ve davetleri yeniden göndermeniz gerekir.

Henüz alan adınız yoksa herhangi bir kayıt kuruluşundan (Cloudflare, Namecheap, Porkbun, Gandi ve diğerleri) satın alabilirsiniz — genellikle yılda birkaç dolar veya avro. Düğüm için tek bir alt alan adı yeterlidir; alan adının kendisini başka amaçlar için de kullanabilirsiniz.

Alan adınızın yönetim panelinde bir **A kaydı** oluşturun: ad — örneğin `node` (`node.example.org` olur), değer — sunucunun IP adresi.

Birkaç dakika bekleyin ve herhangi bir bilgisayardan kontrol edin:

```
ping node.example.org
```

Yanıtta sunucunuzun IP adresi görünmelidir. Görünmüyorsa devam etmenin anlamı yok: HTTPS sertifikası yalnızca zaten sunucuyu gösteren bir alan adına verilir.

> Alan adı Cloudflare tarafından sunuluyorsa bu kayıt için proxy'yi kapatın (gri bulut, "DNS only"). Yoksa telefonlar ve diğer düğümler sunucunuza değil Cloudflare'e bağlanır.

## 3. Sunucuya bağlanın

Bilgisayarınızda bir terminal açın (Windows'ta PowerShell, Mac'te Terminal) ve şunu girin:

```
ssh root@node.example.org
```

İlk bağlantıda `yes` yanıtını verin ve sağlayıcıdan aldığınız parolayı girin.

## 4. Docker ve git'i kurun

```
apt update && apt upgrade -y
apt install -y git
curl -fsSL https://get.docker.com | sh
```

Son komut resmi Docker kurulum betiğidir. Her şeyin yerinde olduğunu kontrol edin:

```
docker compose version
```

`Docker Compose version v…` gibi bir satır görmelisiniz.

> Güncellemeden sonra ekranda veya bir sonraki girişte `*** System restart required ***` yazısı çıkarsa sunucuyu `reboot` komutuyla yeniden başlatın, bir dakika sonra yeniden bağlanın (3. adım) ve devam edin.

## 5. Güvenlik duvarını açın

```
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8765/tcp
ufw enable
```

Soruya `y` yanıtını verin. 80 ve 443 portları HTTPS için (telefonlar ve panel), 8765 diğer düğümlerle iletişim için gereklidir.

> Docker, konteynerlerinin portlarını `ufw`'yi atlayarak kendisi açar. Bu yüzden paketimizde yönetim paneli (8766 portu) yalnızca sunucunun kendisine açıktır — bunu `docker-compose.yml` içinde değiştirmeyin.

## 6. Nevod'u indirin

> Bundan sonraki tüm komutlar sunucuda yazılır: giriş satırının solunda `root@…` görünmelidir. Orada `PS C:\…>` veya bilgisayarınızın adı varsa sunucuyla bağlantı kapanmıştır — yeniden bağlanın (3. adım).

```
git clone https://github.com/avk0978/nevod-messenger.git /opt/nevod
cd /opt/nevod/installer/docker
```

## 7. Ayarları doldurun

Şablondan ayar dosyasını oluşturun:

```
cp .env.example .env
```

Yönetim paneli için bir parola belirleyin. En kolayı uzun, rastgele bir parola üretmektir:

```
openssl rand -base64 24
```

Sonucu kopyalayın ve güvenli bir yere kaydedin — örneğin bir parola yöneticisine (Bitwarden, KeePass, iPhone ve Mac'teki Şifreler). Şimdi ayar dosyasını açın:

```
nano .env
```

İki satırı değiştirin:

```
NEVOD_DOMAIN=node.example.org
NEVOD_ADMIN_PASSWORD=buraya-uretilen-parola
```

Gerisini olduğu gibi bırakın. Dosyayı kaydedin: **Ctrl+O**, sonra **Enter**; çıkmak için **Ctrl+X**.

| Ayar | Anlamı |
|---|---|
| `NEVOD_DOMAIN` | Düğümün alan adı. Telefonlar `https://alanadi/nevod-ws` adresine, diğer düğümler `alanadi:8765` adresine bağlanır. |
| `NEVOD_ADMIN_PASSWORD` | Yönetim panelinin parolası. Bu olmadan düğüm başlamaz. |
| `NEVOD_ADMIN_PUBLIC` | `true` — panel tarayıcıda `https://alanadi/nevod-admin` adresinde açılır; `false` — panel internete kapalıdır (bkz. 10. adım). |
| `TURN_SECRET` | Yalnızca kendi arama aktarıcınızı kuruyorsanız, bkz. [Kendi düğümünüz üzerinden aramalar](../node-turn/). Genellikle boştur. |

## 8. Düğümü başlatın

```
docker compose up -d --build
```

İlk başlatma birkaç dakika sürer: Docker düğüm imajını oluşturur ve Caddy'yi indirir. Komut bitince kontrol edin:

```
docker compose ps
```

Her iki konteyner — `nevod_node` ve `nevod_caddy` — `Up` (veya `running`) durumunda olmalıdır.

## 9. Her şeyin çalıştığını kontrol edin

Tarayıcıda `https://node.example.org` adresini açın — "Nevod node — https://nevod.network" satırı görünmeli ve tarayıcı sertifika hakkında uyarı vermemelidir.

Şimdi `https://node.example.org/nevod-admin` adresini açın. Tarayıcı kullanıcı adı ve parola sorar: kullanıcı adı herhangi bir şey olabilir, parola `.env`'ye yazdığınızdır. Yönetim paneli açılır. Orada önce ne yapılacağı — [Yönetim panelinde ilk ayarlar](../node-panel/) bölümünde.

> Aynı adresten art arda beş yanlış parola, o adres için paneli 15 dakika kilitler. Bu olursa sadece bekleyin.

## 10. İsteğe bağlı: paneli internete kapatın

Panel adresinin internetten hiç açılmamasını istiyorsanız `.env`'deki `NEVOD_ADMIN_PUBLIC=true` satırını `NEVOD_ADMIN_PUBLIC=false` olarak değiştirin ve uygulayın:

```
docker compose up -d
```

O zaman panele yalnızca bir SSH tüneli üzerinden erişilebilir. Bilgisayarınızda şunu çalıştırın

```
ssh -L 8766:127.0.0.1:8766 root@node.example.org
```

ve bu pencere açıkken tarayıcıda `http://localhost:8766/nevod-admin` adresini açın.

Bilgisayarınızda 8766 portu zaten kullanılıyorsa (örneğin orada başka bir Nevod düğümü çalışıyorsa) başka bir port seçin: `ssh -L 18766:127.0.0.1:8766 root@node.example.org` ve `http://localhost:18766/nevod-admin`. İlk sayı bilgisayarınızdaki port, ikincisi sunucudaki panel portudur — onu değiştirmeyin.

## Bir şeyler ters giderse

| Ne görüyorsunuz | Genellikle sebep |
|---|---|
| Tarayıcı sertifikanın geçersiz olduğunu söylüyor veya site açılmıyor | Alan adı henüz sunucuyu göstermiyor (2. adım) ya da 80/443 portu kapalı (1. ve 5. adımlar). Caddy günlüğüne bakın: `docker compose logs caddy`. Sebep giderilince Caddy kendisi yeniden dener. |
| `docker compose up`, `address already in use` diyor | Sunucuda zaten başka bir web sunucusu çalışıyor (çoğu zaman sağlayıcının Apache'si veya nginx'i). Durdurun: `systemctl disable --now apache2` veya `systemctl disable --now nginx`. |
| `set NEVOD_ADMIN_PASSWORD in .env` veya `set NEVOD_DOMAIN in .env` hatası | `.env`'deki o satır doldurulmamış (7. adım). |
| `.env`'de alan adını yanlış yazdınız (sertifika alınamıyor, Caddy günlüğünde `NXDOMAIN`) | Düğümü durdurun: `docker compose down`, `.env`'deki `NEVOD_DOMAIN`'i düzeltin, veri klasörünü silin: `rm -rf data`, ve yeniden başlatın: `docker compose up -d`. `data` klasörünü yalnızca düğümde henüz kimse kayıtlı değilken silin — aksi halde düğüm eski adreste kalır ve bunu elle düzeltmeniz gerekir. |
| Panel durmadan parola soruyor | Parola yanlış. Hangisinin yazılı olduğunu görmek için: `grep PASSWORD .env`. |
| Panel "Too many failed logins" yanıtını veriyor | Parola tahminine karşı koruma devreye girdi — 15 dakika bekleyin. |
| `nevod_node` sürekli yeniden başlıyor | Düğüm günlüğü sebebi gösterir: `docker compose logs --tail 50 nevod_node`. |

Her iki konteynerin tam günlükleri: `docker compose logs`. Tüm `docker compose` komutları `/opt/nevod/installer/docker` klasöründen çalıştırılır.
