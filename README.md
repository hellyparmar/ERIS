# Enterprise Retail Intelligence System (ERIS)

ERIS is a high-performance, multi-tenant backend built with FastAPI, designed to provide real-time sales analytics, inventory management, and AI-powered business intelligence for modern retail enterprises.

## Architecture Overview

The system follows a modular, layer-based architecture:

- **API Layer**: FastAPI routers with standardized docstrings and Pydantic V2 schemas.
- **Service Layer**: Business logic for transaction processing, inventory alerts, and user management.
- **Data Layer**: SQLAlchemy models with multi-tenant isolation via `organization_id`.
- **Intelligence Layer**: ARIMA-based forecasting, anomaly detection, and an AI chat assistant with RAG.

## Prerequisites

- Python 3.9+
- PostgreSQL (or SQLite for development)
- Ollama (optional, for local AI assistant)
- Anthropic/OpenAI API Keys (optional, for cloud AI)

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/hellyparmar/R-DIOS.git
   cd "Enterprise Retail Intelligence System"
   ```

2. **Setup Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the `backend/` directory based on the provided guide in `API_USAGE.md`.

## Running the Application

### Development Mode

```bash
cd backend
uvicorn app.main:app --reload
```

### Accessing Documentation

Once the server is running, you can access the interactive documentation at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Testing

Run the comprehensive test suite with:

```bash
cd backend
python -m pytest tests/test_workflows.py -v
```

## Deployment

Refer to the `docs/DEVELOPMENT.md` for detailed production deployment strategies using Docker and Nginx.
