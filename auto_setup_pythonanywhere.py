#!/usr/bin/env python3
"""
PythonAnywhere Auto-Setup Script for INTELLIQ SHC Backend
This script automates the complete setup of Django backend on PythonAnywhere
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def run_command(command, check=True, shell=False):
    """Run a shell command and return the result"""
    try:
        if isinstance(command, str) and not shell:
            command = command.split()
        result = subprocess.run(
            command,
            check=check,
            shell=shell,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)

def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Python 3.8+ is required")
        return False
    
    print_success("Python version is compatible")
    return True

def install_requirements():
    """Install Python requirements"""
    print_header("Installing Requirements")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print_error("requirements.txt not found!")
        return False
    
    print_info("Upgrading pip...")
    success, _, _ = run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    if success:
        print_success("Pip upgraded")
    else:
        print_warning("Could not upgrade pip, continuing...")
    
    print_info("Installing requirements from requirements.txt...")
    success, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"
    ])
    
    if success:
        print_success("Requirements installed successfully")
        return True
    else:
        print_error(f"Failed to install requirements: {stderr}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    print_header("Setting Up Environment Variables")
    
    env_file = Path(".env")
    if env_file.exists():
        print_info(".env file already exists, skipping...")
        return True
    
    print_info("Creating .env file...")
    
    # Generate a secure secret key
    import secrets
    secret_key = secrets.token_urlsafe(50)
    
    env_content = f"""# Django Settings
SECRET_KEY={secret_key}
DEBUG=False

# PythonAnywhere Settings
ALLOWED_HOSTS=yourusername.pythonanywhere.com

# Database (SQLite for PythonAnywhere free tier)
# For MySQL, uncomment and configure:
# DB_NAME=your_db_name
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_HOST=yourusername.mysql.pythonanywhere-services.com
# DB_PORT=3306

# Gemini AI (Optional - add your API key)
# GEMINI_API_KEY=your_gemini_api_key_here
"""
    
    try:
        with open(env_file, "w") as f:
            f.write(env_content)
        print_success(".env file created")
        print_warning("Please update .env file with your actual values!")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False

def update_settings_for_pythonanywhere():
    """Update settings.py for PythonAnywhere"""
    print_header("Updating Settings for PythonAnywhere")
    
    settings_file = Path("backend_project/settings.py")
    if not settings_file.exists():
        print_error("settings.py not found!")
        return False
    
    try:
        with open(settings_file, "r") as f:
            content = f.read()
        
        # Check if already updated
        if "pythonanywhere" in content.lower():
            print_info("Settings already configured for PythonAnywhere")
            return True
        
        # Read current settings
        with open(settings_file, "r") as f:
            lines = f.readlines()
        
        # Create backup
        backup_file = Path("backend_project/settings.py.backup")
        with open(backup_file, "w") as f:
            f.writelines(lines)
        print_success("Backup created: settings.py.backup")
        
        # Update settings
        new_lines = []
        for line in lines:
            # Update ALLOWED_HOSTS
            if line.strip().startswith("ALLOWED_HOSTS") and "['*']" in line:
                new_lines.append("ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'yourusername.pythonanywhere.com').split(',')\n")
            # Update DEBUG
            elif line.strip().startswith("DEBUG = True"):
                new_lines.append("DEBUG = os.environ.get('DEBUG', 'False') == 'True'\n")
            # Update STATIC_ROOT for PythonAnywhere
            elif line.strip().startswith("STATIC_URL"):
                new_lines.append(line)
                # Add STATIC_ROOT after STATIC_URL
                if "STATIC_ROOT" not in content:
                    new_lines.append("STATIC_ROOT = BASE_DIR / 'staticfiles'\n")
            else:
                new_lines.append(line)
        
        # Write updated settings
        with open(settings_file, "w") as f:
            f.writelines(new_lines)
        
        print_success("Settings updated for PythonAnywhere")
        return True
        
    except Exception as e:
        print_error(f"Failed to update settings: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    
    directories = [
        "staticfiles",
        "media",
        "media/documents",
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {directory}")
        else:
            print_info(f"Directory already exists: {directory}")
    
    return True

def run_migrations():
    """Run Django migrations"""
    print_header("Running Database Migrations")
    
    # Make migrations
    print_info("Creating migrations...")
    success, stdout, stderr = run_command([sys.executable, "manage.py", "makemigrations"])
    if success:
        print_success("Migrations created")
    else:
        if "No changes detected" in stderr:
            print_info("No new migrations needed")
        else:
            print_warning(f"Migration creation: {stderr}")
    
    # Apply migrations
    print_info("Applying migrations...")
    success, stdout, stderr = run_command([sys.executable, "manage.py", "migrate"])
    
    if success:
        print_success("Migrations applied successfully")
        return True
    else:
        print_error(f"Migration failed: {stderr}")
        return False

def collect_static_files():
    """Collect static files"""
    print_header("Collecting Static Files")
    
    print_info("Collecting static files...")
    success, stdout, stderr = run_command([
        sys.executable, "manage.py", "collectstatic", "--noinput"
    ])
    
    if success:
        print_success("Static files collected")
        return True
    else:
        print_warning(f"Static collection warning: {stderr}")
        return True  # Not critical

def create_superuser():
    """Optionally create superuser"""
    print_header("Superuser Creation")
    
    response = input("Do you want to create a superuser? (y/n): ").strip().lower()
    if response != 'y':
        print_info("Skipping superuser creation")
        return True
    
    print_info("Creating superuser...")
    print_warning("You'll be prompted for username, email, and password")
    
    success, _, _ = run_command([
        sys.executable, "manage.py", "createsuperuser"
    ], check=False)
    
    if success:
        print_success("Superuser created")
    else:
        print_warning("Superuser creation skipped or failed")
    
    return True

def create_wsgi_file():
    """Create WSGI configuration file for PythonAnywhere"""
    print_header("Creating WSGI Configuration")
    
    wsgi_content = """# This file configures your web app on PythonAnywhere
# Add this to your PythonAnywhere Web tab -> WSGI configuration file

import os
import sys

# Add your project directory to the path
path = '/home/yourusername/path/to/your/project/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend_project.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
"""
    
    wsgi_file = Path("pythonanywhere_wsgi.py")
    try:
        with open(wsgi_file, "w") as f:
            f.write(wsgi_content)
        print_success("WSGI configuration file created: pythonanywhere_wsgi.py")
        print_warning("Please update the path in pythonanywhere_wsgi.py with your actual project path")
        return True
    except Exception as e:
        print_error(f"Failed to create WSGI file: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")
    
    print_info("Next steps to deploy on PythonAnywhere:")
    print("\n1. Upload your project files to PythonAnywhere")
    print("   - Use Files tab or Git to upload your code")
    
    print("\n2. Configure Web App:")
    print("   - Go to Web tab in PythonAnywhere dashboard")
    print("   - Click 'Add a new web app'")
    print("   - Choose 'Manual configuration' -> 'Python 3.10' (or your version)")
    print("   - Update WSGI configuration file with content from pythonanywhere_wsgi.py")
    print("   - Update the path in WSGI file to your actual project path")
    
    print("\n3. Configure Static Files:")
    print("   - In Web tab, scroll to 'Static files' section")
    print("   - Add URL: /static/")
    print("   - Add Directory: /home/yourusername/path/to/backend/staticfiles")
    print("   - Add URL: /media/")
    print("   - Add Directory: /home/yourusername/path/to/backend/media")
    
    print("\n4. Configure Environment Variables:")
    print("   - In Web tab, find 'Environment variables' section")
    print("   - Add variables from your .env file")
    print("   - Or use .env file (if supported)")
    
    print("\5. Update ALLOWED_HOSTS:")
    print("   - In settings.py or .env, set ALLOWED_HOSTS to your PythonAnywhere domain")
    print("   - Example: 'yourusername.pythonanywhere.com'")
    
    print("\n6. Reload Web App:")
    print("   - Click the green 'Reload' button in Web tab")
    
    print("\n7. Test your API:")
    print("   - Visit: https://yourusername.pythonanywhere.com/api/")
    print("   - Check if endpoints are working")
    
    print(f"\n{Colors.WARNING}Important Notes:")
    print("   - Update CORS_ALLOWED_ORIGINS in settings.py with your frontend URL")
    print("   - Update CSRF_TRUSTED_ORIGINS with your frontend URL")
    print("   - For production, set DEBUG=False in .env")
    print("   - Keep your SECRET_KEY secure and never commit it to Git")
    print(f"{Colors.ENDC}")

def main():
    """Main setup function"""
    print_header("INTELLIQ SHC - PythonAnywhere Auto-Setup")
    
    # Check if we're in the backend directory
    if not Path("manage.py").exists():
        print_error("Please run this script from the backend directory!")
        print_info("Expected structure: backend/manage.py should exist")
        sys.exit(1)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Requirements", install_requirements),
        ("Create Environment File", create_env_file),
        ("Update Settings", update_settings_for_pythonanywhere),
        ("Create Directories", create_directories),
        ("Run Migrations", run_migrations),
        ("Collect Static Files", collect_static_files),
        ("Create WSGI File", create_wsgi_file),
        ("Create Superuser", create_superuser),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print_error(f"Error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print_header("Setup Completed with Warnings")
        print_warning(f"Some steps failed: {', '.join(failed_steps)}")
        print_info("Please review the errors above and fix them manually")
    else:
        print_success("All setup steps completed successfully!")
    
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

