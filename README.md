# Persons Service

Учебный REST API для операций над сущностью Person на Python, FastAPI и PostgreSQL.

Реализованы HTTP API, сервисный слой, Repository, SQLAlchemy-адаптер, Unit of Work,
фабрика приложения и миграция таблицы `persons`.

- [Развёрнутый сервис](https://lab1-template-vn31.onrender.com/api/v1/persons)
- [Swagger UI](https://lab1-template-vn31.onrender.com/docs)
- [GitHub Actions](https://github.com/kkochiyan/lab1-template/actions)

Render используется вместо Heroku.

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

## Проверки через Newman

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

Для проверки развёрнутого сервиса:

```sh
npx --yes newman@6 run 'postman/[inst] Lab1.postman_collection.json' \
  -e 'postman/[inst][heroku] Lab1.postman_environment.json' \
  --delay-request 100 --timeout-request 60000
```

Имя environment-файла сохранено из шаблона задания; `baseUrl` внутри него
указывает на Render.

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

Задания выполняются последовательно: `test → build → deploy`.

- `test` устанавливает зависимости и выполняет проверки Python-проекта.
- `build` начинается только после успешного `test`, собирает и публикует образ.
- `deploy` начинается только после успешного `build`, обновляет Render и запускает Newman.

Последовательность шагов:

1. Устанавливает Python 3.13 и зависимости проекта с инструментами тестирования.
2. Проверяет зависимости и запускает 10 тестов pytest без PostgreSQL.
3. При успешных тестах собирает Docker-образ `persons-service:ci` для `linux/amd64`.
4. Проверяет импорт приложения и наличие маршрута API внутри образа.
5. Для `master` публикует тот же проверенный образ в GHCR с тегами SHA коммита и `latest`.
6. Если `RENDER_DEPLOY_ENABLED=true`, отдельный job передаёт Render API точный
   digest образа (идентификатор его содержимого), ожидает статус `live`
   и готовность API с БД. При старте контейнера выполняются миграции.
7. Запускает Newman и сохраняет JUnit-отчёт в артефактах Actions.

Pull request запускает только тесты и сборку — без публикации и деплоя.
Для деплоя используются REST API и Bearer-токен, без CLI и deploy hooks.
Автоматический деплой включён переменной `RENDER_DEPLOY_ENABLED=true`.
Для проверки результата в Actions должны успешно завершиться все три job —
`test`, `build` и `deploy`, включая шаг Newman. Пропущенный `deploy` не подтверждает
успешное развёртывание.

## Настройки Render

Существующий сервис `srv-darg407avr4c73ehgf8g` переведён с Git-репозитория
на **Existing Image**. Второй Web Service не создавался; URL и база сохранены.
Render запускает готовый образ, собранный в GitHub Actions.

| Настройка | Значение |
|---|---|
| Публичный URL | `https://lab1-template-vn31.onrender.com` |
| Источник | `ghcr.io/kkochiyan/lab1-template:latest` |
| Доступ к пакету GHCR | Public |
| Docker Command | Пустое поле — используется CMD из Dockerfile |
| `DATABASE_URL` | Адрес PostgreSQL с префиксом `postgresql+asyncpg://`, задан в Render |

При автоматическом деплое Actions передаёт конкретный digest, поэтому
развёртывается именно образ текущего прогона, а не произвольная версия `latest`.
Учётные данные PostgreSQL хранятся в настройках Render и не включаются в образ.

В GitHub → Settings → Secrets and variables → Actions настроены:

| Раздел | Имя | Значение |
|---|---|---|
| Repository secrets | `RENDER_API_KEY` | API-ключ Render, без публикации в репозитории |
| Repository variables | `RENDER_SERVICE_ID` | `srv-darg407avr4c73ehgf8g` |
| Repository variables | `RENDER_SERVICE_URL` | `https://lab1-template-vn31.onrender.com` |
| Repository variables | `RENDER_DEPLOY_ENABLED` | `true` |

Для ручного запуска: Actions → **Test, build and deploy** → Run workflow →
`master`. Push в `master` запускает тот же цикл автоматически.

Newman получает URL из `RENDER_SERVICE_URL`, поэтому проверяет именно настроенный
сервис. Скрипт сверяет этот URL с ответом Render API и отказывается деплоить
в сервис, который собирается из Git. Если адрес сервиса изменится, нужно обновить
и `RENDER_SERVICE_URL`, и `baseUrl` в Postman environment.

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
