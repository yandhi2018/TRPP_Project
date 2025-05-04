# Итоговый проект по предмету ТРПП по теме Web-разработка: форум по играм.
## Команда состоит из двух человек, а именно: Бражкин Алексей (backend), Мнацаканян Артем (frontend).
---
# Game Forum - форум для геймеров

## Описание проекта
Game Forum - это веб-приложение на Flask, представляющее собой форум для обсуждения компьютерных игр с возможностью торговли игровыми предметами.

## Основные функции
- Регистрация и аутентификация пользователей
- Создание и редактирование постов
- Разделы: обсуждения, гайды, торговая площадка
- Комментирование постов
- Загрузка изображений
- Поиск и фильтрация контента

## Зависимости
- Python 3.8+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Werkzeug
- Flask-Migrate

## Установка и запуск
1. Клонировать репозиторий:
   ```bash
   git clone https://github.com/yandhi2018/forum_app.git
   cd forum_app
   ```
2. Создать виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate     # Windows
   ```
3. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Инициализировать базу данных:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```
5. Запустить приложение:
   ```bash
   flask run
   ```
Приложение будет доступно по адресу: http://127.0.0.1:5000
### Настройка системы сборки
#### Создан файл requirements.txt:
- Flask==2.0.1
- Flask-SQLAlchemy==2.5.1
- Flask-Login==0.5.0
- Flask-Migrate==3.1.0
- Werkzeug==2.0.1
#### Создан файл setup.py:
```python
from setuptools import setup, find_packages

setup(
    name="game_forum",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask>=2.0.1',
        'Flask-SQLAlchemy>=2.5.1',
        'Flask-Login>=0.5.0',
        'Flask-Migrate>=3.1.0',
        'Werkzeug>=2.0.1',
    ],
    python_requires='>=3.8',
)
```
