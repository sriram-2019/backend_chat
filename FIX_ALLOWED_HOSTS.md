# Fix ALLOWED_HOSTS Error on PythonAnywhere

## Error Message
```
Invalid HTTP_HOST header: 'chatbackend1.pythonanywhere.com'. 
You may need to add 'chatbackend1.pythonanywhere.com' to ALLOWED_HOSTS.
```

## Solution

### Step 1: Update settings.py on PythonAnywhere

1. Go to PythonAnywhere → **Files** tab
2. Navigate to: `/home/chatbackend1/backend_chat/backend_project/settings.py`
3. Find the line with `ALLOWED_HOSTS`
4. Update it to:

```python
ALLOWED_HOSTS = [
    'chatbackend1.pythonanywhere.com',
    'www.chatbackend1.pythonanywhere.com',
    'localhost',
    '127.0.0.1',
]
```

Or for quick testing (less secure):

```python
ALLOWED_HOSTS = ['*']
```

### Step 2: Also Update CSRF_TRUSTED_ORIGINS

In the same `settings.py` file, find `CSRF_TRUSTED_ORIGINS` and update it:

```python
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://chatbackend1.pythonanywhere.com",
    "http://chatbackend1.pythonanywhere.com",
]
```

### Step 3: Reload Web App

1. Go to PythonAnywhere → **Web** tab
2. Click the green **Reload** button
3. Wait for it to reload (usually takes 10-30 seconds)

### Step 4: Test Again

After reloading, test:
- `https://chatbackend1.pythonanywhere.com/` - Should return JSON
- `https://chatbackend1.pythonanywhere.com/api/login/` - Should work

## Quick Copy-Paste for settings.py

Replace the `ALLOWED_HOSTS` line in your PythonAnywhere `settings.py`:

```python
ALLOWED_HOSTS = [
    'chatbackend1.pythonanywhere.com',
    'www.chatbackend1.pythonanywhere.com',
    'localhost',
    '127.0.0.1',
]
```

And update `CSRF_TRUSTED_ORIGINS`:

```python
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://chatbackend1.pythonanywhere.com",
    "http://chatbackend1.pythonanywhere.com",
]
```

## Why This Happens

Django's security middleware checks the `Host` header of incoming requests. If the host is not in `ALLOWED_HOSTS`, Django raises a `DisallowedHost` exception, which results in a 400 Bad Request error.

This is a security feature to prevent HTTP Host header attacks.

