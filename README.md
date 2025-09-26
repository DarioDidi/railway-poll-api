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

## AUTH endpoints:

| Endpoint | Method | Description |
|--------|----------|-------------|
|/api/auth/login/|	POST|	User login|
|/api/auth/logout/|	POST|	User logout|
|/api/auth/password/reset/|	POST|	Password reset request|
|/api/auth/password/reset/confirm/|	POST|	Password reset confirmation|
|/api/auth/password/change/|	POST|	Password change|
|/api/auth/user/|	GET, PUT, PATCH|	User details|
|/api/auth/token/verify/|	POST|	Token verification|
|/api/auth/token/refresh/|	POST|	Token refresh (JWT)|
|/api/auth/registration/|	POST|	User registration|
|/api/auth/registration/verify-email/|	POST|	Email verification|

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
