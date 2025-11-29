# GIA API

A FastAPI application with modular route structure.

## Setup

1. Create and activate virtual environment:
```bash
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

Start the development server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Available Endpoints

### Health Check
- `GET /health` - Health check endpoint
- `GET /health/heartbeat` - Heartbeat endpoint for monitoring

### Root
- `GET /` - Root endpoint with API information

## Project Structure

```
gia-api/
├── main.py                 # FastAPI application entry point
├── routes/                 # Routes package
│   └── health/            # Health route module
│       ├── __init__.py
│       └── health.py      # Health check endpoints
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Adding New Routes

To add a new route module:

1. Create a new folder under `routes/` (e.g., `routes/users/`)
2. Add `__init__.py` to the folder
3. Create your route file (e.g., `users.py`) with a router
4. Import and include the router in `main.py`

Example:
```python
from routes.users.users import router as users_router
app.include_router(users_router, prefix="/users", tags=["Users"])
```

# gia-api
