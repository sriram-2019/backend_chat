# Fix 400 Bad Request Error on PythonAnywhere

## Common Causes and Solutions

### 1. Root URL (/) Not Configured

Your Django project only has `/admin/` and `/api/` routes. Accessing the root `/` will cause a 400 error.

**Solution:** Test the API endpoints directly:
- ✅ `https://chatbackend1.pythonanywhere.com/api/` (might return 400 if no view)
- ✅ `https://chatbackend1.pythonanywhere.com/api/login/` (should work)
- ✅ `https://chatbackend1.pythonanywhere.com/api/register/` (should work)

### 2. Check PythonAnywhere Error Logs

1. Go to **Web** tab in PythonAnywhere
2. Click on **"Error log"** link
3. Look for the actual error message (not just 400)

### 3. Update ALLOWED_HOSTS

Make sure your `settings.py` has:

```python
ALLOWED_HOSTS = ['chatbackend1.pythonanywhere.com', 'www.chatbackend1.pythonanywhere.com']
```

Or for testing:
```python
ALLOWED_HOSTS = ['*']  # Only for testing, change in production
```

### 4. Check if Database is Migrated

Run migrations on PythonAnywhere:

```bash
cd /home/chatbackend1/backend_chat
python3.10 manage.py migrate
```

### 5. Add a Simple Root View (Optional)

If you want the root URL to work, add this to `backend_project/urls.py`:

```python
from django.http import JsonResponse

def root_view(request):
    return JsonResponse({
        'message': 'INTELLIQ SHC API',
        'status': 'running',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/'
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]
```

### 6. Test Specific Endpoints

Try these endpoints to see which ones work:

```bash
# Test login endpoint (GET should work)
curl https://chatbackend1.pythonanywhere.com/api/login/

# Test register endpoint
curl https://chatbackend1.pythonanywhere.com/api/register/

# Test with POST (for actual API calls)
curl -X POST https://chatbackend1.pythonanywhere.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### 7. Check CORS Settings

For production, update CORS in `settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://localhost:3000",  # For local dev
]

CSRF_TRUSTED_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://chatbackend1.pythonanywhere.com",
]
```

### 8. Verify WSGI Configuration

Make sure your WSGI file has the correct path:

```python
import os
import sys

path = '/home/chatbackend1/backend_chat'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Quick Diagnostic Steps

1. **Check Error Log:**
   - Web tab → Error log
   - Look for the actual error message

2. **Test API Endpoint:**
   ```bash
   curl https://chatbackend1.pythonanywhere.com/api/login/
   ```

3. **Check if Server is Running:**
   - Web tab → Check if web app shows "Running"

4. **Verify Settings:**
   - Make sure `ALLOWED_HOSTS` includes your domain
   - Make sure `DEBUG = False` in production

5. **Check Static Files:**
   - Web tab → Static files section
   - Make sure static files are configured

## Most Likely Issue

The 400 error on root `/` is **normal** - you don't have a view for it. 

**Test the actual API endpoints:**
- `https://chatbackend1.pythonanywhere.com/api/login/` (GET should return something)
- `https://chatbackend1.pythonanywhere.com/api/register/` (POST with data)

If these also return 400, check the error log for the specific error message.

