from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role
from ..security import hash_content
from ..trust_engine import apply_verification_outcome

router = APIRouter(prefix="/verifications", tags=["verifications"])


@router.post("")
def verify_submission(
    payload: schemas.VerificationCreate,
    db: Session = Depends(get_db),
    reviewer: models.User = Depends(require_role("student", "lecturer", "admin")),
):
    submission = db.query(models.Submission).filter(models.Submission.id == payload.submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    verification = models.Verification(
        submission_id=submission.id,
        method=payload.method,
        outcome=payload.outcome,
        reviewer_id=reviewer.id,
        notes=payload.notes,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)

    task = db.query(models.Task).filter(models.Task.id == submission.task_id).first()
    apply_verification_outcome(db, submission.student_id, task.project_id, payload.outcome.value)

    if payload.outcome.value == "disputed":
        submission.status = "disputed"
        db.commit()

    db.add(models.AuditLog(
        event_type="submission_verified",
        ref_id=submission.id,
        actor_id=reviewer.id,
        hash=hash_content(f"{submission.id}:{payload.outcome.value}:{datetime.utcnow()}"),
    ))
    db.commit()

    return {"submission_id": submission.id, "outcome": payload.outcome.value}
