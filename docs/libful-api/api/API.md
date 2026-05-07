# Документація API libful

`libful API` — це REST API для обліку користувачів бібліотеки, відвідувань, книжкового каталогу, фізичних примірників книг, видачі книг та штрафів.

Базовий префікс поточної версії API:

```text
/api/v1
```

Автоматична OpenAPI/Swagger-документація доступна за стандартними адресами FastAPI:

- `/docs`
- `/redoc`
- `/openapi.json`

## Веб-інтерфейс

Для ручної роботи бібліотекаря й адміністратора в репозиторії є простий GUI:

```text
libfull_gui/
```

GUI використовує ті самі endpoint-и, які описані в цій документації. Він не має окремої backend-логіки для бібліотечних операцій: усі створення, пошуки, видачі, повернення, штрафи й ролі виконуються через `libful API`.

Локальний запуск:

```bash
python3 libfull_gui/server.py
```

Адреса сторінки:

```text
http://127.0.0.1:8080
```

За замовчуванням `server.py` проксіює браузерні запити `/api/v1/...` на FastAPI за адресою:

```text
http://127.0.0.1:8000
```

Тому у верхній панелі GUI поле `API` зазвичай має залишатися:

```text
/api/v1
```

Якщо FastAPI працює на іншій адресі, GUI-сервер можна запустити з параметром `--api`:

```bash
python3 libfull_gui/server.py --api http://127.0.0.1:8001
```

Авторизація в GUI виконується через HTTP Basic Auth: введені логін і пароль додаються до кожного запиту як заголовок `Authorization`. Остаточну перевірку прав завжди виконує API.

## Загальні правила

API приймає та повертає JSON. Для `POST` і `PATCH` запитів потрібно передавати тіло запиту з заголовком:

```http
Content-Type: application/json
```

Дати й час передаються у форматі ISO 8601:

```text
2026-05-07T12:30:00Z
```

Пагінація для списків виконується через query-параметри:

- `limit` — кількість записів, від 1 до 100.
- `offset` — кількість записів, які треба пропустити; мінімальне значення `0`.

Для частини endpoint-ів `limit` є необов'язковим. Якщо його не передати, API повертає всі записи після `offset`. Для `GET /users/search` значення `limit` за замовчуванням дорівнює `20`.

## Авторизація та права доступу

API використовує HTTP Basic Auth. У запиті треба передавати `username` і пароль користувача:

```bash
curl -u admin:secret http://localhost:8000/api/v1/users/
```

Якщо в системі ще немає жодного користувача з роллю `admin`, наступний створений користувач може бути створений без авторизації через `POST /api/v1/users/`; він автоматично отримує роль `admin`. Після появи першого адміністратора створення користувачів вимагає право `manage_users`.

Стандартні ролі:

- `admin` — має всі права.
- `librarian` — може читати користувачів, працювати з каталогом, відвідуваннями, видачами й штрафами, але не може керувати користувачами та ролями.

Користувач без ролей не має доступу до захищених операцій.

Основні права:

| Право | Що дозволяє |
| --- | --- |
| `read_users` | Читати та шукати користувачів, переглядати ролі |
| `manage_users` | Створювати, оновлювати й видаляти користувачів |
| `manage_roles` | Додавати й прибирати ролі користувачів |
| `read_catalog` | Читати авторів, жанри, книги й примірники |
| `manage_catalog` | Створювати, оновлювати й видаляти об'єкти каталогу |
| `manage_check_ins` | Працювати з відвідуваннями |
| `manage_book_rents` | Видавати, повертати книги, змінювати дедлайни й дивитися історію |
| `manage_fines` | Переглядати, попередньо рахувати й оплачувати штрафи |

## Типові HTTP-статуси

- `200 OK` — запит успішно виконано.
- `201 Created` — ресурс створено.
- `204 No Content` — ресурс видалено, тіло відповіді відсутнє.
- `401 Unauthorized` — відсутні або неправильні Basic Auth credentials.
- `403 Forbidden` — користувач автентифікований, але не має потрібного права.
- `404 Not Found` — ресурс або пов'язаний ресурс не знайдено.
- `409 Conflict` — конфлікт бізнес-правил або унікальності.
- `422 Unprocessable Entity` — помилка валідації payload, query-параметрів або доменного статусу.

Типова помилка FastAPI має поле `detail`:

```json
{
  "detail": "User not found"
}
```

## Користувачі

Користувачі ідентифікуються в CRUD endpoint-ах через `username`.

### Модель користувача

Відповідь `UserRead`:

```json
{
  "id": 1,
  "username": "reader01",
  "first_name": "Олена",
  "last_name": "Коваль",
  "email": "olena@example.com",
  "phone": "+380501112233",
  "created_at": "2026-05-07T12:30:00",
  "roles": [
    {
      "id": 1,
      "name": "admin"
    }
  ]
}
```

Поле `password` можна передавати під час створення або оновлення, але API не повертає пароль чи `password_hash`.
Поле `roles` у відповіді показує поточні ролі користувача.

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/users/` | Створити користувача |
| `GET` | `/api/v1/users/` | Отримати список користувачів |
| `GET` | `/api/v1/users/search` | Знайти користувачів за фільтрами |
| `GET` | `/api/v1/users/{username}` | Отримати користувача за username |
| `PATCH` | `/api/v1/users/{username}` | Частково оновити користувача |
| `DELETE` | `/api/v1/users/{username}` | Видалити користувача |
| `GET` | `/api/v1/users/{username}/roles` | Отримати ролі користувача |
| `PUT` | `/api/v1/users/{username}/roles/{role_name}` | Додати роль користувачу |
| `DELETE` | `/api/v1/users/{username}/roles/{role_name}` | Прибрати роль користувача |

### Створення користувача

`POST /api/v1/users/`

Тіло запиту:

```json
{
  "username": "reader01",
  "first_name": "Олена",
  "last_name": "Коваль",
  "email": "olena@example.com",
  "phone": "+380501112233",
  "password": "secret",
  "roles": ["librarian"]
}
```

Обов'язкові поля:

- `username`
- `first_name`
- `last_name`

Валідація:

- `username`, `first_name`, `last_name`: 1-100 символів.
- `email`: до 255 символів, якщо передано.
- `phone`: до 30 символів, якщо передано.
- `password`: необов'язковий, але якщо передано, має містити хоча б 1 символ.
- `roles`: необов'язковий список значень `admin` або `librarian`.
- `username`, `email` і `phone` мають бути унікальними серед користувачів, якщо передані.

Якщо в системі немає адміністратора, створений користувач автоматично отримує `admin`. Після цього створення користувачів потребує права `manage_users`.
Користувачі з ролями повинні мати пароль; інакше вони не зможуть пройти Basic Auth, тому API повертає `422 Unprocessable Entity`.

Можливі помилки:

- `401 Unauthorized` — credentials не передані або неправильні.
- `403 Forbidden` — користувач не має права `manage_users`.
- `409 Conflict` — користувач із таким `username`, `email` або `phone` уже існує.
- `422 Unprocessable Entity` — некоректний email або payload.

### Список користувачів

`GET /api/v1/users/?limit=20&offset=0`

Query-параметри:

- `limit`: необов'язковий, 1-100.
- `offset`: необов'язковий, за замовчуванням `0`.

### Пошук користувачів

`GET /api/v1/users/search`

Query-параметри:

- `id`
- `first_name`
- `last_name`
- `email`
- `phone`
- `limit`, за замовчуванням `20`
- `offset`, за замовчуванням `0`

Текстові поля шукаються частковим збігом без урахування регістру. Якщо передати кілька фільтрів, вони застосовуються одночасно.

Приклад:

```http
GET /api/v1/users/search?last_name=Коваль&limit=10
```

### Оновлення користувача

`PATCH /api/v1/users/{username}`

Тіло може містити будь-яку підмножину полів:

```json
{
  "username": "reader01-new",
  "email": "new-email@example.com",
  "phone": "+380501112244"
}
```

Якщо передати новий `username`, наступні CRUD-запити до цього користувача мають використовувати вже нове значення.

### Ролі користувача

`GET /api/v1/users/{username}/roles`

Відповідь:

```json
[
  {
    "id": 1,
    "name": "admin"
  }
]
```

`PUT /api/v1/users/{username}/roles/librarian` додає роль користувачу.

`DELETE /api/v1/users/{username}/roles/librarian` прибирає роль користувача.

Дозволені `role_name`:

- `admin`
- `librarian`

Додавати й прибирати ролі може тільки `admin`. API повертає `409 Conflict`, якщо операція видалила б останнього адміністратора.
Якщо користувач не має пароля, додавання ролі повертає `422 Unprocessable Entity`.

## Ролі

### Модель ролі

```json
{
  "id": 1,
  "name": "admin"
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `GET` | `/api/v1/roles/` | Отримати список стандартних ролей |

## Відвідування

Відвідування зберігають факт приходу користувача до бібліотеки.

### Модель відвідування

```json
{
  "id": 1,
  "user_id": 1,
  "check_in_datetime": "2026-05-07T12:30:00"
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/check-ins/` | Створити запис відвідування |
| `GET` | `/api/v1/check-ins/` | Отримати список відвідувань |
| `GET` | `/api/v1/check-ins/users/{user_id}/count` | Порахувати відвідування користувача |
| `DELETE` | `/api/v1/check-ins/{check_in_id}` | Видалити запис відвідування |

### Створення відвідування

`POST /api/v1/check-ins/`

```json
{
  "user_id": 1,
  "check_in_datetime": "2026-05-07T12:30:00Z"
}
```

Обов'язкове поле:

- `user_id`

`check_in_datetime` необов'язкове. Якщо не передати дату й час, сервіс створить запис з дефолтним значенням, визначеним у моделі або базі даних.

Можливі помилки:

- `404 Not Found` — користувача не знайдено.
- `422 Unprocessable Entity` — некоректний `user_id` або дата.

### Список відвідувань

`GET /api/v1/check-ins/?user_id=1&limit=50&offset=0`

Query-параметри:

- `user_id`: необов'язковий фільтр за користувачем.
- `limit`
- `offset`

Якщо `user_id` передано, але такого користувача не існує, API повертає `404 Not Found`.

### Кількість відвідувань користувача

`GET /api/v1/check-ins/users/{user_id}/count`

Відповідь:

```json
{
  "user_id": 1,
  "attendance_count": 12
}
```

## Автори

### Модель автора

```json
{
  "id": 1,
  "full_name": "Леся Українка"
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/authors/` | Створити автора |
| `GET` | `/api/v1/authors/` | Отримати список авторів |
| `GET` | `/api/v1/authors/{author_id}` | Отримати автора |
| `PATCH` | `/api/v1/authors/{author_id}` | Оновити автора |
| `DELETE` | `/api/v1/authors/{author_id}` | Видалити автора |

### Створення автора

`POST /api/v1/authors/`

```json
{
  "full_name": "Леся Українка"
}
```

Валідація:

- `full_name`: 1-100 символів.

## Жанри

### Модель жанру

```json
{
  "id": 1,
  "name": "Поезія"
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/genres/` | Створити жанр |
| `GET` | `/api/v1/genres/` | Отримати список жанрів |
| `GET` | `/api/v1/genres/{genre_id}` | Отримати жанр |
| `PATCH` | `/api/v1/genres/{genre_id}` | Оновити жанр |
| `DELETE` | `/api/v1/genres/{genre_id}` | Видалити жанр |

### Створення жанру

`POST /api/v1/genres/`

```json
{
  "name": "Поезія"
}
```

Валідація:

- `name`: 1-100 символів.

## Книги

Книга описує бібліографічну одиницю каталогу. Фізичні примірники зберігаються окремо в `/book-copies`.

### Модель книги

```json
{
  "id": 1,
  "title": "Лісова пісня",
  "author_id": 1,
  "publish_year": 1911,
  "genre_id": 1,
  "isbn": "9780000000001",
  "created_at": "2026-05-07T12:30:00"
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/books/` | Створити книгу |
| `GET` | `/api/v1/books/` | Отримати список книг |
| `GET` | `/api/v1/books/search` | Знайти книги |
| `GET` | `/api/v1/books/{book_id}` | Отримати книгу |
| `GET` | `/api/v1/books/{book_id}/copies/count` | Порахувати примірники книги |
| `PATCH` | `/api/v1/books/{book_id}` | Оновити книгу |
| `DELETE` | `/api/v1/books/{book_id}` | Видалити книгу |

### Створення книги

`POST /api/v1/books/`

```json
{
  "title": "Лісова пісня",
  "author_id": 1,
  "publish_year": 1911,
  "genre_id": 1,
  "isbn": "9780000000001"
}
```

Обов'язкові поля:

- `title`
- `author_id`
- `genre_id`

Валідація:

- `title`: 1-100 символів.
- `author_id`: існуючий автор, значення від 1.
- `genre_id`: існуючий жанр, значення від 1.
- `publish_year`: необов'язковий, від 0.
- `isbn`: необов'язковий, 1-20 символів, має бути унікальним.

Можливі помилки:

- `404 Not Found` — автора або жанр не знайдено.
- `409 Conflict` — книга з таким ISBN уже існує.

### Пошук книг

`GET /api/v1/books/search?title=лісова&author=українка&isbn=978`

Query-параметри:

- `title`
- `author`
- `isbn`
- `limit`
- `offset`

Текстові поля шукаються частковим збігом без урахування регістру.

### Кількість примірників книги

`GET /api/v1/books/{book_id}/copies/count`

Відповідь:

```json
{
  "book_id": 1,
  "copies_count": 3
}
```

## Примірники книг

Примірник книги — це фізична копія книги з інвентарним номером і статусом.

### Дозволені статуси

- `available` — доступний для видачі.
- `borrowed` — виданий користувачу.
- `lost` — втрачений.
- `damaged` — пошкоджений.

### Модель примірника

```json
{
  "id": 1,
  "book_id": 1,
  "inventory_number": "INV-0001",
  "status": "available",
  "created_at": "2026-05-07T12:30:00"
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/book-copies/` | Створити примірник |
| `GET` | `/api/v1/book-copies/` | Отримати список примірників |
| `GET` | `/api/v1/book-copies/{book_copy_id}` | Отримати примірник |
| `PATCH` | `/api/v1/book-copies/{book_copy_id}` | Оновити примірник |
| `DELETE` | `/api/v1/book-copies/{book_copy_id}` | Видалити примірник |

### Створення примірника

`POST /api/v1/book-copies/`

```json
{
  "book_id": 1,
  "inventory_number": "INV-0001",
  "status": "available"
}
```

Обов'язкові поля:

- `book_id`
- `inventory_number`
- `status`

Валідація:

- `book_id`: існуюча книга, значення від 1.
- `inventory_number`: 1-50 символів, має бути унікальним.
- `status`: одне зі значень `available`, `borrowed`, `lost`, `damaged`.

Можливі помилки:

- `404 Not Found` — книгу не знайдено.
- `409 Conflict` — примірник із таким інвентарним номером уже існує.
- `422 Unprocessable Entity` — некоректний статус.

### Список примірників

`GET /api/v1/book-copies/?book_id=1&status=available&limit=20&offset=0`

Query-параметри:

- `book_id`
- `status`
- `limit`
- `offset`

Якщо передати `book_id`, API перевіряє існування книги. Якщо книги немає, повертається `404 Not Found`.

## Видача книг, повернення та штрафи

Endpoint-и `/book-rents` описують доменні операції: видачу примірника користувачу, повернення, історію, прострочення і штрафи.

### Модель видачі

```json
{
  "id": 1,
  "book_copy_id": 1,
  "user_id": 1,
  "rented_at": "2026-05-07T12:30:00",
  "due_at": "2026-05-21T12:30:00",
  "returned_at": null,
  "return_status": null,
  "notes": "Видано на 14 днів"
}
```

### Модель штрафу

```json
{
  "id": 1,
  "book_rent_id": 1,
  "user_id": 1,
  "fine_type": "overdue",
  "amount_uah": 10,
  "days_overdue": 2,
  "notes": "Overdue for 2 day(s), 5 UAH per day",
  "created_at": "2026-05-23T12:30:00",
  "paid_at": null
}
```

### Endpoint-и

| Метод | Шлях | Опис |
| --- | --- | --- |
| `POST` | `/api/v1/book-rents/issue` | Видати примірник користувачу |
| `POST` | `/api/v1/book-rents/{book_rent_id}/return` | Повернути примірник |
| `PATCH` | `/api/v1/book-rents/{book_rent_id}/deadline` | Змінити дедлайн активної видачі |
| `GET` | `/api/v1/book-rents/history` | Отримати історію видач |
| `GET` | `/api/v1/book-rents/overdue` | Отримати активні прострочені видачі |
| `GET` | `/api/v1/book-rents/{book_rent_id}/fines/preview` | Попередньо розрахувати штрафи |
| `GET` | `/api/v1/book-rents/fines` | Отримати список штрафів |
| `POST` | `/api/v1/book-rents/fines/{fine_id}/pay` | Позначити штраф як оплачений |

### Видача книги

`POST /api/v1/book-rents/issue`

```json
{
  "book_copy_id": 1,
  "user_id": 1,
  "due_at": "2026-05-21T12:30:00Z",
  "notes": "Видано на 14 днів"
}
```

Обов'язкові поля:

- `book_copy_id`
- `user_id`

Правила:

- користувач має існувати;
- примірник має існувати;
- примірник має мати статус `available`;
- примірник не повинен мати активної неповерненої видачі;
- після успішної видачі статус примірника стає `borrowed`.

Можливі помилки:

- `404 Not Found` — користувача або примірник не знайдено.
- `409 Conflict` — примірник недоступний для видачі або вже має активну видачу.

### Повернення книги

`POST /api/v1/book-rents/{book_rent_id}/return`

```json
{
  "return_status": "available",
  "returned_at": "2026-05-20T16:00:00Z",
  "notes": "Повернено без пошкоджень"
}
```

Обов'язкове поле:

- `return_status`

Дозволені статуси повернення:

- `available`
- `damaged`
- `lost`

Правила:

- повернути можна тільки активну видачу;
- якщо `returned_at` не передано, використовується поточний час;
- статус пов'язаного примірника змінюється на `return_status`;
- під час повернення автоматично створюються або оновлюються неоплачені штрафи за прострочення та пошкодження.

Можливі помилки:

- `404 Not Found` — видачу не знайдено.
- `409 Conflict` — видачу вже повернено.
- `422 Unprocessable Entity` — некоректний `return_status`.

### Зміна дедлайну

`PATCH /api/v1/book-rents/{book_rent_id}/deadline`

```json
{
  "due_at": "2026-05-28T12:30:00Z"
}
```

Правила:

- дедлайн можна змінити тільки для активної видачі;
- для вже поверненої видачі API повертає `409 Conflict`.

### Історія видач

`GET /api/v1/book-rents/history`

Query-параметри:

- `book_id`
- `book_copy_id`
- `user_id`
- `rented_from`
- `rented_to`
- `limit`
- `offset`

Приклад:

```http
GET /api/v1/book-rents/history?user_id=1&rented_from=2026-05-01T00:00:00Z
```

Результат сортується від найновіших видач до старіших.

### Прострочені видачі

`GET /api/v1/book-rents/overdue`

Query-параметри:

- `user_id`
- `as_of` — дата й час, на які треба перевірити прострочення; якщо не передано, використовується поточний час.
- `limit`
- `offset`

Видача вважається простроченою, якщо:

- `returned_at` дорівнює `null`;
- `due_at` не дорівнює `null`;
- `due_at` менший за час перевірки.

### Попередній розрахунок штрафів

`GET /api/v1/book-rents/{book_rent_id}/fines/preview`

Query-параметри:

- `as_of`
- `return_status`: `available`, `damaged` або `lost`.

Приклад:

```http
GET /api/v1/book-rents/1/fines/preview?as_of=2026-05-23T12:30:00Z&return_status=damaged
```

Відповідь:

```json
[
  {
    "fine_type": "overdue",
    "amount_uah": 10,
    "days_overdue": 2,
    "notes": "Overdue for 2 day(s), 5 UAH per day"
  },
  {
    "fine_type": "damage",
    "amount_uah": 100,
    "days_overdue": null,
    "notes": "Book copy returned damaged"
  }
]
```

Preview не записує штрафи в базу даних. Він лише показує, які штрафи були б застосовані.

### Правила штрафів

Підтримувані типи штрафів:

- `overdue` — прострочення дедлайну.
- `damage` — повернення примірника зі статусом `damaged`.

Ставки штрафів:

- прострочення: `5` грн за кожен день;
- пошкодження: `100` грн.

Неповний день прострочення рахується як повний день. Наприклад, 2 години після `due_at` — це 1 день прострочення.

Якщо `due_at` не заданий, штраф за прострочення не нараховується.

### Список штрафів

`GET /api/v1/book-rents/fines`

Query-параметри:

- `book_rent_id`
- `user_id`
- `is_paid`: `true` або `false`.
- `limit`
- `offset`

Приклад:

```http
GET /api/v1/book-rents/fines?user_id=1&is_paid=false
```

### Оплата штрафу

`POST /api/v1/book-rents/fines/{fine_id}/pay`

Тіло запиту не потрібне.

Правила:

- якщо штраф існує і ще не оплачений, API заповнює `paid_at` поточним часом;
- повторна оплата вже оплаченого штрафу повертає `409 Conflict`.

## Типові use cases

### Додати нову книгу до бібліотеки

1. Створити автора: `POST /api/v1/authors/`.
2. Створити жанр: `POST /api/v1/genres/`.
3. Створити книгу з `author_id` і `genre_id`: `POST /api/v1/books/`.
4. Додати один або кілька фізичних примірників: `POST /api/v1/book-copies/`.

### Зареєструвати нового читача і його відвідування

1. Створити користувача: `POST /api/v1/users/`.
2. За потреби знайти користувача: `GET /api/v1/users/search`.
3. Створити запис відвідування: `POST /api/v1/check-ins/`.
4. Переглянути кількість відвідувань: `GET /api/v1/check-ins/users/{user_id}/count`.

### Видати книгу читачу

1. Знайти книгу: `GET /api/v1/books/search`.
2. Перевірити кількість примірників: `GET /api/v1/books/{book_id}/copies/count`.
3. Знайти доступний примірник: `GET /api/v1/book-copies/?book_id={book_id}&status=available`.
4. Видати примірник: `POST /api/v1/book-rents/issue`.
5. Після видачі примірник автоматично отримує статус `borrowed`.

### Повернути книгу і нарахувати штрафи

1. За потреби переглянути можливі штрафи: `GET /api/v1/book-rents/{book_rent_id}/fines/preview`.
2. Повернути книгу: `POST /api/v1/book-rents/{book_rent_id}/return`.
3. Перевірити створені штрафи: `GET /api/v1/book-rents/fines?book_rent_id={book_rent_id}`.
4. Позначити штраф як оплачений: `POST /api/v1/book-rents/fines/{fine_id}/pay`.

### Знайти проблемні активні видачі

1. Отримати всі прострочені видачі: `GET /api/v1/book-rents/overdue`.
2. Обмежити пошук користувачем: `GET /api/v1/book-rents/overdue?user_id={user_id}`.
3. Переглянути історію користувача: `GET /api/v1/book-rents/history?user_id={user_id}`.
4. Переглянути неоплачені штрафи: `GET /api/v1/book-rents/fines?user_id={user_id}&is_paid=false`.

## Важливі доменні обмеження

- Захищені endpoint-и вимагають HTTP Basic Auth.
- Якщо в системі немає користувача з роллю `admin`, наступний створений користувач створюється без авторизації та автоматично отримує роль `admin`.
- API не дозволяє видалити останнього адміністратора або прибрати в останнього адміністратора роль `admin`.
- CRUD користувачів використовує `username` як path-параметр, а не `id`.
- Видати можна тільки примірник зі статусом `available`.
- Активна видача — це запис `book_rents`, у якого `returned_at = null`.
- Один примірник не може мати дві активні видачі.
- Повернення книги змінює статус примірника на `available`, `damaged` або `lost`.
- Статуси примірників і ставки штрафів наразі захардкоджені в бізнес-логіці.
- `DELETE` endpoint-и повертають `204 No Content` без JSON-тіла.

## Швидкий приклад через curl

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -u admin:secret \
  -H "Content-Type: application/json" \
  -d '{
    "username": "reader01",
    "first_name": "Олена",
    "last_name": "Коваль",
    "email": "olena@example.com",
    "phone": "+380501112233",
    "password": "secret"
  }'
```

```bash
curl -X POST http://localhost:8000/api/v1/book-rents/issue \
  -u librarian:secret \
  -H "Content-Type: application/json" \
  -d '{
    "book_copy_id": 1,
    "user_id": 1,
    "due_at": "2026-05-21T12:30:00Z",
    "notes": "Видано на 14 днів"
  }'
```
