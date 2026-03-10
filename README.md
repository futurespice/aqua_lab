# 🏥 Aqualab Inventory Management System

**Информационная система учета медикаментов и расходных материалов для лаборатории Aqualab**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)

## 📋 Описание проекта

Полноценная система управления складом медикаментов и расходных материалов с современным веб-интерфейсом. Система разработана для упрощения учета, мониторинга остатков, контроля сроков годности и формирования отчетности.

### ✨ Основные возможности

#### 🔐 Аутентификация и безопасность
- Вход в систему с использованием Django Auth
- Разграничение прав доступа
- Защита от CSRF атак

#### 💊 Управление медикаментами
- Полный CRUD функционал
- Учет производителя, дозировки, действующего вещества
- Контроль сроков годности с уведомлениями
- Мониторинг остатков с алертами о низком количестве
- Условия хранения и примечания

#### 🔬 Управление расходными материалами
- Учет различных типов расходников
- Контроль минимальных остатков
- Категоризация материалов
- Расчет общей стоимости на складе

#### 📊 Операции прихода/расхода
- Приход товара на склад
- Расход товара
- Списание просроченных/поврежденных товаров
- Корректировка остатков
- История всех операций с датами и пользователями

#### 📈 Панель управления (Dashboard)
- Визуализация ключевых метрик
- Статистика по категориям
- Алерты о низких остатках
- Уведомления об истекающих сроках годности
- График последних операций

#### 👥 Управление поставщиками
- База данных поставщиков
- Контактная информация
- История поставок

#### 📁 Категории товаров
- Гибкая система категоризации
- Удобная фильтрация по категориям

#### 🎨 Современный UI/UX
- Адаптивный дизайн (Bootstrap 5)
- Интуитивная навигация
- Цветовые индикаторы статусов
- Иконки для быстрого распознавания

#### 🚀 REST API
- Полноценный RESTful API
- Документация OpenAPI/Swagger
- Фильтрация и поиск
- Пагинация результатов

## 🛠 Технологический стек

### Backend
- **Python 3.10+**
- **Django 5.0.1** - веб-фреймворк
- **Django REST Framework 3.14** - API
- **drf-spectacular** - OpenAPI документация
- **SQLite** - база данных (легко мигрируется на PostgreSQL)

### Frontend
- **Bootstrap 5.3** - CSS фреймворк
- **Bootstrap Icons** - иконки
- **jQuery 3.7** - JavaScript библиотека
- **HTML5/CSS3**

### Дополнительные библиотеки
- **python-decouple** - управление конфигурацией
- **crispy-forms** + **crispy-bootstrap5** - красивые формы
- **django-filter** - фильтрация данных
- **django-widget-tweaks** - настройка виджетов форм
- **reportlab** - генерация PDF отчетов
- **openpyxl** - работа с Excel

## 📦 Установка и запуск

### Требования
- Python 3.10 или выше
- pip
- virtualenv (рекомендуется)

### Шаг 1: Клонирование репозитория
```bash
git clone <repository-url>
cd aqua_lab
```

### Шаг 2: Создание виртуального окружения
```bash
# Для Linux/MacOS
python3 -m venv .venv
source .venv/bin/activate

# Для Windows
python -m venv .venv
.venv\Scripts\activate
```

### Шаг 3: Установка зависимостей
```bash
pip install -r requirements.txt
```

### Шаг 4: Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Шаг 5: Применение миграций
```bash
python manage.py makemigrations
python manage.py migrate
```

### Шаг 6: Создание суперпользователя
```bash
python manage.py createsuperuser
```
Введите:
- Имя пользователя (например: admin)
- Email (можно оставить пустым)
- Пароль (минимум 8 символов)

### Шаг 7: Сбор статических файлов
```bash
python manage.py collectstatic --noinput
```

### Шаг 8: Запуск сервера разработки
```bash
python manage.py runserver
```

Сайт будет доступен по адресу: **http://127.0.0.1:8000**

## 🌐 Основные URL-адреса

| Раздел | URL | Описание |
|--------|-----|----------|
| Главная страница | `/` | Панель управления |
| Медикаменты | `/medications/` | Список всех медикаментов |
| Расходники | `/consumables/` | Список расходных материалов |
| Операции | `/transactions/` | История операций |
| Отчеты | `/reports/` | Отчеты и аналитика |
| Админ-панель | `/admin/` | Django Admin |
| API | `/api/` | REST API endpoints |
| API Docs | `/api/docs/` | Swagger документация |
| Вход | `/login/` | Страница входа |

## 📊 Структура проекта

```
aqua_lab/
├── config/                  # Конфигурация Django
│   ├── __init__.py
│   ├── settings.py         # Основные настройки
│   ├── urls.py             # Корневые URL
│   └── wsgi.py             # WSGI приложение
│
├── inventory/              # Основное приложение
│   ├── migrations/         # Миграции БД
│   ├── __init__.py
│   ├── admin.py           # Админ-панель
│   ├── api_urls.py        # API маршруты
│   ├── api_views.py       # API представления
│   ├── apps.py            # Конфигурация приложения
│   ├── forms.py           # Формы Django
│   ├── models.py          # Модели данных
│   ├── serializers.py     # DRF сериализаторы
│   ├── urls.py            # Web маршруты
│   └── views.py           # Web представления
│
├── templates/              # HTML шаблоны
│   ├── base.html          # Базовый шаблон
│   └── inventory/         # Шаблоны приложения
│       ├── dashboard.html
│       ├── login.html
│       ├── medication_*.html
│       └── ...
│
├── static/                 # Статические файлы
├── media/                  # Загружаемые файлы
├── db.sqlite3             # База данных SQLite
├── manage.py              # Django CLI
├── requirements.txt       # Python зависимости
├── .env                   # Переменные окружения
└── README.md             # Документация
```

## 🔧 Основные модели данных

### Category (Категория)
- Название
- Описание

### Supplier (Поставщик)
- Название компании
- Контактное лицо
- Телефон, Email
- Адрес
- Статус активности

### Medication (Медикамент)
- Название
- Категория
- Производитель
- Действующее вещество
- Дозировка
- Единица измерения
- Количество на складе
- Минимальное количество
- Цена
- Срок годности
- Условия хранения

### ConsumableMaterial (Расходный материал)
- Название
- Категория
- Описание
- Единица измерения
- Количество
- Минимальное количество
- Цена

### Transaction (Операция)
- Тип операции (приход/расход/списание/корректировка)
- Тип товара
- Связь с медикаментом/расходником
- Количество
- Цена
- Поставщик
- Пользователь
- Дата операции

## 🎯 API Endpoints

### Медикаменты
```
GET    /api/medications/              - Список медикаментов
POST   /api/medications/              - Создать медикамент
GET    /api/medications/{id}/         - Детали медикамента
PUT    /api/medications/{id}/         - Обновить медикамент
DELETE /api/medications/{id}/         - Удалить медикамент
GET    /api/medications/low_stock/    - Медикаменты с низким остатком
GET    /api/medications/expiring_soon/ - Истекающие медикаменты
GET    /api/medications/expired/      - Просроченные медикаменты
```

### Расходные материалы
```
GET    /api/consumables/              - Список материалов
POST   /api/consumables/              - Создать материал
GET    /api/consumables/{id}/         - Детали материала
PUT    /api/consumables/{id}/         - Обновить материал
DELETE /api/consumables/{id}/         - Удалить материал
GET    /api/consumables/low_stock/    - Материалы с низким остатком
```

### Операции
```
GET    /api/transactions/             - Список операций
POST   /api/transactions/             - Создать операцию
GET    /api/transactions/{id}/        - Детали операции
```

### Другие endpoints
- `/api/categories/` - Категории
- `/api/suppliers/` - Поставщики

## 📱 Использование системы

### 1. Первый вход
После установки:
1. Перейдите на `http://127.0.0.1:8000`
2. Войдите используя учетные данные суперпользователя
3. Вы попадете на панель управления

### 2. Добавление категорий
1. Перейдите в админ-панель `/admin/`
2. Создайте категории (например: Антибиотики, Анальгетики, Лабораторные материалы)

### 3. Добавление поставщиков
1. В админке создайте поставщиков с контактной информацией

### 4. Добавление товаров
1. Перейдите в раздел "Медикаменты" или "Расходные материалы"
2. Нажмите "Добавить"
3. Заполните форму
4. Сохраните

### 5. Создание операций
1. Перейдите в раздел "Операции"
2. Нажмите "Новая операция"
3. Выберите тип операции
4. Выберите товар
5. Укажите количество и цену
6. Сохраните

Система автоматически обновит остатки на складе!

## ⚠️ Важные замечания

### Безопасность
- **Обязательно** измените `SECRET_KEY` в production
- Установите `DEBUG=False` в production
- Используйте HTTPS в production
- Настройте `ALLOWED_HOSTS` для вашего домена
- Используйте PostgreSQL вместо SQLite для production

### Резервное копирование
Регулярно делайте бэкапы базы данных:
```bash
python manage.py dumpdata > backup.json
```

Восстановление:
```bash
python manage.py loaddata backup.json
```

## 🚀 Развертывание в production

### 1. Обновите настройки
В `config/settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Используйте PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aqualab_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Установите дополнительные пакеты
```bash
pip install gunicorn psycopg2-binary
```

### 3. Соберите статику
```bash
python manage.py collectstatic
```

### 4. Запустите с Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 5. Настройте Nginx
Примерный конфиг:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/aqua_lab/staticfiles/;
    }

    location /media/ {
        alias /path/to/aqua_lab/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 Вклад в проект

Если вы хотите внести вклад:
1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Сделайте коммит изменений
4. Отправьте Pull Request

## 📝 Лицензия

Этот проект разработан для лаборатории Aqualab.

## 👨‍💻 Автор

Разработано для лаборатории Aqualab  
Версия: 1.0.0  
Год: 2024

## 📞 Поддержка

При возникновении проблем:
1. Проверьте документацию
2. Посмотрите логи: `python manage.py runserver --verbosity 3`
3. Обратитесь к разработчику

---

**Спасибо за использование Aqualab Inventory Management System! 🏥💊🔬**
