from fastapi import APIRouter
from sqlmodel import text

from app.core.db import engine

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
	with engine.connect() as conn:
		conn.execute(text("SELECT 1"))
	return {"status": "ok", "db": "ok"}
