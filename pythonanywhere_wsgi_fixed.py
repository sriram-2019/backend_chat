"""
PythonAnywhere WSGI Configuration File
Copy this content to your PythonAnywhere Web tab -> WSGI configuration file

For project structure: /home/chatbackend1/backend_chat/backend_project/
The path should point to: /home/chatbackend1/backend_chat/
"""

import os
import sys

# Add your project directory to the Python path
# This should be the directory that CONTAINS backend_project folder
# For your structure: /home/chatbackend1/backend_chat/
path = '/home/chatbackend1/backend_chat'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

