"""DevHarbor bekçisi çalışıyor mu? (GitHub Actions her 30 dakikada çalıştırır)

Bekçi, gizli kayıt kanalındaki sabitlenmiş "nabız" mesajını 5 dakikada bir günceller.
Bu betik o mesajın zamanına bakar; 30 dakikadan eskiyse bot üzerinden sahibine özel mesaj atar.
Bot süreci kapalı olsa bile anahtarı geçerli olduğu için mesaj gönderebilir.

Gerekli ortam değişkenleri (GitHub "Secrets"):
  BOT_TOKEN       bekçi botunun anahtarı
  KAYIT_KANAL_ID  gizli kayıt kanalının kimliği (-100...)
  SAHIP_ID        uyarının gideceği Telegram kullanıcı kimliği
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ESIK_DK = 30          # bu kadar dakikadır nabız yoksa uyar
TEKRAR_DK = 360       # kapalı kalmaya devam ederse 6 saatte bir hatırlat
CALISMA_ARALIGI = 35  # GitHub zamanlayıcısı gecikebildiği için pencere biraz geniş


def api(token: str, yontem: str, **veri) -> dict:
    istek = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{yontem}",
        data=urllib.parse.urlencode(veri).encode(),
    )
    with urllib.request.urlopen(istek, timeout=30) as yanit:
        return json.load(yanit)


def main() -> int:
    # Windows PowerShell ile girilen değerlerin başına görünmez BOM (﻿) ve sonuna satır sonu gelebilir
    def ortam(ad: str) -> str:
        return os.environ[ad].strip().lstrip("﻿").strip()

    token = ortam("BOT_TOKEN")
    kanal = ortam("KAYIT_KANAL_ID")
    sahip = ortam("SAHIP_ID")

    sohbet = api(token, "getChat", chat_id=kanal)["result"]
    metin = (sohbet.get("pinned_message") or {}).get("text", "")
    bulunan = re.search(r"NABIZ:(\d+)", metin)
    if not bulunan:
        api(token, "sendMessage", chat_id=sahip,
            text="⚠️ DevHarbor bekçisi: kayıt kanalında sabitlenmiş nabız mesajı bulunamadı. Bekçinin durumu bilinmiyor.")
        print("Nabız mesajı yok")
        return 0

    yas_dk = (time.time() - int(bulunan.group(1))) / 60
    print(f"Son nabız {yas_dk:.0f} dakika önce")
    if yas_dk < ESIK_DK:
        return 0

    ilk_uyari = yas_dk < ESIK_DK + CALISMA_ARALIGI
    hatirlatma = yas_dk >= TEKRAR_DK and (yas_dk % TEKRAR_DK) < CALISMA_ARALIGI
    if ilk_uyari or hatirlatma:
        saat = int(yas_dk // 60)
        sure = f"{saat} saat {int(yas_dk % 60)} dakika" if saat else f"{int(yas_dk)} dakika"
        api(token, "sendMessage", chat_id=sahip, text=(
            f"🔴 DevHarbor bekçisi {sure}dır çalışmıyor.\n\n"
            "Bilgisayar kapalı, uykuda ya da internet kesik olabilir.\n"
            "Grup bu sürede kilitli: kimse testsiz giremez, dosya giremez.\n"
            "Ama spam/link taraması ve şikayetler bekçi açılana kadar işlenmez."))
        print("Uyarı gönderildi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
