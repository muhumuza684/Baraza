from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_role, get_current_user
from ..security import hash_content

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("")
def create_project(
    payload: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    lecturer: models.User = Depends(require_role("lecturer", "admin")),
):
    project = models.Project(
        title=payload.title,
        course=payload.course,
        lecturer_id=lecturer.id,
        group_code=payload.group_code,
        deadline=payload.deadline,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    db.add(models.AuditLog(
        event_type="project_created",
        ref_id=project.id,
        actor_id=lecturer.id,
        hash=hash_content(project.id + str(datetime.utcnow())),
    ))
    db.commit()

    return {"id": project.id, "title": project.title, "group_code": project.group_code}


@router.post("/{project_id}/tasks", response_model=schemas.TaskOut)
def create_task(
    project_id: str,
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    lecturer: models.User = Depends(require_role("lecturer", "admin")),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = models.Task(
        project_id=project_id,
        role_name=payload.role_name,
        deadline=payload.deadline,
        assigned_student_id=payload.assigned_student_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{project_id}/tasks")
def list_tasks(project_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    return [
        {
            "id": t.id,
            "role_name": t.role_name,
            "assigned_student_id": t.assigned_student_id,
            "deadline": t.deadline,
        }
        for t in tasks
    ]


@router.post("/{project_id}/tasks/{task_id}/join")
def join_task(
    project_id: str,
    task_id: str,
    db: Session = Depends(get_db),
    student: models.User = Depends(require_role("student")),
):
    """A student claims an unassigned role. Keeps decomposition fair -- students pick
    from a lecturer-defined template rather than a group leader assigning roles."""
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_student_id and task.assigned_student_id != student.id:
        raise HTTPException(status_code=400, detail="Task already assigned to another student")

    task.assigned_student_id = student.id
    db.commit()
    db.refresh(task)
    return {"task_id": task.id, "assigned_student_id": task.assigned_student_id}
