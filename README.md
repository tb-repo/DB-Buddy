# DB-Buddy

AI-driven self-service chat application for database assistance. Helps users get recommendations for SQL queries, performance tuning, and database sizing before reaching the DBA team.

## Features

- **SQL Recommendations**: Get help with query optimization and best practices
- **Performance Tuning**: Assistance with slow queries, CPU, and memory issues  
- **Database Sizing**: Hardware recommendations based on workload requirements
- **Interactive Chat**: Question-driven conversation flow to gather requirements

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and go to `http://localhost:5000`

## Usage

1. Select your issue type (SQL, Performance, or Sizing)
2. Answer the guided questions about your requirements
3. Receive tailored recommendations
4. Consult DBA team for complex production issues

## Architecture

- **Backend**: Flask API with conversation flow management
- **Frontend**: HTML/CSS/JavaScript chat interface
- **Session Management**: In-memory conversation tracking
- **Recommendation Engine**: Rule-based suggestions for common DB issues