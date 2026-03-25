# ERIS Developer Guide

This guide is for developers who want to contribute to the Enterprise Retail Intelligence System (ERIS).

## Project Structure

```text
Enterprise Retail Intelligence System/
├── backend/
│   ├── app/
│   │   ├── api/             # Integration logic (GST, Tally, etc.)
│   │   ├── ml/              # Machine Learning models (RAG, Forecasting)
│   │   ├── models/          # SQLAlchemy Database Models
│   │   ├── routers/         # FastAPI Route Handlers
│   │   ├── schemas/         # Pydantic Request/Response Schemas
│   │   ├── services/        # Business Logic Services
│   │   ├── utils/           # Shared Utilities
│   │   └── main.py          # Application Entry Point
│   ├── tests/               # Pytest Suite
│   └── requirements.txt     # Python Dependencies
├── frontend/                # Vite + React Application
└── docs/                    # Documentation
```

## Adding a New Endpoint

To add a new feature (e.g., "Supplier Management"):

1. **Define Schema**: Create `backend/app/schemas/supplier.py`.
2. **Define Model**: Create `Supplier` model in `backend/app/models/multitenant_models.py`.
3. **Write Logic**: Implement core logic in `backend/app/services/supplier_service.py`.
4. **Create Router**: Create `backend/app/routers/suppliers.py` and register it in `app/main.py`.
5. **Add Tests**: Create `backend/tests/test_suppliers.py`.

## Adding a New ML Model

1. **Model Implementation**: Create a subfolder in `backend/app/ml/`.
2. **Provider Integration**: If it's an LLM, update `backend/app/ml/assistant/llm_provider.py`.
3. **RAG Service**: If it requires knowledge base, index documents in `backend/app/ml/rag/rag_service.py`.
4. **API Endpoint**: Expose the model via a router (e.g., `intelligence.py`).

## Coding Standards

- **Type Annotations**: Always use type hints for function arguments and return values.
- **Docstrings**: All endpoints and public methods MUST have detailed docstrings.
- **Pydantic Models**: All request/response bodies MUST use Pydantic models.
- **Error Handling**: Use `AppException` and appropriate HTTP status codes.
- **Testing**: Every new feature requires at least one integration test and relevant unit tests.

## Git Workflow

1. Create a feature branch: `git checkout -b feature/xyz`
2. Commit changes with clear, descriptive messages.
3. Push branch and create a Pull Request.
4. Ensure CI tests pass before merging.
