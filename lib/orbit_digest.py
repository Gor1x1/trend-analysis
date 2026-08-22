# -*- coding: utf-8 -*-
r"""Машинный разбор улова Virlo: доли, хуки, концовки, кандидаты в разбор.

    python orbit_digest.py <ответ-virlo.json> [--top 20] [--json кандидаты.json]

На входе — сырой ответ `get_keyword_search_results(data_type="videos")`,
сохранённый в файл. Считает то, что глазами по сотне роликов не сосчитать:

- **силу залёта** каждого ролика и порядок по ней;
- **доли верхней четверти против нижней** по полям машинной разметки:
  формат, визуальный хук, титры, лицо в кадре, длина речи;
- **хуки дословно** (`hook_text`) с типом и цифрами донора;
- **концовки** (`cta_usages`) — что просят у зрителя и как часто.

`--json` дополнительно выкладывает кандидатов в формате `refs_build.py`,
чтобы сразу скачать топ и разобрать по файлам.

Ничего не тратит: работа идёт по уже оплаченному улову.
"""
import json
import math
import sys
from collections import Counter


def virality(views, followers):
    if not views or not followers or followers < 2 or views <= followers:
        return None
    return round(math.log(views / followers) * math.log(followers), 1)


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    data = d.get("data", d)
    return data.get("videos") or data.get("slideshows") or []


def share(items, getter):
    """Считает доли значений поля — с знаменателем, как требует канон."""
    c = Counter()
    for it in items:
        v = getter(it)
        if v:
            c[v] += 1
    return c


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    # Консоль Windows живёт в cp1251 и давится тире и стрелками.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    vids = load(sys.argv[1])
    top_n = 20
    if "--top" in sys.argv:
        top_n = int(sys.argv[sys.argv.index("--top") + 1])

    for v in vids:
        a = v.get("author") or {}
        v["_followers"] = a.get("followers")
        v["_handle"] = a.get("username")
        v["_force"] = virality(v.get("views"), v["_followers"])
        v["_int"] = v.get("intelligence") or {}

    ranked = sorted([v for v in vids if v["_force"] is not None],
                    key=lambda v: -v["_force"])
    print("роликов в файле: %d · с посчитанной силой: %d" % (len(vids), len(ranked)))
    if not ranked:
        return

    half = max(1, len(ranked) // 4)
    top, bottom = ranked[:half], ranked[-half:]

    print("\n=== ТОП-%d ПО СИЛЕ ЗАЛЁТА ===" % top_n)
    for i, v in enumerate(ranked[:top_n], 1):
        it = v["_int"]
        print("%2d | сила %5.1f | %-9s | %10s просм | %8s подп | %s" % (
            i, v["_force"], v.get("platform"), v.get("views"),
            v["_followers"], "@" + str(v["_handle"])))
        print("     %s" % (v.get("url")))
        print("     формат: %-18s визуал: %-24s титры: %s" % (
            it.get("content_format"), it.get("visual_hook_type"),
            it.get("has_onscreen_captions")))
        hook = (it.get("hook_text") or "").replace("\n", " / ")
        if hook:
            print("     хук [%s]: %s" % (it.get("hook_type"), hook[:150]))
        cta = it.get("cta_usages") or []
        if cta:
            print("     концовка: %s" % "; ".join(
                "%s → %s" % (c.get("type"), (c.get("text") or "")[:60]) for c in cta))
        print("     дата: %s · опубликовано %s" % (
            v.get("publish_date", "")[:10], v.get("upload_region")))

    print("\n=== ВЕРХНЯЯ ЧЕТВЕРТЬ (%d) ПРОТИВ НИЖНЕЙ (%d) ===" % (len(top), len(bottom)))
    fields = [
        ("формат подачи", lambda v: v["_int"].get("content_format")),
        ("визуальный тип первого кадра", lambda v: v["_int"].get("visual_hook_type")),
        ("тип хука", lambda v: v["_int"].get("hook_type")),
        ("что в кадре", lambda v: v["_int"].get("visual_format")),
        ("обстановка", lambda v: v["_int"].get("setting")),
        ("подача речи", lambda v: v["_int"].get("speaking_style")),
        ("эмоция", lambda v: v["_int"].get("emotional_tone")),
    ]
    for label, getter in fields:
        ct, cb = share(top, getter), share(bottom, getter)
        keys = [k for k, _ in (ct + cb).most_common(6)]
        print("\n%s:" % label)
        for k in keys:
            print("   %-26s верх %2d/%-3d  низ %2d/%-3d" % (
                k, ct.get(k, 0), len(top), cb.get(k, 0), len(bottom)))

    for label, getter in [("титры на экране", lambda v: v["_int"].get("has_onscreen_captions")),
                          ("лицо в кадре", lambda v: v["_int"].get("has_face_visible")),
                          ("текст поверх видео", lambda v: v["_int"].get("has_text_overlay"))]:
        t = sum(1 for v in top if getter(v) is True)
        b = sum(1 for v in bottom if getter(v) is True)
        print("\n%-20s верх %d/%d · низ %d/%d" % (label, t, len(top), b, len(bottom)))

    print("\n=== КОНЦОВКИ: ЧТО ПРОСЯТ У ЗРИТЕЛЯ ===")
    cta_types, cta_texts = Counter(), []
    for v in ranked:
        for c in (v["_int"].get("cta_usages") or []):
            cta_types[c.get("type")] += 1
            if c.get("text"):
                cta_texts.append((v["_force"], c.get("type"), c["text"], v.get("url")))
    total_with_cta = sum(1 for v in ranked if v["_int"].get("cta_usages"))
    print("роликов с призывом: %d из %d" % (total_with_cta, len(ranked)))
    for k, n in cta_types.most_common():
        print("   %-14s %d" % (k, n))
    print("\nсильнейшие по силе залёта, дословно:")
    for f, t, text, url in sorted(cta_texts, key=lambda x: -x[0])[:15]:
        print("   %5.1f [%s] «%s»  %s" % (f, t, text.replace("\n", " ")[:70], url))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        cand = [{
            "url": v.get("url"), "platform": v.get("platform"),
            "author": v["_handle"], "followers": v["_followers"],
            "views": v.get("views"), "likes": v.get("likes"),
            "comments": v.get("comments"),
            "published": (v.get("publish_date") or "")[:10],
            "title": (v.get("description") or "")[:120],
            "hook_text": v["_int"].get("hook_text"),
            "format": v["_int"].get("content_format"),
        } for v in ranked[:top_n]]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(cand, f, ensure_ascii=False, indent=1)
        print("\nкандидаты выложены: %s (%d)" % (out, len(cand)))


if __name__ == "__main__":
    main()
