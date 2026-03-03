<div align="center">

<img src="icon.png" width="120" alt="GoatsPass Logo"/>

# GoatsPass

**Локальный менеджер паролей с шифрованием AES-256-GCM**

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Encryption](https://img.shields.io/badge/encryption-AES--256--GCM-red)

</div>

---

## ✨ Возможности

- 🔒 **AES-256-GCM** шифрование всей базы паролей
- 🧠 **Argon2id** для хеширования мастер-пароля (с fallback на PBKDF2, 600k итераций)
- 📋 Автоочистка буфера обмена через 30 секунд
- 🔑 **TOTP / 2FA** поддержка
- 🎲 Генератор паролей и парольных фраз
- 📊 Анализ надёжности паролей с энтропией
- 🏷️ Категории и теги
- ⭐ Избранное
- 🔍 Поиск по всем полям
- ⏱️ Автоблокировка через 5 минут бездействия
- 💾 Все данные хранятся **только локально**
- 🖥️ Работает на **Windows и Linux**

---

## 🚀 Быстрый старт

### Linux

```bash
git clone https://github.com/necouncil/GoatsPass
cd GoatsPass
chmod +x install.sh
./install.sh
```

Или запустить напрямую (зависимости установятся автоматически):
```bash
python3 goatspass.py
```

### Windows

**Вариант 1 — Готовый EXE** (не требует Python):
> Скачать `GoatsPass.exe` из раздела [Releases](../../releases)

**Вариант 2 — Установщик**:
```
Запустить install.bat от имени пользователя
```

**Вариант 3 — Напрямую** (нужен Python 3.9+):
```cmd
python goatspass.py
```

---

## 📦 Зависимости

Устанавливаются автоматически при первом запуске:

| Пакет | Назначение |
|-------|-----------|
| `cryptography` | AES-256-GCM шифрование |
| `argon2-cffi` | Хеширование мастер-пароля |
| `Pillow` | Отображение иконки |

Или вручную:
```bash
pip install -r requirements.txt
```

---

## 🏗️ Сборка EXE (Windows)

```cmd
python build_exe.py
```

Готовый `GoatsPass.exe` появится в папке `dist/`.

Требует Python + PyInstaller (установится автоматически).

---

## 🔐 Безопасность

- База данных хранится локально: `~/.local/share/GoatsPass/vault.gp` (Linux) / `%APPDATA%\GoatsPass\vault.gp` (Windows)
- Мастер-пароль **никогда** не сохраняется
- При 5 неверных попытках — блокировка
- Буфер обмена очищается автоматически

---

## 📁 Структура проекта

```
GoatsPass/
├── goatspass.py      # Основное приложение
├── icon.png          # Иконка приложения
├── requirements.txt  # Python зависимости
├── install.sh        # Установщик Linux
├── install.bat       # Установщик Windows
├── build_exe.py      # Сборка .exe для Windows
└── README.md
```

---

## 🖥️ Скриншоты

> Экран входа / Менеджер паролей / Генератор

---

## 📄 Лицензия

MIT License — делай что хочешь, на свой страх и риск.

---

<div align="center">
Made with ❤️ by <a href="https://github.com/necouncil">necouncil</a>
</div>
