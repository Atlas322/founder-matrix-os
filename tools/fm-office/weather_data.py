"""Мини хотын бодит цаг агаар: Open-Meteo (түлхүүргүй, үнэгүй). Байршлыг 2 оронтой бутархай хүртэл бүдгэрүүлж (~1 км) илгээнэ.
current(lat, lon) → {"t", "temp", "code", "cloud", "is_day", "precip", "snow", "wind", "sunrise", "sunset", "kind", "label"} — 10 мин cache.
kind: clear | cloudy | overcast | fog | rain | snow | storm  (WMO weather code-оос)
"""
import json, time, urllib.parse, urllib.request

URL = "https://api.open-meteo.com/v1/forecast"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
_cache = {}
AQ_LEVELS = [(50, "сайн"), (100, "дунд"), (150, "мэдрэг хүнд эрүүл бус"), (200, "эрүүл бус"), (300, "маш эрүүл бус"), (10 ** 6, "аюултай")]


def aq_label(aqi):
    """US AQI → монгол шошго (EPA-ийн 6 шат)."""
    a = float(aqi or 0)
    return next(l for lim, l in AQ_LEVELS if a <= lim)


def air(lat, lon):
    q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "timezone": "Asia/Ulaanbaatar", "current": "pm2_5,pm10,us_aqi"})
    with urllib.request.urlopen(urllib.request.Request(f"{AQ_URL}?{q}", headers={"User-Agent": "fm-office/1.0"}), timeout=12) as r:
        c = json.loads(r.read())["current"]
    return {"pm25": c.get("pm2_5"), "pm10": c.get("pm10"), "aqi": c.get("us_aqi"), "aq_label": aq_label(c.get("us_aqi"))}


LABEL = {"clear": "цэлмэг", "cloudy": "үүлэрхэг", "overcast": "бүрхэг", "fog": "манантай", "rain": "бороотой", "snow": "цастай", "storm": "аадар"}


def kind_of(code, cloud=0):
    c = int(code)
    if c in (95, 96, 99):
        return "storm"
    if 71 <= c <= 77 or c in (85, 86):
        return "snow"
    if 51 <= c <= 67 or 80 <= c <= 82:
        return "rain"
    if c in (45, 48):
        return "fog"
    if c == 3 or cloud >= 80:
        return "overcast"
    if c in (1, 2) and cloud >= 35:
        return "cloudy"
    return "clear"


def current(lat, lon, ttl=600):
    key = (round(lat, 2), round(lon, 2))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    q = urllib.parse.urlencode({"latitude": key[0], "longitude": key[1], "timezone": "Asia/Ulaanbaatar", "forecast_days": 1,
                                "current": "temperature_2m,weather_code,cloud_cover,is_day,precipitation,snowfall,wind_speed_10m",
                                "daily": "sunrise,sunset"})
    with urllib.request.urlopen(urllib.request.Request(f"{URL}?{q}", headers={"User-Agent": "fm-office/1.0"}), timeout=12) as r:
        d = json.loads(r.read())
    c = d["current"]
    k = kind_of(c["weather_code"], c.get("cloud_cover", 0))
    out = {"t": c["time"], "temp": c["temperature_2m"], "code": c["weather_code"], "cloud": c.get("cloud_cover", 0), "is_day": c.get("is_day", 1),
           "precip": c.get("precipitation", 0), "snow": c.get("snowfall", 0), "wind": c.get("wind_speed_10m", 0),
           "sunrise": d["daily"]["sunrise"][0], "sunset": d["daily"]["sunset"][0], "kind": k, "label": LABEL[k]}
    try:
        out.update(air(*key))                                  # агаарын чанар (утаа) — алдаа гарвал цаг агаар хэвээр
    except Exception:
        out.update({"pm25": None, "pm10": None, "aqi": None, "aq_label": "—"})
    _cache[key] = (time.time(), out)
    return out
