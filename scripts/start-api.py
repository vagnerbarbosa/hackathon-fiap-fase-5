#!/usr/bin/env python3
"""
Start API script - Cross-platform (Linux, macOS, Windows)
Universal fallback that works on any OS with Python 3.

Usage: python scripts/start-api.py [options]
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_project_dir() -> Path:
    """Get project root directory."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent


def check_docker() -> bool:
    """Check if Docker is installed."""
    if shutil.which("docker") is None:
        print("❌ Error: Docker is not installed")
        print("Please install Docker from: https://docs.docker.com/get-docker/")
        return False
    return True


def check_docker_compose() -> str | None:
    """Check if Docker Compose is installed and return command."""
    # Try 'docker compose' (newer) first
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True,
            text=True,
            check=True
        )
        return "docker compose"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try 'docker-compose' (older)
    if shutil.which("docker-compose") is not None:
        return "docker-compose"

    print("❌ Error: Docker Compose is not installed")
    print("Please install Docker Compose from: https://docs.docker.com/compose/install/")
    return None


def setup_env_file(project_dir: Path) -> None:
    """Create .env file from .env.example if not exists."""
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"

    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        if env_example.exists():
            print("Creating .env from .env.example...")
            shutil.copy(env_example, env_file)
            print("✅ Created .env file")
            print("")
            print("⚠️  Please edit .env file with your configuration:")
            print("  - Set DATABASE_URL")
            print("  - Set API_KEY (for production)")
            print("  - Adjust other settings as needed")
            print("")
            input("Press Enter to continue or Ctrl+C to exit and edit .env first...")
        else:
            print("❌ Error: Neither .env nor .env.example found")
            sys.exit(1)


def run_command(cmd: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"🔄 Running: {cmd}")
    result = subprocess.run(
        cmd if platform.system() == "Windows" else cmd.split(),
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def wait_for_services(timeout: int = 60) -> tuple[bool, bool]:
    """Wait for API and Frontend to be healthy."""
    import urllib.request
    import urllib.error

    print("⏳ Waiting for services to be ready...")
    start_time = time.time()
    api_healthy = False
    frontend_healthy = False

    while time.time() - start_time < timeout:
        # Check API
        if not api_healthy:
            try:
                response = urllib.request.urlopen(
                    "http://localhost:8001/health",
                    timeout=2
                )
                if response.status == 200:
                    print("✅ API is healthy")
                    api_healthy = True
            except (urllib.error.URLError, urllib.error.HTTPError):
                pass

        # Check Frontend
        if not frontend_healthy:
            try:
                response = urllib.request.urlopen(
                    "http://localhost:5173",
                    timeout=2
                )
                if response.status == 200:
                    print("✅ Frontend is healthy")
                    frontend_healthy = True
            except (urllib.error.URLError, urllib.error.HTTPError):
                pass

        # Break if both are healthy
        if api_healthy and frontend_healthy:
            return True, True

        print(f"⏳ Waiting... API: {api_healthy} | Frontend: {frontend_healthy}", end="\r")
        time.sleep(2)

    if not api_healthy:
        print("❌ API failed to start within expected time")
    if not frontend_healthy:
        print("⚠️ Frontend may still be starting...")

    return api_healthy, frontend_healthy


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Start the FIAP STRIDE API + FRONTEND with Docker Compose",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/start-api.py              # Start API + Frontend with build
  python scripts/start-api.py --no-build   # Start quickly without rebuild
  python scripts/start-api.py --foreground # Run in foreground mode

Services started:
  • Frontend (React): http://localhost:5173
  • API (FastAPI):    http://localhost:8001
  • PostgreSQL:       localhost:5432
  • Redis:            localhost:6379
"""
    )

    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip Docker build (use existing images)"
    )
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="Run in foreground (don't detach)"
    )
    parser.add_argument(
        "--no-migrations",
        action="store_true",
        help="Skip database migrations"
    )

    args = parser.parse_args()

    # Get project directory
    project_dir = get_project_dir()

    print("=" * 60)
    print("     FIAP STRIDE API + FRONTEND - Docker Startup")
    print("=" * 60)
    print("")

    # Check prerequisites
    if not check_docker():
        sys.exit(1)

    compose_cmd = check_docker_compose()
    if compose_cmd is None:
        sys.exit(1)

    # Setup .env file
    setup_env_file(project_dir)

    # Create directories
    (project_dir / "storage").mkdir(exist_ok=True)
    (project_dir / "logs").mkdir(exist_ok=True)

    # Build and start containers
    if not args.no_build:
        print("🔨 Building and starting containers...")
        run_command(f"{compose_cmd} up --build -d", cwd=project_dir)
    else:
        print("🚀 Starting containers (skipping build)...")
        run_command(f"{compose_cmd} up -d", cwd=project_dir)

    if args.foreground:
        print("👀 Running in foreground mode. Press Ctrl+C to stop.")
        try:
            run_command(f"{compose_cmd} logs -f", cwd=project_dir, check=False)
        except KeyboardInterrupt:
            print("\n👋 Stopped by user")
        return

    # Wait for services
    time.sleep(5)  # Give containers time to start

    api_healthy, frontend_healthy = wait_for_services()
    if not api_healthy:
        print(f"Check logs with: {compose_cmd} logs api")
        sys.exit(1)

    # Run migrations
    if not args.no_migrations:
        print("")
        print("🔄 Running database migrations...")
        try:
            run_command(f"{compose_cmd} exec api alembic upgrade head", cwd=project_dir)
        except SystemExit:
            print("⚠️  Warning: Migrations failed. Database may already be up to date.")

    # Success message
    print("")
    print("=" * 60)
    print("     🚀 API + FRONTEND Started Successfully!")
    print("=" * 60)
    print("")
    print("Frontend (React App):")
    print("  • Application: http://localhost:5173")
    print("")
    print("API Endpoints:")
    print("  • Health Check: http://localhost:8001/health")
    print("  • Swagger UI:   http://localhost:8001/docs")
    print("  • API Version:  http://localhost:8001/version")
    print("")
    print("To stop all services:")
    print(f"  {compose_cmd} down")
    print("")
    print("To view logs:")
    print(f"  API:      {compose_cmd} logs -f api")
    print(f"  Frontend: {compose_cmd} logs -f frontend")
    print("")
    print("Happy hacking! 🛡️🔍")


if __name__ == "__main__":
    main()
