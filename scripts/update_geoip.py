"""Baixa a base de países por IP usada no bloqueio por país (src/judo_chat/geoblock.py).

A base é a "IP to Country Lite" da DB-IP (https://db-ip.com, licença CC BY 4.0), que sai todo
mês e não exige conta, ao contrário da GeoLite2 da MaxMind. O formato é o mesmo (MMDB com
country.iso_code), então JUDO_CHAT_GEOIP_DB pode apontar para uma GeoLite2-Country.mmdb.

Uso: uv run python scripts/update_geoip.py
"""

import gzip
import shutil
import sys
import urllib.error
import urllib.request
from datetime import date

from judo_chat.config import get_settings

_URL = "https://download.db-ip.com/free/dbip-country-lite-{month}.mmdb.gz"


def _months() -> list[str]:
    # No começo do mês a base nova pode ainda não ter saído: tenta a do mês anterior.
    today = date.today()
    previous = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)
    return [today.strftime("%Y-%m"), previous.strftime("%Y-%m")]


def main() -> int:
    target = get_settings().geoip_db
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")
    for month in _months():
        url = _URL.format(month=month)
        try:
            # A Cloudflare na frente da DB-IP devolve 403 para o User-Agent padrão do urllib.
            request = urllib.request.Request(url, headers={"User-Agent": "judo-chat-geoip/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response, open(partial, "wb") as out:
                with gzip.GzipFile(fileobj=response) as unzipped:
                    shutil.copyfileobj(unzipped, out)
        except urllib.error.HTTPError as error:
            print(f"{url}: HTTP {error.code}", file=sys.stderr)
            continue
        partial.replace(target)
        print(f"Base {month} salva em {target}")
        return 0
    partial.unlink(missing_ok=True)
    print("Nenhuma base disponível para baixar.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
