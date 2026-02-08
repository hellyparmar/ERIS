# Page Standardization Guide

This document outlines the standard page structure and spacing for all R-DIOS pages.

## Standard Page Structure

All pages should follow this structure for consistency:

```jsx
import { PageWrapper, PageHeader } from '../components/layout/PageWrapper';

const MyPage = () => {
  return (
    <PageWrapper>
      {/* Header Section */}
      <PageHeader
        title="Page Title"
        description="Page description here"
        actions={/* Optional action buttons */}
      />

      {/* Content Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Cards/Content */}
      </div>

      {/* Additional Sections */}
      <div className="space-y-6">
        {/* More content */}
      </div>
    </PageWrapper>
  );
};
```

## Standardized Spacing

- **Page wrapper spacing**: `space-y-6` (24px between sections)
- **Grid gaps**: `gap-6` (24px)
- **Title to description margin**: `mb-1` (4px)
- **Header bottom margin**: Built into PageHeader component

## Standardized Header

Use the `PageHeader` component for all pages:

```jsx
<PageHeader
  title="Page Title"
  description="Short description"
  actions={<button>Action</button>}
  animate={true} // Optional: enable fade-in animation
/>
```

## Loading States

All pages should use consistent loading overlays:

```jsx
{loading && (
  <div className="fixed inset-0 bg-background/50 backdrop-blur-sm flex items-center justify-center z-50">
    <div className="text-center space-y-4">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full animate-pulse">
        <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
      <p className="text-lg font-semibold text-foreground">Page is loading...</p>
    </div>
  </div>
)}
```

## Pages Updated (✓ Standardized)

- ✓ Dashboard
- ✓ Analytics (partially)
- PageWrapper component created for future use

## Next Steps

All remaining pages should be updated to use the new `PageWrapper` and `PageHeader` components to ensure consistency across the entire application.
