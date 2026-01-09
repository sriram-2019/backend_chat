# Fix CORS Error with Credentials

## Error Message
```
Access to fetch at 'https://chatbackend1.pythonanywhere.com/api/login/' from origin 'http://localhost:3000' 
has been blocked by CORS policy: Response to preflight request doesn't pass access control check: 
The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' 
when the request's credentials mode is 'include'.
```

## Problem

When using `credentials: 'include'` in fetch requests (which is set in `lib/api.ts`), the server **cannot** use `Access-Control-Allow-Origin: *`. It must specify the exact origin.

## Solution

### Step 1: Update settings.py on PythonAnywhere

1. Go to PythonAnywhere → **Files** tab
2. Navigate to: `/home/chatbackend1/backend_chat/backend_project/settings.py`
3. Find the CORS Settings section (around line 97-103)
4. Update it to:

```python
# CORS Settings
CORS_ALLOW_CREDENTIALS = True
# When CORS_ALLOW_CREDENTIALS is True, you cannot use CORS_ALLOW_ALL_ORIGINS
# Must specify exact origins
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your production frontend URL here when deployed
    # "https://your-frontend-domain.com",
]
```

### Step 2: Reload Web App

1. Go to PythonAnywhere → **Web** tab
2. Click **Reload** button

## Why This Works

- `CORS_ALLOW_CREDENTIALS = True` allows cookies/credentials to be sent
- `CORS_ALLOW_ALL_ORIGINS = False` prevents wildcard `*` origin
- `CORS_ALLOWED_ORIGINS` explicitly lists allowed origins
- This combination allows credentials while maintaining security

## Testing

After updating and reloading:
1. Try logging in from `http://localhost:3000`
2. Check browser console (F12) - CORS error should be gone
3. API requests should work with credentials

## Additional Notes

- If you deploy your frontend to a different domain, add it to `CORS_ALLOWED_ORIGINS`
- For production, consider using environment variables for allowed origins
- Never use `CORS_ALLOW_ALL_ORIGINS = True` with `CORS_ALLOW_CREDENTIALS = True`

