# Task Management Application

A web-based task management application designed for small teams and freelancers. Built with Python 3.14, FastAPI, and React.

## Features

- **Dashboard**: Overview of tasks, projects, and team activity
- **Task Management**: Create, edit, delete, and track tasks
- **Project Organization**: Organize tasks into projects
- **User Authentication**: Login and registration system
- **Priority & Status Tracking**: Track task progress with multiple statuses
- **Comments**: Add comments to tasks for collaboration
- **Favorites**: Mark important tasks as favorites
- **Search & Filter**: Find tasks quickly with filters

## Docker Deployment

### Prerequisites
- Docker and Docker Compose installed on your system

### Quick Start with Docker

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Build and run with Docker directly:**
   ```bash
   # Build the image
   docker build -t task-management .

   # Run the container
   docker run -p 8000:8000 task-management
   ```

3. **Access the application:**
   Open your browser and navigate to `http://localhost:8000`

### Docker Configuration

The Docker setup includes:
- **Multi-stage build**: Builds React frontend and Python backend separately
- **Health checks**: Automatic health monitoring via `/health` endpoint
- **Non-root user**: Runs with non-privileged user for security
- **Optimized layers**: Efficient caching for faster rebuilds

### Production Considerations

For production deployment:
1. Change the `SECRET_KEY` environment variable
2. Use a proper database (PostgreSQL/MySQL) instead of SQLite
3. Add a reverse proxy (nginx) for SSL termination
4. Set up proper volume mounting for persistent data
5. Configure proper logging and monitoring

## Project Structure

```
TaskManagement/
├── main.py                 # FastAPI backend application
├── config.py              # Configuration settings
├── database.py            # Database connection
├── models.py              # SQLAlchemy models
├── schemas.py              # Pydantic schemas
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── templates/              # Jinja2 HTML templates (server-rendered)
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── tasks.html
│   ├── task_form.html
│   ├── task_detail.html
│   ├── projects.html
│   └── project_form.html
├── static/                 # Static files
│   └── css/
│       └── custom.css
└── frontend/               # React frontend (optional alternative)
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── index.css
```

## Setup & Installation

### Backend (FastAPI)

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   # or
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application:**
   - Open browser: http://localhost:8000
   - API docs: http://localhost:8000/docs

### Frontend (React - Optional Alternative)

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

4. **Access the React app:**
   - Open browser: http://localhost:3000

## Default Login Credentials

- **Username:** admin
- **Password:** admin123

## API Endpoints

### Authentication
- `POST /api/login` - Login
- `POST /api/logout` - Logout
- `POST /api/register` - Register new user

### Tasks
- `GET /api/tasks` - List all tasks (with filters)
- `POST /api/tasks` - Create new task
- `GET /api/tasks/{id}` - Get task details
- `PUT /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/favorite` - Toggle favorite

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Comments
- `GET /api/tasks/{id}/comments` - Get task comments
- `POST /api/tasks/{id}/comments` - Add comment
- `PUT /api/comments/{id}` - Update comment
- `DELETE /api/comments/{id}` - Delete comment

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

## Task Statuses

- **To Do** - Task is pending
- **In Progress** - Task is being worked on
- **Review** - Task is under review
- **Done** - Task is completed

## Task Priorities

- **Low** - Low priority
- **Medium** - Medium priority (default)
- **High** - High priority
- **Urgent** - Urgent priority

## Technology Stack

### Backend
- Python 3.14
- FastAPI
- SQLAlchemy
- SQLite (default database)
- Pydantic

### Frontend (Option 1)
- Jinja2 Templates
- Bootstrap 5
- Chart.js
- Vanilla JavaScript

### Frontend (Option 2 - React)
- React 18
- React Router
- Tailwind CSS
- Axios
- Lucide Icons

## Database

The application uses SQLite by default. The database file `task_management.db` will be created automatically on first run.

To use a different database, update the `DATABASE_URL` in `config.py`:
- PostgreSQL: `postgresql://user:password@localhost/dbname`
- MySQL: `mysql://user:password@localhost/dbname`

## Development

### Running Tests
```bash
# Backend tests (if implemented)
pytest
```

### Building for Production

**Backend:**
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

**Frontend (React):**
```bash
cd frontend
npm run build
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
