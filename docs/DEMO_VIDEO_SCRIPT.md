# R-DIOS Demo Video Script (10 Minutes)

## Video Overview

**Title:** R-DIOS: AI-Powered Retail Intelligence Platform  
**Duration:** 10 minutes  
**Audience:** Academic evaluators, potential employers, Petpooja stakeholders

---

## Section 1: Introduction (1 min)

**[0:00 - 1:00]**

### Narration
>
> "Welcome to R-DIOS - Retail Data Intelligence and Operations System. This is an AI-powered enterprise intelligence platform I developed during my MSc Data Science internship at Petpooja.
>
> R-DIOS helps small and medium retailers make data-driven decisions through three core capabilities:
>
> 1. **AI-powered demand forecasting** with validated 4.57% MAPE accuracy
> 2. **Natural language analytics** - ask questions in plain English or Hindi
> 3. **Multi-store operations** - manage multiple locations from one dashboard"

### Visuals

- Show R-DIOS logo/splash screen
- Quick montage of dashboard, forecasting, AI assistant

---

## Section 2: Dashboard Overview (2 min)

**[1:00 - 3:00]**

### Narration
>
> "Let's start with the dashboard. Here you'll see real-time KPIs including total revenue, order count, average order value, and inventory status.
>
> The system processes over 232,000 transaction records and provides insights across multiple stores. Notice the revenue trend chart showing seasonal patterns - you can see spikes during Diwali and dips during monsoon season.
>
> I've implemented both light and dark modes for accessibility, and the entire interface is mobile-responsive."

### Actions

1. Navigate to Dashboard page
2. Point out KPI cards (hover over each)
3. Show revenue trend chart
4. Toggle dark mode
5. Resize browser to show mobile view

---

## Section 3: AI Demand Forecasting (3 min)

**[3:00 - 6:00]**

### Narration
>
> "Now let's look at the forecasting module - the core ML capability of R-DIOS.
>
> I implemented Facebook Prophet with external regressors for Indian holidays and monsoon seasons. Through rigorous 5-fold time-series cross-validation, the model achieved **4.57% MAPE** - significantly better than the industry benchmark of 15-25%.
>
> What makes this special is the data fusion approach. By incorporating external factors like Diwali, Eid, and monsoon periods, accuracy improved by 48% compared to using date alone.
>
> The confidence intervals you see here represent 95% prediction bounds. This helps retailers understand uncertainty when making inventory decisions."

### Actions

1. Navigate to Forecasts page
2. Select 30-day forecast horizon
3. Show Prophet predictions with confidence bands
4. Point to validation metrics displayed
5. Show model comparison if available

### Technical Points to Mention

- Walk-forward validation (no data leakage)
- 365-day training window, 30-day horizon
- Holiday effects: Diwali +35%, Eid +30%
- Monsoon effect: -₹7,846/day

---

## Section 4: AI Assistant (2 min)

**[6:00 - 8:00]**

### Narration
>
> "The AI Assistant uses GPT-4 to convert natural language questions into SQL queries. Let me demonstrate.
>
> If I ask 'What were our top 5 products last month?' - the system understands this, generates the appropriate query, and returns formatted results.
>
> The assistant supports both English and Hindi, making it accessible to retailers across India who may not be comfortable with technical interfaces."

### Actions

1. Navigate to AI Assistant
2. Ask: "What were sales last week?"
3. Show the response
4. Ask: "Top 5 products by revenue this month"
5. Toggle language to Hindi
6. Ask a question in Hindi (if implemented)

### Points to Address

- Show query generation (if visible)
- Demonstrate confidence in results
- Mention semantic layer for accuracy

---

## Section 5: Multi-Store & Analytics (1.5 min)

**[8:00 - 9:30]**

### Narration
>
> "R-DIOS supports multi-store operations. Retailers can switch between locations, compare performance, and identify which stores need attention.
>
> The analytics module includes customer segmentation using RFM analysis, inventory optimization with reorder alerts, and tax compliance features for GST reporting."

### Actions

1. Show store selector dropdown
2. Switch between stores
3. Navigate to Inventory page briefly
4. Show Tax Compliance page
5. Demonstrate export (PDF/Excel)

---

## Section 6: Validation & Conclusion (0.5 min)

**[9:30 - 10:00]**

### Narration
>
> "To summarize the key achievements:
>
> - **4.57% forecast accuracy** - validated through academic-standard methodology
> - **76% improvement** over naive baseline
> - **48% improvement** from external data fusion
>
> This demonstrates that integrated, AI-powered retail intelligence can significantly outperform traditional forecasting methods.
>
> Thank you for watching. The full source code and documentation are available on GitHub."

### Visuals

- Show validation results summary
- Display key metrics on screen
- End with GitHub URL / contact info

---

## Recording Checklist

### Before Recording

- [ ] Clear browser cache/history
- [ ] Close unnecessary tabs
- [ ] Ensure backend is running (`uvicorn main:app`)
- [ ] Ensure frontend is running (`npm run dev`)
- [ ] Test all features work
- [ ] Prepare sample queries
- [ ] Check microphone levels

### Recording Setup

- **Screen resolution:** 1920x1080
- **Browser:** Chrome (incognito mode)
- **Recording tool:** OBS Studio / Loom
- **Audio:** Clear, consistent narration

### After Recording

- [ ] Review for errors
- [ ] Add captions/subtitles
- [ ] Export at 1080p
- [ ] Upload to YouTube (unlisted) or Loom
- [ ] Add to thesis documentation

---

## Talking Points Cheat Sheet

| Topic | Key Stat | Context |
|-------|----------|---------|
| Forecast accuracy | 4.57% MAPE | Industry: 15-25% |
| R² score | 0.877 | Excellent fit |
| Baseline improvement | 76% | Over naive |
| Regressor impact | 48% | Holiday/monsoon |
| Transactions | 232K+ | Real data |
| API endpoints | 54 | Full REST API |

---

## Contingency Plans

**If forecasting page doesn't load:**

- Show pre-captured screenshots
- Display validation_results/model_comparison.png

**If AI Assistant fails:**

- Show example query/response from documentation
- Explain the architecture without live demo

**If backend is slow:**

- Pre-load pages in separate tabs
- Cut to pre-recorded segments
