# Task 2.1: Environment Configuration - Backend
**Owner:** Backend Lead  
**Duration:** 3 hours  
**Deadline:** Feb 18, 6:00 PM IST  
**Priority:** 🟡 HIGH (Needed before Task 2.2)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #1.1 PostgreSQL Infrastructure

---

## Description

Implement environment-based configuration for backend. Remove all hardcoded URLs, database connection strings, and API keys. Use `.env` file pattern with validation.

## Acceptance Criteria

- [ ] `.env.example` created with all required variables
- [ ] `main.py` updated to load all config from `.env`
- [ ] All hardcoded URLs removed (grep verification)
- [ ] Database connection uses environment variable
- [ ] API keys loaded from environment (OpenRouter, OpenWeather)
- [ ] Settings validation: fails early if required vars missing
- [ ] Documentation: list of all env variables required
- [ ] Team can copy `.env.example` to `.env` and start server

## Environment Variables

### Database Configuration
```bash
# PostgreSQL connection
DATABASE_URL=postgresql://app_user:password@localhost:5432/enterprise_retail
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_RECYCLE=3600
```

### API Configuration
```bash
# API server
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
API_WORKERS=4

# CORS settings
CORS_ORIGINS=http://localhost:5173,https://app.example.com
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
```

### External APIs
```bash
# OpenRouter (LLM)
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openrouter/auto

# OpenWeather
OPENWEATHER_API_KEY=your_key_here

# JWT Authentication
JWT_SECRET_KEY=your_secret_key_generate_with_secrets.token_urlsafe(32)
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=30
```

### Feature Flags
```bash
# Feature toggles
ENABLE_INVOICING=True
ENABLE_BILL_MANAGEMENT=True
ENABLE_FORECASTING=True
ENABLE_WEATHER_INTEGRATION=True
```

### Logging Configuration
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/enterprise_retail.log
```

## Implementation

### Step 1: Create `.env.example`
```bash
# .env.example (committed to git)
DATABASE_URL=postgresql://app_user:password@localhost:5432/enterprise_retail
DATABASE_POOL_SIZE=10
API_HOST=0.0.0.0
API_PORT=8000
OPENROUTER_API_KEY=
OPENWEATHER_API_KEY=
JWT_SECRET_KEY=
```

### Step 2: Update `main.py`
```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# Validate required env vars
REQUIRED_VARS = [
    'DATABASE_URL',
    'JWT_SECRET_KEY',
    'OPENROUTER_API_KEY'
]

for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# Configuration class
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 30))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

config = Config()

# Use config
engine = create_engine(
    config.DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", 10))
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        workers=int(os.getenv("API_WORKERS", 4)),
        reload=config.DEBUG
    )
```

### Step 3: Verify No Hardcoded URLs
```bash
# Check for hardcoded localhost
grep -r "localhost:8000" src/
grep -r "127.0.0.1" src/
grep -r "hardcoded" src/

# Should return: nothing (0 matches)
```

### Step 4: Update Database Connection Points
```python
# Find and replace all database connection code
# Before:
engine = create_engine("sqlite:///petpooja_retail_db.sqlite3")

# After:
engine = create_engine(os.getenv("DATABASE_URL"))
```

## File Changes

| File | Change | Impact |
|------|--------|--------|
| `.env.example` | NEW | Provides template for developers |
| `main.py` | UPDATE | Load config from .env |
| `config.py` | NEW/UPDATE | Centralized configuration class |
| `requirements.txt` | ADD `python-dotenv` | .env file support |

## Deployment Instructions

**Development:**
```bash
cp .env.example .env
# Edit .env with local settings
source .env
python main.py
```

**Production:**
```bash
# Set env vars via platform (Heroku, Docker, etc.)
heroku config:set DATABASE_URL=postgresql://...
docker run -e DATABASE_URL=postgresql://... app:latest
```

## Related Issues
- #1.1 PostgreSQL Infrastructure
- #2.2 Environment Configuration - Frontend
- #3.1 Pagination Implementation

## Validation

```python
# Script to validate all env vars are set correctly
import os
from dotenv import load_dotenv

load_dotenv()

checks = [
    ("DATABASE_URL", lambda x: x.startswith("postgresql://")),
    ("API_HOST", lambda x: x in ["0.0.0.0", "127.0.0.1"]),
    ("API_PORT", lambda x: 1 <= int(x) <= 65535),
    ("JWT_SECRET_KEY", lambda x: len(x) >= 32),
]

for var, validator in checks:
    value = os.getenv(var)
    if not value or not validator(value):
        print(f"❌ Invalid: {var}")
    else:
        print(f"✅ Valid: {var}")
```

## Definition of Done
✅ `.env.example` created with all variables  
✅ `main.py` loads config from `.env`  
✅ No hardcoded URLs found (grep returns 0)  
✅ Validation script passes all checks  
✅ Team can start server with just `.env` file  
✅ Documentation updated
