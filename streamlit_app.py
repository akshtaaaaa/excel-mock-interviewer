import streamlit as st
import os
import logging
import json
import textwrap
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage
import time
import traceback

# Load environment variables
load_dotenv()

# =========================
# Logging Configuration
# =========================
def setup_logging():
    """Setup comprehensive logging system with rotation"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Clean up old log files (keep only last 7 days)
    cleanup_old_logs()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/excel_interview_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def cleanup_old_logs():
    """Clean up log files older than 7 days"""
    try:
        import glob
        from datetime import timedelta
        
        log_files = glob.glob('logs/*.log')
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_file in log_files:
            file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_time < cutoff_date:
                os.remove(log_file)
                logger.info(f"Removed old log file: {log_file}")
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")

# Initialize logger
logger = setup_logging()

# =========================
# Metrics Tracking
# =========================
class MetricsTracker:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.token_usage = {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'calls': 0
        }
        self.errors = []
        self.questions_generated = 0
        self.evaluations_completed = 0
        self.response_times = []
    
    def log_api_call(self, input_tokens, output_tokens, response_time):
        """Log API call metrics"""
        self.token_usage['total_tokens'] += input_tokens + output_tokens
        self.token_usage['input_tokens'] += input_tokens
        self.token_usage['output_tokens'] += output_tokens
        self.token_usage['calls'] += 1
        self.response_times.append(response_time)
        
        logger.info(f"API Call - Input: {input_tokens}, Output: {output_tokens}, "
                   f"Total: {input_tokens + output_tokens}, Time: {response_time:.2f}s")
    
    def log_error(self, error_type, error_message, traceback_str=None):
        """Log errors with context"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message,
            'traceback': traceback_str
        }
        self.errors.append(error_data)
        logger.error(f"Error - {error_type}: {error_message}")
        if traceback_str:
            logger.error(f"Traceback: {traceback_str}")
    
    def log_question_generated(self, question_number, question_text):
        """Log question generation"""
        self.questions_generated += 1
        logger.info(f"Question {question_number} generated: {question_text[:100]}...")
    
    def log_evaluation_completed(self, question_number, score, response_time):
        """Log evaluation completion"""
        self.evaluations_completed += 1
        logger.info(f"Evaluation {question_number} completed - Score: {score}, Time: {response_time:.2f}s")
    
    def get_session_summary(self):
        """Get complete session summary"""
        total_time = time.time() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        summary = {
            'session_id': self.session_id,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'total_time': total_time,
            'token_usage': self.token_usage,
            'questions_generated': self.questions_generated,
            'evaluations_completed': self.evaluations_completed,
            'errors_count': len(self.errors),
            'avg_response_time': avg_response_time,
            'errors': self.errors
        }
        
        # Log session completion to main log file
        logger.info(f"SESSION COMPLETED - ID: {self.session_id}")
        logger.info(f"Total tokens: {self.token_usage['total_tokens']}")
        logger.info(f"Questions generated: {self.questions_generated}")
        logger.info(f"Evaluations completed: {self.evaluations_completed}")
        logger.info(f"Errors encountered: {len(self.errors)}")
        logger.info(f"Session duration: {total_time:.2f} seconds")
        logger.info(f"Average response time: {avg_response_time:.2f} seconds")
        logger.info("=" * 50)
        
        return summary

# Initialize metrics tracker
metrics = MetricsTracker()

# Page configuration
st.set_page_config(
    page_title="Excel Interview Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    .chat-message.user {
        background-color: #2b313e;
        flex-direction: row-reverse;
        text-align: right;
    }
    .chat-message.bot {
        background-color: #475063;
    }
    .chat-message .avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        margin: 0 1rem;
    }
    .evaluation-box {
        background-color: #1e3a5f;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
        margin: 1rem 0;
    }
    .score-high {
        color: #4ade80;
        font-weight: bold;
    }
    .score-medium {
        color: #fbbf24;
        font-weight: bold;
    }
    .score-low {
        color: #f87171;
        font-weight: bold;
    }
    .summary-container {
        background-color: #1e1e1e;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .summary-row {
        display: flex;
        align-items: flex-start;
        margin-bottom: 1rem;
        padding: 0.5rem;
        border-radius: 0.25rem;
        background-color: #2a2a2a;
    }
    .summary-question {
        flex: 1;
        margin-right: 1rem;
        word-wrap: break-word;
    }
    .summary-score {
        min-width: 80px;
        text-align: center;
        font-weight: bold;
    }
    .answer-text {
        font-size: 0.9rem;
        line-height: 1.4;
        color: #e0e0e0;
    }
    .question-label {
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "session_started" not in st.session_state:
    st.session_state.session_started = True
    logger.info(f"New interview session started - Session ID: {metrics.session_id}")
if "skipped_questions" not in st.session_state:
    st.session_state.skipped_questions = []
if "user_info_collected" not in st.session_state:
    st.session_state.user_info_collected = False
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

# LLM Setup
@st.cache_resource
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ GOOGLE_API_KEY environment variable is not set.")
        st.stop()
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=api_key
    )

llm = get_llm()

# System message
def get_system_message(difficulty_level):
    """Get system message based on difficulty level"""
    if difficulty_level == "Beginner":
        return SystemMessage(
            content="You are an Excel Interviewer AI for BEGINNER level. "
                    "You must ask EXACTLY ONE basic Excel interview question. "
                    "Focus on: basic formulas (SUM, AVERAGE, COUNT), basic functionalities, "
                    "simple data entry, basic formatting, and fundamental Excel concepts. "
                    "Do NOT provide multiple questions. Do NOT provide answers. "
                    "Do NOT continue with follow-up questions. "
                    "Your response should contain ONLY the single question you want to ask."
        )
    elif difficulty_level == "Intermediate":
        return SystemMessage(
            content="You are an Excel Interviewer AI for INTERMEDIATE level. "
                    "You must ask EXACTLY ONE intermediate Excel interview question. "
                    "Focus on: intermediate formulas (VLOOKUP, IF, INDEX/MATCH), "
                    "data analysis, pivot tables, charts, conditional formatting, "
                    "and small case studies with practical scenarios. "
                    "Do NOT provide multiple questions. Do NOT provide answers. "
                    "Do NOT continue with follow-up questions. "
                    "Your response should contain ONLY the single question you want to ask."
        )
    else:  # Advanced
        return SystemMessage(
            content="You are an Excel Interviewer AI for ADVANCED level. "
                    "You must ask EXACTLY ONE advanced Excel interview question. "
                    "Focus on: complex case studies, advanced formulas (array formulas, "
                    "DAX, Power Query), data modeling, automation, complex scenarios "
                    "requiring multiple Excel features, and real-world business problems. "
                    "Do NOT provide multiple questions. Do NOT provide answers. "
                    "Do NOT continue with follow-up questions. "
                    "Your response should contain ONLY the single question you want to ask."
        )

def extract_single_question(response_text):
    """Extract only the first question from the response"""
    lines = response_text.strip().split('\n')
    question_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Stop if we hit a second question indicator
        if line.startswith('Q2:') or line.startswith('Question 2:') or line.startswith('**Question 2:'):
            break
        # Stop if we hit evaluation or feedback sections
        if any(keyword in line.lower() for keyword in ['evaluation:', 'feedback:', 'score:', 'mark:']):
            break
        question_lines.append(line)
    
    return '\n'.join(question_lines).strip()

def generate_question(question_number, previous_answer=None):
    """Generate a question based on the current state and difficulty level"""
    start_time = time.time()
    try:
        # Get difficulty-specific system message
        difficulty_level = st.session_state.user_info.get('difficulty_level', 'Intermediate')
        system_msg = get_system_message(difficulty_level)
        
        if question_number == 1:
            response = llm.invoke(system_msg.content)
        else:
            follow_prompt = f"{system_msg.content}\n\nPrevious answer: {previous_answer}\n\nNow ask the next Excel question."
            response = llm.invoke(follow_prompt)
        
        response_time = time.time() - start_time
        
        # Extract token usage if available
        input_tokens = len(system_msg.content.split()) if question_number == 1 else len(follow_prompt.split())
        output_tokens = len(response.content.split())
        
        # Log metrics
        metrics.log_api_call(input_tokens, output_tokens, response_time)
        
        question_text = extract_single_question(response.content)
        metrics.log_question_generated(question_number, question_text)
        
        # Log difficulty level
        logger.info(f"Question {question_number} generated for {difficulty_level} level")
        
        return question_text
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = f"Error generating question {question_number}: {str(e)}"
        traceback_str = traceback.format_exc()
        
        metrics.log_error("QuestionGeneration", error_msg, traceback_str)
        st.error(f"❌ Error generating question: {e}")
        return None

def evaluate_answer(question, answer):
    """Evaluate the user's answer based on difficulty level"""
    start_time = time.time()
    try:
        # Get difficulty level for context
        difficulty_level = st.session_state.user_info.get('difficulty_level', 'Intermediate')
        
        # Create difficulty-specific evaluation prompt
        if difficulty_level == "Beginner":
            eval_context = "This is a BEGINNER level Excel question. Evaluate based on basic Excel knowledge, simple formulas, and fundamental concepts."
        elif difficulty_level == "Intermediate":
            eval_context = "This is an INTERMEDIATE level Excel question. Evaluate based on intermediate formulas, data analysis skills, and practical application."
        else:  # Advanced
            eval_context = "This is an ADVANCED level Excel question. Evaluate based on complex problem-solving, advanced features, and comprehensive Excel expertise."
        
        eval_prompt = f"Evaluate this Excel answer on a scale of 0-5 and provide brief feedback:\n\n{eval_context}\n\nQuestion: {question}\nAnswer: {answer}\n\nProvide: Score (0-5) and brief feedback."
        eval_response = llm.invoke(eval_prompt)
        
        response_time = time.time() - start_time
        
        # Extract token usage
        input_tokens = len(eval_prompt.split())
        output_tokens = len(eval_response.content.split())
        
        # Log metrics
        metrics.log_api_call(input_tokens, output_tokens, response_time)
        
        # Extract score for logging
        score = extract_score(eval_response.content)
        metrics.log_evaluation_completed(len(st.session_state.evaluations) + 1, score, response_time)
        
        # Log evaluation with difficulty context
        logger.info(f"Answer evaluated for {difficulty_level} level - Score: {score}")
        
        return eval_response.content
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = f"Error evaluating answer: {str(e)}"
        traceback_str = traceback.format_exc()
        
        metrics.log_error("Evaluation", error_msg, traceback_str)
        st.error(f"❌ Error evaluating answer: {e}")
        return "Error in evaluation"

def get_score_color(score):
    """Get color class based on score"""
    if score >= 4:
        return "score-high"
    elif score >= 2:
        return "score-medium"
    else:
        return "score-low"

def extract_score(evaluation_text):
    """Extract score from evaluation text"""
    import re
    score_match = re.search(r'(\d+)/5', evaluation_text)
    if score_match:
        return int(score_match.group(1))
    return 0

# Sidebar
with st.sidebar:
    st.title("📊 Excel Interview")
    st.markdown("---")
    
    # Progress
    progress = (st.session_state.current_question) / 5
    st.progress(progress)
    st.write(f"Question {st.session_state.current_question} of 5")
    
    # Reset button
    if st.button("🔄 Reset Interview", type="secondary"):
        st.session_state.messages = []
        st.session_state.current_question = 0
        st.session_state.interview_completed = False
        st.session_state.user_answers = []
        st.session_state.evaluations = []
        st.session_state.skipped_questions = []
        st.session_state.user_info_collected = False
        st.session_state.user_info = {}
        st.rerun()
    
    # Instructions
    st.markdown("### Instructions")
    st.markdown("""
    1. Answer each Excel question thoughtfully
    2. Provide detailed explanations
    3. Include formulas or steps when relevant
    4. You'll receive feedback after each answer
    5. Use "Skip" if you don't know the answer
    """)
    
    # Session info
    st.markdown("---")
    st.markdown("### ℹ️ Interview Progress")
    st.text(f"Questions: {metrics.questions_generated}/5")
    st.text(f"Evaluations: {metrics.evaluations_completed}")

def collect_user_information():
    """Collect user information before starting interview"""
    st.markdown("### 📋 Interview Information")
    st.markdown("Please provide the following information before starting the interview:")
    
    with st.form("user_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            examiner_name = st.text_input("Examiner Name", placeholder="Enter your name")
            difficulty_level = st.selectbox(
                "Level of Difficulty",
                ["Beginner", "Intermediate", "Advanced"]
            )
        
        with col2:
            interview_date = st.date_input("Interview Date", value=datetime.now().date())
            examiner_profile = st.selectbox(
                "Examiner Profile",
                ["HR Manager", "Technical Lead", "Senior Developer", "Team Lead", "Manager", "Director", "Other"]
            )
        
        # Password field
        password = st.text_input("Password", type="password", placeholder="Enter password to start interview")
        
        submitted = st.form_submit_button("Start Interview", type="primary")
        
        if submitted:
            if not examiner_name or not password:
                st.error("Please fill in all required fields (Examiner Name and Password)")
                return False
            
            # Store user information
            st.session_state.user_info = {
                "examiner_name": examiner_name,
                "difficulty_level": difficulty_level,
                "interview_date": interview_date.strftime("%Y-%m-%d"),
                "examiner_profile": examiner_profile,
                "password_provided": bool(password)
            }
            
            # Log user information
            logger.info("=" * 50)
            logger.info("INTERVIEW INFORMATION COLLECTED")
            logger.info(f"Examiner Name: {examiner_name}")
            logger.info(f"Difficulty Level: {difficulty_level}")
            logger.info(f"Interview Date: {interview_date.strftime('%Y-%m-%d')}")
            logger.info(f"Examiner Profile: {examiner_profile}")
            logger.info(f"Password Provided: {'Yes' if password else 'No'}")
            logger.info("=" * 50)
            
            st.session_state.user_info_collected = True
            st.rerun()
    
    return False

# Main interface
st.title("🎯 Excel Interview Assistant")

# Show user information form if not collected yet
if not st.session_state.user_info_collected:
    st.markdown("Welcome! Please provide your information to start the Excel interview.")
    collect_user_information()
    st.stop()

# Show interview interface after user info is collected
difficulty_level = st.session_state.user_info['difficulty_level']
difficulty_emoji = {"Beginner": "🌱", "Intermediate": "📊", "Advanced": "🚀"}.get(difficulty_level, "📊")

st.markdown(f"Welcome, **{st.session_state.user_info['examiner_name']}**! I'll ask you 5 {difficulty_level.lower()} Excel questions and evaluate your answers.")
st.markdown(f"**Interview Details:** {difficulty_emoji} **{difficulty_level} Level** | {st.session_state.user_info['interview_date']} | {st.session_state.user_info['examiner_profile']}")

# Show difficulty-specific information
if difficulty_level == "Beginner":
    st.info("🎯 **Beginner Level**: Questions will focus on basic Excel formulas, simple functionalities, and fundamental concepts.")
elif difficulty_level == "Intermediate":
    st.info("🎯 **Intermediate Level**: Questions will include intermediate formulas, data analysis, and small case studies.")
else:  # Advanced
    st.info("🎯 **Advanced Level**: Questions will be complex case studies requiring advanced Excel features and problem-solving skills.")

# Chat interface
chat_container = st.container()

with chat_container:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show evaluation if it's a bot message with evaluation
            if message["role"] == "assistant" and "evaluation" in message:
                evaluation = message["evaluation"]
                score = extract_score(evaluation)
                score_class = get_score_color(score)
                
                st.markdown(f"""
                <div class="evaluation-box">
                    <h4>📊 Evaluation</h4>
                    <p><span class="{score_class}">Score: {score}/5</span></p>
                    <p>{evaluation}</p>
                </div>
                """, unsafe_allow_html=True)

# Generate first question if interview hasn't started
if st.session_state.current_question == 0 and not st.session_state.interview_completed:
    with st.spinner("Generating first question..."):
        question = generate_question(1)
        if question:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"**Q1:** {question}"
            })
            st.session_state.current_question = 1
            st.rerun()
def move_to_next_question():
    """Move to the next question or complete interview"""
    if st.session_state.current_question < 5:
        with st.spinner("Generating next question..."):
            # Get the last user input (answer or skip)
            last_user_input = st.session_state.messages[-2]["content"]
            next_question = generate_question(
                st.session_state.current_question + 1, 
                last_user_input
            )
            if next_question:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"**Q{st.session_state.current_question + 1}:** {next_question}"
                })
                st.session_state.current_question += 1
    else:
        # Interview completed
        st.session_state.interview_completed = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": "🎉 **Interview Completed!**\n\nThank you for participating in the Excel interview. You've answered all 5 questions!"
        })
        
        # Log interview completion with user info
        logger.info("Interview completed successfully")
        logger.info("FINAL INTERVIEW SUMMARY:")
        logger.info(f"Examiner: {st.session_state.user_info.get('examiner_name', 'N/A')}")
        logger.info(f"Difficulty: {st.session_state.user_info.get('difficulty_level', 'N/A')}")
        logger.info(f"Date: {st.session_state.user_info.get('interview_date', 'N/A')}")
        logger.info(f"Profile: {st.session_state.user_info.get('examiner_profile', 'N/A')}")
        
        session_summary = metrics.get_session_summary()
        logger.info(f"Session summary saved: {session_summary}")
    
    st.rerun()

# Chat input and skip option
if st.session_state.current_question > 0 and not st.session_state.interview_completed:
    # Create two columns for input and skip button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        prompt = st.chat_input("Type your answer here...")
    
    with col2:
        skip_clicked = st.button("⏭️ Skip", type="secondary", help="Skip this question")
    
    # Handle answer submission
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.user_answers.append(prompt)
        
        # Get current question
        current_question_text = st.session_state.messages[-2]["content"]  # Previous assistant message
        
        # Evaluate answer
        with st.spinner("Evaluating your answer..."):
            evaluation = evaluate_answer(current_question_text, prompt)
            st.session_state.evaluations.append(evaluation)
            
            # Add evaluation message
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Thank you for your answer!",
                "evaluation": evaluation
            })
        
        # Move to next question
        move_to_next_question()
    
    # Handle skip
    elif skip_clicked:
        # Add skip message
        st.session_state.messages.append({"role": "user", "content": "[Question Skipped]"})
        st.session_state.skipped_questions.append(st.session_state.current_question)
        
        # Add skip acknowledgment
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Question skipped. Moving to the next question..."
        })
        
        # Log skip
        logger.info(f"Question {st.session_state.current_question} skipped by user")
        
        # Move to next question
        move_to_next_question()



# Show completion summary
if st.session_state.interview_completed:
    st.markdown("---")
    st.markdown("### 📈 Interview Summary")
    
    # Calculate total score
    total_score = 0
    scores = []
    for evaluation in st.session_state.evaluations:
        score = extract_score(evaluation)
        scores.append(score)
        total_score += score
    
    # Counts
    total_questions = 5
    answered_count = len(st.session_state.evaluations)
    skipped_count = len(st.session_state.skipped_questions) if st.session_state.skipped_questions else (total_questions - answered_count)
    
    # Average over answered questions (reference)
    avg_score = total_score / answered_count if answered_count else 0
    
    # Penalized overall score (skipped count treated as 0)
    overall_score = total_score / total_questions if total_questions else 0
    
    # Show only overall performance without per-question details
    st.markdown("---")
    st.markdown("### 📊 Overall Performance")
    st.metric("Score", f"{overall_score:.1f}/5")
    st.caption(f"Answered: {answered_count} | Skipped: {skipped_count}")
    
    # Add performance insights
    st.markdown("---")
    st.markdown("### 📊 Performance Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        excellent_count = sum(1 for score in scores if score >= 4)
        st.metric("Excellent (4-5)", f"{excellent_count}/{answered_count}")
    
    with col2:
        good_count = sum(1 for score in scores if 2 <= score < 4)
        st.metric("Good (2-3)", f"{good_count}/{answered_count}")
    
    with col3:
        needs_improvement = sum(1 for score in scores if score < 2)
        st.metric("Needs Improvement (0-1)", f"{needs_improvement}/{answered_count}")
    
    with col4:
        st.metric("Skipped", f"{skipped_count}/5")
    
    # Difficulty-specific feedback
    difficulty_level = st.session_state.user_info.get('difficulty_level', 'Intermediate')
    st.markdown("---")
    st.markdown("### 🎯 Difficulty Level Assessment")
    
    if difficulty_level == "Beginner":
        if overall_score >= 4:
            st.success("🌟 **Excellent!** You have strong fundamental Excel skills. Consider advancing to Intermediate level.")
        elif overall_score >= 2:
            st.info("👍 **Good progress!** You understand basic Excel concepts. Practice more with formulas and formatting.")
        else:
            st.warning("📚 **Keep learning!** Focus on basic Excel functions, formulas, and data entry.")
    elif difficulty_level == "Intermediate":
        if overall_score >= 4:
            st.success("🌟 **Outstanding!** You have solid intermediate Excel skills. Ready for Advanced challenges!")
        elif overall_score >= 2:
            st.info("👍 **Good work!** You're developing intermediate skills. Practice with pivot tables and data analysis.")
        else:
            st.warning("📚 **Keep practicing!** Focus on intermediate formulas like VLOOKUP and data analysis features.")
    else:  # Advanced
        if overall_score >= 4:
            st.success("🌟 **Exceptional!** You have advanced Excel expertise. You're ready for complex business scenarios!")
        elif overall_score >= 2:
            st.info("👍 **Strong skills!** You handle advanced features well. Practice with complex case studies.")
        else:
            st.warning("📚 **Keep advancing!** Focus on complex formulas, automation, and business problem-solving.")
    
    # Add download functionality
    st.markdown("---")
    st.markdown("### 📥 Download Results")
    
    # Create a summary report
    report_text = f"""Excel Interview Results
========================

INTERVIEW INFORMATION:
Examiner Name: {st.session_state.user_info.get('examiner_name', 'N/A')}
Difficulty Level: {st.session_state.user_info.get('difficulty_level', 'N/A')}
Interview Date: {st.session_state.user_info.get('interview_date', 'N/A')}
Examiner Profile: {st.session_state.user_info.get('examiner_profile', 'N/A')}

PERFORMANCE SUMMARY:
Overall Score: {overall_score:.1f}/5
Questions Answered: {answered_count}/5
Questions Skipped: {skipped_count}/5

DIFFICULTY LEVEL ASSESSMENT:
Difficulty: {st.session_state.user_info.get('difficulty_level', 'N/A')}
"""
    
    # Add difficulty-specific feedback to report
    difficulty_level = st.session_state.user_info.get('difficulty_level', 'Intermediate')
    if difficulty_level == "Beginner":
        if overall_score >= 4:
            report_text += "Assessment: Excellent! Strong fundamental Excel skills. Ready for Intermediate level.\n"
        elif overall_score >= 2:
            report_text += "Assessment: Good progress! Understanding basic concepts. Practice more with formulas.\n"
        else:
            report_text += "Assessment: Keep learning! Focus on basic Excel functions and data entry.\n"
    elif difficulty_level == "Intermediate":
        if overall_score >= 4:
            report_text += "Assessment: Outstanding! Solid intermediate skills. Ready for Advanced challenges!\n"
        elif overall_score >= 2:
            report_text += "Assessment: Good work! Developing intermediate skills. Practice pivot tables.\n"
        else:
            report_text += "Assessment: Keep practicing! Focus on VLOOKUP and data analysis.\n"
    else:  # Advanced
        if overall_score >= 4:
            report_text += "Assessment: Exceptional! Advanced Excel expertise. Ready for complex scenarios!\n"
        elif overall_score >= 2:
            report_text += "Assessment: Strong skills! Handle advanced features well. Practice case studies.\n"
        else:
            report_text += "Assessment: Keep advancing! Focus on complex formulas and automation.\n"
    
    report_text += f"""
DETAILED RESULTS:
"""
    
    question_num = 1
    answer_index = 0
    
    for i in range(1, 6):  # Q1 to Q5
        if i in st.session_state.skipped_questions:
            report_text += f"""
Q{i}: Skipped
Answer: [Question Skipped]
---
"""
        elif answer_index < len(st.session_state.user_answers):
            answer = st.session_state.user_answers[answer_index]
            score = scores[answer_index]
            report_text += f"""
Q{i}: {score}/5
Answer: {answer}
---
"""
            answer_index += 1
    
    report_text += f"""
Performance Breakdown:
- Excellent (4-5): {excellent_count}/{answered_count}
- Good (2-3): {good_count}/{answered_count}
- Needs Improvement (0-1): {needs_improvement}/{answered_count}
- Skipped: {skipped_count}/5

Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Download interview report
    st.download_button(
        label="📄 Download Interview Report",
        data=report_text,
        file_name=f"excel_interview_results_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )
    
