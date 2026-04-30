"""
Audit log routes.

Audit logs help file owners understand who tried to access shared files and
whether each attempt succeeded or failed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db


router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("", response_model=list[schemas.AccessLogResponse])
def list_audit_logs(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[models.AccessLog]:
    """
    Return audit logs for files owned by the current user.

    The join with File prevents one user from reading audit logs for another
    user's files. Audit logs matter because secure file sharing is not just about
    allowing valid access; it is also about seeing denied attempts such as
    expired links, revoked links, and password failures.
    """
    return (
        db.query(models.AccessLog)
        .join(models.File, models.AccessLog.file_id == models.File.id)
        .filter(models.File.owner_id == current_user.id)
        .order_by(models.AccessLog.created_at.desc())
        .all()
    )
