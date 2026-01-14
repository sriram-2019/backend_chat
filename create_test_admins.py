"""
Standalone script to create test admin users.
Run this from anywhere: python create_test_admins.py
The script will automatically find the project root.
"""
import os
import sys
import django

# Find project root by looking for manage.py or backend_project directory
script_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = script_dir

# Try to find project root (directory containing manage.py and backend_project/)
project_root = None
for _ in range(5):  # Search up to 5 levels up
    if os.path.exists(os.path.join(current_dir, 'manage.py')) and \
       os.path.exists(os.path.join(current_dir, 'backend_project')):
        project_root = current_dir
        break
    parent_dir = os.path.dirname(current_dir)
    if parent_dir == current_dir:  # Reached filesystem root
        break
    current_dir = parent_dir

if not project_root:
    print("Error: Could not find project root directory.")
    print("Please run this script from the project root (where manage.py is located).")
    print(f"Current directory: {script_dir}")
    sys.exit(1)

# Add project root to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Change to project root directory
os.chdir(project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    print(f"Project root found: {project_root}")
    print(f"Make sure backend_project/settings.py exists and is valid.")
    sys.exit(1)

from django.contrib.auth.models import User
from core.models import AdminProfile

def create_test_admins():
    test_admins = [
        {
            'email': 'admin1@test.com',
            'password': 'admin123',
            'full_name': 'Dr. John Smith',
            'username': 'admin1',
            'prof_id': 'PROF001',
            'phone': '+1234567890',
            'department': 'Computer Science'
        },
        {
            'email': 'admin2@test.com',
            'password': 'admin123',
            'full_name': 'Dr. Sarah Johnson',
            'username': 'admin2',
            'prof_id': 'PROF002',
            'phone': '+1234567891',
            'department': 'Mathematics'
        },
        {
            'email': 'admin3@test.com',
            'password': 'admin123',
            'full_name': 'Prof. Michael Brown',
            'username': 'admin3',
            'prof_id': 'PROF003',
            'phone': '+1234567892',
            'department': 'Physics'
        },
        {
            'email': 'admin4@test.com',
            'password': 'admin123',
            'full_name': 'Dr. Emily Davis',
            'username': 'admin4',
            'prof_id': 'PROF004',
            'phone': '+1234567893',
            'department': 'Chemistry'
        },
        {
            'email': 'admin5@test.com',
            'password': 'admin123',
            'full_name': 'Prof. David Wilson',
            'username': 'admin5',
            'prof_id': 'PROF005',
            'phone': '+1234567894',
            'department': 'Engineering'
        },
    ]

    created_count = 0
    skipped_count = 0

    print("Creating test admin users...")
    print("=" * 60)

    for admin_data in test_admins:
        email = admin_data['email']
        username = admin_data['username']
        
        # Check if user already exists
        if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
            print(f"⚠ Skipping {email} - already exists")
            skipped_count += 1
            continue

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=admin_data['password'],
                is_staff=True  # Admin users are staff
            )

            # Create admin profile
            AdminProfile.objects.create(
                user=user,
                full_name=admin_data['full_name'],
                email=email,
                prof_id=admin_data['prof_id'],
                phone=admin_data['phone'],
                department=admin_data['department']
            )

            print(f"✓ Created: {admin_data['full_name']} ({email})")
            created_count += 1

        except Exception as e:
            print(f"✗ Error creating {email}: {str(e)}")

    print("=" * 60)
    print(f"Summary: {created_count} created, {skipped_count} skipped")
    print("=" * 60)
    print("\nTest Admin Credentials:")
    print("Email: admin1@test.com through admin5@test.com")
    print("Password: admin123 (for all)")
    print("\nYou can now test admin login with these credentials.")

if __name__ == '__main__':
    create_test_admins()
