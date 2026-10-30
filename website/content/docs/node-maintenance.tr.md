# Bakım

Düğümü güncellemek, yedekler, başka bir sunucuya taşımak, günlükler ve olağan sunucu bakımı. Tüm `docker compose` komutları sunucuda `/opt/nevod/installer/docker` klasöründen çalıştırılır:

```
cd /opt/nevod/installer/docker
```

## Düğümü güncellemek

Düğümün yeni sürümleri [GitHub'daki kaynak kodunda](https://github.com/avk0978/nevod-messenger) yayınlanır — haberdar olmak için orada **Watch**'a tıklayın. Güncelleme:

```
cd /opt/nevod
git pull
cd installer/docker
docker compose up -d --build
```

Düğüm yeni sürümle yeniden başlar; kullanıcılar kendiliğinden yeniden bağlanır ve `data/` klasöründeki veriler korunur. Güncellemeden sonra paneldeki **Tanılama** → **Kontrol et**'e bakın.

Birkaç güncellemeden sonra eski imajlar disk alanı kaplar — silebilirsiniz:

```
docker image prune -f
```

## Yedek

Sunucudaki en değerli şey `data/` klasörü ve içindeki `node.json` dosyasıdır: bu, düğümün kimliğidir. Onu kaybederseniz düğümün yeni bir kimlikle yeniden oluşturulması ve tüm kullanıcıların yeniden kaydolması gerekir. En az haftada bir ve her ayar değişikliğinden sonra yedek alın.

**Yedek almak** (düğüm birkaç saniye durur):

```
docker compose stop nevod_node
tar czf ~/nevod-backup-$(date +%F).tar.gz data .env
docker compose start nevod_node
```

**Bilgisayarınıza indirmek.** Bilgisayarınızda:

```
scp root@node.example.org:~/nevod-backup-*.tar.gz .
```

Yedeği aynı sunucuda tutmayın: sunucuya bir şey olursa yedek de onunla birlikte gider.

> Yedekte düğümün anahtarları ve `.env`'deki panel parolası bulunur. Onu bir parola kadar özenle saklayın: şifreli bir disk, ek dosya destekli bir parola yöneticisi veya benzeri bir yer.

## Geri yükleme ve başka bir sunucuya taşıma

Bir düğüm yeni bir sunucuya da bu şekilde taşınır. Alan adı aynı kalır — yalnızca gösterdiği sunucu değişir.

1. Yeni sunucuda [kurulumun](../node-install/) 1. ve 3–6. adımlarını uygulayın (sunucu, Docker, güvenlik duvarı, Nevod'u indirmek) — 7–8. adımlar **olmadan**.
2. Yedeği yeni sunucuya kopyalayın ve paketin klasörüne açın:

   ```
   scp nevod-backup-TARIH.tar.gz root@YENI-IP:/opt/nevod/installer/docker/
   ```

   ve yeni sunucuda:

   ```
   cd /opt/nevod/installer/docker
   tar xzf nevod-backup-TARIH.tar.gz
   ```

3. **Eski sunucudaki düğümü durdurun** (`docker compose down`) — aynı kimliğe sahip iki düğüm aynı anda çalışmamalıdır.
4. Alan adının A kaydını yeni sunucunun IP'sine çevirin ve `ping node.example.org` yeni adresi gösterene kadar bekleyin.
5. Düğümü yeni sunucuda başlatın: `docker compose up -d --build`. Caddy sertifikayı kendisi yeniden alır.

Kullanıcıların bir şey yapmasına gerek yoktur: uygulama aynı alan adına bağlanır ve orada aynı düğümü bulur.

> Düğümün **alan adı** bu kadar kolay değiştirilemez: diğer düğümlerle bağlantı adresi ilk başlatmada düğümün kimliğine yazılır. Değiştirmek zorunda kalmayacağınız bir alan adı seçin.

## Günlükler

```
docker compose logs --tail 100 nevod_node
docker compose logs -f nevod_node
```

İlk komut son 100 satırı, ikincisi günlüğü gerçek zamanlı olarak gösterir (çıkmak için **Ctrl+C**). Caddy günlüğü — `docker compose logs caddy`. Düğümün son kayıtları panelde de görülebilir: **Tanılama → Günlükler**.

Günlüklerin boyutu sınırlıdır: konteyner başına 10'ar MB'lık 3 dosya; eski kayıtların üzerine kendiliğinden yazılır. Mesaj metinleri günlüğe asla girmez.

## Yeniden başlatma, durdurma, parola

| Ne gerekiyor | Komut |
|---|---|
| Düğümü yeniden başlatmak (örneğin paneldeki adı veya görünürlüğü değiştirdikten sonra) | `docker compose restart nevod_node` |
| Her şeyi durdurmak | `docker compose down` |
| Yeniden başlatmak | `docker compose up -d` |
| Neyin çalıştığını görmek | `docker compose ps` |

**Panelin ana parolasını değiştirmek:** yenisini `.env`'deki `NEVOD_ADMIN_PASSWORD` satırına yazın (`nano .env`) ve `docker compose up -d` çalıştırın — düğüm yeni parolayla yeniden başlar. "Güvenlik" sayfasındaki kişisel hesaplar bundan etkilenmez.

## Sunucu bakımı

- **Sistem güncellemeleri** — ayda bir veya daha sık:

  ```
  apt update && apt upgrade -y
  reboot
  ```

  Yeniden başlatmadan sonra düğüm, Caddy ve coturn (kurduysanız) kendiliğinden başlar.
- **Disk alanı** — `df -h /`. Alan azsa eski imajları (`docker image prune -f`) ve sunucudaki eski yedekleri silin.
- **HTTPS sertifikasını** Caddy kendisi yeniler. Yapacak bir şey yok, ama 80 portu açık kalmalıdır.
- **Düğüme erişilemiyor mu?** Bunu hemen öğrenmenin en kolay yolu, ücretsiz bir site erişilebilirlik izleme hizmetini `https://node.example.org` adresine yönlendirmektir: düğüm yanıt vermeyi keserse size e-posta gönderir.

## Düğüm uzun süre çalışmadıysa

Çevrimiçi olmayan kullanıcılar için mesajları düğüm 72 saate kadar saklar, sonra siler. 72 saat boyunca iletişim kurmayan bir düğümü ağın diğer düğümleri listelerinden kaldırır — başlatıldıktan sonra listeler paylaşıldıkça kendiliğinden geri döner.
