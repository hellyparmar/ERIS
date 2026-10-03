import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ImportJob, User
from app.routers.common import get_or_404, page_response, paginate
from app.security import get_current_user, require_manager
from app.services import forecasting as F
from app.services.importer import TEMPLATES, error_report_csv, inspect_file, run_import, sample_csv, template_csv

router = APIRouter(prefix="/api/imports", tags=["data import"])
MAX_BYTES = 15 * 1024 * 1024


def _csv_response(text: str, filename: str) -> Response:
    return Response(text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _read_upload(file: UploadFile) -> bytes:
    content = file.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "File is larger than 15 MB")
    if not content:
        raise HTTPException(400, "The file is empty")
    return content


def _parse_mapping(mapping: str | None) -> dict | None:
    if not mapping:
        return None
    try:
        m = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(422, "mapping must be a JSON object of {template column: file column}") from None
    if not isinstance(m, dict) or not all(isinstance(k, str) and (v is None or isinstance(v, str)) for k, v in m.items()):
        raise HTTPException(422, "mapping must be a JSON object of {template column: file column}")
    return m


def job_dict(j: ImportJob) -> dict:
    return {"id": j.id, "kind": j.kind, "filename": j.filename, "status": j.status, "dry_run": j.dry_run,
            "total_rows": j.total_rows, "created": j.created_count, "updated": j.updated_count,
            "errors": j.error_count, "user": j.user.full_name if j.user else None,
            "created_at": j.created_at.isoformat() if j.created_at else None}


@router.get("")
def import_types(_: User = Depends(get_current_user)):
    return [{"kind": k, "columns": t["columns"], "required": t["required"], "help": t["help"]}
            for k, t in TEMPLATES.items()]


@router.get("/templates/{kind}")
def download_template(kind: str):
    return _csv_response(template_csv(kind), f"eris_{kind}_template.csv")


@router.get("/samples/{kind}")
def download_sample(kind: str, with_errors: bool = False, _: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    suffix = "_with_errors" if with_errors else ""
    return _csv_response(sample_csv(db, kind, with_errors), f"eris_{kind}_sample{suffix}.csv")


@router.get("/history")
def import_history(kind: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
                   user: User = Depends(require_manager), db: Session = Depends(get_db)):
    q = select(ImportJob).order_by(ImportJob.id.desc())
    if kind:
        q = q.where(ImportJob.kind == kind)
    if user.role != "admin":
        q = q.where(ImportJob.user_id == user.id)
    rows, total = paginate(db, q, page, page_size)
    return page_response([job_dict(r[0]) for r in rows], total, page, page_size)


@router.get("/history/{job_id}/errors.csv")
def import_errors(job_id: int, user: User = Depends(require_manager), db: Session = Depends(get_db)):
    job = get_or_404(db, ImportJob, job_id, "Import")
    if user.role != "admin" and job.user_id != user.id:
        raise HTTPException(403, "You can only download reports for your own imports")
    return _csv_response(error_report_csv(job), f"eris_import_{job_id}_errors.csv")


@router.post("/{kind}/inspect")
def inspect(kind: str, file: UploadFile = File(...), _: User = Depends(require_manager)):
    """Headers, suggested column mapping and the first rows - shown to the user before validation."""
    return inspect_file(kind, _read_upload(file), file.filename)


@router.post("/{kind}")
def upload(kind: str, file: UploadFile = File(...), dry_run: bool = True, update_stock: bool = False,
           skip_duplicates: bool = True, mapping: str | None = Form(None),
           user: User = Depends(require_manager), db: Session = Depends(get_db)):
    result = run_import(db, kind, _read_upload(file), user, dry_run=dry_run, update_stock=update_stock,
                        mapping=_parse_mapping(mapping), filename=file.filename, skip_duplicates=skip_duplicates)
    if result["committed"] and kind == "sales":
        F.clear_cache()
    return result
