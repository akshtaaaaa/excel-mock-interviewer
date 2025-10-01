# Excel Interview Assistant

A Streamlit-based chat interface for conducting Excel interviews with AI-powered question generation and evaluation.

## Features

- 🎯 **Interactive Chat Interface**: Chat-like UI for natural conversation flow
- 📊 **Advanced Excel Questions**: AI-generated challenging Excel interview questions
- 📈 **Real-time Evaluation**: Immediate scoring and feedback after each answer
- 📱 **Progress Tracking**: Visual progress bar and question counter
- 🎨 **Modern UI**: Clean, responsive design with custom styling
- 🔄 **Session Management**: Maintains interview state throughout the session
- 📊 **Comprehensive Logging**: Track errors, token usage, and performance metrics
- 📈 **Analytics Dashboard**: Real-time metrics display in sidebar
- 📥 **Downloadable Reports**: Get detailed session logs and interview results

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Google API Key

Create a `.env` file in the project directory:

```bash
# .env
GOOGLE_API_KEY=your_google_api_key_here
```

Or set the environment variable:

```bash
export GOOGLE_API_KEY='your_google_api_key_here'
```

### 3. Run the Streamlit App

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## How to Use

1. **Start the Interview**: The app will automatically generate the first Excel question
2. **Answer Questions**: Type your answers in the chat input at the bottom
3. **Get Feedback**: Receive immediate evaluation with scores (0-5) and feedback
4. **Track Progress**: Monitor your progress with the sidebar progress bar
5. **View Summary**: See your final scores and answers summary at the end

## Features Overview

### Chat Interface
- Clean, modern chat UI with message bubbles
- Real-time typing indicators during question generation and evaluation

### Question Generation
- AI-powered Excel questions that get progressively challenging
- Questions consider your previous answers for better follow-ups
- Each question is generated individually to maintain focus

### Evaluation System
- Immediate scoring on a 0-5 scale
- Detailed feedback for each answer
- Color-coded scores (green for high, yellow for medium, red for low)

### Session Management
- Maintains interview state throughout the session
- Progress tracking with visual indicators
- Reset functionality to start over

## File Structure

```
├── streamlit_app.py      # Main Streamlit application
├── admin_logs.py        # Admin script for log analysis
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── logs/                # Log files directory (auto-created)
│   └── excel_interview_YYYYMMDD.log
└── README.md           # This file
```

## Technical Details

- **Framework**: Streamlit
- **LLM**: Google Gemini 2.5 Flash
- **Language**: Python 3.8+
- **Dependencies**: See requirements.txt


## Logging & Analytics

The application includes comprehensive logging for administrators:

### Background Logging
- All API calls and token usage tracked
- Error logging with stack traces
- Session completion summaries
- Automatic log cleanup (7-day retention)

### Admin Tools
```bash
# View today's logs
python3 admin_logs.py logs

# Analyze token usage
python3 admin_logs.py tokens

# Clean up old logs
python3 admin_logs.py cleanup
```

### Log Files
- Daily log files: `logs/excel_interview_YYYYMMDD.log`
- Contains all API calls, errors, and session data
- Human-readable format for easy analysis
- Automatic rotation and cleanup

