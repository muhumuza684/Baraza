from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, projects, submissions, verification, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Baraza API", description="Group-project contribution & trust engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(submissions.router)
app.include_router(verification.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "baraza-api"}
