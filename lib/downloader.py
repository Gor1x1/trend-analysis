# -*- coding: utf-8 -*-
r"""Скачивание чужих роликов для разбора (секция 1, агент ref-downloader).

    python downloader.py <url> [папка-refs] [имя] [подписчиков]

Кладёт каждый ролик в **свою папку**: <папка-refs>\<имя>\<имя>.mp4 плюс
<имя>.meta.json рядом. Туда же потом лягут расшифровка, ритм и контактный
лист — всё, что относится к одному ролику, лежит вместе.

Без второго аргумента — runs\<сегодня>\refs (разбор вне товара),
без третьего — id ролика.

## Если TikTok не качается

Это почти всегда **устаревший yt-dlp**, а не открытый Chrome.
TikTok отдаёт JS-задачу вместо страницы; решать её умеют только свежие
сборки. Симптом — "Unexpected response from webpage request".
Лечение (проверено 22.08.2026, ночная 2026.08.20 решает задачу сама):

    python -m pip install -U --pre "yt-dlp[default]"

Куки Chrome — запасной путь и только для закрытых роликов (приватные,
возрастные, Instagram по подписке). Читаются лишь при закрытом Chrome:
открытый держит базу кук под замком. Скрипт сам проверяет, запущен ли
Chrome, и не тратит попытку впустую.
"""
import json
import math
import os
import subprocess
import sys
from datetime import date, datetime

try:
    import yt_dlp
except ImportError:
    sys.exit("yt-dlp не установлен: python -m pip install yt-dlp")

# Корень завода. На другой машине задаётся переменной FACTORY_DIR,
# чтобы скрипт работал без правки кода.
FACTORY = os.environ.get("FACTORY_DIR") or r"C:\Ferma\factory"

# Старше этого срока сборка yt-dlp считается протухшей: площадки ломают
# экстракторы чаще, чем выходят стабильные релизы.
STALE_DAYS = 21


def chrome_running():
    """Открытый Chrome держит базу кук — попытка с куками бессмысленна."""
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
                             capture_output=True, text=True, timeout=15)
        return "chrome.exe" in out.stdout
    except Exception:
        return False


def build_age_days():
    """Сколько дней сборке yt-dlp. None — если версию не разобрать."""
    try:
        v = yt_dlp.version.__version__.split(".")
        built = datetime(int(v[0]), int(v[1]), int(v[2]))
        return (datetime.now() - built).days
    except Exception:
        return None


def virality(views, followers):
    """Сила залёта по формуле индустрии: ln(просмотры/подписчики) * ln(подписчики).

    35+ исключительное · 25–35 очень сильное · 18–25 сильное ·
    10–18 заметное · ниже 10 в работу не берём (config/trend-criteria.md).
    """
    if not views or not followers or followers < 2 or views <= followers:
        return None
    return round(math.log(views / followers) * math.log(followers), 1)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    refs = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        FACTORY, "runs", date.today().isoformat(), "refs")
    name = sys.argv[3] if len(sys.argv) > 3 else "%(id)s"
    # TikTok и Instagram число подписчиков через yt-dlp не отдают, а без
    # него не посчитать силу залёта. Передаём его из улова Virlo.
    known_followers = None
    if len(sys.argv) > 4:
        try:
            known_followers = int(sys.argv[4])
        except ValueError:
            sys.exit("подписчиков — число, а не %r" % sys.argv[4])

    # Папка на ролик: refs\top01\top01.mp4. Имя с подстановкой (%(id)s)
    # своей папки не получает — она создаётся только под явное имя.
    outdir = os.path.join(refs, name) if "%(" not in name else refs
    os.makedirs(outdir, exist_ok=True)

    opts = {
        "outtmpl": os.path.join(outdir, name + ".%(ext)s"),
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    def grab(extra=None):
        o = dict(opts, **(extra or {}))
        with yt_dlp.YoutubeDL(o) as ydl:
            info = ydl.extract_info(url, download=True)
            return info, ydl.prepare_filename(info)

    try:
        info, path = grab()
    except yt_dlp.utils.DownloadError as first:
        age = build_age_days()
        stale = age is None or age > STALE_DAYS
        # Закрытый ролик (приватный, возрастной, Instagram по подписке) —
        # единственный случай, когда куки помогают. Открытый Chrome
        # держит базу под замком, поэтому даже не пробуем.
        if not chrome_running():
            try:
                info, path = grab({"cookiesfrombrowser": ("chrome",)})
            except yt_dlp.utils.DownloadError:
                info = None
        else:
            info = None
        if info is None:
            hint = []
            if stale:
                hint.append(
                    f'сборке yt-dlp {age if age is not None else "?"} дней — '
                    'обнови ночную: python -m pip install -U --pre "yt-dlp[default]"')
            if chrome_running():
                hint.append("Chrome открыт — куки недоступны; для закрытых "
                            "роликов закрой браузер и повтори")
            sys.exit("не скачалось: %s\n%s" % (first, "\n".join(hint) or
                     "ссылка удалена или закрыта — качать вручную"))

    base, _ = os.path.splitext(path)
    if not os.path.exists(path) and os.path.exists(base + ".mp4"):
        path = base + ".mp4"

    up = info.get("upload_date") or ""
    views = info.get("view_count")
    followers = (known_followers or info.get("channel_follower_count")
                 or info.get("uploader_subscriber_count"))
    meta = {
        "file": path,
        "url": info.get("webpage_url") or url,
        "platform": info.get("extractor_key", "").lower(),
        "title": info.get("title"),
        "author": info.get("uploader") or info.get("channel"),
        "author_url": info.get("uploader_url") or info.get("channel_url"),
        "published": f"{up[:4]}-{up[4:6]}-{up[6:]}" if len(up) == 8 else None,
        "views": views,
        "likes": info.get("like_count"),
        "comments": info.get("comment_count"),
        "followers": followers,
        # Считается здесь, а не глазами: по этому числу аналитик строит
        # порядок разбора и решает, что вообще брать в работу.
        "virality": virality(views, followers),
        "duration_sec": info.get("duration"),
        "downloaded": datetime.now().isoformat(timespec="seconds"),
    }
    with open(base + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    out = json.dumps(meta, ensure_ascii=False, indent=2)
    try:
        print(out)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(out.encode("utf-8"))


if __name__ == "__main__":
    main()
