# Структура API-роутерів

У проєкті endpoint-модулі мають розділяти CRUD-операції та доменні операції на окремі `APIRouter`.

Це зроблено для того, щоб у коді та Swagger-документації не змішувати повторюваний CRUD із більш змістовними endpoint-ами на кшталт пошуку, статистики чи службових дій.

## Базовий шаблон

```python
crud_router = APIRouter(
    prefix="/users",
    tags=["Users / CRUD"],
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)
```

CRUD-операції треба реєструвати на `crud_router`:

```python
@crud_router.get("/")
@crud_router.post("/")
@crud_router.patch("/{user_id}")
@crud_router.delete("/{user_id}")
```

Доменні endpoint-и треба реєструвати на звичайний `router`:

```python
@router.get("/search")
@router.get("/stats")
@router.get("/me")
```

## Навіщо це потрібно

Таке розділення допомагає:

- тримати endpoint-файли більш читабельними
- не змішувати стандартний CRUD із бізнесовими діями
- зробити Swagger-документацію зручнішою для перегляду
- швидко знаходити нестандартні API-операції
- підтримувати однакову структуру для всіх ресурсів

## Підключення у v1 router

У `libful_api/api/v1/router.py` треба підключати обидва роутери:

```python
router.include_router(users.crud_router)
router.include_router(users.router)
```

Якщо endpoint-модуль має тільки CRUD і поки не має доменних endpoint-ів, все одно варто залишати обидва роутери. Це зберігає однакову структуру й спрощує майбутні зміни.

## Правила тегів

CRUD-тег має мати формат:

```text
<Resource> / CRUD
```

Приклади:

- `Users / CRUD`
- `Books / CRUD`
- `Book copies / CRUD`
- `Check-ins / CRUD`

Доменний тег має бути просто назвою ресурсу:

- `Users`
- `Books`
- `Book copies`
- `Check-ins`

## Правило для нових endpoint-ів

Якщо endpoint просто створює, читає, оновлює або видаляє ресурс, він належить до `crud_router`.

Якщо endpoint виконує пошук, рахує статистику, повертає агреговані дані або описує окрему бізнесову дію, він належить до звичайного `router`.
