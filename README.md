# Spend Tracker

A simple full-stack expense tracking application built as a technical assignment for a Backend Engineer role.

The application allows users to add expenses, filter expenses, view spending summaries, and identify categories where spending increased by more than 20% compared with the previous month.

## Tech Stack

- **Backend:** Python, Django, Django REST Framework
- **Database:** SQLite
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **ORM:** Django ORM

## Features

- Add expenses with amount, category, note, and date
- Validate expense data on the backend
- List all expenses
- Filter expenses by category and date range
- Calculate total spending
- Calculate spending by category
- Calculate month-over-month spending change
- Identify categories with more than 20% spending increase
- Django Admin support
- Automated tests for core functionality
- Simple frontend connected to the REST API

## Project Structure

```text
spend-tracker/
│
├── manage.py
├── requirements.txt
├── README.md
│
├── spend_tracker/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── main/
│   ├── admin.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

## ===================================================Setup

### 1. Create virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Start the server

```bash
python manage.py runserver
```
### ===============================================

Open:

**Application:** `http://127.0.0.1:8000/`

**Admin:** `http://127.0.0.1:8000/admin/`

## API Endpoints

### Create Expense

```http
POST /api/expenses/
```

Example request:

```json
{
  "amount": 500,
  "category": "Food",
  "note": "Lunch",
  "date": "2026-09-22"
}
```

### List Expenses

```http
GET /api/expenses/
```

### Filter by Category

```http
GET /api/expenses/?category=Food
```

### Filter by Date Range

```http
GET /api/expenses/?start_date=2026-09-01&end_date=2026-09-22
```

### Get Summary

```http
GET /api/summary/
```

The summary includes:

- Total spend
- Spend by category
- Current month spend
- Previous month spend
- Month-over-month difference and percentage
- Categories with more than 20% spending increase

## Validation

The API validates input on the server side.

Examples:

- Amount must be greater than `0`
- Category cannot be empty
- Date must be valid

Invalid requests return appropriate `400 Bad Request` responses with validation details.

## Testing

Run all automated tests:

```bash
python manage.py test
```

Tests cover:

- Expense creation
- Invalid amounts
- Invalid categories
- Expense listing
- Category filtering
- Date filtering
- Date-range filtering
- Total and category calculations
- Month-over-month calculation
- January/December year transition
- Division-by-zero handling
- Spending increase insights

## Design Decisions

### Django REST Framework

DRF provides serializers, validation, API views, and standard HTTP responses with minimal code.

### SQLite

SQLite keeps the project simple and requires no separate database server, making it suitable for this assignment.

### Django ORM

Database calculations such as `Sum`, grouping, and date filtering are handled through the Django ORM.

### Backend Validation

Validation is performed on the backend so invalid data cannot bypass the frontend.

### Month-over-Month Calculation

The application compares the current calendar month with the previous calendar month.

January correctly compares against December of the previous year.

## Future Improvements

With more time, I would add:

- JWT authentication
- PostgreSQL for production
- API pagination
- Advanced filtering
- API documentation with Swagger/OpenAPI
- Docker and CI/CD
- Charts for spending trends
- User-specific expense tracking

## AI Usage

AI tools were used as a development assistant for project structure, API implementation, validation, testing ideas, and code review. I reviewed, adapted, tested, and modified the suggestions to meet the assignment requirements.