"""
Pytest configuration and fixtures for GIA tests.
"""
import sys
import os
from pathlib import Path

# Add api directory to path for imports
root_dir = Path(__file__).parent.parent
api_dir = root_dir / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Check for required dependencies
def pytest_configure(config):
    """Configure pytest and check for dependencies."""
    missing_deps = []
    
    try:
        import celery
    except ImportError:
        missing_deps.append("celery")
    
    if missing_deps:
        import warnings
        warnings.warn(
            f"Missing dependencies: {', '.join(missing_deps)}. "
            f"Some tests may fail. Install with: cd api && pip install -r requirements.txt",
            UserWarning
        )
