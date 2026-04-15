"""
Task Management Application - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List
from math import ceil

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from database import get_db, init_db, engine
from models import User, Project, Task, Comment, Team, TaskStatus, TaskPriority
from config import SECRET_KEY
from schemas import (
    UserCreate, UserUpdate, UserResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    CommentCreate, CommentUpdate, CommentResponse,
    LoginRequest, Token, DashboardStats, TaskListResponse,
    TeamCreate, TeamUpdate, TeamResponse
)

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        create_default_data()
    except Exception as e:
        print(f"Database initialization error: {e}")
        # Continue without database initialization for now
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="Task Management",
    description="Web-based task management for small teams and freelancers",
    version="1.0.0",
    lifespan=lifespan
)

# Dynamic CORS middleware to handle multiple origins with credentials
from fastapi import Request, Response

@app.middleware("http")
async def dynamic_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    
    # List of allowed origins
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
        "https://task-management-psi-sandy-64.vercel.app",
        "https://localhost:3000",
        "https://localhost:5173"
    ]
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = Response()
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "600"
        return response
    
    # Handle actual requests
    response = await call_next(request)
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
    
    return response

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_id",
    max_age=1800,  # 30 minutes
    same_site="lax",  # Allow cross-origin requests
    httponly=False,  # Allow JavaScript access (needed for axios)
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def create_default_data():
    """Create default user and sample data"""
    db = next(get_db())
    try:
        # Check if default user exists
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="Administrator",
                hashed_password=hash_password("admin123"),
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            
            # Create sample team
            team = Team(name="Default Team", description="Default team for new users")
            db.add(team)
            db.commit()
            
            # Create sample project
            project = Project(name="Sample Project", description="A sample project to get started", team=team)
            db.add(project)
            db.commit()
            
            # Create sample tasks
            tasks = [
                Task(
                    title="Welcome to Task Management",
                    description="This is your first task. Feel free to edit or delete it.",
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                    project=project,
                    created_by=admin_user.id,
                    assigned_to=admin_user.id
                ),
                Task(
                    title="Explore the Dashboard",
                    description="Check out the dashboard to see your task overview.",
                    status=TaskStatus.IN_PROGRESS,
                    priority=TaskPriority.LOW,
                    project=project,
                    created_by=admin_user.id,
                    assigned_to=admin_user.id
                ),
                Task(
                    title="Create Your First Task",
                    description="Try creating a new task to get familiar with the interface.",
                    status=TaskStatus.DONE,
                    priority=TaskPriority.MEDIUM,
                    project=project,
                    created_by=admin_user.id,
                    assigned_to=admin_user.id,
                    completed_at=datetime.utcnow()
                )
            ]
            for task in tasks:
                db.add(task)
            db.commit()
    finally:
        db.close()


def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return hash_password(plain_password) == hashed_password


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current logged in user from session"""
    username = request.session.get("user")
    if username:
        return db.query(User).filter(User.username == username).first()
    return None


# ==================== Page Routes ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home/Dashboard page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Get dashboard stats
    total_tasks = db.query(Task).count()
    todo_tasks = db.query(Task).filter(Task.status == TaskStatus.TODO).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    review_tasks = db.query(Task).filter(Task.status == TaskStatus.REVIEW).count()
    done_tasks = db.query(Task).filter(Task.status == TaskStatus.DONE).count()
    overdue_tasks = db.query(Task).filter(
        Task.due_date < datetime.utcnow(),
        Task.status != TaskStatus.DONE
    ).count()
    total_projects = db.query(Project).filter(Project.is_active == True).count()
    total_users = db.query(User).count()
    
    # Get recent tasks
    recent_tasks = db.query(Task).order_by(Task.updated_at.desc()).limit(5).all()
    
    stats = DashboardStats(
        total_tasks=total_tasks,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        review_tasks=review_tasks,
        done_tasks=done_tasks,
        overdue_tasks=overdue_tasks,
        total_projects=total_projects,
        total_users=total_users,
        recent_tasks=[TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            estimated_hours=t.estimated_hours,
            actual_hours=t.actual_hours,
            tags=t.tags,
            attachment_count=t.attachment_count,
            comment_count=t.comment_count,
            view_count=t.view_count,
            is_favorite=t.is_favorite,
            created_at=t.created_at,
            updated_at=t.updated_at,
            completed_at=t.completed_at,
            project_id=t.project_id,
            created_by=t.created_by,
            assigned_to=t.assigned_to,
            project_name=t.project.name if t.project else None,
            creator_name=t.creator.full_name if t.creator else None,
            assignee_name=t.assignee.full_name if t.assignee else None
        ) for t in recent_tasks]
    )
    
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "stats": stats
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse(request, "register.html")


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[int] = None,
    search: Optional[str] = None
):
    """Tasks list page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    # Build query
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        query = query.filter(
            or_(
                Task.title.contains(search),
                Task.description.contains(search)
            )
        )
    
    tasks = query.order_by(Task.updated_at.desc()).all()
    
    # Get projects for filter
    projects = db.query(Project).filter(Project.is_active == True).all()
    
    # Convert to response format
    task_list = [TaskResponse(
        id=t.id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        due_date=t.due_date,
        estimated_hours=t.estimated_hours,
        actual_hours=t.actual_hours,
        tags=t.tags,
        attachment_count=t.attachment_count,
        comment_count=t.comment_count,
        view_count=t.view_count,
        is_favorite=t.is_favorite,
        created_at=t.created_at,
        updated_at=t.updated_at,
        completed_at=t.completed_at,
        project_id=t.project_id,
        created_by=t.created_by,
        assigned_to=t.assigned_to,
        project_name=t.project.name if t.project else None,
        creator_name=t.creator.full_name if t.creator else None,
        assignee_name=t.assignee.full_name if t.assignee else None
    ) for t in tasks]
    
    return templates.TemplateResponse(request, "tasks.html", {
        "user": user,
        "tasks": task_list,
        "projects": projects,
        "filters": {"status": status, "priority": priority, "project_id": project_id, "search": search}
    })


@app.get("/tasks/new", response_class=HTMLResponse)
async def new_task_page(request: Request, db: Session = Depends(get_db)):
    """Create new task page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    projects = db.query(Project).filter(Project.is_active == True).all()
    users = db.query(User).filter(User.is_active == True).all()
    
    return templates.TemplateResponse(request, "task_form.html", {
        "user": user,
        "task": None,
        "projects": projects,
        "users": users,
        "action": "create"
    })


@app.get("/tasks/{task_id}", response_class=HTMLResponse)
async def task_detail_page(request: Request, task_id: int, db: Session = Depends(get_db)):
    """Task detail page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Increment view count
    task.view_count += 1
    db.commit()
    
    # Get comments
    comments = db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at.desc()).all()
    
    projects = db.query(Project).filter(Project.is_active == True).all()
    users = db.query(User).filter(User.is_active == True).all()
    
    comment_list = [CommentResponse(
        id=c.id,
        content=c.content,
        is_edited=c.is_edited,
        created_at=c.created_at,
        updated_at=c.updated_at,
        task_id=c.task_id,
        author_id=c.author_id,
        author_name=c.author.full_name if c.author else None,
        author_avatar=c.author.avatar_url if c.author else None
    ) for c in comments]
    
    return templates.TemplateResponse(request, "task_detail.html", {
        "user": user,
        "task": task,
        "comments": comment_list,
        "projects": projects,
        "users": users
    })


@app.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
async def edit_task_page(request: Request, task_id: int, db: Session = Depends(get_db)):
    """Edit task page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    projects = db.query(Project).filter(Project.is_active == True).all()
    users = db.query(User).filter(User.is_active == True).all()
    
    return templates.TemplateResponse(request, "task_form.html", {
        "user": user,
        "task": task,
        "projects": projects,
        "users": users,
        "action": "edit"
    })


@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, db: Session = Depends(get_db)):
    """Projects list page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    projects = db.query(Project).filter(Project.is_active == True).order_by(Project.created_at.desc()).all()
    
    project_list = []
    for p in projects:
        task_count = db.query(Task).filter(Task.project_id == p.id).count()
        project_list.append(ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            color=p.color,
            team_id=p.team_id,
            is_active=p.is_active,
            created_at=p.created_at,
            task_count=task_count
        ))
    
    return templates.TemplateResponse(request, "projects.html", {
        "user": user,
        "projects": project_list
    })


@app.get("/projects/new", response_class=HTMLResponse)
async def new_project_page(request: Request, db: Session = Depends(get_db)):
    """Create new project page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(request, "project_form.html", {
        "user": user,
        "project": None,
        "action": "create"
    })


@app.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def edit_project_page(request: Request, project_id: int, db: Session = Depends(get_db)):
    """Edit project page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return templates.TemplateResponse(request, "project_form.html", {
        "user": user,
        "project": project,
        "action": "edit"
    })


# ==================== API Routes ====================

# Auth API
@app.post("/api/login")
async def api_login(request_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login API"""
    user = db.query(User).filter(User.username == request_data.username).first()
    if not user or not verify_password(request_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    # Set session
    request.session["user"] = user.username
    
    return {"message": "Login successful", "username": user.username}


@app.post("/api/logout")
async def api_logout(request: Request):
    """Logout API"""
    request.session.clear()
    return RedirectResponse(url="/login")


@app.post("/api/register", response_model=UserResponse)
async def api_register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user API"""
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        team_id=user_data.team_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


# Tasks API
@app.get("/api/tasks", response_model=TaskListResponse)
async def api_get_tasks(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[int] = None,
    search: Optional[str] = None
):
    """Get tasks API"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        query = query.filter(
            or_(
                Task.title.contains(search),
                Task.description.contains(search)
            )
        )
    
    total = query.count()
    tasks = query.order_by(Task.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    task_list = [TaskResponse(
        id=t.id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        due_date=t.due_date,
        estimated_hours=t.estimated_hours,
        actual_hours=t.actual_hours,
        tags=t.tags,
        attachment_count=t.attachment_count,
        comment_count=t.comment_count,
        view_count=t.view_count,
        is_favorite=t.is_favorite,
        created_at=t.created_at,
        updated_at=t.updated_at,
        completed_at=t.completed_at,
        project_id=t.project_id,
        created_by=t.created_by,
        assigned_to=t.assigned_to,
        project_name=t.project.name if t.project else None,
        creator_name=t.creator.full_name if t.creator else None,
        assignee_name=t.assignee.full_name if t.assignee else None
    ) for t in tasks]
    
    return TaskListResponse(
        tasks=task_list,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size)
    )


@app.post("/api/tasks", response_model=TaskResponse)
async def api_create_task(task_data: TaskCreate, request: Request, db: Session = Depends(get_db)):
    """Create task API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        project_id=task_data.project_id,
        assigned_to=task_data.assigned_to,
        due_date=task_data.due_date,
        estimated_hours=task_data.estimated_hours,
        tags=task_data.tags,
        created_by=user.id,
        status=TaskStatus.TODO
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        tags=task.tags,
        attachment_count=task.attachment_count,
        comment_count=task.comment_count,
        view_count=task.view_count,
        is_favorite=task.is_favorite,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        project_id=task.project_id,
        created_by=task.created_by,
        assigned_to=task.assigned_to,
        project_name=task.project.name if task.project else None,
        creator_name=task.creator.full_name if task.creator else None,
        assignee_name=task.assignee.full_name if task.assignee else None
    )


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def api_get_task(task_id: int, db: Session = Depends(get_db)):
    """Get single task API"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        tags=task.tags,
        attachment_count=task.attachment_count,
        comment_count=task.comment_count,
        view_count=task.view_count,
        is_favorite=task.is_favorite,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        project_id=task.project_id,
        created_by=task.created_by,
        assigned_to=task.assigned_to,
        project_name=task.project.name if task.project else None,
        creator_name=task.creator.full_name if task.creator else None,
        assignee_name=task.assignee.full_name if task.assignee else None
    )


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
async def api_update_task(task_id: int, task_data: TaskUpdate, request: Request, db: Session = Depends(get_db)):
    """Update task API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
        if task_data.status == TaskStatus.DONE and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif task_data.status != TaskStatus.DONE:
            task.completed_at = None
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    if task_data.estimated_hours is not None:
        task.estimated_hours = task_data.estimated_hours
    if task_data.actual_hours is not None:
        task.actual_hours = task_data.actual_hours
    if task_data.tags is not None:
        task.tags = task_data.tags
    if task_data.project_id is not None:
        task.project_id = task_data.project_id
    if task_data.assigned_to is not None:
        task.assigned_to = task_data.assigned_to
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        tags=task.tags,
        attachment_count=task.attachment_count,
        comment_count=task.comment_count,
        view_count=task.view_count,
        is_favorite=task.is_favorite,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        project_id=task.project_id,
        created_by=task.created_by,
        assigned_to=task.assigned_to,
        project_name=task.project.name if task.project else None,
        creator_name=task.creator.full_name if task.creator else None,
        assignee_name=task.assignee.full_name if task.assignee else None
    )


@app.delete("/api/tasks/{task_id}")
async def api_delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete task API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@app.post("/api/tasks/{task_id}/favorite")
async def api_toggle_favorite(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Toggle task favorite status"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.is_favorite = not task.is_favorite
    db.commit()
    
    return {"is_favorite": task.is_favorite}


# Comments API
@app.get("/api/tasks/{task_id}/comments", response_model=List[CommentResponse])
async def api_get_comments(task_id: int, db: Session = Depends(get_db)):
    """Get task comments"""
    comments = db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at.desc()).all()
    
    return [CommentResponse(
        id=c.id,
        content=c.content,
        is_edited=c.is_edited,
        created_at=c.created_at,
        updated_at=c.updated_at,
        task_id=c.task_id,
        author_id=c.author_id,
        author_name=c.author.full_name if c.author else None,
        author_avatar=c.author.avatar_url if c.author else None
    ) for c in comments]


@app.post("/api/tasks/{task_id}/comments", response_model=CommentResponse)
async def api_create_comment(task_id: int, comment_data: CommentCreate, request: Request, db: Session = Depends(get_db)):
    """Create comment API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    comment = Comment(
        content=comment_data.content,
        task_id=task_id,
        author_id=user.id
    )
    db.add(comment)
    
    # Update comment count
    task.comment_count += 1
    
    db.commit()
    db.refresh(comment)
    
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        is_edited=comment.is_edited,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_name=user.full_name,
        author_avatar=user.avatar_url
    )


@app.put("/api/comments/{comment_id}", response_model=CommentResponse)
async def api_update_comment(comment_id: int, comment_data: CommentUpdate, request: Request, db: Session = Depends(get_db)):
    """Update comment API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    comment.content = comment_data.content
    comment.is_edited = True
    db.commit()
    db.refresh(comment)
    
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        is_edited=comment.is_edited,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_name=comment.author.full_name if comment.author else None,
        author_avatar=comment.author.avatar_url if comment.author else None
    )


@app.delete("/api/comments/{comment_id}")
async def api_delete_comment(comment_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete comment API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    # Update comment count
    task = db.query(Task).filter(Task.id == comment.task_id).first()
    if task:
        task.comment_count = max(0, task.comment_count - 1)
    
    db.delete(comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}


# Projects API
@app.get("/api/projects", response_model=List[ProjectResponse])
async def api_get_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    projects = db.query(Project).filter(Project.is_active == True).order_by(Project.created_at.desc()).all()
    
    return [ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        color=p.color,
        team_id=p.team_id,
        is_active=p.is_active,
        created_at=p.created_at,
        task_count=db.query(Task).filter(Task.project_id == p.id).count()
    ) for p in projects]


@app.post("/api/projects", response_model=ProjectResponse)
async def api_create_project(project_data: ProjectCreate, request: Request, db: Session = Depends(get_db)):
    """Create project API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        color=project_data.color,
        team_id=project_data.team_id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        color=project.color,
        team_id=project.team_id,
        is_active=project.is_active,
        created_at=project.created_at,
        task_count=0
    )


@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
async def api_update_project(project_id: int, project_data: ProjectUpdate, request: Request, db: Session = Depends(get_db)):
    """Update project API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.color is not None:
        project.color = project_data.color
    if project_data.is_active is not None:
        project.is_active = project_data.is_active
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        color=project.color,
        team_id=project.team_id,
        is_active=project.is_active,
        created_at=project.created_at,
        task_count=db.query(Task).filter(Task.project_id == project.id).count()
    )


@app.delete("/api/projects/{project_id}")
async def api_delete_project(project_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete project API"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Soft delete
    project.is_active = False
    db.commit()
    
    return {"message": "Project deleted successfully"}


# Users API
@app.get("/api/users", response_model=List[UserResponse])
async def api_get_users(db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).filter(User.is_active == True).all()
    return users


# Dashboard API
@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def api_dashboard_stats(request: Request, db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    total_tasks = db.query(Task).count()
    todo_tasks = db.query(Task).filter(Task.status == TaskStatus.TODO).count()
    in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    review_tasks = db.query(Task).filter(Task.status == TaskStatus.REVIEW).count()
    done_tasks = db.query(Task).filter(Task.status == TaskStatus.DONE).count()
    overdue_tasks = db.query(Task).filter(
        Task.due_date < datetime.utcnow(),
        Task.status != TaskStatus.DONE
    ).count()
    total_projects = db.query(Project).filter(Project.is_active == True).count()
    total_users = db.query(User).count()
    
    recent_tasks = db.query(Task).order_by(Task.updated_at.desc()).limit(5).all()
    
    return DashboardStats(
        total_tasks=total_tasks,
        todo_tasks=todo_tasks,
        in_progress_tasks=in_progress_tasks,
        review_tasks=review_tasks,
        done_tasks=done_tasks,
        overdue_tasks=overdue_tasks,
        total_projects=total_projects,
        total_users=total_users,
        recent_tasks=[TaskResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            estimated_hours=t.estimated_hours,
            actual_hours=t.actual_hours,
            tags=t.tags,
            attachment_count=t.attachment_count,
            comment_count=t.comment_count,
            view_count=t.view_count,
            is_favorite=t.is_favorite,
            created_at=t.created_at,
            updated_at=t.updated_at,
            completed_at=t.completed_at,
            project_id=t.project_id,
            created_by=t.created_by,
            assigned_to=t.assigned_to,
            project_name=t.project.name if t.project else None,
            creator_name=t.creator.full_name if t.creator else None,
            assignee_name=t.assignee.full_name if t.assignee else None
        ) for t in recent_tasks]
    )


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Docker containers"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
