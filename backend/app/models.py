import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Enum, Text, Float, Integer, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_id():
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    admin = "admin"
    lecturer = "lecturer"
    student = "student"


class SubmissionStatus(str, enum.Enum):
    on_time = "on_time"
    late = "late"
    missed = "missed"
    disputed = "disputed"


class VerificationOutcome(str, enum.Enum):
    verified = "verified"
    disputed = "disputed"
    pending = "pending"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    matric_no = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.student)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="assigned_student")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String, nullable=False)
    course = Column(String, nullable=False)
    lecturer_id = Column(String, ForeignKey("users.id"), nullable=False)
    group_code = Column(String, nullable=False, index=True)
    deadline = Column(DateTime, nullable=False)
    checkpoint_at = Column(DateTime, nullable=True)  # ~50% of window, informational
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    role_name = Column(String, nullable=False)  # e.g. Research, Implementation, Testing, Writeup
    assigned_student_id = Column(String, ForeignKey("users.id"), nullable=True)
    deadline = Column(DateTime, nullable=False)

    project = relationship("Project", back_populates="tasks")
    assigned_student = relationship("User", back_populates="tasks")
    submissions = relationship("Submission", back_populates="task", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    content_hash = Column(String, nullable=False)
    signature = Column(String, nullable=False)  # HMAC of content_hash + student_id, proves authorship
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.on_time)
    ip_fingerprint = Column(String, nullable=True)  # soft anomaly signal only, never a hard block

    task = relationship("Task", back_populates="submissions")
    verifications = relationship("Verification", back_populates="submission", cascade="all, delete-orphan")


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(String, primary_key=True, default=gen_id)
    submission_id = Column(String, ForeignKey("submissions.id"), nullable=False)
    method = Column(String, nullable=False)  # peer | auto | instructor
    outcome = Column(Enum(VerificationOutcome), nullable=False, default=VerificationOutcome.pending)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    submission = relationship("Submission", back_populates="verifications")


class TrustRecord(Base):
    __tablename__ = "trust_records"
    __table_args__ = (UniqueConstraint("student_id", "project_id", name="uq_student_project_trust"),)

    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)

    # Markov layer: counts of transitions into each state, used to derive audit probability
    state_on_time = Column(Integer, default=0)
    state_late = Column(Integer, default=0)
    state_missed = Column(Integer, default=0)
    state_disputed = Column(Integer, default=0)
    current_state = Column(String, default="on_time")

    # Bayesian layer: Beta(alpha, beta) posterior over "this student delivers reliably"
    beta_alpha = Column(Float, default=1.0)  # starts at Beta(1,1) = uniform prior
    beta_beta = Column(Float, default=1.0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=gen_id)
    event_type = Column(String, nullable=False)
    ref_id = Column(String, nullable=False)
    actor_id = Column(String, nullable=True)
    hash = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
