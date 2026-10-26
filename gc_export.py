"""Выгрузка данных из GetCourse через API экспорта.

Использование: python3 gc_export.py deals 2025-01-01
               python3 gc_export.py users 2020-01-01
               python3 gc_export.py group <group_id>
Результат сохраняется в raw/<имя>.json
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNT = "annaosipova.ru"


def load_key():
    key = os.environ.get("GC_KEY")
    if not key:
        with open(os.path.join(HERE, "КЛЮЧ_API.txt"), encoding="utf-8") as f:
            key = f.read().strip()
    if not key or "ВСТАВЬТЕ" in key:
        sys.exit("Ключ API не найден")
    return key


def call(path, params):
    url = f"https://{ACCOUNT}/pl/api/account/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "club-analytics"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def export(path, params, name):
    key = load_key()
    res = call(path, {"key": key, **params})
    if not res.get("success"):
        sys.exit(f"Ошибка запуска экспорта: {res.get('error_message') or res}")
    export_id = res["info"]["export_id"]
    print(f"Экспорт {name} запущен (id {export_id}), жду файл…", flush=True)
    for attempt in range(120):
        time.sleep(15)
        res = call(f"exports/{export_id}", {"key": key})
        if res.get("success"):
            info = res["info"]
            os.makedirs(os.path.join(HERE, "raw"), exist_ok=True)
            out = os.path.join(HERE, "raw", f"{name}.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False)
            print(f"Готово: {len(info['items'])} строк → {out}")
            return out
        if res.get("error_code") not in (909, 910):
            sys.exit(f"Ошибка получения экспорта: {res.get('error_message') or res}")
    sys.exit("Экспорт не успел сформироваться")


if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "deals":
        export("deals", {"created_at[from]": sys.argv[2]}, "deals")
    elif kind == "users":
        export("users", {"created_at[from]": sys.argv[2]}, "users")
    elif kind == "group":
        export(f"groups/{sys.argv[2]}/users", {}, f"group_{sys.argv[2]}")
