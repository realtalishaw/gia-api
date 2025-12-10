# Tests

This directory contains tests for the GIA project, including API, context engine, and other components.

## Setup

### 1. Activate Virtual Environment

Make sure you have a virtual environment activated with all dependencies installed:

```bash
# If you have a venv in the project
source venv/bin/activate  # or .venv/bin/activate

# Or create one if needed
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd api
pip install -r requirements.txt
cd ..
```

### 2. Verify Dependencies

Check that celery and other dependencies are available:

```bash
python -c "import celery; print('Celery OK')"
python -c "import pytest; print('Pytest OK')"
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run only unit tests (skip integration tests):
```bash
pytest -m "not integration"
```

### Run only integration tests:
```bash
pytest -m integration
```

### Run a specific test file:
```bash
pytest tests/test_context_worker.py
```

### Run with verbose output:
```bash
pytest -v
```

## Test Structure

- `test_context_worker.py` - Tests for context worker ingestion functionality
  - Unit tests with mocked dependencies
  - Integration tests that require Supabase credentials

## Integration Tests

Integration tests require environment variables to be set:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY` - Supabase API key

Integration tests are marked with `@pytest.mark.integration` and will be skipped if credentials are not available.

## Troubleshooting

### "ModuleNotFoundError: No module named 'celery'"

This means celery is not installed in the current Python environment. Solutions:

1. **Activate your virtual environment:**
   ```bash
   source venv/bin/activate  # or wherever your venv is
   ```

2. **Install dependencies:**
   ```bash
   cd api
   pip install -r requirements.txt
   cd ..
   ```

3. **Verify pytest is using the correct Python:**
   ```bash
   which pytest
   which python
   # They should both point to your venv
   ```

4. **Run pytest with the venv Python explicitly:**
   ```bash
   python -m pytest
   ```

### "ImportError" when importing test modules

Make sure you're running pytest from the project root directory, not from the `tests/` or `api/` directory.

## Writing New Tests

1. Create test files following the pattern `test_*.py` in the `tests/` directory
2. Use `@pytest.mark.integration` for tests that require external services
3. Mock external dependencies for unit tests
4. Follow the existing test structure and naming conventions
5. Import from `api.` prefix for API components (e.g., `from api.context_engine.worker.tasks import ...`)
