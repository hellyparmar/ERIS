# Task 4.1: Comprehensive Testing - Unit & Integration
**Owner:** QA Lead  
**Duration:** 8 hours  
**Deadline:** Feb 19, 6:00 PM IST  
**Priority:** 🟡 HIGH (Gate approval requirement)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #3.2 Pagination Frontend

---

## Description

Execute comprehensive testing suite: 54 unit tests, 37 integration tests, and database validation. Verify all functionality works correctly before gate approval on Feb 20.

## Acceptance Criteria

- [ ] All 54 unit tests passing
- [ ] All 37 integration tests passing
- [ ] 0 critical issues found
- [ ] 0-2 high issues (acceptable if documented)
- [ ] Test coverage > 80%
- [ ] All test reports generated
- [ ] Team notified of results
- [ ] Ready for gate approval

## Test Coverage by Component

### Backend Tests (30 unit tests)
- User authentication (4 tests)
- Product management (6 tests)
- Inventory operations (8 tests)
- Sales processing (6 tests)
- Invoice generation (6 tests)

### Frontend Tests (24 unit tests)
- Component rendering (8 tests)
- Form validation (6 tests)
- API client (6 tests)
- Pagination (4 tests)

### Integration Tests (37 tests)
- User login → Dashboard (1 test)
- Add product → Inventory load (1 test)
- Create sale → Invoice generation (1 test)
- And 34 more end-to-end scenarios

## Backend Test Setup

### Step 1: Install Testing Framework
```bash
pip install pytest pytest-cov pytest-asyncio
```

### Step 2: Create Test Configuration
```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, app

@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal()
    
    engine.dispose()

@pytest.fixture
def client(test_db):
    """Create test client"""
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
```

### Step 3: Create Unit Tests
```python
# tests/test_auth.py
def test_user_login_success(client, test_db):
    """Test successful user login"""
    # Create test user
    user = User(email="test@example.com", password_hash="hashed_pwd")
    test_db.add(user)
    test_db.commit()
    
    # Test login
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "test_password"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_user_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com",
        "password": "wrong_password"
    })
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

# tests/test_inventory.py
def test_get_inventory_list(client):
    """Test get inventory list"""
    response = client.get("/api/v1/inventory/list?limit=50&offset=0")
    
    assert response.status_code == 200
    assert "data" in response.json()
    assert "pagination" in response.json()
    assert len(response.json()["data"]) <= 50

def test_get_inventory_with_pagination(client):
    """Test pagination metadata"""
    response = client.get("/api/v1/inventory/list?limit=50&offset=100")
    data = response.json()
    
    assert response.status_code == 200
    assert data["pagination"]["offset"] == 100
    assert data["pagination"]["hasMore"] is True or False
```

### Step 4: Run Tests
```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_user_login_success -v

# Run with output
pytest -v --tb=short
```

## Frontend Test Setup

### Step 1: Install Testing Libraries
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest vitest
```

### Step 2: Create Test Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
})
```

### Step 3: Create Component Tests
```typescript
// src/components/__tests__/Pagination.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Pagination } from '../Pagination/Pagination'

describe('Pagination', () => {
  it('renders pagination controls', () => {
    render(
      <Pagination
        currentPage={1}
        totalPages={10}
        totalItems={500}
        itemsPerPage={50}
        onPageChange={jest.fn()}
        onLimitChange={jest.fn()}
      />
    )

    expect(screen.getByText('Page')).toBeInTheDocument()
    expect(screen.getByText('of 10')).toBeInTheDocument()
  })

  it('calls onPageChange with new page', () => {
    const mockOnPageChange = jest.fn()
    render(
      <Pagination
        currentPage={1}
        totalPages={10}
        totalItems={500}
        itemsPerPage={50}
        onPageChange={mockOnPageChange}
        onLimitChange={jest.fn()}
      />
    )

    fireEvent.click(screen.getByTitle('Next page'))
    expect(mockOnPageChange).toHaveBeenCalledWith(2)
  })
})
```

### Step 4: Run Tests
```bash
# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Watch mode (auto-run on file changes)
npm run test:watch
```

## Test Execution Plan

**Day 1 (Feb 18):** Backend unit tests (2 hours) + Frontend unit tests (2 hours) = 4 hours
**Day 2 (Feb 19):** Integration tests (6 hours) + Load testing (2 hours) = 8 hours

## Expected Results

```
Backend Tests:
✅ Authentication: 4/4 passing
✅ Products: 6/6 passing
✅ Inventory: 8/8 passing
✅ Sales: 6/6 passing
✅ Invoicing: 6/6 passing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 30/30 passing

Frontend Tests:
✅ Components: 8/8 passing
✅ Forms: 6/6 passing
✅ API Client: 6/6 passing
✅ Pagination: 4/4 passing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 24/24 passing

Integration Tests:
✅ User flows: 15/15 passing
✅ Data flows: 12/12 passing
✅ Error scenarios: 10/10 passing
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 37/37 passing

FINAL: 91/91 tests passing (100%)
Coverage: 85% code covered
```

## Related Issues
- #3.2 Pagination Frontend
- #4.2 Load Testing & Performance

## Test Reports Location
- Backend: `tests/report_backend.html`
- Frontend: `coverage/index.html`
- Integration: `tests/report_integration.html`

## Definition of Done
✅ All 54 unit tests passing  
✅ All 37 integration tests passing  
✅ Test coverage > 80%  
✅ 0 critical issues  
✅ Test reports generated and reviewed  
✅ Ready for gate approval
