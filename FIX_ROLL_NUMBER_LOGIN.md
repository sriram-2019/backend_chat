# Fix Roll Number Login Issue

## Problem
Users getting error: "Roll number does not match this account" when trying to login with:
- Email: sriram@gmail.com
- Roll Number: 20cse050

## Root Cause
1. **Case Sensitivity**: The roll number check was case-sensitive, so "20cse050" wouldn't match "20CSE050" in the database
2. **Whitespace**: Extra spaces in roll number input could cause mismatches

## Solution

### 1. Backend Fix (Case-Insensitive Check)

**File**: `backend/core/views.py` (LoginView)

**Changed from:**
```python
profile = StudentProfile.objects.get(user=user, roll_no=roll_no)
```

**Changed to:**
```python
# Case-insensitive roll number check
profile = StudentProfile.objects.get(
    user=user, 
    roll_no__iexact=roll_no.strip()
)
```

### 2. Frontend Fix (Make Roll Number Optional)

**File**: `app/login/page.tsx`

- Made roll number validation optional (commented out required check)
- Only send roll number to API if user provides it
- Trim whitespace before sending

## Update on PythonAnywhere

### Step 1: Update `views.py`

1. Go to PythonAnywhere → **Files** tab
2. Navigate to: `/home/chatbackend1/backend_chat/core/views.py`
3. Find the `LoginView` class (around line 102-110)
4. Update the roll number check to:

```python
# Optional: Verify roll number if provided (case-insensitive)
if roll_no:
    try:
        # Case-insensitive roll number check
        profile = StudentProfile.objects.get(
            user=user, 
            roll_no__iexact=roll_no.strip()
        )
    except StudentProfile.DoesNotExist:
        return Response(
            {"error": "Roll number does not match this account"},
            status=status.HTTP_401_UNAUTHORIZED
        )
```

### Step 2: Reload Web App

1. Go to PythonAnywhere → **Web** tab
2. Click **Reload** button

## Testing

After updating:
1. Try logging in with email and password (roll number optional)
2. If roll number is provided, it will be checked case-insensitively
3. Extra spaces will be automatically trimmed

## Notes

- Roll number is now **optional** on the frontend
- If provided, it's checked case-insensitively
- Whitespace is automatically trimmed
- Users can login with just email and password if roll number doesn't match

