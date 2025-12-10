#!/usr/bin/env python3
"""
Start script for GIA services.

Usage:
    python start.py                    # Interactive mode - choose services
    python start.py --all              # Start all services
    python start.py --api --worker     # Start specific services
    python start.py --help             # Show help

Available services:
    --api              FastAPI server
    --task-worker      Celery task worker (agent tasks)
    --context-worker   Celery context worker (context ingestion)
    --flower           Flower monitoring dashboard (task worker, port 5555)
    --flower-context   Flower monitoring dashboard (context worker, port 5556)
    --web              Admin panel web app
"""
import subprocess
import sys
import signal
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

# Service configurations
# Detect Python executable
PYTHON_EXE = sys.executable

SERVICES = {
    'api': {
        'name': 'API Server',
        'color': Colors.CYAN,
        'command': [PYTHON_EXE, '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'],
        'cwd': 'api',
        'env': {},
    },
    'task-worker': {
        'name': 'Task Worker',
        'color': Colors.GREEN,
        'command': [PYTHON_EXE, '-m', 'celery', '-A', 'worker.celery_app', 'worker', '--loglevel=info', 
                   '--queues=agent_initialization_queue,agent_results_queue'],
        'cwd': 'api',
        'env': {},
    },
    'context-worker': {
        'name': 'Context Worker',
        'color': Colors.MAGENTA,
        'command': [PYTHON_EXE, '-m', 'celery', '-A', 'context_engine.worker.celery_app', 'worker', 
                   '--loglevel=info', '--queues=context_queue'],
        'cwd': 'api',
        'env': {},
    },
    'flower': {
        'name': 'Flower Monitoring (Task Worker)',
        'color': Colors.YELLOW,
        'command': [PYTHON_EXE, '-m', 'celery', '-A', 'worker.celery_app', 'flower', '--port=5555', 
                   '--address=0.0.0.0', '--unauthenticated_api'],
        'cwd': 'api',
        'env': {},
    },
    'flower-context': {
        'name': 'Flower Monitoring (Context Worker)',
        'color': Colors.YELLOW,
        'command': [PYTHON_EXE, '-m', 'celery', '-A', 'context_engine.worker.celery_app', 'flower', 
                   '--port=5556', '--address=0.0.0.0', '--unauthenticated_api'],
        'cwd': 'api',
        'env': {},
    },
    'web': {
        'name': 'Admin Panel',
        'color': Colors.BLUE,
        'command': ['npm', 'run', 'dev'],
        'cwd': 'admin-panel',
        'env': {},
    },
}

# Store running processes
processes: List[subprocess.Popen] = []

# Get the Python executable being used
PYTHON_EXE = sys.executable


def print_colored(message: str, color: str = Colors.RESET, service: Optional[str] = None):
    """Print colored message with optional service prefix."""
    prefix = f"[{service}] " if service else ""
    print(f"{color}{prefix}{message}{Colors.RESET}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print_colored("\n\n🛑 Shutting down all services...", Colors.YELLOW)
    for proc in processes:
        if proc.poll() is None:  # Process is still running
            print_colored(f"Stopping {proc.args[0]}...", Colors.YELLOW)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    print_colored("✅ All services stopped.", Colors.GREEN)
    sys.exit(0)


def run_service(service_key: str, service_config: Dict):
    """Run a single service."""
    import queue
    import threading
    
    name = service_config['name']
    color = service_config['color']
    command = service_config['command']
    cwd = Path(__file__).parent / service_config['cwd']
    env = {**os.environ, **service_config['env']}
    
    print_colored(f"🚀 Starting {name}...", color, service_key)
    print_colored(f"   Command: {' '.join(command)}", Colors.RESET, service_key)
    print_colored(f"   Directory: {cwd}", Colors.RESET, service_key)
    
    try:
        # Start the process
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        processes.append(proc)
        
        # Function to read output
        def read_output():
            for line in iter(proc.stdout.readline, ''):
                if line:
                    print_colored(line.rstrip(), color, service_key)
            proc.stdout.close()
        
        # Start output reader in separate thread
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        # Wait for process to complete
        proc.wait()
        if proc.returncode != 0:
            print_colored(f"❌ {name} exited with code {proc.returncode}", Colors.RED, service_key)
        else:
            print_colored(f"✅ {name} stopped", Colors.GREEN, service_key)
    except Exception as e:
        print_colored(f"❌ Error starting {name}: {e}", Colors.RED, service_key)


def run_service_background(service_key: str, service_config: Dict):
    """Run a service in the background (non-blocking)."""
    import threading
    
    def run():
        run_service(service_key, service_config)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread


def interactive_select():
    """Interactive service selection."""
    print_colored("\n" + "="*60, Colors.BOLD)
    print_colored("GIA Services Startup", Colors.BOLD)
    print_colored("="*60 + "\n", Colors.BOLD)
    
    print_colored("Available services:", Colors.BOLD)
    for i, (key, config) in enumerate(SERVICES.items(), 1):
        print_colored(f"  {i}. {config['name']} ({key})", config['color'])
    
    print_colored("\n  a. All services", Colors.BOLD)
    print_colored("  q. Quit\n", Colors.BOLD)
    
    selection = input("Select services (comma-separated numbers, 'a' for all, 'q' to quit): ").strip().lower()
    
    if selection == 'q':
        print_colored("Exiting...", Colors.YELLOW)
        sys.exit(0)
    
    if selection == 'a':
        return list(SERVICES.keys())
    
    selected = []
    for item in selection.split(','):
        item = item.strip()
        try:
            index = int(item) - 1
            if 0 <= index < len(SERVICES):
                selected.append(list(SERVICES.keys())[index])
        except ValueError:
            print_colored(f"Invalid selection: {item}", Colors.RED)
    
    return selected


def check_dependencies():
    """Check if required Python packages are installed."""
    missing = []
    try:
        import celery
    except ImportError:
        missing.append('celery')
    
    try:
        import uvicorn
    except ImportError:
        missing.append('uvicorn')
    
    try:
        import supabase
    except ImportError:
        missing.append('supabase')
    
    if missing:
        print_colored("⚠️  Missing Python dependencies:", Colors.YELLOW)
        for pkg in missing:
            print_colored(f"   - {pkg}", Colors.YELLOW)
        print_colored("\n💡 Install dependencies with:", Colors.CYAN)
        print_colored(f"   cd api && {PYTHON_EXE} -m pip install -r requirements.txt", Colors.CYAN)
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Start GIA services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--api', action='store_true', help='Start API server')
    parser.add_argument('--task-worker', action='store_true', help='Start task worker')
    parser.add_argument('--context-worker', action='store_true', help='Start context worker')
    parser.add_argument('--flower', action='store_true', help='Start Flower monitoring (task worker)')
    parser.add_argument('--flower-context', action='store_true', help='Start Flower monitoring (context worker)')
    parser.add_argument('--web', action='store_true', help='Start admin panel web app')
    parser.add_argument('--all', action='store_true', help='Start all services')
    parser.add_argument('--skip-deps-check', action='store_true', help='Skip dependency check')
    
    args = parser.parse_args()
    
    # Check dependencies unless skipped
    if not args.skip_deps_check:
        if not check_dependencies():
            print_colored("\n❌ Please install missing dependencies before starting services.", Colors.RED)
            sys.exit(1)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Determine which services to start
    if args.all:
        selected_services = list(SERVICES.keys())
    elif any([args.api, args.task_worker, args.context_worker, args.flower, args.flower_context, args.web]):
        selected_services = []
        if args.api:
            selected_services.append('api')
        if args.task_worker:
            selected_services.append('task-worker')
        if args.context_worker:
            selected_services.append('context-worker')
        if args.flower:
            selected_services.append('flower')
        if args.flower_context:
            selected_services.append('flower-context')
        if args.web:
            selected_services.append('web')
    else:
        # Interactive mode
        selected_services = interactive_select()
    
    if not selected_services:
        print_colored("No services selected. Exiting.", Colors.YELLOW)
        sys.exit(0)
    
    print_colored(f"\n🚀 Starting {len(selected_services)} service(s)...\n", Colors.BOLD)
    
    # Start all selected services in background threads
    threads = []
    for service_key in selected_services:
        if service_key in SERVICES:
            thread = run_service_background(service_key, SERVICES[service_key])
            threads.append(thread)
            time.sleep(0.5)  # Small delay between starts
        else:
            print_colored(f"⚠️  Unknown service: {service_key}", Colors.YELLOW)
    
    print_colored("\n✅ All services started!", Colors.GREEN)
    print_colored("Press Ctrl+C to stop all services\n", Colors.YELLOW)
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
            # Check if any process died unexpectedly
            for proc in processes:
                if proc.poll() is not None and proc.returncode != 0:
                    print_colored(f"\n⚠️  A service has stopped unexpectedly. Check logs above.", Colors.YELLOW)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    main()
