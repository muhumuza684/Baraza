"""
The trust engine: two layers working together.

1) Markov layer
   Tracks each student's submission-state history (on_time / late / missed / disputed)
   for a given project. The *distribution* of recent states drives how often that
   student's future submissions get audited -- a student trending toward late/missed
   gets checked more often, a consistently on_time student gets checked less.

2) Bayesian layer
   A Beta(alpha, beta) posterior over "this student delivers verified work reliably".
   Every verified outcome is a success (alpha += 1); every disputed outcome is a
   failure (beta += 1). The posterior mean is the trust score; the posterior's
   spread gives an honest confidence width instead of a single opaque number.
"""

from sqlalchemy.orm import Session

from . import models

# Base audit probability per current state -- illustrative, tune with real data later.
AUDIT_PROBABILITY = {
    "on_time": 0.10,
    "late": 0.35,
    "missed": 0.75,
    "disputed": 0.90,
}


def get_or_create_trust_record(db: Session, student_id: str, project_id: str) -> models.TrustRecord:
    record = (
        db.query(models.TrustRecord)
        .filter_by(student_id=student_id, project_id=project_id)
        .first()
    )
    if record is None:
        record = models.TrustRecord(student_id=student_id, project_id=project_id)
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def apply_submission_state(db: Session, student_id: str, project_id: str, status: str) -> models.TrustRecord:
    """Update the Markov layer after a new submission is recorded."""
    record = get_or_create_trust_record(db, student_id, project_id)

    if status == "on_time":
        record.state_on_time += 1
    elif status == "late":
        record.state_late += 1
    elif status == "missed":
        record.state_missed += 1
    elif status == "disputed":
        record.state_disputed += 1

    record.current_state = status
    db.commit()
    db.refresh(record)
    return record


def apply_verification_outcome(db: Session, student_id: str, project_id: str, outcome: str) -> models.TrustRecord:
    """Update the Bayesian layer after a submission is verified or disputed."""
    record = get_or_create_trust_record(db, student_id, project_id)

    if outcome == "verified":
        record.beta_alpha += 1.0
    elif outcome == "disputed":
        record.beta_beta += 1.0
        record.current_state = "disputed"
        record.state_disputed += 1

    db.commit()
    db.refresh(record)
    return record


def trust_summary(record: models.TrustRecord) -> dict:
    alpha, beta = record.beta_alpha, record.beta_beta
    mean = alpha / (alpha + beta)
    # Variance of a Beta distribution; we surface its square-root-ish spread as a
    # simple "confidence width" so the score is never presented as a bare point estimate.
    variance = (alpha * beta) / (((alpha + beta) ** 2) * (alpha + beta + 1))
    confidence_width = variance ** 0.5

    return {
        "student_id": record.student_id,
        "project_id": record.project_id,
        "current_state": record.current_state,
        "trust_mean": round(mean, 4),
        "trust_confidence_width": round(confidence_width, 4),
        "audit_probability": AUDIT_PROBABILITY.get(record.current_state, 0.25),
    }
