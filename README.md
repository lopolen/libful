# libful

`libful` — програмний засіб для обліку відвідувань, читачів, книжкового каталогу, примірників книг, видачі книг та штрафів у бібліотеці.

Проєкт реалізований як REST API на FastAPI.

## Можливості

- облік користувачів бібліотеки;
- реєстрація відвідувань;
- ведення каталогу авторів, жанрів і книг;
- облік фізичних примірників книг;
- видача та повернення книг;
- контроль прострочених видач;
- попередній розрахунок і оплата штрафів.

## Технології

- Python 3.11 або новіший;
- FastAPI;
- SQLAlchemy;
- Alembic;
- Pydantic;
- SQLite для локальної розробки.

## Документація

- Повна API-документація проєкту: [`docs/libful-api/api/API.md`](docs/libful-api/api/API.md).
- Правила структури роутерів: [`docs/libful-api/api/RouterStructure.md`](docs/libful-api/api/RouterStructure.md).
- Статуси примірників книг: [`docs/libful-api/books/BookCopyStatuses.md`](docs/libful-api/books/BookCopyStatuses.md).
- Дедлайни та штрафи: [`docs/libful-api/books/BookRentFines.md`](docs/libful-api/books/BookRentFines.md).

Після запуску застосунку автоматична Swagger-документація доступна за адресою:

```text
http://127.0.0.1:8000/docs
```

## Первинне налаштування

Найпростіший спосіб підготувати середовище — запустити скрипт:

```bash
bash scripts/setup.sh
```

Скрипт виконує такі дії:

1. Створює віртуальне середовище `.venv`.
2. Оновлює `pip`.
3. Встановлює залежності з `requirements.txt`.
4. Перевіряє файл `libful_api/config/database_url.env`.
5. Якщо конфігурації бази даних немає, створює її з SQLite URL `sqlite:///./dev.db`.
6. Запускає міграції Alembic.
7. Створює `requirements.lock.txt` через `pip freeze` для локального знімка встановлених версій.

Після цього API можна запустити так:

```bash
source .venv/bin/activate
uvicorn libful_api.main:app --reload
```

Адреса локального API:

```text
http://127.0.0.1:8000
```

## Ручне налаштування

Якщо потрібно налаштувати проєкт без скрипта, виконай команди нижче.

Створи та активуй віртуальне середовище:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Онови `pip` і встанови залежності:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Перевір конфігурацію бази даних:

```bash
cat libful_api/config/database_url.env
```

Для локальної розробки достатньо такого значення:

```env
DATABASE_URL=sqlite:///./dev.db
```

Застосуй міграції:

```bash
alembic upgrade head
```

За потреби зафіксуй точні встановлені версії залежностей:

```bash
pip freeze > requirements.lock.txt
```

Запусти сервер:

```bash
uvicorn libful_api.main:app --reload
```

## Робота з базою даних

За замовчуванням локальна база даних зберігається у файлі `dev.db`.

URL бази даних читається з файлу:

```text
libful_api/config/database_url.env
```

Поточне локальне значення:

```env
DATABASE_URL=sqlite:///./dev.db
```

Щоб створити або оновити схему бази даних, використовуй Alembic:

```bash
alembic upgrade head
```

Щоб створити нову міграцію після зміни моделей:

```bash
alembic revision --autogenerate -m "describe change"
```

## Основні endpoint-и

Усі endpoint-и мають базовий префікс:

```text
/api/v1
```

Основні групи API:

- `/users` — користувачі;
- `/check-ins` — відвідування;
- `/authors` — автори;
- `/genres` — жанри;
- `/books` — книги;
- `/book-copies` — фізичні примірники книг;
- `/book-rents` — видача, повернення, прострочення та штрафи.

Детальний опис запитів, відповідей, помилок і use cases є в [`docs/libful-api/api/API.md`](docs/libful-api/api/API.md).

## Корисні команди

Запуск API в режимі розробки:

```bash
uvicorn libful_api.main:app --reload
```

Запуск міграцій:

```bash
alembic upgrade head
```

Перевірка поточної версії міграцій:

```bash
alembic current
```

Створення знімка залежностей:

```bash
pip freeze > requirements.lock.txt
```

## Примітки для розробників

- Віртуальне середовище `.venv` не потрібно комітити.
- `requirements.txt` містить основний список залежностей для встановлення.
- `requirements.lock.txt` є локальним знімком точних версій після встановлення.
- У CRUD endpoint-ах користувачі ідентифікуються через `username`.
- Після зміни моделей потрібно створити й застосувати міграцію Alembic.
