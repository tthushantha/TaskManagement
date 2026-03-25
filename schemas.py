"""
Pydantic schemas for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from models import TaskStatus, TaskPriority


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    team_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None
    team_id: Optional[int] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    avatar_url: Optional[str] = None
    team_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Team schemas
class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class TeamResponse(TeamBase):
    id: int
    created_at: datetime
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = "#007bff"


class ProjectCreate(ProjectBase):
    team_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    team_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    task_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Task schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM


class TaskCreate(TaskBase):
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    tags: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    tags: Optional[str] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    tags: Optional[str] = None
    attachment_count: int
    comment_count: int
    view_count: int
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    project_id: Optional[int] = None
    created_by: Optional[int] = None
    assigned_to: Optional[int] = None
    
    # Include related data
    project_name: Optional[str] = None
    creator_name: Optional[str] = None
    assignee_name: Optional[str] = None

    class Config:
        from_attributes = True


# Comment schemas
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    task_id: int


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class CommentResponse(CommentBase):
    id: int
    is_edited: bool
    created_at: datetime
    updated_at: datetime
    task_id: int
    author_id: int
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None

    class Config:
        from_attributes = True


# Auth schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# Dashboard schemas
class DashboardStats(BaseModel):
    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    review_tasks: int
    done_tasks: int
    overdue_tasks: int
    total_projects: int
    total_users: int
    recent_tasks: List[TaskResponse] = []


# Filter schemas
class TaskFilter(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    created_by: Optional[int] = None
    search: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_overdue: Optional[bool] = None


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
