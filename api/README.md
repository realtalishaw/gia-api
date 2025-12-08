# API

FastAPI backend for the General Intelligence Agency.

## Setup

1. Activate the virtual environment:
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

- `POST /agent` - Create a new agent
- `GET /agents` - Get all agents
- `POST /agents/feedback` - Submit feedback for an agent
- `POST /webhook` - Handle webhook events


