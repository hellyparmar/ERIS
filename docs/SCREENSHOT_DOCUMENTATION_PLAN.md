# R-DIOS Screenshot Documentation Plan

## Overview

This document provides a structured approach to capturing comprehensive visual evidence of the R-DIOS system for academic submission and stakeholder presentations.

**Objective:** Create 20-30 annotated screenshots demonstrating all core features and workflows

**Tools Required:**

- Browser screenshot tool (built-in or Greenshot/Flameshot)
- Image annotation software (built-in or Snagit)
- Image optimization (TinyPNG or similar)

---

## Screenshot Checklist

### Category 1: Dashboard & Overview (5 screenshots)

#### 1.1 Dashboard - Light Mode - Desktop

- **File:** `01_dashboard_light_desktop.png`
- **URL:** `http://localhost:5173/dashboard`
- **Viewport:** 1920x1080
- **Annotations:**
  - Highlight KPI cards (Revenue, Transactions, Growth)
  - Point out real-time data indicator
  - Mark navigation sidebar
  - Circle date range selector
- **Caption:** "Main dashboard showing real-time KPIs and revenue trends"

#### 1.2 Dashboard - Dark Mode - Desktop

- **File:** `02_dashboard_dark_desktop.png`
- **URL:** `http://localhost:5173/dashboard`
- **Viewport:** 1920x1080
- **Action:** Toggle dark mode
- **Annotations:**
  - Show theme toggle button
  - Highlight improved readability
- **Caption:** "Dark mode for reduced eye strain during extended use"

#### 1.3 Dashboard - Mobile Responsive

- **File:** `03_dashboard_mobile.png`
- **URL:** `http://localhost:5173/dashboard`
- **Viewport:** 375x667 (iPhone SE)
- **Annotations:**
  - Show responsive layout
  - Highlight touch-friendly controls
- **Caption:** "Mobile-responsive design for on-the-go access"

#### 1.4 Revenue Trend Chart - Interactive

- **File:** `04_revenue_chart_interactive.png`
- **URL:** `http://localhost:5173/dashboard`
- **Action:** Hover over chart data point
- **Annotations:**
  - Show tooltip with exact values
  - Highlight zoom controls
  - Mark export button
- **Caption:** "Interactive charts with drill-down capabilities"

#### 1.5 Multi-Store Comparison

- **File:** `05_multi_store_comparison.png`
- **URL:** `http://localhost:5173/dashboard`
- **Action:** Select multiple stores
- **Annotations:**
  - Show store selector dropdown
  - Highlight comparative metrics
  - Mark best/worst performers
- **Caption:** "Compare performance across multiple store locations"

---

### Category 2: Forecasting Module (7 screenshots)

#### 2.1 Forecast Page - Initial View

- **File:** `06_forecast_initial.png`
- **URL:** `http://localhost:5173/forecasts`
- **Annotations:**
  - Show product selector
  - Highlight forecast configuration panel
  - Mark historical data view
- **Caption:** "Forecast generation interface with configurable parameters"

#### 2.2 Product Selection

- **File:** `07_forecast_product_select.png`
- **URL:** `http://localhost:5173/forecasts`
- **Action:** Open product dropdown
- **Annotations:**
  - Show search functionality
  - Highlight product categories
  - Mark recently forecasted items
- **Caption:** "Smart product search with category filtering"

#### 2.3 Forecast Configuration

- **File:** `08_forecast_config.png`
- **URL:** `http://localhost:5173/forecasts`
- **Action:** Expand configuration panel
- **Annotations:**
  - Highlight forecast horizon selector (7, 14, 30 days)
  - Show confidence level slider (90%, 95%, 99%)
  - Mark model selector (Prophet, ARIMA, Ensemble)
- **Caption:** "Flexible forecast configuration for different use cases"

#### 2.4 Forecast Generation - Loading

- **File:** `09_forecast_loading.png`
- **URL:** `http://localhost:5173/forecasts`
- **Action:** Click "Generate Forecast" button
- **Annotations:**
  - Show loading spinner
  - Highlight progress indicator
  - Mark estimated time remaining
- **Caption:** "Real-time progress tracking during forecast generation"

#### 2.5 Forecast Results - Chart View

- **File:** `10_forecast_results_chart.png`
- **URL:** `http://localhost:5173/forecasts`
- **Action:** View generated forecast
- **Annotations:**
  - Highlight predicted values (blue line)
  - Show actual historical values (green line)
  - Mark confidence interval bands (shaded area)
  - Point out MAPE accuracy metric
- **Caption:** "7-day demand forecast with 95% confidence intervals (MAPE: 14.2%)"

#### 2.6 Forecast Results - Table View

- **File:** `11_forecast_results_table.png`
- **URL:** `http://localhost:5173/forecasts`
- **Action:** Switch to table view
- **Annotations:**
  - Show date, predicted demand, lower/upper bounds
  - Highlight recommended order quantity
  - Mark export to Excel button
- **Caption:** "Detailed forecast data with actionable order recommendations"

#### 2.7 Forecast Accuracy Metrics

- **File:** `12_forecast_accuracy.png`
- **URL:** `http://localhost:5173/forecasts`
- **Action:** Scroll to metrics section
- **Annotations:**
  - Highlight MAPE, RMSE, MAE, R² values
  - Show model comparison (Prophet vs ARIMA)
  - Mark confidence score
- **Caption:** "Transparent accuracy metrics build user trust"

---

### Category 3: AI Assistant (8 screenshots)

#### 3.1 AI Assistant - Initial State

- **File:** `13_ai_assistant_initial.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Annotations:**
  - Show chat interface
  - Highlight suggested queries
  - Mark voice input button (if available)
- **Caption:** "Natural language query interface with suggested questions"

#### 3.2 Query Example 1 - Simple Aggregation

- **File:** `14_ai_query_simple.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** Type "Show total revenue this month"
- **Annotations:**
  - Show user query
  - Highlight AI response with formatted data
  - Mark response time
- **Caption:** "Simple query: 'Show total revenue this month' (Response time: 1.2s)"

#### 3.3 SQL Preview - Human-in-the-Loop

- **File:** `15_ai_sql_preview.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** AI shows SQL before execution
- **Annotations:**
  - Highlight generated SQL query
  - Show confidence score (95%)
  - Mark "Execute" and "Modify" buttons
  - Point out plain English explanation
- **Caption:** "Transparent SQL generation with human-in-the-loop confirmation"

#### 3.4 Query Example 2 - Comparison

- **File:** `16_ai_query_comparison.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** Type "Compare this week's revenue to last week"
- **Annotations:**
  - Show comparative results (table or chart)
  - Highlight percentage change
  - Mark insights/recommendations
- **Caption:** "Time-based comparison with automatic insights"

#### 3.5 Query Example 3 - Top N

- **File:** `17_ai_query_topn.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** Type "Top 10 products by profit margin"
- **Annotations:**
  - Show ranked results
  - Highlight profit margin column
  - Mark drill-down capability
- **Caption:** "Ranking queries with sortable results"

#### 3.6 Error Handling - Invalid Query

- **File:** `18_ai_error_handling.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** Type ambiguous query "Show sales"
- **Annotations:**
  - Show clarification request
  - Highlight suggested refinements
  - Mark help button
- **Caption:** "Graceful error handling with helpful suggestions"

#### 3.7 Query History

- **File:** `19_ai_query_history.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** Open query history panel
- **Annotations:**
  - Show recent queries
  - Highlight "Re-run" button
  - Mark "Save as Template" option
- **Caption:** "Query history for easy re-use and template creation"

#### 3.8 Template Library

- **File:** `20_ai_templates.png`
- **URL:** `http://localhost:5173/ai-assistant`
- **Action:** Open template library
- **Annotations:**
  - Show pre-built query templates
  - Highlight categories (Sales, Inventory, Customers)
  - Mark customization options
- **Caption:** "Template library helps users learn effective querying"

---

### Category 4: Reports & Exports (3 screenshots)

#### 4.1 Report Builder

- **File:** `21_report_builder.png`
- **URL:** `http://localhost:5173/reports`
- **Annotations:**
  - Show drag-and-drop interface
  - Highlight available widgets
  - Mark preview pane
- **Caption:** "Custom report builder with drag-and-drop widgets"

#### 4.2 PDF Export Preview

- **File:** `22_pdf_export.png`
- **URL:** `http://localhost:5173/reports`
- **Action:** Click "Export to PDF"
- **Annotations:**
  - Show PDF preview
  - Highlight branding options
  - Mark download button
- **Caption:** "Professional PDF reports with custom branding"

#### 4.3 Scheduled Reports

- **File:** `23_scheduled_reports.png`
- **URL:** `http://localhost:5173/reports`
- **Action:** Open schedule configuration
- **Annotations:**
  - Show frequency selector (Daily, Weekly, Monthly)
  - Highlight email recipients
  - Mark report template
- **Caption:** "Automated report delivery via email"

---

### Category 5: Integrations & Settings (4 screenshots)

#### 5.1 Integration Dashboard

- **File:** `24_integrations_dashboard.png`
- **URL:** `http://localhost:5173/integrations`
- **Annotations:**
  - Show connected ERPs (Odoo, Tally, WooCommerce)
  - Highlight sync status (green = active, red = error)
  - Mark last sync timestamp
- **Caption:** "Real-time integration status monitoring"

#### 5.2 ERP Configuration - Odoo

- **File:** `25_erp_config_odoo.png`
- **URL:** `http://localhost:5173/integrations/odoo`
- **Annotations:**
  - Show connection settings
  - Highlight sync frequency
  - Mark data mapping configuration
- **Caption:** "Flexible ERP integration with custom field mapping"

#### 5.3 Data Sync Logs

- **File:** `26_sync_logs.png`
- **URL:** `http://localhost:5173/integrations/logs`
- **Annotations:**
  - Show sync history
  - Highlight error messages
  - Mark retry button
- **Caption:** "Detailed sync logs for troubleshooting"

#### 5.4 User Settings & Preferences

- **File:** `27_user_settings.png`
- **URL:** `http://localhost:5173/settings`
- **Annotations:**
  - Show theme selector
  - Highlight notification preferences
  - Mark language options
- **Caption:** "Customizable user preferences and notifications"

---

### Category 6: Validation Results (3 screenshots)

#### 6.1 Validation Report - Model Comparison

- **File:** `28_validation_model_comparison.png`
- **Source:** `validation_results/model_comparison.png`
- **Annotations:**
  - Highlight Prophet (14.2% MAPE)
  - Show ARIMA (16.8% MAPE)
  - Mark baseline (28.5% MAPE)
  - Point out 50% improvement
- **Caption:** "Rigorous validation showing 50% improvement over baseline"

#### 6.2 Validation Report - Predicted vs Actual

- **File:** `29_validation_predicted_actual.png`
- **Source:** `validation_results/predicted_vs_actual.png`
- **Annotations:**
  - Highlight close tracking
  - Show confidence intervals
  - Mark accuracy metrics
- **Caption:** "Predicted vs actual revenue demonstrating forecast accuracy"

#### 6.3 Validation Report - Error Distribution

- **File:** `30_validation_error_dist.png`
- **Source:** `validation_results/error_distribution.png`
- **Annotations:**
  - Show normal distribution
  - Highlight mean near zero (unbiased)
  - Mark 90% within ±20%
- **Caption:** "Error distribution analysis confirms model reliability"

---

## Annotation Guidelines

### Visual Hierarchy

1. **Primary annotations (red):** Key features being demonstrated
2. **Secondary annotations (blue):** Supporting information
3. **Tertiary annotations (green):** Context or optional features

### Annotation Types

- **Arrows:** Point to specific UI elements
- **Boxes:** Highlight regions or groups
- **Numbers:** Sequential steps in a workflow
- **Text labels:** Explain functionality

### Best Practices

- Keep annotations minimal (3-5 per screenshot)
- Use consistent colors and styles
- Ensure text is readable (14pt+ font)
- Avoid cluttering the interface
- Save both annotated and clean versions

---

## File Organization

```
docs/screenshots/
├── 01_dashboard/
│   ├── 01_dashboard_light_desktop.png
│   ├── 02_dashboard_dark_desktop.png
│   ├── 03_dashboard_mobile.png
│   ├── 04_revenue_chart_interactive.png
│   └── 05_multi_store_comparison.png
├── 02_forecasting/
│   ├── 06_forecast_initial.png
│   ├── 07_forecast_product_select.png
│   └── ...
├── 03_ai_assistant/
│   └── ...
├── 04_reports/
│   └── ...
├── 05_integrations/
│   └── ...
├── 06_validation/
│   └── ...
└── README.md (this file)
```

---

## Usage in Documentation

### Thesis/Report

```markdown
## System Implementation

### Dashboard Interface

![Dashboard Overview](docs/screenshots/01_dashboard/01_dashboard_light_desktop.png)
*Figure 1: Main dashboard showing real-time KPIs and revenue trends*

The dashboard provides at-a-glance visibility into key business metrics...
```

### Presentation Slides

- Use high-resolution images (1920x1080 minimum)
- Crop to focus on relevant areas
- Add slide titles matching screenshot captions

### GitHub README

```markdown
## Features

### 📊 Real-Time Dashboard
![Dashboard](docs/screenshots/01_dashboard/01_dashboard_light_desktop.png)

### 🔮 AI-Powered Forecasting
![Forecasting](docs/screenshots/02_forecasting/10_forecast_results_chart.png)
```

---

## Automation Script

For batch screenshot capture, use the provided script:

```bash
# Install dependencies
npm install -g puppeteer-screenshot-cli

# Capture all screenshots
./scripts/capture_screenshots.sh
```

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Capture screenshots (estimated time: 2-3 hours)
3. ⏳ Annotate images (estimated time: 2-3 hours)
4. ⏳ Organize files
5. ⏳ Update documentation with embedded images

**Total Estimated Time:** 4-6 hours
