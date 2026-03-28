from fastapi import APIRouter
from app.api.v1 import books, taxonomy, search, comparisons

api_router = APIRouter()

api_router.include_router(books.router, prefix="/books", tags=["Books"])
api_router.include_router(taxonomy.router, prefix="/taxonomy", tags=["Fiqh Taxonomy"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(comparisons.router, prefix="/comparisons", tags=["Ittifaq/Ikhtilaf"])
