# Flask Status Service

A simple Flask application that provides a status web page and health check endpoints, designed to run in Docker containers with Alpine Linux.

## Features

- 🐍 Python 3.12 with Flask
- 🐳 Docker containers using Alpine Linux
- 🔧 VS Code DevContainer support
- ⚙️ Configuration via environment variables
- 🏥 Health check endpoints
- 📊 Status web page
- 🔒 Non-root user for security

## Project Structure

```
.
├── .devcontainer/
│   ├── devcontainer.json    # VS Code dev container configuration
│   └── Dockerfile          # Development container image
├── app/                    # Application source code
│   ├── __init__.py         # Package initialization
│   ├── main.py             # Main Flask application
│   └── test_main.py        # Unit tests for main module
├── tests/                  # Test files
│   ├── __init__.py         # Test package initialization
│   └── test_main.py        # Integration tests
├── run.py                  # Application entry point
├── Dockerfile             # Production container image
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Production Python dependencies
├── requirements-dev.txt   # Development Python dependencies
├── .env                   # Development environment variables
├── .env.production        # Production environment variables
└── README.md              # This file
```

## Quick Start

### Using VS Code DevContainer (Recommended for Development)

1. Open the project in VS Code
2. Install the "Dev Containers" extension
3. Press `Ctrl+Shift+P` and run "Dev Containers: Reopen in Container"
4. VS Code will build and start the development container
5. The Flask app will be available at http://localhost:5000

### Using Docker Compose

#### Development Mode
```bash
# Start development container
docker-compose --profile dev up --build

# Access the application at http://localhost:5000
```

#### Production Mode
```bash
# Start production container
docker-compose --profile prod up --build

# Access the application at http://localhost:5000
```

### Manual Docker Build

#### Development
```bash
# Build development image
docker build -f .devcontainer/Dockerfile -t flask-status-dev .

# Run development container
docker run -p 5000:5000 --env-file .env flask-status-dev
```

#### Production
```bash
# Build production image
docker build -t flask-status-prod .

# Run production container
docker run -p 5000:5000 --env-file .env.production flask-status-prod
```

## Configuration

The application is configured using environment variables. Copy and modify the environment files as needed:

### Development Configuration (`.env`)
```bash
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SERVICE_NAME=Flask Status Service
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
```

### Production Configuration (`.env.production`)
```bash
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SERVICE_NAME=Flask Status Service
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
```

## API Endpoints

- `GET /` - Main status page (HTML)
- `GET /health` - Health check endpoint (JSON)
- `GET /status` - Detailed status information (JSON)

### Example Health Check Response
```json
{
  "status": "healthy",
  "service": "Flask Status Service",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2025-08-01T12:00:00.000000"
}
```

## Development

### Prerequisites
- VS Code with Dev Containers extension
- Docker Desktop

### Development Workflow
1. Open project in VS Code DevContainer
2. Make changes to the code
3. The Flask development server will automatically reload
4. Test your changes at http://localhost:5000

### Running Tests
```bash
# Inside the dev container
pytest tests/

# Run with coverage
pytest tests/ --cov=app

# Run specific test file
pytest tests/test_main.py
```

### Code Formatting
```bash
# Format code with Black
black .

# Sort imports
isort .

# Lint with flake8
flake8 .
```

## Deployment

### Production Deployment with Docker
1. Update `.env.production` with your configuration
2. Build the production image: `docker build -t flask-status .`
3. Run with: `docker run -p 5000:5000 --env-file .env.production flask-status`

### Production Deployment with Docker Compose
1. Update `.env.production` with your configuration
2. Run: `docker-compose --profile prod up -d`

## Security Features

- Non-root users in both development and production containers
- Minimal Alpine Linux base images
- Health checks for container monitoring
- Environment-based configuration

## Monitoring

The service includes built-in health check endpoints for monitoring:
- Docker health checks are configured in the production Dockerfile
- `/health` endpoint returns service status in JSON format
- `/status` endpoint provides detailed system information

## License

This project is provided as-is for educational and development purposes.
