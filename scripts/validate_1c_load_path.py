#!/usr/bin/env python3
"""Проверка: выбрана ли правильная папка для загрузки конфигурации 1С."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "1c-config"


def check(path: Path) -> int:
    cfg = path / "Configuration.xml"
    dump = path / "ConfigDumpInfo.xml"
    errors = []
    if not cfg.is_file():
        errors.append(f"Нет Configuration.xml в: {path}")
        if path == ROOT and (ROOT / "1c-config" / "Configuration.xml").is_file():
            errors.append(
                "Вероятно выбран корень репозитория. Укажите папку: 1c-config"
            )
    if not dump.is_file():
        errors.append(f"Нет ConfigDumpInfo.xml в: {path}")
    for d in ("Catalogs", "Documents", "Enums", "Languages"):
        if not (path / d).is_dir():
            errors.append(f"Нет папки {d}/")
    if errors:
        print("ОШИБКА — папка не подходит для загрузки в 1С:\n")
        for e in errors:
            print(f"  • {e}")
        print(f"\nПравильный путь: {CONFIG_DIR}")
        return 1
    print(f"OK — папка готова к загрузке: {path}")
    print("Конфигуратор → Конфигурация → Загрузить конфигурацию из файлов...")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else CONFIG_DIR
    raise SystemExit(check(target.resolve()))
