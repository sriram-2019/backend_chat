# PythonAnywhere WSGI Configuration Fix

## Error: `ModuleNotFoundError: No module named 'backend_project'`

This error occurs when PythonAnywhere can't find your Django project module. Here's how to fix it:

## Solution

### Step 1: Find Your Project Path

1. Go to PythonAnywhere **Files** tab
2. Navigate to your project directory (e.g., `/home/yourusername/newchat/backend`)
3. Note the full path

### Step 2: Update WSGI Configuration

1. Go to PythonAnywhere **Web** tab
2. Click on your web app (or create one if you haven't)
3. Scroll down to **"WSGI configuration file"** section
4. Click on the file link to edit it
5. Replace the entire content with:

```python
import os
import sys

# IMPORTANT: Replace 'yourusername' and 'newchat' with your actual values
path = '/home/yourusername/newchat/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Step 3: Verify Your Project Structure

Make sure your project structure on PythonAnywhere looks like this:

```
/home/yourusername/newchat/
└── backend/
    ├── manage.py
    ├── backend_project/
    │   ├── __init__.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── core/
    │   ├── __init__.py
    │   ├── models.py
    │   ├── views.py
    │   └── ...
    └── requirements.txt
```

### Step 4: Common Path Issues

**If your project is directly in `/home/yourusername/backend/`:**

```python
path = '/home/yourusername/backend'
```

**If your project is in `/home/yourusername/mysite/backend/`:**

```python
path = '/home/yourusername/mysite/backend'
```

**If you're using Git and cloned to a specific folder:**

```python
# Check where you cloned it
path = '/home/yourusername/your-repo-name/backend'
```

### Step 5: Reload Web App

After updating the WSGI file:
1. Click the green **"Reload"** button in the Web tab
2. Check the error log if it still fails

## Alternative: Using Virtual Environment

If you're using a virtual environment, add this before the path setup:

```python
import os
import sys

# Activate virtual environment (if using one)
# venv_path = '/home/yourusername/.virtualenvs/yourvenv'
# activate_this = os.path.join(venv_path, 'bin/activate_this.py')
# exec(open(activate_this).read(), {'__file__': activate_this})

# Add project path
path = '/home/yourusername/newchat/backend'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Debugging Steps

1. **Check the error log** in Web tab for more details
2. **Verify the path exists**: Use PythonAnywhere Bash console:
   ```bash
   ls -la /home/yourusername/newchat/backend
   ```
3. **Check if settings.py exists**:
   ```bash
   ls -la /home/yourusername/newchat/backend/backend_project/settings.py
   ```
4. **Test Python import** in Bash:
   ```bash
   cd /home/yourusername/newchat/backend
   python3.10
   >>> import backend_project
   ```
   If this fails, the path is wrong.

## Quick Fix Template

Copy this and replace `yourusername` and `newchat`:

```python
import os
import sys

path = '/home/YOUR_USERNAME_HERE/YOUR_PROJECT_FOLDER_HERE/backend'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Still Having Issues?

1. Make sure you're using Python 3.10 (or the version you installed Django with)
2. Check that all files were uploaded correctly
3. Verify `backend_project/__init__.py` exists
4. Check file permissions (should be readable)

