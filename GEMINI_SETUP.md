# Gemini AI Integration Setup Guide

## Prerequisites

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Setup Steps

### 1. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key

### 2. Create .env File

Create a `.env` file in the `backend` directory (same level as `manage.py`):

```env
GEMINI_API_KEY=your_actual_api_key_here
```

**Important**: Replace `your_actual_api_key_here` with your actual Gemini API key.

### 3. Run Migrations

After adding the new models (KnowledgeBase and intent field), run:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 4. Test the Integration

Start your Django server:

```bash
python manage.py runserver
```

The chat endpoint (`/api/chat/`) will now use Gemini AI to respond to messages.

## How It Works

1. **Knowledge Base First**: The system first checks if there's a matching question in the Knowledge Base
2. **AI Fallback**: If no match is found, it uses Gemini AI with conversation context
3. **Context Management**: The last 10 messages are used to provide context to the AI
4. **History Saved**: All conversations are saved to the database for future context

## Adding Knowledge Base Entries

You can add Q&A pairs to the Knowledge Base through Django Admin:

1. Go to `/admin/`
2. Navigate to "Knowledge Base"
3. Add questions and answers

## Troubleshooting

- **"AI service is not configured"**: Make sure your `.env` file exists and contains `GEMINI_API_KEY`
- **Import errors**: Make sure you've installed all requirements: `pip install -r requirements.txt`
- **API errors**: Check that your Gemini API key is valid and has sufficient quota

