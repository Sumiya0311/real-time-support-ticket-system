Real-Time Support Ticket System

Project Overview

A backend application built with FastAPI to manage customer support tickets, user authentication, ticket categories, agent assignment, notifications, and real-time messaging.

Features

- User registration and login with JWT authentication
- Role-based access control for Admins, Agents, and Customers
- Create, view, and update support tickets
- Ticket categories management
- Ticket assignment to available agents
- Ticket status history tracking
- Real-time messaging using WebSockets
- In-app notifications
- Email notifications
- Automated API and service tests

Technology Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- MySQL
- Pydantic
- JWT authentication
- WebSockets
- Pytest

Project Setup

1. Clone the repository

git clone YOUR_GITHUB_REPOSITORY_URL
cd real_time_support_ticket_system

2. Create and activate a virtual environment

python -m venv venv

Windows PowerShell:

.\venv\Scripts\Activate.ps1

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a ".env" file in the project root using ".env.example" as a template.

Configure the database connection, secret key, and SMTP settings. Never commit real passwords or secret keys to GitHub.

5. Run the application

python -m uvicorn app.main:app --reload

Open the API documentation at:

http://127.0.0.1:8000/docs

Run Automated Tests

python -m pytest -v

Test Results

Latest recorded run: 27 tests passed.

Security

- Keep ".env" and credentials private.
- Use appropriate roles and authentication for protected endpoints.
- Configure secure production credentials before deployment.

License

For educational and project demonstration purposes.