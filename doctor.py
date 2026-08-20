# -*- coding: utf-8 -*-
r"""Проверка окружения: всё ли готово к первому анализу.

    python doctor.py

Проверяет по очереди: Python, ffmpeg, yt-dlp, faster-whisper, OpenCV,
папку агентов Claude Code и подключение Virlo. По каждому пункту говорит
«готово» или что именно доставить — командой, которую можно скопировать.

Ничего не устанавливает и никуда не ходит платно. Ключ Virlo только
читается из настроек и никуда не отправляется.
"""
import importlib
import json
import os
import shutil
import subprocess
import sys

OK, BAD, WARN = "  готово", "  НЕТ", "  внимание"
problems = []


def say(line):
    try:
        print(line)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((line + "\n").encode("utf-8"))


def check_python():
    v = sys.version_info
    if (v.major, v.minor) >= (3, 10):
        say("Python %d.%d.%d%s" % (v.major, v.minor, v.micro, OK))
    else:
        say("Python %d.%d%s — нужен 3.10 или новее, скачать: python.org"
            % (v.major, v.minor, BAD))
        problems.append("python")


def check_binary(name, hint):
    path = shutil.which(name)
    if path:
        say("%s%s" % (name, OK))
        return True
    say("%s%s — %s" % (name, BAD, hint))
    problems.append(name)
    return False


def check_module(mod, human, install):
    try:
        importlib.import_module(mod)
        say("%s%s" % (human, OK))
        return True
    except ImportError:
        say("%s%s — поставить: %s" % (human, BAD, install))
        problems.append(human)
        return False


def check_ytdlp():
    if not check_module("yt_dlp", "yt-dlp",
                        'python -m pip install -U --pre "yt-dlp[default]"'):
        return
    try:
        from yt_dlp.version import __version__ as ver
    except ImportError:
        import yt_dlp
        ver = getattr(yt_dlp, "__version__", "?")
    # ночная сборка помечается датой с суффиксом; стабильная отстаёт
    if "dev" in ver or len(ver.split(".")) > 3:
        say("     версия %s — ночная сборка, как надо" % ver)
    else:
        say("     версия %s%s — стабильная отстаёт и ломается на TikTok."
            % (ver, WARN))
        say('     обновить: python -m pip install -U --pre "yt-dlp[default]"')


def check_agents():
    home = os.path.expanduser("~")
    folder = os.path.join(home, ".claude", "agents")
    if not os.path.isdir(folder):
        say("агенты Claude Code%s — папки %s нет" % (BAD, folder))
        problems.append("агенты")
        return
    ours = ["trendy-lead.md", "pain-hunter.md", "bank-keeper.md"]
    missing = [a for a in ours if not os.path.exists(os.path.join(folder, a))]
    if missing:
        say("агенты анализа%s — не скопированы: %s" % (BAD, ", ".join(missing)))
        say("     скопируйте файлы из папки agents этого репозитория в %s" % folder)
        problems.append("агенты")
    else:
        total = len([f for f in os.listdir(folder) if f.endswith(".md")])
        say("агенты анализа на месте (всего в папке: %d)%s" % (total, OK))


def check_virlo():
    cfg = os.path.join(os.path.expanduser("~"), ".claude.json")
    if not os.path.exists(cfg):
        say("ключ Virlo%s — нет файла %s" % (BAD, cfg))
        problems.append("virlo")
        return
    try:
        with open(cfg, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        say("ключ Virlo%s — файл настроек не читается (%s)" % (WARN, e))
        return
    servers = data.get("mcpServers") or {}
    for proj in (data.get("projects") or {}).values():
        servers = {**servers, **(proj.get("mcpServers") or {})}
    virlo = next((v for k, v in servers.items() if "virlo" in k.lower()), None)
    if not virlo:
        say("ключ Virlo%s — сервер не прописан в .claude.json" % BAD)
        say("     скажите Claude: «подключи Virlo как MCP-сервер», ключ берётся"
            " в кабинете virlo.ai, раздел API")
        problems.append("virlo")
        return
    has_key = bool((virlo.get("headers") or {}).get("Authorization"))
    say("Virlo подключён%s" % (OK if has_key else BAD + " — нет заголовка Authorization"))
    if not has_key:
        problems.append("virlo")
    else:
        say("     баланс проверяется из Claude: «проверь баланс Virlo» — бесплатно")


def check_ffmpeg():
    if not check_binary("ffmpeg", "скачать с ffmpeg.org и добавить в PATH"):
        return
    try:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        say("     " + out.stdout.split("\n")[0][:70])
    except Exception:
        pass


def main():
    say("Проверка окружения для анализа трендов")
    say("=" * 46)
    check_python()
    check_ffmpeg()
    check_binary("ffprobe", "идёт вместе с ffmpeg")
    check_ytdlp()
    check_module("faster_whisper", "faster-whisper",
                 "python -m pip install faster-whisper")
    check_module("cv2", "OpenCV (ритм планов)",
                 "python -m pip install opencv-python numpy")
    check_agents()
    check_virlo()
    say("=" * 46)
    if problems:
        say("Не готово: %s" % ", ".join(problems))
        say("Почините пункты выше и запустите проверку снова.")
        say("Можно просто показать этот вывод Claude и попросить починить.")
        sys.exit(1)
    say("Всё на месте. Можно запускать: скажите Claude «проанализируй <товар>».")


if __name__ == "__main__":
    main()
