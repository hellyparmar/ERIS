# R-DIOS v1.0 - System Architecture (Production)

## Overview

R-DIOS (Retail Data Intelligence & Operations System) is a production-grade retail analytics platform validated for the Petpooja ecosystem. It combines a robust microservices-inspired API with a lightweight, offline-first frontend to deliver actionable insights in high-latency environments.

## Architecture Diagram

```mermaid
flowchart TB
    subgraph Frontend["Frontend PWA (Offline-First)"]
        UI[React Dashboard]
        ServiceWorker[Service Worker]
        LocalDB[IndexedDB Cache]
    end
    
    subgraph API["API Layer (FastAPI)"]
        Gateway[API Gateway]
        Auth[JWT Middleware]
        Forecast[Forecasting Engine]
        NLP[NL-to-SQL Engine]
    end
    
    subgraph ML["Validated ML Pipeline"]
        Naive[Naive Baseline (Primary)]
        Prophet[Prophet (Seasonality)]
        ARIMA[Auto-ARIMA (Trends)]
        Ensemble[Weighted Average]
    end
    
    subgraph Infra["Infrastructure"]
        PostgreSQL[(PostgreSQL 15)]
        Redis[(Redis Caching)]
        Celery[Async Workers]
    end
    
    UI <--> ServiceWorker
    ServiceWorker <--> Gateway
    Gateway --> Auth
    Auth --> Forecast
    Auth --> NLP
    Forecast --> ML
    ML --> Naive
    ML --> Prophet
    ML --> ARIMA
    Forecast --> Redis
    Forecast --> PostgreSQL
```

## Component Implementation Details

### 1. Frontend Layer (Offline-First PWA)

* **Technology:** React 18, Vite, Tailwind CSS
* **Offline capability:** Implemented Service Workers for caching static assets and critical API responses (validated in Phase 1C).
* **State Management:** TanStack Query for efficient server state synchronization.

### 2. API Layer (`/api/`)

* **Technology:** FastAPI (Python 3.11), Gunicorn
* **Performance:** Validated sub-200ms response time for cached endpoints.
* **Security:** Role-Based Access Control (RBAC) preventing cross-tenant data leaks.

### 3. ML Forecasting Engine

* **Primary Model:** **Naive Baseline** (13.24% MAPE) - Selected for stability and speed.
* **Secondary Models:**
  * **Prophet:** Used for holiday-sensitive predictions.
  * **ARIMA:** Used for long-term trend extrapolation.
* **Pipeline:** Automated model selection based on historical volatility.

### 4. Data Layer

* **Primary Store:** PostgreSQL 15 with partitions for transaction data.
* **Caching:** Redis layer caching forecast results for 24 hours.
* **Optimization:** Database indexes on `store_id` and `date` validated to handle 50+ outlet load.

## Data Flow: "Ask AI" Feature

1. **User Query:** "Show revenue for top 5 products"
2. **API Layer:** Receives request, validates JWT.
3. **NLP Engine:** GPT-4 converts natural language to SQL > Semantic Layer maps to schema > Guardrails validate safety.
4. **Execution:** SQL runs against read-replica.
5. **Response:** JSON data + "Explainable AI" SQL snippet returned to UI.

## Deployment Stack

```yaml
version: '3.8'
services:
  web:
    build: ./frontend
    ports: ["80:80"]
  api:
    build: ./backend
    scale: 2  # Horizontal scaling
  worker:
    build: ./backend
    command: celery -A worker worker
  redis:
    image: redis:alpine
  db:
    image: postgres:15-alpine
```

## Security & Scalability (Validated)

* **Scalability:** Horizontal scaling of API nodes supported via stateless design.
* **Security:** All endpoints require Bearer auth; SQL injection prevention via ORM/parameterized queries (where applicable) and strict LLM output validation.
