# Project Architecture – Odoo 19 (hr_hospital)

---

## 🇬🇧 English Version

### 1. Overview

This project is built on **Odoo 19 (source installation)** with a clean local development architecture that includes:

- Python 3.11 (virtual environment)
- Odoo 19 server
- PostgreSQL database
- Custom modules (hr_hospital)
- PyCharm IDE for development and debugging

All components run locally and are connected via configuration files and controlled runtime context.

---

### 2. Project Structure

odoo-dev/
│
├── venv/                # Python virtual environment
├── odoo/                # Odoo source code
│   ├── odoo-bin         # Main server entry point
│   ├── odoo/            # Core framework
│   ├── addons/          # Official modules
│   └── odoo.conf        # Server configuration
│
├── addons-custom/
│   └── hr_hospital/     # Custom module
│
└── PostgreSQL Database  # odoo_db1

The Odoo server is always started from the root directory of the Odoo repository using `odoo-bin`.

---

### 3. Python Environment

The project uses an isolated virtual environment:

/Users/alex/odoo-dev/venv/bin/python

This ensures:
- Dependency isolation
- Compatibility control
- No interference with system Python

Special attention was given to avoid PYTHONPATH conflicts, especially with the standard `http` module.

---

### 4. Odoo Server Execution

The server is started using:

python odoo-bin -c odoo.conf -d odoo_db1 -u hr_hospital --dev=all

Where:
- `odoo-bin` is the entry point
- `odoo.conf` contains DB and addons configuration
- `odoo_db1` is the PostgreSQL database
- `-u hr_hospital` updates the custom module
- `--dev=all` enables development mode

---

### 5. PostgreSQL Integration

Odoo connects to PostgreSQL via:

- Host: 127.0.0.1
- Port: 5432
- User: odoo
- Database: odoo_db1

The database layer stores:
- Models
- Business data
- Metadata
- Access control

---

### 6. Custom Module Architecture

The `hr_hospital` module is separated from the core and included via `addons_path`.

This guarantees:
- Clean separation of concerns
- Safe upgrades
- Modular development

---

### 7. Context & Actions

During development, special attention was paid to Odoo context behavior:

- `active_id` exists in form view context
- `active_ids` exists in list view with selected records
- Safe pattern: `context.get('active_ids', [])`

This prevents frontend evaluation errors.

---

### 8. Development Environment (PyCharm)

PyCharm is configured with:
- Virtual environment interpreter
- Absolute path to `odoo-bin`
- Correct working directory
- Disabled automatic PYTHONPATH injection

This ensures stable debugging and predictable runtime behavior.

---

### 9. Final Architecture Summary

The final system architecture provides:

- Clean dependency isolation
- Stable runtime execution
- Clear separation between core and custom modules
- Reliable database integration
- Safe context handling

---

## 🇺🇦 Українська версія

### 1. Загальний опис

Проєкт побудований на **Odoo 19 (встановлення з вихідного коду)** з локальною архітектурою розробки, що включає:

- Python 3.11 (віртуальне середовище)
- Сервер Odoo 19
- Базу даних PostgreSQL
- Користувацький модуль hr_hospital
- IDE PyCharm для розробки та налагодження

Усі компоненти працюють локально та взаємодіють через конфігураційні файли.

---

### 2. Структура проєкту

odoo-dev/
│
├── venv/                # Віртуальне середовище Python
├── odoo/                # Вихідний код Odoo
│   ├── odoo-bin         # Точка входу сервера
│   ├── odoo/            # Ядро фреймворку
│   ├── addons/          # Стандартні модулі
│   └── odoo.conf        # Конфігурація сервера
│
├── addons-custom/
│   └── hr_hospital/     # Користувацький модуль
│
└── База PostgreSQL      # odoo_db1

---

### 3. Віртуальне середовище Python

Використовується ізольоване середовище для:
- Контролю залежностей
- Уникнення конфліктів
- Стабільної роботи Odoo

Особливу увагу приділено уникненню конфліктів PYTHONPATH.

---

### 4. Запуск сервера

Сервер запускається через:

python odoo-bin -c odoo.conf -d odoo_db1 -u hr_hospital --dev=all

---

### 5. Інтеграція з PostgreSQL

Odoo підключається до PostgreSQL через локальний сервер (127.0.0.1:5432).  
База даних зберігає всі моделі, бізнес-логіку та права доступу.

---

### 6. Архітектура модуля

Модуль `hr_hospital` ізольований від ядра та підключений через `addons_path`, що забезпечує модульність і безпечні оновлення.

---

### 7. Контекст та дії

Було враховано особливості контексту Odoo:
- active_id — для form view
- active_ids — для list view
- Безпечний виклик через context.get()

---

### 8. Середовище розробки

PyCharm налаштований з правильним інтерпретатором та робочою директорією, без автоматичного втручання в PYTHONPATH.

---

### 9. Підсумок

Архітектура забезпечує:
- Стабільність
- Модульність
- Чисту структуру
- Надійне підключення до БД
- Безпечну роботу контексту
