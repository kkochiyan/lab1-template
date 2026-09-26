# Persons Service

Учебный REST API для операций над сущностью Person на Python, FastAPI и PostgreSQL.

Реализованы HTTP API, сервисный слой, Repository, SQLAlchemy-адаптер, Unit of Work,
фабрика приложения и миграция таблицы `persons`.

## Подготовка окружения

Требуется Python 3.13 или новее. Команды выполняются из корня проекта:

```sh
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

Если `.venv` уже существует, достаточно активировать его и установить зависимости.
Если `.env` уже существует, сохраните его настройки вместо повторного копирования.

В `.env` задайте `DATABASE_URL` для своей PostgreSQL. Значения в примере рассчитаны
на БД `persons` и пользователя `program` с паролем `test` на `localhost:5433`.
Локальный `.env` исключён из Git.

## Запуск

Запустите Docker Desktop. Затем поднимите PostgreSQL и проверьте его готовность:

```sh
docker compose up -d
docker compose exec db pg_isready -U program -d persons
```

После ответа `accepting connections` примените миграции и запустите приложение:

```sh
alembic upgrade head
python -m uvicorn app.main:app --app-dir src --reload --port 8080 --env-file .env
```

API будет доступен по адресу `http://localhost:8080/api/v1/persons`,
документация — `http://localhost:8080/docs`.
При остановке приложение освобождает пул соединений с БД.
Таблицы создаются миграциями, а не автоматически при запуске приложения.

## Тесты

Unit-тесты и HTTP-тесты не требуют запущенного PostgreSQL:

```sh
python -m pytest
```

В наборе 10 основных тестов: операции сервиса, HTTP-ответы, откат UoW
и жизненный цикл приложения.

## Проверка с PostgreSQL

Полный цикл проверен через HTTP на реальном Uvicorn и локальной PostgreSQL:

- создание: `201`, пустое тело и `Location`;
- получение записи и списка: `200` и JSON;
- частичное обновление: пропущенные поля сохраняются, явный `null` очищает поле;
- сохранение изменений после перезапуска процесса приложения;
- удаление: `204` с пустым телом;
- отсутствующая запись: `404` для GET, PATCH и DELETE;
- неверные данные и некорректный JSON: `400` с `message` и `errors`;
- откат незафиксированной записи при ошибке внутри UoW.

Проверочные записи удалены или отменены откатом. Проверка с БД выполнялась
отдельно и не увеличивает набор из 10 автоматических тестов.
Для PATCH поле `name` обязательно согласно заданному OpenAPI.

## Проверки преподавателя через Newman

Оригинальная коллекция `postman/[inst] Lab1.postman_collection.json` проверена
через Newman с PostgreSQL: все 5 запросов и 5 проверок прошли без ошибок.
Коллекция проверяет создание, получение записи и списка, обновление и удаление.

Для повторного запуска нужны Node.js с npm, запущенный PostgreSQL и приложение
на порту `8080`. В отдельном терминале из корня проекта выполните:

```sh
npx --yes newman@6 run 'postman/[inst] Lab1.postman_collection.json' \
  -e 'postman/[inst][local] Lab1.postman_environment.json' \
  --delay-request 100
```

Коллекция создаёт запись, а последним запросом удаляет её. Это отдельная
интеграционная проверка; набор из 10 тестов pytest не изменён.

## Docker-образ приложения

`Dockerfile` подготовлен на основе `python:3.13-slim`. В образ устанавливается
приложение с рабочими зависимостями, добавляются миграции Alembic. Uvicorn
запускается от непривилегированного пользователя на `0.0.0.0` без `--reload`.

Настройки контейнера передаются через переменные окружения:

- `DATABASE_URL` — обязательный адрес PostgreSQL для драйвера `asyncpg`;
- `PORT` — порт сервера, по умолчанию `8080`.

`.dockerignore` исключает локальные секреты, виртуальное окружение и кеши
из контекста сборки. Значение `DATABASE_URL` в образ не записывается.
При запуске приложения в той же Docker-сети, что и Compose-сервис `db`,
адрес БД будет `postgresql+asyncpg://program:test@db:5432/persons`.
`localhost` внутри контейнера обозначает сам контейнер.

Согласно заданию образ должен собираться только в GitHub Actions.
Сборка настроена в `.github/workflows/build.yml`. Текущий Compose запускает
только PostgreSQL. В Docker-образе команда запуска сначала выполняет
`python -m alembic upgrade head`, затем запускает Uvicorn. При ошибке миграции
сервер не запускается. При локальном запуске без Docker миграции выполняются вручную.

## GitHub Actions

Workflow `.github/workflows/build.yml` запускается при push в `master`,
при pull request в эту ветку и вручную через вкладку Actions:

1. Устанавливает Python 3.13 и зависимости проекта с инструментами тестирования.
2. Проверяет зависимости и запускает 10 тестов pytest без PostgreSQL.
3. При успешных тестах собирает Docker-образ `persons-service:ci` для `linux/amd64`.
4. Проверяет импорт приложения и наличие маршрута API внутри образа.

5. Для `master` публикует тот же проверенный образ в GHCR с тегами SHA коммита и `latest`.
6. Если `RENDER_DEPLOY_ENABLED=true`, отдельный job передаёт Render API точный
   digest образа, ожидает статус `live` и готовность API с БД.
7. Запускает Newman и сохраняет JUnit-отчёт в артефактах Actions.

Pull request запускает только тесты и сборку — без публикации и деплоя.
Для деплоя используются REST API и Bearer-токен, без CLI и deploy hooks.
Автоматический деплой пока выключен: настройте параметры ниже.

## Подключение Render

Render используется вместо Heroku по согласованию с преподавателем.
Текущий адрес: https://lab1-template-vn31.onrender.com.
Текущий сервис `srv-darg407avr4c73ehgf8g` подключён к Git-репозиторию.
Такой режим собирает образ на Render, поэтому для требования «сборка только
в GitHub Actions» нужен сервис **Existing Image**.

Порядок первоначальной настройки:

1. Отправить изменения в `master` и дождаться успешного job `build`.
   Он опубликует `ghcr.io/kkochiyan/lab1-template:latest`.
2. В GitHub открыть профиль → Packages → `lab1-template` → Package settings.
   Для доступа Render сделать образ Public либо настроить в Render credential
   с GitHub-токеном `read:packages`. По умолчанию новый пакет приватный.
3. В Render создать Web Service → **Existing Image** с адресом образа выше.
   Выбрать регион существующей БД и подходящий тариф, добавить `DATABASE_URL`
   с префиксом `postgresql+asyncpg://` из настроек текущего сервиса.
   Поле **Docker Command оставить пустым**, чтобы использовать команду из образа.
   Старый сервис и БД не удалять до проверки нового.
4. В GitHub Settings → Secrets and variables → Actions добавить secret
   `RENDER_API_KEY` (Render → Account Settings → API Keys).
5. В разделе Variables добавить:

   | Имя | Значение |
   |---|---|
   | `RENDER_SERVICE_ID` | ID сервиса Existing Image (`srv-...`) |
   | `RENDER_SERVICE_URL` | Его публичный адрес `https://...onrender.com` |
   | `RENDER_DEPLOY_ENABLED` | `true` |

6. Если URL изменился, обновить `baseUrl` в
   `postman/[inst][heroku] Lab1.postman_environment.json`. Название файла оставлено
   для совместимости с шаблоном, внутри указано окружение Render.
7. Запустить workflow **Test, build and deploy** через Actions → Run workflow
   на ветке `master`. Последующие push в `master` выполнят весь цикл автоматически.

Newman получает URL из `RENDER_SERVICE_URL`, поэтому проверяет именно настроенный
сервис. Скрипт сверяет этот URL с ответом Render API и отказывается деплоить
в Git-backed сервис. Пока нет ключа и сервиса Existing Image, автоматический
деплой не считается проверенным. Обычные тесты и публикация образа работают
без Render API key.

Шаблонный `classroom.yml` сохранён с ручным запуском. Он содержит интеграцию
с системой оценивания преподавателя и не нужен для обычного деплоя.
Его запуск требует отдельной настройки преподавательских секретов.

Документация: [Render Existing Image](https://render.com/docs/deploying-an-image),
[Render Deploy API](https://api-docs.render.com/reference/create-deploy),
[GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## Структура

```text
src/app/
├── main.py              # Фабрика приложения и точка входа
├── config.py            # Настройки из окружения и .env
├── dependencies.py      # Предоставление сервиса маршрутам
├── db/                  # Подключение, ORM-модели и реализация UoW
├── services/            # Операции приложения
├── uow/                 # Интерфейс Unit of Work
├── repositories/        # Операции хранения
└── routers/             # HTTP-маршруты и схемы
```

Деплой описан в `scripts/deploy_render.py`, запускаемом из GitHub Actions.
