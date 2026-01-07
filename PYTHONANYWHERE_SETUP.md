# PythonAnywhere Deployment Guide

This guide will help you deploy the INTELLIQ SHC Django backend on PythonAnywhere.

## Quick Setup (Automated)

1. **Upload your project to PythonAnywhere**
   ```bash
   # Option 1: Using Git (Recommended)
   cd ~
   git clone <your-repo-url> newchat
   cd newchat/backend
   
   # Option 2: Using Files tab
   # Upload your project files via PythonAnywhere Files tab
   ```

2. **Run the automated setup script**
   ```bash
   cd ~/newchat/backend  # or your project path
   python3.10 auto_setup_pythonanywhere.py
   ```

3. **Follow the on-screen instructions**

## Manual Setup

### Step 1: Install Dependencies

```bash
cd ~/newchat/backend
pip3.10 install --user -r requirements.txt
```

### Step 2: Configure Settings

1. Update `backend_project/settings.py`:
   ```python
   ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']
   DEBUG = False
   ```

2. Create `.env` file:
   ```bash
   nano .env
   ```
   Add:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=yourusername.pythonanywhere.com
   ```

### Step 3: Run Migrations

```bash
python3.10 manage.py migrate
```

### Step 4: Collect Static Files

```bash
python3.10 manage.py collectstatic --noinput
```

### Step 5: Configure Web App

1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** → **"Python 3.10"**
4. Click **"Next"**

### Step 6: Configure WSGI File

1. Click on the WSGI configuration file link
2. Replace the content with:

```python
import os
import sys

# Add your project directory to the path
path = '/home/yourusername/newchat/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend_project.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Important:** Replace `yourusername` with your actual PythonAnywhere username and update the path if different.

### Step 7: Configure Static Files

In the **Web** tab, scroll to **"Static files"** section:

1. **Static files:**
   - URL: `/static/`
   - Directory: `/home/yourusername/newchat/backend/staticfiles`

2. **Media files:**
   - URL: `/media/`
   - Directory: `/home/yourusername/newchat/backend/media`

### Step 8: Configure Environment Variables

In the **Web** tab, find **"Environment variables"** section and add:

- `SECRET_KEY`: Your Django secret key
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `yourusername.pythonanywhere.com`

### Step 9: Update CORS Settings

Update `backend_project/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://localhost:3000",  # For local development
]

CSRF_TRUSTED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://localhost:3000",
]
```

### Step 10: Reload Web App

Click the green **"Reload"** button in the Web tab.

### Step 11: Test Your API

Visit: `https://yourusername.pythonanywhere.com/api/`

You should see your API endpoints working.

## Database Setup

### SQLite (Default - Free Tier)

SQLite is already configured and works out of the box. No additional setup needed.

### MySQL (Paid Tier)

If you want to use MySQL:

1. **Create MySQL Database:**
   - Go to **Databases** tab
   - Create a new MySQL database
   - Note the database name, username, and password

2. **Update settings.py:**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': os.environ.get('DB_NAME', 'your_db_name'),
           'USER': os.environ.get('DB_USER', 'your_db_user'),
           'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
           'HOST': os.environ.get('DB_HOST', 'yourusername.mysql.pythonanywhere-services.com'),
           'PORT': '3306',
           'OPTIONS': {
               'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
           },
       }
   }
   ```

3. **Install MySQL client:**
   ```bash
   pip3.10 install --user mysqlclient
   ```

4. **Update requirements.txt:**
   ```
   mysqlclient==2.1.1
   ```

5. **Run migrations:**
   ```bash
   python3.10 manage.py migrate
   ```

## Troubleshooting

### Issue: 500 Internal Server Error

1. Check the **Error log** in Web tab
2. Common causes:
   - Wrong path in WSGI file
   - Missing environment variables
   - Database connection issues
   - Import errors

### Issue: Static files not loading

1. Verify static files directory path in Web tab
2. Run `collectstatic` again:
   ```bash
   python3.10 manage.py collectstatic --noinput
   ```

### Issue: CORS errors

1. Update `CORS_ALLOWED_ORIGINS` in settings.py
2. Make sure your frontend URL is included
3. Reload the web app

### Issue: Database locked (SQLite)

SQLite can have locking issues on PythonAnywhere. Consider:
- Using MySQL (paid tier)
- Or ensure only one process accesses the database

### Issue: Module not found

1. Install missing packages:
   ```bash
   pip3.10 install --user <package-name>
   ```

2. Check Python version matches (3.10 recommended)

## Security Checklist

- [ ] Set `DEBUG = False` in production
- [ ] Use a strong `SECRET_KEY`
- [ ] Update `ALLOWED_HOSTS` with your domain
- [ ] Configure CORS properly
- [ ] Use HTTPS (PythonAnywhere provides this)
- [ ] Keep dependencies updated
- [ ] Don't commit `.env` file to Git

## Updating Your App

1. **Pull latest changes:**
   ```bash
   cd ~/newchat
   git pull
   ```

2. **Install new dependencies:**
   ```bash
   cd backend
   pip3.10 install --user -r requirements.txt
   ```

3. **Run migrations:**
   ```bash
   python3.10 manage.py migrate
   ```

4. **Collect static files:**
   ```bash
   python3.10 manage.py collectstatic --noinput
   ```

5. **Reload web app** in Web tab

## API Endpoints

Your API will be available at:
- Base URL: `https://yourusername.pythonanywhere.com/api/`
- Example: `https://yourusername.pythonanywhere.com/api/login/`
- Example: `https://yourusername.pythonanywhere.com/api/chat/message/`

## Frontend Configuration

Update your frontend `.env` or API configuration:

```javascript
// lib/api.ts or similar
const API_BASE_URL = 'https://yourusername.pythonanywhere.com/api';
```

## Support

For issues:
1. Check PythonAnywhere error logs
2. Check Django logs in console
3. Verify all paths and configurations
4. Test endpoints using curl or Postman

## Notes

- Free tier has limitations (limited requests, no always-on tasks)
- Consider upgrading for production use
- Scheduled tasks require paid tier
- File uploads are limited on free tier

