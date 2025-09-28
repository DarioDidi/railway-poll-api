# Django Polls API

A comprehensive poll management system built with Django REST Framework, PostgreSQL, and Celery, designed for deployment on Render.com.

## Features

- **Poll Management**: Create, read, update, and delete polls with multiple options
- **Voting System**: Secure voting with duplicate prevention
- **Real-time Results**: Live result computation with caching
- **User Authentication**: JWT-based authentication system
- **Advanced Analytics**: Comprehensive voting analytics and trends
- **Security**: IP blocking, rate limiting, and suspicious activity monitoring
- **Export Functionality**: Export results in JSON and CSV formats
- **API Documentation**: Complete Swagger/OpenAPI documentation

## Technology Stack

- **Backend**: Django 5.2, Django REST Framework
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis broker
- **Authentication**: JWT with SimpleJWT
- **Documentation**: drf-yasg for Swagger
- **Deployment**: Render.com with Docker-based deployment
- **Testing**: Pytest with comprehensive test coverage
- **Search**: Robust searching with advance django filters

## AUTH endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
POST | /api/auth/registration/          | Register(with email) |
POST | /api/auth/login/                 | Login (email + password) |
POST | /api/auth/password/reset/        | Get reset code (returns code in response) |
POST | /api/auth/password/reset/confirm/| Reset with code + new password |
POST | /api/auth/password/change/       | Change password (authenticated) |
GET/PUT/PATCH |/api/auth/user/         | Profile managementA |
POST | /api/auth/token/verify/          | Token verification |
POST | /api/auth/token/refresh/         | Token refresh |
## Model Endpoints

| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET | `/api/polls/` | List polls | Optional |
| POST | `/api/polls/` | Create poll | Required |
| GET | `/api/polls/{id}/` | Retrieve poll | No |
| PUT | `/api/polls/{id}/` | Update poll | Owner only |
| DELETE | `/api/polls/{id}/` | Delete poll | Owner only |
| POST | `/api/polls/{id}/vote/` | Cast vote | Optional* |
| GET | `/api/polls/{id}/results/` | Get results | No |
| GET | `/api/analytics/` | Get analytics | Required |
| GET | `/api/docs/` | API documentation | No |

## Documentation endpoints:

    A JSON view of your API specification at /swagger.json
    A YAML view of your API specification at /swagger.yaml
    A swagger-ui view of your API specification at /swagger/
    A ReDoc view of your API specification at /redoc/

## 🔍 Search and Filtering API Guide

The Polls API provides comprehensive search and filtering capabilities to help you find exactly what you need.

1. Field-Based Filtering
```
GET /api/polls/?question=technology&creator_email=user@example.com&is_active=true
```
2. Date Range Filtering
```
GET /api/polls/?created_after=2023-01-01T00:00:00Z&created_before=2023-12-31T23:59:59Z
GET /api/polls/?expires_after=2023-06-01T00:00:00Z&expires_before=2023-06-30T23:59:59Z

```
3. Status Filtering
```
GET /api/polls/?status=active      # Currently active polls
GET /api/polls/?status=upcoming    # Polls that haven't started
GET /api/polls/?status=expired     # Polls that have ended

```
4. Search Functionality
```
GET /api/polls/?search=technology  # Searches question and creator_email fields

```
The enhanced search endpoint (/api/polls/search/) provides additional filtering options:
http

GET /api/polls/search/?min_votes=10&max_votes=100&question=technology&status=active

    min_votes: Filter polls with at least this many votes

    max_votes: Filter polls with at most this many votes

    Combines with all regular filters: Works with date ranges, status, etc.

Additional Useful Search Functionality

- Option Content Search
Usage:
```
GET /api/polls/?option_contains=python
```
- Vote Count Range
```
GET /api/polls/search/?min_votes=5&max_votes=50
```
- Creator-Based Filtering
```
GET /api/polls/?creator_emails=user1@example.com,user2@example.com
```

5. Ordering
```
GET /api/polls/?ordering=created_at           # Oldest first
GET /api/polls/?ordering=-created_at          # Newest first
GET /api/polls/?ordering=expiry_date          # Expiring soonest
GET /api/polls/?ordering=-total_votes         # Most popular first
```
6. Pagination

- All list endpoints support pagination with configurable page sizes.


