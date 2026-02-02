# AI Assistant - Google Gemini API Setup Guide

## Overview
The AI Assistant feature uses Google's Gemini API for multilingual conversational AI. This guide will help you set up the API key.

## Step 1: Get Your Free Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"** or **"Create API Key"**
4. Copy the generated API key (it will look like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

## Step 2: Configure the API Key

### Option A: Environment Variable (Recommended)

Create or edit the `.env` file in the project root:

```bash
# Add this line to your .env file
GEMINI_API_KEY=your_api_key_here
```

### Option B: Direct Configuration (Development Only)

Edit `api/routes/ai_assistant.py` and replace:
```python
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
```

With:
```python
GEMINI_API_KEY = "your_api_key_here"  # NOT RECOMMENDED FOR PRODUCTION
```

## Step 3: Restart the Backend Server

After adding the API key, restart the FastAPI server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python3 -m uvicorn api.main:app --reload --port 8000
```

## Step 4: Verify Setup

1. Open your browser and navigate to: `http://localhost:8000/api/v1/ai/status`
2. You should see:
   ```json
   {
     "service": "Google Gemini",
     "configured": true,
     "model": "gemini-pro",
     "active_sessions": 0
   }
   ```

If `"configured": false`, the API key is not properly set.

## Step 5: Test the AI Assistant

1. Navigate to the AI Assistant page in your application: `http://localhost:5174/ai-assistant`
2. Type a message in any of the supported languages
3. The AI should respond appropriately

## Supported Languages

The AI Assistant supports 7 languages with both native and Roman script:
- **English** (en)
- **Hindi** (hi) - हिन्दी / Roman
- **Gujarati** (gu) - ગુજરાતી / Roman
- **Marathi** (mr) - मराठी / Roman
- **Tamil** (ta) - தமிழ் / Roman
- **Telugu** (te) - తెలుగు / Roman
- **Urdu** (ur) - اردو / Roman

## Features

✅ Auto-detection of language from user input
✅ Support for both native script and Roman transliteration
✅ Mid-conversation language switching
✅ Context-aware responses for retail intelligence
✅ Quick action buttons for common queries

## Troubleshooting

### "AI service not configured" Error
- Ensure the API key is correctly set in `.env`
- Restart the backend server
- Check `/api/v1/ai/status` endpoint

### API Key Invalid
- Verify the key is copied correctly (no extra spaces)
- Ensure you're using a valid Gemini API key
- Check [Google AI Studio](https://makersuite.google.com/app/apikey) for key status

### Rate Limiting
- Free tier has usage limits
- Monitor your usage at [Google AI Studio](https://makersuite.google.com/)
- Consider upgrading if needed

## API Endpoints

- `POST /api/v1/ai/chat` - Send message to AI
- `GET /api/v1/ai/history/{session_id}` - Get chat history
- `DELETE /api/v1/ai/history/{session_id}` - Clear chat history
- `GET /api/v1/ai/status` - Check service status

## Security Notes

⚠️ **IMPORTANT**: 
- Never commit API keys to version control
- Use environment variables for production
- Add `.env` to `.gitignore`
- Rotate keys periodically
- Monitor API usage for unusual activity

## Next Steps

Once configured, the AI Assistant will be fully functional and ready to help users with:
- Sales data analysis
- Inventory management insights
- Forecasting queries
- Business intelligence questions
- All in 7 different languages!
