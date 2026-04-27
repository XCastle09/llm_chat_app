# LLM Chat Application

Чат-приложение с интеграцией локальной языковой модели (LLM), разработанное в рамках курсовой работы по предмету "Web Application Development".

## 📋 О проекте

Приложение представляет собой аналог ChatGPT, где пользователи могут:
- Регистрироваться и входить в систему (логин/пароль или через GitHub)
- Создавать несколько чатов
- Задавать вопросы и получать ответы от локальной языковой модели (LLM)
- Просматривать историю диалогов

Все данные сохраняются в PostgreSQL, а сессии пользователей защищены с помощью JWT токенов.

---

## 🛠 Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.12 + FastAPI |
| База данных | PostgreSQL 16 |
| Миграции | Alembic |
| Кэш и сессии | Redis |
| Аутентификация | JWT (access + refresh) |
| OAuth 2.0 | GitHub OAuth |
| LLM | llama-cpp-python + Saiga YandexGPT 8B (GGUF) |
| Фронтенд | SPA (HTML, CSS, JavaScript) |

---

## 🏗 Архитектура

### Выбранный подход: **SPA + MCS**

- **SPA (Single-Page Application)** – фронтенд загружается один раз, все взаимодействия с сервером происходят через `fetch API`, страница не перезагружается.
- **MCS (Model-Controller-Service)** – серверная архитектура, где:
  - **Model** (модели) – SQLAlchemy, описывают структуру БД (файл `models.py`)
  - **Controller** (контроллеры) – роутеры FastAPI, только маршрутизация (папка `routers/`)
  - **Service** (сервисы) – вся бизнес-логика (папка `services/`)

### Как работают JWT + Refresh токены + Redis:
Пользователь входит (POST /auth/login)
↓

Сервер создаёт:

Access token (срок жизни 15 минут) – для доступа к API

Refresh token (срок жизни 30 дней) – для обновления access токена
↓

Refresh token сохраняется в Redis по ключу refresh:{user_id}
с TTL 30 дней
↓

Клиент хранит оба токена в localStorage
↓

При каждом запросе клиент отправляет Access token в заголовке
Authorization: Bearer {access_token}
↓

При истечении Access token (ошибка 401):

Клиент отправляет Refresh token на /auth/refresh

Сервер проверяет Refresh token в Redis

Если валиден – выдаёт новый Access token
↓

Если Refresh token истёк или не найден в Redis –
пользователь должен войти заново

text

---

## 📁 Структура кода
llm_chat_app/
├── app/
│ ├── init.py
│ ├── main.py # FastAPI приложение
│ ├── config.py # Загрузка .env
│ ├── database.py # SQLAlchemy engine + session
│ ├── models.py # Модели: User, Chat, Message
│ ├── schemas.py # Pydantic схемы
│ ├── dependencies.py # get_current_user (JWT проверка)
│ ├── redis_client.py # Подключение к Redis
│ ├── llm_service.py # Загрузка GGUF модели
│ │
│ ├── routers/ # КОНТРОЛЛЕРЫ (только маршруты)
│ │ ├── auth.py # /auth/* эндпоинты
│ │ ├── chats.py # /chats/* эндпоинты
│ │ └── ask.py # /ask эндпоинт
│ │
│ ├── services/ # СЕРВИСЫ (бизнес-логика)
│ │ ├── auth_service.py # JWT, хэширование, Redis
│ │ ├── chat_service.py # Работа с чатами
│ │ └── llm_chat_service.py # LLM + сохранение сообщений
│ │
│ └── static/ # SPA фронтенд
│ ├── index.html
│ ├── style.css
│ └── script.js
│
├── models/ # GGUF файлы LLM
├── migrations/ # Alembic миграции
├── requirements.txt
├── .env.example # Пример переменных окружения
├── .gitignore
└── README.md

---

## 🚀 Инструкция по запуску

### Требования

- Windows 11 / 10 / macOS / Linux
- Python 3.10 или 3.11 (рекомендуется) / 3.12
- PostgreSQL 16 (установлен и запущен)
- Redis (установлен и запущен)
- 8+ ГБ оперативной памяти (для работы LLM)

---

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/XCastle09/llm_chat_app.git
cd llm_chat_app

### Шаг 2: Создание виртуального окружения

python -m venv venv
Активация:

Windows: venv\Scripts\activate

macOS/Linux: source venv/bin/activate

### Шаг 3: Установка зависимостей

pip install -r requirements.txt

### Шаг 4: Настройка переменных окружения
Скопируйте .env.example в .env:

copy .env.example .env   # Windows
cp .env.example .env      # macOS/Linux
Откройте файл .env и заполните свои значения:

env
# PostgreSQL (замените your_password на ваш пароль)
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/llm_chat
SYNC_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/llm_chat

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret Key (сгенерируйте командой ниже)
SECRET_KEY=your_generated_secret_key_here

# GitHub OAuth (заполните после регистрации приложения)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# Путь к LLM модели
LLM_MODEL_PATH=./models/your_model.gguf
Как сгенерировать SECRET_KEY:

python -c "import secrets; print(secrets.token_urlsafe(32))"

### Шаг 5: Настройка баз данных
PostgreSQL:
Войдите в psql:

bash
psql -U postgres -h localhost -p 5432
Введите пароль, затем создайте базу данных:

sql
CREATE DATABASE llm_chat;
\q
Примените миграции Alembic:
bash
alembic upgrade head
Redis:
Убедитесь, что Redis запущен. Проверка:

bash
redis-cli ping
# Должен ответить PONG
### Шаг 6: Скачивание LLM модели
Скачайте GGUF модель (рекомендуется Saiga YandexGPT 8B) с Hugging Face

Поместите файл .gguf в папку models/

Укажите путь в .env (переменная LLM_MODEL_PATH)

### Шаг 7: Запуск приложения
bash
uvicorn app.main:app --reload --port 8000
Откройте браузер: http://localhost:8000

### Шаг 8: Настройка GitHub OAuth (опционально)
Перейдите на GitHub → Settings → Developer settings → OAuth Apps

Нажмите New OAuth App

Заполните:

Application name: LLM Chat App

Homepage URL: http://localhost:8000

Authorization callback URL: http://localhost:8000/auth/github/callback

Скопируйте Client ID и Client Secret в файл .env

Перезапустите сервер