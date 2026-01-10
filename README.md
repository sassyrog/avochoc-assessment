# Asset Management Service

This project is a backend API for managing digital assets like laptops, monitors, and phones. It provides features for asset tracking, user authentication, security alerts, and AI-powered image analysis.

## Core Features

- **Asset Management**: Full CRUD operations for company assets.
- **Authentication**: Secure access using JWT tokens.
- **Performance**: Redis-based caching for listing assets with cache invalidation.
- **Security Alerts**: Tracks login IP addresses and logs warnings if a login occurs from a new location (this is the "Geo-Location Alert" feature)
- **AI Image Analysis**: Automatically generates descriptive text for assets based on uploaded images.

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **Migrations**: Alembic
- **Caching**: Redis
- **Dependency Management**: Poetry (official per assessment requirements) and uv (development)
- **Containerization**: Docker
- **Testing**: Pytest

## AI Configuration

For generating asset descriptions from images, the system was tested using the **HuggingFaceTB/SmolVLM2-2.2B-Instruct** model. 

The service uses a provider-based architecture that supports local inference tools like **Ollama** or **LMStudio**. This allows for image processing without relying on external cloud APIs or incurring usage costs during development testing. Also makes AI integration provider and model agnostic, which is useful for production use.

## Scope and Considerations

The following items highlight decisions made for the MVP of this assessment:

- **Email Delivery**: The geo-location alert system logs security warnings to the console and prints a mock notification. A full SMTP or third-party email service (like SendGrid) integration was omitted to simplify the setup.
- **Image Persistence**: Uploaded images are processed in-memory and discarded once the AI description is generated. They are not saved to disk or the database, as per the assessment requirements.
- **User Management**: The focus is on registration, login, and secure endpoint protection. Extended user management features like profile updates or account deletion are not included in this scope.
- **Authentication Library**: While the assessment requirements mentioned FastAPI Users, a custom JWT-based authentication service was implemented to provide more direct control over the specific login alert behavior required (a decision I'd probably make in a real-world app).
- **Production Hardening**: Deployment-specific configurations such as SSL, rate limiting, and production-grade server tuning are not included in this version.
- **Missing Additional Data Validation**: Input validation is handled using Pydantic models and FastAPI's built-in validation features. I didn't do too much additional validation (i.e password strength, etc) as I was focused on the core features of the assessment.


### Dependency Management

This project supports both **Poetry** and **uv**. While `uv` is used for faster local development and environment management, **Poetry is the official dependency manager** required for this assessment.

A `poetry.lock` file is provided to ensure consistent installs in the evaluation environment.

### Installation

1. **Install dependencies**:
   You can use either tool, but Poetry is recommended for consistency with the assessment requirements:
   ```bash
   # Using Poetry (Official)
   poetry install

   # Using uv (Development)
   uv sync
   ```

2. **Setup environment variables**:
   Copy the example environment file and update any necessary values.
   ```bash
   cp .env.example .env
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**:
   ```bash
   poetry run alembic upgrade head
   ```

5. **Run the API**:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Testing

The project includes unit and integration tests using Pytest and pytest-cov, coverage being one of those things I'd be pedantic about in a real-world app.

Run the test suite:
```bash
poetry run pytest
```

Run tests with a coverage report:
```bash
poetry run pytest --cov=app tests/
```

## Documentation

The interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
