from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role, get_current_user
from ..trust_engine import get_or_create_trust_record, trust_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me", response_model=list)
def my_trust(db: Session = Depends(get_db), student: models.User = Depends(require_role("student"))):
    records = db.query(models.TrustRecord).filter(models.TrustRecord.student_id == student.id).all()
    return [trust_summary(r) for r in records]


@router.get("/project/{project_id}")
def project_dashboard(
    project_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("lecturer", "admin")),
):
    """The contribution-balance view: verified/disputed counts and trust score
    per student on this project -- the headline chart from the mockup."""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    student_ids = {t.assigned_student_id for t in tasks if t.assigned_student_id}

    rows = []
    total_verified = 0
    per_student_verified = {}

    for sid in student_ids:
        student = db.query(models.User).filter(models.User.id == sid).first()
        student_task_ids = [t.id for t in tasks if t.assigned_student_id == sid]
        submissions = db.query(models.Submission).filter(models.Submission.task_id.in_(student_task_ids)).all()

        verified_count = 0
        disputed_count = 0
        for s in submissions:
            for v in s.verifications:
                if v.outcome.value == "verified":
                    verified_count += 1
                elif v.outcome.value == "disputed":
                    disputed_count += 1

        record = get_or_create_trust_record(db, sid, project_id)
        summary = trust_summary(record)

        per_student_verified[sid] = verified_count
        total_verified += verified_count

        rows.append({
            "student_id": sid,
            "student_name": student.name if student else "Unknown",
            "verified_count": verified_count,
            "disputed_count": disputed_count,
            "trust_mean": summary["trust_mean"],
            "contribution_share_pct": 0.0,  # filled in below once total is known
        })

    for row in rows:
        row["contribution_share_pct"] = (
            round(100 * per_student_verified[row["student_id"]] / total_verified, 1)
            if total_verified > 0 else 0.0
        )

    return {"project_id": project_id, "title": project.title, "students": rows}
