import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role
from ..security import hash_content, sign
from ..trust_engine import apply_submission_state

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=schemas.SubmissionOut)
def submit_work(
    payload: schemas.SubmissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    student: models.User = Depends(require_role("student")),
):
    task = db.query(models.Task).filter(models.Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_student_id != student.id:
        raise HTTPException(status_code=403, detail="This task is not assigned to you")

    content_hash = hash_content(payload.content)
    signature = sign(content_hash, student.id)

    # Soft anomaly signal only -- never a hard block. See ip_fingerprint on the model.
    client_ip = request.client.host if request.client else "unknown"
    ip_fingerprint = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    now = datetime.utcnow()
    if now <= task.deadline:
        status = "on_time"
    else:
        status = "late"

    submission = models.Submission(
        task_id=task.id,
        student_id=student.id,
        content_hash=content_hash,
        signature=signature,
        status=status,
        ip_fingerprint=ip_fingerprint,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    apply_submission_state(db, student.id, task.project_id, status)

    db.add(models.AuditLog(
        event_type="submission_created",
        ref_id=submission.id,
        actor_id=student.id,
        hash=content_hash,
    ))
    db.commit()

    return submission


@router.get("/mine")
def my_submissions(db: Session = Depends(get_db), student: models.User = Depends(require_role("student"))):
    subs = db.query(models.Submission).filter(models.Submission.student_id == student.id).all()
    return [
        {
            "id": s.id,
            "task_id": s.task_id,
            "status": s.status.value,
            "submitted_at": s.submitted_at,
        }
        for s in subs
    ]
