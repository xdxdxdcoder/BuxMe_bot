# Buxme AI-Scout

Buxme AI-Scout — frontend-only Mini App для MAX, которая помогает менеджерам Buxme находить потенциальных B2B-клиентов с полевыми торговыми командами. MVP создан для трека «Эффективный бизнес» хакатона MAX.

> Все компании, контакты, сигналы, источники, AI Score и AI-тексты в текущей версии являются синтетическими mock-данными. Реальный поиск по 2ГИС, реестрам, сайтам и вакансиям не реализован и не имитируется как работающая интеграция.

## Работающее решение в MAX

- Выданный бот: `@t519_hakaton_max_bot`
- Название: «Хакатон МАХ 519»
- Публичная Mini App: `https://bux-me-bot.vercel.app/`
- Кнопка Mini App: «Открыть» после привязки организаторами.
- Прямая ссылка после привязки: `https://max.ru/t519_hakaton_max_bot?startapp`

На онлайн-этапе название, username и логотип выданного бота не изменяются.

## Назначение и пользователь

Приоритетный пользователь — менеджер Buxme, который ищет компании с потенциально распределённой полевой командой. Сегодня он вручную сопоставляет вакансии, сайты, каталоги и открытые реестры. AI-Scout собирает сигналы в одной карточке, формирует объяснимый приоритет и помогает подготовить первый контакт.

## Основной сценарий

1. Открыть Mini App из бота MAX.
2. Ввести любой непустой код сотрудника — в MVP используется mock-аутентификация.
3. Указать регион, например `Краснодарский край`.
4. Нажать «Найти компании» и увидеть демонстрационные стадии поиска.
5. Отфильтровать результаты или добавить компанию в избранное.
6. Открыть подробную карточку компании.
7. Посмотреть AI Score, причины, сигналы и явно обозначенные демонстрационные источники.
8. Создать mock-оффер или mock-скрипт.
9. Ответить на три вопроса после первого контакта и выполнить mock-пересчёт рейтинга.

Ожидаемый результат: пользователь получает приоритизированную карточку потенциального клиента и готовый следующий шаг для контакта.

## Реализованные возможности

- mobile-first и desktop layout;
- MAX UI и MAX Bridge adapter;
- mock-вход сотрудника;
- поиск региона через изолированный `searchCompanies(region)`;
- loading, skeleton, empty и error states;
- 4 синтетические компании;
- фильтрация и сортировка по AI Score;
- поиск внутри результатов;
- избранное, недавние регионы и статусы;
- подробная карточка компании;
- mock-генерация оффера и скрипта;
- mock-пересчёт оценки после контакта;
- сохранение пользовательского состояния в `localStorage`;
- поддержка MAX BackButton и haptic feedback с безопасным fallback в браузере.

## Архитектура

```text
src/
  app/                       композиция приложения и общее состояние
  components/                переиспользуемый UI
  features/
    auth/                    вход сотрудника
    scout/                   поиск, загрузка и результаты
    company/                 карточка и экран компании
    contact-scoring/         вопросы после контакта
  hooks/                     localStorage и MAX BackButton
  mocks/                     синтетические компании
  services/
    api/                     будущий HTTP adapter
    auth/                    mock/live интерфейсы авторизации
    max/                     MAX Bridge adapter
    scout/                   ScoutService и AI actions
  types/                     TypeScript API-типы
  styles/                    дизайн-система
```

React-компоненты не зависят от источника данных. Сейчас используется `MockScoutService`; будущий backend сможет реализовать тот же `ScoutService` без переписывания UI.

## Стек и зависимости

- React 19, TypeScript, Vite;
- официальный `@maxhub/max-ui`;
- официальный MAX Bridge через `window.WebApp`;
- React Router с `MemoryRouter` — URL fragment остаётся свободным для `WebAppData` MAX;
- Lucide icons;
- Vitest, Testing Library, ESLint;
- Docker и nginx для воспроизводимого production-запуска.

Точные версии зафиксированы в `pnpm-lock.yaml`.

## Запуск одной командой через Docker

Требуются Docker и Docker Compose.

```bash
docker compose up --build
```

После запуска откройте `http://localhost:8080`. Сборка содержит только frontend. Токен бота для локальной проверки не нужен.

### Остановка

```bash
docker compose down
```

### Повторный запуск

```bash
docker compose up --build
```

Используемый локальный порт: `8080`.

## Запуск без Docker

Требуется Node.js 20+ и pnpm. На macOS можно дважды нажать `start.command` либо выполнить:

```bash
./start.command
```

Ручной запуск:

```bash
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

Development URL: `http://localhost:5173`.

Production build:

```bash
pnpm build
pnpm preview
```

## Переменные окружения

Скопируйте `.env.example` в `.env`, если нужно переопределить значения:

```env
VITE_APP_MODE=mock
VITE_API_BASE_URL=
VITE_MAX_BOT_USERNAME=t519_hakaton_max_bot

# Только backend/server-side
BOT_TOKEN=
MAX_WEBHOOK_SECRET=
MAX_API_BASE_URL=https://platform-api2.max.ru
MAX_BOT_USERNAME=t519_hakaton_max_bot
MINI_APP_URL=https://bux-me-bot.vercel.app/
```

Все переменные `VITE_*` публичны и попадают в браузерный bundle. `BOT_TOKEN` и `MAX_WEBHOOK_SECRET` добавляются только в server-side Environment Variables Vercel и никогда не должны иметь префикс `VITE_`.

`.env` добавлен в `.gitignore`, в репозитории находится только `.env.example` без значений секретов.

## MAX-бот и приветствие

Backend для приветствия отделён от React-приложения:

- `api/max/webhook.py` — HTTPS webhook, проверяющий заголовок `X-Max-Bot-Api-Secret`;
- `server/max_client.py` — универсальный асинхронный клиент MAX Bot API на `httpx`;
- `server/certs/russian_trusted_root_ca.pem` — официальный корневой сертификат Минцифры с проверенным SHA-256 fingerprint;
- `server/bot_handler.py` — обработка `bot_started`, `/start` и `/help`;
- `server/config.py` — загрузка конфигурации через `pydantic-settings`;
- `tests/backend/test_bot_handler.py` — unit-тесты сценариев бота.

При запуске бот отправляет краткую инструкцию и кнопку `open_app`, которая открывает привязанную Mini App. Production webhook:

```text
https://bux-me-bot.vercel.app/api/max/webhook
```

После добавления server-side переменных необходимо создать подписку MAX на события `bot_started` и `message_created` через `POST https://platform-api2.max.ru/subscriptions`. Тот же `MAX_WEBHOOK_SECRET`, который передан при создании подписки, должен храниться в Vercel.

Для повторной безопасной регистрации без вывода секретов в терминал:

```bash
python scripts/register_max_webhook.py
```

## Работа с данными

- Источник mock-данных: `src/mocks/companies.ts`.
- Сервис поиска: `src/services/scout/scoutService.ts`.
- Все организации и контакты вымышлены.
- Искусственная задержка демонстрирует будущий асинхронный поиск.
- Стадии проверки источников являются визуальной демонстрацией, а не реальным парсингом.
- AI-оффер, скрипт и пересчёт рейтинга являются mock-функциями.
- Результаты не должны использоваться для принятия реальных коммерческих решений.

## Проверка решения

1. Запустить проект через Docker.
2. Открыть `http://localhost:8080`.
3. Нажать «Войти» с пустым полем и проверить validation error.
4. Ввести `BUX-2048` и войти.
5. Нажать поиск с пустым регионом и проверить validation error.
6. Ввести `Краснодарский край` и запустить поиск.
7. Убедиться, что отображаются стадии поиска и 4 результата.
8. Проверить поиск, фильтр AI Score, сортировку и избранное.
9. Открыть «Кубань Про Дистрибьюшн».
10. Проверить контакты, статус, источники, оффер и скрипт.
11. Заполнить три ответа и пересчитать рейтинг.
12. Повторить проверку на мобильной ширине 390 px и desktop.

Автоматические проверки:

```bash
pnpm lint
pnpm typecheck
pnpm test
pnpm build
python -m unittest discover -s tests/backend
```

## Размещение и подключение к MAX

1. Frontend размещён на Vercel: `https://bux-me-bot.vercel.app/`.
2. Отправить этот постоянный публичный HTTPS URL через официальную форму хакатона: `https://sbor-ssylok-dlya-mini-prilojeniy.testograf.ru/`.
3. Привязку URL к выданному боту выполняют организаторы.
4. После подтверждения открыть `@t519_hakaton_max_bot` и нажать «Открыть».

Самостоятельно регистрироваться в «MAX для партнёров» или менять административные настройки выданного бота не требуется и не разрешается условиями хакатона.

## Внешние сервисы и интеграции

- Vercel — HTTPS-хостинг frontend и Python serverless webhook;
- MAX — среда запуска после привязки организаторами;
- MAX Bridge CDN — интеграция интерфейса с клиентом MAX;
- Google Fonts CDN — загрузка Manrope с системным fallback.

Публичный webhook принимает только события MAX и защищён отдельным секретом. Поисковый backend AI-Scout по-прежнему не подключён.

## Известные ограничения

- поиск компаний, источники и AI-функции смоделированы;
- вход не проверяет внутреннюю учётную запись Buxme;
- данные сохраняются только на устройстве пользователя;
- без привязки организаторами приложение работает как обычный HTTPS-сайт, а не внутри MAX;
- Secure MAX identity validation потребует server-side компонента в следующей версии;
- реальный bot token используется только server-side webhook и не попадает во frontend bundle.

## Безопасность

- рабочие токены и секреты отсутствуют в репозитории и хранятся как sensitive variables Vercel;
- `.env` игнорируется Git;
- URL и внешние действия проходят через MAX Bridge adapter;
- `initDataUnsafe` не используется как доказательство личности;
- зависимости и версии зафиксированы;
- mock-интеграции явно обозначены.

## Масштабирование после MVP

Неизменными остаются UX, модель `Company`, scoring interface и основной сценарий. Для следующей версии потребуется backend-разработчик, серверная проверка MAX `initData`, реальные источники, контроль актуальности данных и API-контракты для поиска, генерации материалов и пересчёта рейтинга.
