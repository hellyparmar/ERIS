from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import get_current_user, require_manager
from app.services import forecasting as F
from app.services.importer import TEMPLATES, run_import, template_csv

router = APIRouter(prefix="/api/imports", tags=["data import"])
MAX_BYTES = 15 * 1024 * 1024


@router.get("")
def import_types(_: User = Depends(get_current_user)):
    return [{"kind": k, "columns": t["columns"], "required": t["required"], "help": t["help"]}
            for k, t in TEMPLATES.items()]


@router.get("/templates/{kind}")
def download_template(kind: str):
    return Response(template_csv(kind), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="eris_{kind}_template.csv"'})


@router.post("/{kind}")
def upload(kind: str, file: UploadFile = File(...), dry_run: bool = True, update_stock: bool = False,
                 user: User = Depends(require_manager), db: Session = Depends(get_db)):
    content = file.file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(400, "File is larger than 15 MB")
    result = run_import(db, kind, content, user, dry_run=dry_run, update_stock=update_stock)
    if result["committed"] and kind == "sales":
        F.clear_cache()
    return result
