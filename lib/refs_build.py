# -*- coding: utf-8 -*-
r"""Улов Virlo → папка refs с разобранными роликами (секция 1).

    python refs_build.py <кандидаты.json> <папка-refs> [--top 10] [--only-index]

На входе — список кандидатов из улова, как его отдаёт Virlo:

    [{"url": "...", "author": "@kto", "followers": 20093, "views": 2949031,
      "likes": 104963, "comments": 2000, "published": "2026-08-10",
      "platform": "tiktok", "title": "...", "hook_text": "...",
      "cta": "comment AI", "format": "screen_recording"}, …]

Обязательны только `url`, `views`, `followers` — остальное для индекса.

Что делает:

1. считает силу залёта ln(просмотры/подписчики) * ln(подписчики) и строит
   порядок: top01 — сильнейший (config/trend-criteria.md);
2. пишет `refs/ИНДЕКС.md` — таблицу всего улова: сила, платформа, дата,
   ссылка, хук из машинной разметки, статус разбора;
3. качает первые `--top` в свои папки `refs/topNN/topNN.mp4`;
4. по каждому скачанному прогоняет расшифровку речи и замер ритма,
   складывая всё в ту же папку.

`--only-index` — построить таблицу и ничего не качать: полезно, чтобы
сначала посмотреть глазами, кого берём в разбор.

Сеть трогает только шаг 3. Шаги 1, 2, 4 бесплатны и работают офлайн.
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def virality(views, followers):
    if not views or not followers or followers < 2 or views <= followers:
        return None
    return round(math.log(views / followers) * math.log(followers), 1)


def verdict(force):
    """Словами по шкале из config/trend-criteria.md."""
    if force is None:
        return "—"
    if force >= 35:
        return "исключительное"
    if force >= 25:
        return "очень сильное"
    if force >= 18:
        return "сильное"
    if force >= 10:
        return "заметное"
    return "обычное"


def run(cmd, timeout=900):
    """Возвращает (успех, последняя строка вывода) — без падения всего прогона."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, "не уложился по времени"
    out = (p.stdout or "") + (p.stderr or "")
    tail = [l for l in out.strip().splitlines() if l.strip()]
    return p.returncode == 0, (tail[-1] if tail else "")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, refs = sys.argv[1], sys.argv[2]
    top = 10
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
    only_index = "--only-index" in sys.argv

    with open(src, encoding="utf-8") as f:
        items = json.load(f)

    for it in items:
        it["force"] = virality(it.get("views"), it.get("followers"))
    # Без подписчиков силу не посчитать — такие уходят вниз, но не теряются.
    items.sort(key=lambda i: (i["force"] is None, -(i["force"] or 0)))

    os.makedirs(refs, exist_ok=True)
    rows, log = [], []

    for n, it in enumerate(items, 1):
        it["name"] = "top%02d" % n
        status = "не брали в разбор"
        if n <= top and not only_index:
            folder = os.path.join(refs, it["name"])
            mp4 = os.path.join(folder, it["name"] + ".mp4")
            if os.path.exists(mp4):
                status = "уже был"
            else:
                cmd = [PY, os.path.join(HERE, "downloader.py"),
                       it["url"], refs, it["name"]]
                if it.get("followers"):
                    cmd.append(str(it["followers"]))
                ok, msg = run(cmd)
                status = "скачан" if ok and os.path.exists(mp4) else "не скачался"
                if status == "не скачался":
                    log.append("%s %s — %s" % (it["name"], it["url"], msg[:120]))
            if os.path.exists(mp4):
                ok, _ = run([PY, os.path.join(HERE, "transcribe.py"), mp4])
                status += " · речь" if ok else " · речь не вышла"
                ok, _ = run([PY, os.path.join(HERE, "shotstats.py"), mp4])
                status += " · ритм" if ok else " · ритм не вышел"
        elif n <= top and only_index:
            status = "к разбору"

        it["status"] = status
        hook = (it.get("hook_text") or "").replace("\n", " ")[:60]
        rows.append("| %s | %s | %s | %s | %s | %s | [ссылка](%s) | %s | %s |" % (
            it["name"], it["force"] if it["force"] is not None else "—",
            verdict(it["force"]), it.get("platform", "—"),
            "{:,}".format(it["views"]).replace(",", " ") if it.get("views") else "—",
            it.get("published") or "—", it["url"], hook or "—", status))

    head = [
        "# Индекс улова · refs",
        "",
        "Порядок — по силе залёта `ln(просмотры/подписчики) × ln(подписчики)`.",
        "Шкала: 35+ исключительное · 25–35 очень сильное · 18–25 сильное ·",
        "10–18 заметное · ниже 10 в работу не берём.",
        "",
        "Каждый разобранный ролик лежит в своей папке `topNN/`.",
        "",
        "| № | Сила | Вердикт | Площадка | Просмотры | Дата | Ссылка | Хук машинно | Статус |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    with open(os.path.join(refs, "ИНДЕКС.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(head + rows) + "\n")
        if log:
            f.write("\n## Что не скачалось\n\n" + "\n".join("- " + l for l in log) + "\n")

    print("кандидатов: %d, в разбор: %d" % (len(items), min(top, len(items))))
    for l in log:
        print("не скачалось:", l)


if __name__ == "__main__":
    main()
