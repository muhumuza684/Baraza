from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from .models import Role, SubmissionStatus, VerificationOutcome


class UserRegister(BaseModel):
    name: str
    email: str
    matric_no: Optional[str] = None
    password: str
    role: Role = Role.student


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    matric_no: Optional[str] = None
    role: Role

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    title: str
    course: str
    group_code: str
    deadline: datetime


class TaskCreate(BaseModel):
    role_name: str
    deadline: datetime
    assigned_student_id: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    project_id: str
    role_name: str
    assigned_student_id: Optional[str]
    deadline: datetime

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    task_id: str
    content: str  # raw text/content; the API hashes + signs it server-side


class SubmissionOut(BaseModel):
    id: str
    task_id: str
    student_id: str
    content_hash: str
    submitted_at: datetime
    status: SubmissionStatus

    class Config:
        from_attributes = True


class VerificationCreate(BaseModel):
    submission_id: str
    method: str  # peer | auto | instructor
    outcome: VerificationOutcome
    notes: Optional[str] = None


class TrustOut(BaseModel):
    student_id: str
    project_id: str
    current_state: str
    trust_mean: float
    trust_confidence_width: float
    audit_probability: float


class ContributionRow(BaseModel):
    student_id: str
    student_name: str
    verified_count: int
    disputed_count: int
    trust_mean: float
    contribution_share_pct: float
