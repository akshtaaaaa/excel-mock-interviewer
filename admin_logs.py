#!/usr/bin/env python3
"""
Admin script to view logs and metrics
For developers/administrators only
"""

import os
import json
import glob
from datetime import datetime

def view_todays_logs():
    """View today's log file"""
    log_file = f"logs/excel_interview_{datetime.now().strftime('%Y%m%d')}.log"
    
    if not os.path.exists(log_file):
        print("No log file found for today.")
        return
    
    print(f"📊 Today's Log File: {log_file}")
    print("=" * 60)
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Count different types of log entries
    api_calls = [line for line in lines if "API Call" in line]
    errors = [line for line in lines if "ERROR" in line]
    questions = [line for line in lines if "Question" in line and "generated" in line]
    evaluations = [line for line in lines if "Evaluation" in line and "completed" in line]
    sessions = [line for line in lines if "SESSION COMPLETED" in line]
    user_info = [line for line in lines if "INTERVIEW INFORMATION COLLECTED" in line]
    
    print(f"📈 Summary:")
    print(f"  • API Calls: {len(api_calls)}")
    print(f"  • Questions Generated: {len(questions)}")
    print(f"  • Evaluations Completed: {len(evaluations)}")
    print(f"  • Sessions Completed: {len(sessions)}")
    print(f"  • User Info Collected: {len(user_info)}")
    print(f"  • Errors: {len(errors)}")
    print()
    
    # Show recent activity
    print("🕒 Recent Activity (last 10 entries):")
    for line in lines[-10:]:
        print(f"  {line.strip()}")
    
    if errors:
        print("\n⚠️  Errors Found:")
        for error in errors:
            print(f"  {error.strip()}")
    
    # Show user information if available
    if user_info:
        print("\n👤 User Information Collected:")
        # Find the lines after "INTERVIEW INFORMATION COLLECTED"
        info_started = False
        for line in lines:
            if "INTERVIEW INFORMATION COLLECTED" in line:
                info_started = True
                continue
            elif info_started and "=" in line and len(line.strip()) > 10:
                break
            elif info_started and ("Examiner Name:" in line or "Difficulty Level:" in line or 
                                 "Interview Date:" in line or "Examiner Profile:" in line or 
                                 "Password Provided:" in line):
                print(f"  {line.strip()}")

def analyze_token_usage():
    """Analyze token usage from log files"""
    log_files = glob.glob("logs/*.log")
    
    if not log_files:
        print("No log files found.")
        return
    
    total_tokens = 0
    total_calls = 0
    total_sessions = 0
    
    print("📊 Token Usage Analysis")
    print("=" * 60)
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Extract token usage from log content
            lines = content.split('\n')
            for line in lines:
                if "API Call" in line and "Total:" in line:
                    # Extract total tokens from line like "Total: 150"
                    parts = line.split("Total:")
                    if len(parts) > 1:
                        token_part = parts[1].split(",")[0].strip()
                        try:
                            total_tokens += int(token_part)
                            total_calls += 1
                        except:
                            pass
                
                if "SESSION COMPLETED" in line:
                    total_sessions += 1
                    
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
    
    if total_sessions > 0:
        avg_tokens_per_session = total_tokens / total_sessions
        avg_calls_per_session = total_calls / total_sessions
        
        print(f"📈 Overall Statistics:")
        print(f"  • Total Sessions: {total_sessions}")
        print(f"  • Total Tokens Used: {total_tokens:,}")
        print(f"  • Total API Calls: {total_calls}")
        print(f"  • Average Tokens/Session: {avg_tokens_per_session:.0f}")
        print(f"  • Average Calls/Session: {avg_calls_per_session:.1f}")

def cleanup_logs():
    """Clean up old log files"""
    import shutil
    from datetime import timedelta
    
    log_files = glob.glob("logs/*.log")
    cutoff_date = datetime.now() - timedelta(days=7)
    
    removed_logs = 0
    
    for log_file in log_files:
        if os.path.getmtime(log_file) < cutoff_date.timestamp():
            os.remove(log_file)
            removed_logs += 1
            print(f"Removed: {log_file}")
    
    print(f"🧹 Cleanup Complete: Removed {removed_logs} old log files")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 admin_logs.py [logs|tokens|cleanup]")
        print("  logs    - View today's logs")
        print("  tokens  - Analyze token usage")
        print("  cleanup - Remove old log files")
        return
    
    command = sys.argv[1]
    
    if not os.path.exists("logs"):
        print("❌ No logs directory found.")
        return
    
    if command == "logs":
        view_todays_logs()
    elif command == "tokens":
        analyze_token_usage()
    elif command == "cleanup":
        cleanup_logs()
    else:
        print("Invalid command. Use: logs, tokens, or cleanup")

if __name__ == "__main__":
    main()
