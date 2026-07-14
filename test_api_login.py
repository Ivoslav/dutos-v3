#!/usr/bin/env python3
"""Тест за POST /roster/api/login/ — проверка за JWT или грешка."""

import json
import os
import sys

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dutos_core.settings")
django.setup()

from roster.models import Soldier  # noqa: E402

URL = "http://127.0.0.1:8000/roster/api/login/"
DEFAULT_PASSWORD = "123"


def get_credentials():
    """Взима реален фак. номер от базата (след seed_data: парола 123)."""
    soldier = (
        Soldier.objects.filter(user__isnull=False, is_active=True)
        .select_related("user")
        .first()
    )
    if soldier and soldier.faculty_number:
        return soldier.faculty_number, DEFAULT_PASSWORD
    return None, None


def main():
    username, password = get_credentials()
    if not username:
        print(
            "Няма курсант с Django акаунт. Пусни: python manage.py seed_data",
            file=sys.stderr,
        )
        sys.exit(1)

    device_id = f"TEST-IPHONE-{username}"
    payload = {
        "username": username,
        "password": password,
        "device_id": device_id,
    }

    print(f"Опит за login: username={username!r}, device_id={device_id!r}")

    try:
        response = requests.post(URL, json=payload, timeout=10)
    except requests.RequestException as exc:
        print(f"Грешка при връзка: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"HTTP {response.status_code}")

    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except ValueError:
        print(response.text)
        sys.exit(1)

    if response.status_code == 200 and data.get("tokens"):
        print("\nУспех: сървърът върна JWT токени (access + refresh).")
        print("(Празна таблица AuthorizedDevice не пречи — устройството се създава автоматично.)")
    elif response.status_code == 401:
        print(
            "\n401 = грешен username или парола (Django User), не оторизирано устройство.",
            file=sys.stderr,
        )
        print(
            "Провери в админка: Users → username = фак. номер; Войници → поле „Потребителски акаунт“.",
            file=sys.stderr,
        )
        sys.exit(1)
    elif response.status_code == 403 and "устройство" in data.get("detail", "").lower():
        print(
            "\n403 = device_id вече е регистрирано на друг курсант. "
            "Смени device_id или изтрий записа в AuthorizedDevice.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print("\nГрешка: няма JWT токени в отговора.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
