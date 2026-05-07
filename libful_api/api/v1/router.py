from fastapi import APIRouter

from libful_api.api.v1.endpoints import authors
from libful_api.api.v1.endpoints import book_copies
from libful_api.api.v1.endpoints import book_rents
from libful_api.api.v1.endpoints import books
from libful_api.api.v1.endpoints import check_ins
from libful_api.api.v1.endpoints import genres
from libful_api.api.v1.endpoints import roles
from libful_api.api.v1.endpoints import users


router = APIRouter()

router.include_router(users.router)
router.include_router(users.crud_router)
router.include_router(roles.router)
router.include_router(check_ins.router)
router.include_router(check_ins.crud_router)
router.include_router(authors.router)
router.include_router(authors.crud_router)
router.include_router(genres.router)
router.include_router(genres.crud_router)
router.include_router(books.router)
router.include_router(books.crud_router)
router.include_router(book_copies.router)
router.include_router(book_copies.crud_router)
router.include_router(book_rents.router)
