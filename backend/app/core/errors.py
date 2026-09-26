"""Validation errors in Indonesian.

FastAPI's default 422 body is a list of pydantic errors written in English for
developers. The UI shows one sentence to a person, so this turns the first error
into "<Field>: <what's wrong>." in Indonesian.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

FIELD_LABELS = {
	"email": "Email",
	"password": "Kata sandi",
	"new_password": "Kata sandi baru",
	"current_password": "Kata sandi saat ini",
	"full_name": "Nama lengkap",
	"position": "Jabatan",
	"name": "Nama",
	"code": "Kode",
	"role": "Peran",
	"unit_id": "Unit kerja",
	"title": "Judul",
	"scheduled_start": "Waktu mulai",
	"scheduled_end": "Waktu selesai",
	"actual_start": "Mulai (realisasi)",
	"actual_end": "Selesai (realisasi)",
	"location_type": "Jenis lokasi",
	"user_ids": "Peserta",
	"invitee_ids": "Peserta",
	"note": "Alasan",
	"action": "Tindakan",
	"start": "Waktu mulai",
	"end": "Waktu selesai",
	"timezone": "Zona waktu",
	"tz": "Zona waktu",
}


def _message(error: dict) -> str:
	kind = error.get("type", "")
	ctx = error.get("ctx") or {}
	if kind == "missing":
		return "wajib diisi"
	if kind in ("string_too_short", "too_short"):
		if kind == "too_short" or ctx.get("min_length") == 1:
			return "wajib diisi"
		return f"minimal {ctx.get('min_length')} karakter"
	if kind in ("string_too_long", "too_long"):
		return f"maksimal {ctx.get('max_length')} karakter"
	if kind == "value_error" and "email" in str(error.get("msg", "")).lower():
		return "format email tidak valid"
	if kind == "value_error" and "timezone" in str(error.get("msg", "")).lower():
		return "zona waktu tidak dikenal"
	if kind == "timezone_aware":
		return "waktu harus menyertakan zona waktu (mis. +07:00 atau Z)"
	if kind.startswith(("datetime", "date", "time")):
		return "format tanggal/waktu tidak valid"
	if kind in ("enum", "literal_error"):
		return "pilihan tidak valid"
	if kind.startswith(("int", "float", "bool")):
		return "nilai tidak valid"
	return "data tidak valid"


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
	errors = exc.errors()
	first = errors[0] if errors else {}
	# loc looks like ("body", "email") or ("query", "start"); the last named part is the field.
	field = next((str(p) for p in reversed(first.get("loc", ())) if isinstance(p, str)), "")
	label = FIELD_LABELS.get(field)
	message = _message(first)
	detail = f"{label}: {message}." if label else f"{message[0].upper()}{message[1:]}."
	return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": detail})
