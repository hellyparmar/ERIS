# Task 3.2: Pagination Implementation - Frontend
**Owner:** Frontend Lead  
**Duration:** 5 hours  
**Deadline:** Feb 19, 12:00 PM IST  
**Priority:** 🟡 HIGH (Completes pagination feature)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #3.1 Backend Pagination, #2.2 Frontend Env Config

---

## Description

Implement pagination UI component for inventory page. Display products with pagination controls, showing current page, total records, and ability to navigate between pages.

## Acceptance Criteria

- [ ] Pagination component displays: current page, total items, items per page
- [ ] Navigation buttons: First, Previous, Next, Last
- [ ] Items per page dropdown: 50, 100, 250
- [ ] All 528 pages load successfully
- [ ] Smooth navigation (no crashes)
- [ ] Mobile responsive
- [ ] Maintains scroll position when changing pages
- [ ] API calls use environment-based URL
- [ ] Component has loading/error states
- [ ] Tested with 26K products

## Component Design

### UI Layout
```
┌─────────────────────────────────────────┐
│ Inventory List                    ↻     │
├─────────────────────────────────────────┤
│                                         │
│ [Product 1] [Product 2] [Product 3]   │
│ [Product 4] [Product 5] [Product 6]   │
│ ... (50 items per page)                │
│                                         │
├─────────────────────────────────────────┤
│ Items per page: [50 ▼]                  │
│                                         │
│ [<<] [<] Page 1 of 529 [>] [>>]        │
│ Showing 1-50 of 26,420 items           │
└─────────────────────────────────────────┘
```

## Implementation

### Step 1: Create Pagination Component
```typescript
// src/components/Pagination/Pagination.tsx
import React, { useState } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onLimitChange,
}) => {
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
      {/* Items per page selector */}
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-600">Items per page:</label>
        <select
          value={itemsPerPage}
          onChange={(e) => onLimitChange(Number(e.target.value))}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm"
        >
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={250}>250</option>
        </select>
      </div>

      {/* Page info */}
      <div className="text-sm text-gray-600">
        Showing {startItem.toLocaleString()} to {endItem.toLocaleString()} of {totalItems.toLocaleString()} items
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50"
          title="First page"
        >
          ⟨⟨
        </button>

        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50"
          title="Previous page"
        >
          ⟨
        </button>

        <span className="text-sm text-gray-600">
          Page <input
            type="number"
            value={currentPage}
            onChange={(e) => {
              const page = Math.min(Math.max(1, Number(e.target.value)), totalPages);
              onPageChange(page);
            }}
            min="1"
            max={totalPages}
            className="w-12 text-center border border-gray-300 rounded-md text-sm"
          /> of {totalPages}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50"
          title="Next page"
        >
          ⟩
        </button>

        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50"
          title="Last page"
        >
          ⟩⟩
        </button>
      </div>
    </div>
  );
};
```

### Step 2: Create Inventory List Hook
```typescript
// src/hooks/useInventory.ts
import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface Inventory {
  id: number;
  product_name: string;
  sku: string;
  current_stock: number;
  status: string;
  price: number;
  last_updated: string;
}

interface InventoryResponse {
  data: Inventory[];
  pagination: {
    total: number;
    page: number;
    pages: number;
    hasMore: boolean;
  };
}

export const useInventory = () => {
  const [items, setItems] = useState<Inventory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  const fetchInventory = async (page: number, limit: number) => {
    setLoading(true);
    setError(null);
    
    try {
      const offset = (page - 1) * limit;
      const response = await apiClient.get<InventoryResponse>('/inventory/list', {
        params: { limit, offset },
      });

      setItems(response.data.data);
      setTotalItems(response.data.pagination.total);
      setTotalPages(response.data.pagination.pages);
      setCurrentPage(page);
      setItemsPerPage(limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch inventory');
      console.error('Inventory fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory(currentPage, itemsPerPage);
  }, [currentPage, itemsPerPage]);

  return {
    items,
    loading,
    error,
    currentPage,
    itemsPerPage,
    totalItems,
    totalPages,
    setCurrentPage,
    setItemsPerPage,
  };
};
```

### Step 3: Update Inventory Page
```typescript
// src/pages/InventoryPage.tsx
import React from 'react';
import { useInventory } from '../hooks/useInventory';
import { Pagination } from '../components/Pagination/Pagination';

export const InventoryPage: React.FC = () => {
  const {
    items,
    loading,
    error,
    currentPage,
    itemsPerPage,
    totalItems,
    totalPages,
    setCurrentPage,
    setItemsPerPage,
  } = useInventory();

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Inventory</h1>

      {loading && <div className="text-center py-8">Loading...</div>}

      {!loading && (
        <>
          {/* Items Table */}
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Product Name</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">SKU</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold">Stock</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold">Price</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b hover:bg-gray-50">
                    <td className="px-6 py-4">{item.product_name}</td>
                    <td className="px-6 py-4">{item.sku}</td>
                    <td className="px-6 py-4 text-right">{item.current_stock}</td>
                    <td className="px-6 py-4 text-right">${item.price.toFixed(2)}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${
                        item.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            itemsPerPage={itemsPerPage}
            onPageChange={setCurrentPage}
            onLimitChange={setItemsPerPage}
          />
        </>
      )}
    </div>
  );
};
```

## Testing

### Test Navigation
```typescript
// src/components/Pagination/__tests__/Pagination.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Pagination } from '../Pagination';

describe('Pagination', () => {
  it('renders page buttons', () => {
    const mockOnPageChange = jest.fn();
    render(
      <Pagination
        currentPage={1}
        totalPages={10}
        totalItems={500}
        itemsPerPage={50}
        onPageChange={mockOnPageChange}
        onLimitChange={jest.fn()}
      />
    );

    expect(screen.getByText('Showing 1 to 50')).toBeInTheDocument();
  });

  it('calls onPageChange when next button clicked', () => {
    const mockOnPageChange = jest.fn();
    render(
      <Pagination
        currentPage={1}
        totalPages={10}
        totalItems={500}
        itemsPerPage={50}
        onPageChange={mockOnPageChange}
        onLimitChange={jest.fn()}
      />
    );

    fireEvent.click(screen.getByTitle('Next page'));
    expect(mockOnPageChange).toHaveBeenCalledWith(2);
  });
});
```

## Related Issues
- #3.1 Backend Pagination
- #2.2 Frontend Environment Config
- #1.4 API Testing

## Performance Metrics

| Metric | Target | Note |
|--------|--------|------|
| Page load | < 500ms | Including API call |
| Navigation | < 200ms | Switch between pages |
| Render | < 100ms | React render time |
| Mobile | Responsive | All screen sizes |

## Definition of Done
✅ Pagination component renders correctly  
✅ All 528 pages accessible  
✅ Items per page selector works  
✅ Navigation buttons functional  
✅ Mobile responsive  
✅ No crashes with 26K products  
✅ API calls use environment-based URL
