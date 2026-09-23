"""
Seeds the database with a demo lecturer, three students, one project with three
tasks, and a couple of submissions/verifications so the dashboard has something
to show right after setup.

Run with:  python seed.py
"""
from datetime import datetime, timedelta

from app.database import Base, engine, SessionLocal
from app import models
from app.security import hash_password, hash_content, sign
from app.trust_engine import apply_submission_state, apply_verification_outcome

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def get_or_create_user(name, email, matric_no, password, role):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user
    user = models.User(
        name=name, email=email, matric_no=matric_no,
        password_hash=hash_password(password), role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


lecturer = get_or_create_user("Dr. Engwau Tonny", "lecturer@must.ac.ug", None, "password123", models.Role.lecturer)
s1 = get_or_create_user("Bright A. Muhumuza", "bright@must.ac.ug", "2024/BSE/108/PS", "password123", models.Role.student)
s2 = get_or_create_user("Teammate Two", "teammate2@must.ac.ug", "2024/BSE/109/PS", "password123", models.Role.student)
s3 = get_or_create_user("Teammate Three", "teammate3@must.ac.ug", "2024/BSE/110/PS", "password123", models.Role.student)

project = db.query(models.Project).filter(models.Project.group_code == "SWE3203-G11").first()
if not project:
    project = models.Project(
        title="ORAL-VR: Folk Narrative VR Prototype",
        course="SWE3203",
        lecturer_id=lecturer.id,
        group_code="SWE3203-G11",
        deadline=datetime.utcnow() + timedelta(days=14),
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    roles = [
        ("Research", s1.id),
        ("Implementation", s2.id),
        ("Writeup", s3.id),
    ]
    tasks = []
    for role_name, sid in roles:
        t = models.Task(
            project_id=project.id,
            role_name=role_name,
            assigned_student_id=sid,
            deadline=datetime.utcnow() + timedelta(days=7),
        )
        db.add(t)
        tasks.append(t)
    db.commit()
    for t in tasks:
        db.refresh(t)

    # Demo submissions + verification outcomes so the dashboard isn't empty.
    demo = [
        (tasks[0], s1.id, "on_time", "verified"),
        (tasks[1], s2.id, "late", "verified"),
        (tasks[2], s3.id, "missed", "disputed"),
    ]
    for task, sid, sub_status, outcome in demo:
        content = f"demo submission for {task.role_name}"
        content_hash = hash_content(content)
        signature = sign(content_hash, sid)
        submission = models.Submission(
            task_id=task.id, student_id=sid, content_hash=content_hash,
            signature=signature, status=sub_status,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        apply_submission_state(db, sid, project.id, sub_status)

        verification = models.Verification(
            submission_id=submission.id, method="instructor", outcome=outcome,
            reviewer_id=lecturer.id,
        )
        db.add(verification)
        db.commit()

        apply_verification_outcome(db, sid, project.id, outcome)

print("Seed complete.")
print(f"  Lecturer login: lecturer@must.ac.ug / password123")
print(f"  Student login:  bright@must.ac.ug / password123")
print(f"  Project ID:     {project.id}")
db.close()
