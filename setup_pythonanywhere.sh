#!/bin/bash
# PythonAnywhere Setup Script (Shell Version)
# Run this script from the backend directory

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}INTELLIQ SHC - PythonAnywhere Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found!${NC}"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python3 --version

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python3 -m pip install --user --upgrade pip

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
python3 -m pip install --user -r requirements.txt

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p staticfiles
mkdir -p media
mkdir -p media/documents

# Run migrations
echo -e "${YELLOW}Running migrations...${NC}"
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python3 manage.py collectstatic --noinput

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Configure Web app in PythonAnywhere dashboard"
echo "2. Update WSGI configuration file"
echo "3. Set up static files mapping"
echo "4. Configure environment variables"
echo "5. Reload your web app"
echo -e "\nSee PYTHONANYWHERE_SETUP.md for detailed instructions"

