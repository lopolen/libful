# libful

`libful` — програмний засіб для обліку відвідувань, читачів, книжкового каталогу, примірників книг, видачі книг та штрафів у бібліотеці.

Проєкт складається з REST API на FastAPI та простого веб-інтерфейсу для бібліотекаря й адміністратора.

## Можливості

- облік користувачів бібліотеки;
- реєстрація відвідувань;
- ведення каталогу авторів, жанрів і книг;
- облік фізичних примірників книг;
- видача та повернення книг;
- контроль прострочених видач;
- попередній розрахунок і оплата штрафів;
- рольовий доступ через ролі `admin` і `librarian`;
- окремий веб-інтерфейс для щоденної роботи з API без ручних `curl`-запитів.

## Технології

- Python 3.11 або новіший;
- FastAPI;
- SQLAlchemy;
- Alembic;
- Pydantic;
- SQLite для локальної розробки;
- HTML, CSS і JavaScript без frontend-збірки для `libfull_gui`;
- стандартна бібліотека Python для локального GUI-сервера та API proxy.

## Документація

- Повна API-документація проєкту: [`docs/libful-api/api/API.md`](docs/libful-api/api/API.md).
- Правила структури роутерів: [`docs/libful-api/api/RouterStructure.md`](docs/libful-api/api/RouterStructure.md).
- Ролі та права доступу: [`docs/libful-api/roles/RolesHandling.md`](docs/libful-api/roles/RolesHandling.md).
- Статуси примірників книг: [`docs/libful-api/books/BookCopyStatuses.md`](docs/libful-api/books/BookCopyStatuses.md).
- Дедлайни та штрафи: [`docs/libful-api/books/BookRentFines.md`](docs/libful-api/books/BookRentFines.md).
- Інструкція для веб-інтерфейсу: [`libfull_gui/README.md`](libfull_gui/README.md).

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
7. Перевіряє синтаксис локального GUI-сервера.
8. Створює `requirements.lock.txt` через `pip freeze` для локального знімка встановлених версій.

Після цього API можна запустити так:

```bash
source .venv/bin/activate
uvicorn libful_api.main:app --reload
```

Адреса локального API:

```text
http://127.0.0.1:8000
```

Автоматична документація API:

```text
http://127.0.0.1:8000/docs
```

## Веб-інтерфейс

Окремий простий GUI для бібліотекаря й адміністратора знаходиться в директорії [`libfull_gui`](libfull_gui). Він працює без npm, node чи окремої frontend-збірки.

Після запуску API відкрий GUI в окремому терміналі так:

```bash
python3 libfull_gui/server.py
```

Адреса сторінки:

```text
http://127.0.0.1:8080
```

GUI за замовчуванням проксіює всі запити `/api/v1/...` на `http://127.0.0.1:8000`. У верхній панелі сторінки залиш значення `API` як `/api/v1`, введи логін і пароль користувача API та натисни `Зберегти`.

Якщо API запущений на іншому порту:

```bash
python3 libfull_gui/server.py --api http://127.0.0.1:8001
```

Якщо порт `8080` зайнятий:

```bash
python3 libfull_gui/server.py --port 8081
```

Тоді відкрий:

```text
http://127.0.0.1:8081
```

### Перший запуск системи

Якщо в базі ще немає адміністратора, створи першого користувача через `POST /api/v1/users/` або через GUI у вкладці `Читачі`. API автоматично надасть першому користувачу роль `admin`.

Після появи першого `admin`:

- створювати, оновлювати й видаляти користувачів може тільки користувач з правом `manage_users`;
- додавати й прибирати ролі може тільки `admin`;
- бібліотекар з роллю `librarian` може працювати з каталогом, відвідуваннями, видачами та штрафами, але не керує користувачами і ролями.

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

Запусти GUI:

```bash
python3 libfull_gui/server.py
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
- `/book-rents` — видача, повернення, прострочення та штрафи;
- `/roles` — перегляд стандартних ролей.

Доступ до захищених endpoint-ів виконується через HTTP Basic Auth. Якщо в системі ще немає `admin`, наступний створений користувач автоматично отримує цю роль; далі користувачів і ролі може створювати тільки адміністратор.

Детальний опис запитів, відповідей, помилок і use cases є в [`docs/libful-api/api/API.md`](docs/libful-api/api/API.md).

## Корисні команди

Запуск API в режимі розробки:

```bash
uvicorn libful_api.main:app --reload
```

Запуск веб-інтерфейсу:

```bash
python3 libfull_gui/server.py
```

Запуск веб-інтерфейсу з іншим API:

```bash
python3 libfull_gui/server.py --api http://127.0.0.1:8001
```

Запуск міграцій:

```bash
alembic upgrade head
```

Перевірка поточної версії міграцій:

```bash
alembic current
```

Призначення користувачу ролі `admin` або `librarian` за `id`:

```bash
.venv/bin/python scripts/set_user_role.py 1 admin
.venv/bin/python scripts/set_user_role.py 2 librarian
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
- `libfull_gui` навмисно не має окремих залежностей: сторінка статична, а `server.py` використовує тільки стандартну бібліотеку Python.
- GUI-сервер потрібен не тільки для віддачі HTML, а й для proxy `/api/v1` до FastAPI, щоб браузер не блокував запити через CORS під час локального запуску.
