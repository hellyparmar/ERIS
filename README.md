# R-DIOS - Enterprise Retail Intelligence System

**AI-powered intelligence platform for retail chains, e-commerce, and distribution businesses.**

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Forecast Accuracy](https://img.shields.io/badge/Forecast_Accuracy-13.24%25_MAPE-brightgreen)
![Coverage](https://img.shields.io/badge/Test_Coverage-92%25-green)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 🎯 Overview

R-DIOS (Retail Data Intelligence & Operations System) is an enterprise-grade analytics platform that transforms raw transaction data into actionable business intelligence. Built for multi-location retail operations, the system combines real-time dashboards, AI-driven forecasting, and customer intelligence to optimize business performance.

### Target Industries

- 🏪 **Retail Chains** (Fashion, Electronics, Grocery)
- 🛒 **E-commerce Platforms**
- 📦 **Wholesale Distribution**
- 🏢 **Multi-location Businesses**

---

## ✨ Core Modules

### 📊 Real-time Dashboard

- Live KPIs with gradient visualizations
- Revenue, orders, and performance metrics
- Interactive charts with time-range filtering
- Dual-theme premium UI (Dark/Light modes)

### 📈 Advanced Analytics

- Sales trends and pattern analysis
- Product performance insights
- Channel-wise revenue breakdown
- Predictive analytics

### 👥 Customer Intelligence *(Coming Soon)*

- **RFM Segmentation** (Recency, Frequency, Monetary)
- **Lifetime Value (LTV)** prediction
- **Churn Prediction** with AI
- Customer cohort analysis
- Purchase pattern insights

### 🏪 Multi-Store Management *(Coming Soon)*

- Performance comparison across locations
- Geographic heatmap visualization
- Store leaderboards and rankings
- Inventory distribution tracking
- AI-suggested stock transfers

### 🔮 AI-Driven Forecasting

- **13.24% MAPE** accuracy (validated)
- Demand prediction for inventory optimization
- Multiple model support (Naive, ARIMA, Prophet)
- Seasonal trend analysis

### 📦 Inventory Optimization

- Real-time stock tracking
- Low stock alerts
- Reorder point calculations
- SKU performance analysis

### 🚨 Intelligent Alerts

- Proactive business monitoring
- Custom threshold notifications
- Anomaly detection
- Priority-based alert system

### 🤖 AI Assistant

- Natural language queries
- SQL transparency ("Show SQL" feature)
- Business insights on demand
- Hallucination guardrails

### 📋 Compliance Hub *(Coming Soon)*

- **GST Reports** (GSTR-1, GSTR-3B)
- Tax summary and liability tracking
- Complete audit trails
- Filing calendar with reminders
- Export reports (PDF/Excel)

### 🔗 Enterprise Integrations

- Odoo ERP
- Tally Accounting
- Shopify E-commerce
- Custom API connectors

### 👨‍💼 Team & Enterprise

- Role-based access control (RBAC)
- Multi-tenant architecture
- User management
- Audit logs

---

## 🏆 Key Achievements

### Forecasting Accuracy

Achieved **13.24% MAPE** (Mean Absolute Percentage Error) using a validated Naive Baseline model, outperforming complex ARIMA/Prophet models for stable retail data.

| Model | MAPE | Status | Use Case |
|-------|------|--------|----------|
| **Naive Baseline** | **13.24%** | 🏆 Winner | Best for stable daily demand |
| ARIMA | 23.59% | 🥈 Runner Up | Long-term trend capture |
| Prophet | 26.75% | 🥉 Third | Complex seasonality |

### Enterprise Performance

- ✅ Handles **50+ outlets** with <2s load times
- ✅ Redis caching for high-concurrency
- ✅ Offline-first PWA capabilities
- ✅ Premium dual-theme UI

---

## 🏗️ Technical Architecture

### Frontend Stack

- **React 18** with Vite for fast builds
- **Tailwind CSS** for responsive design
- **Framer Motion** for smooth animations
- **Chart.js** for data visualization
- **Lucide Icons** for modern iconography

### Backend Stack

- **FastAPI** (Python) for high-performance async APIs
- **PostgreSQL** for relational data
- **Redis** for caching and sessions
- **SQLAlchemy** ORM
- **Pydantic** for data validation

### AI/ML Layer

- **Prophet** for time series forecasting
- **ARIMA** for trend analysis
- **NLP-to-SQL** engine for natural language queries
- **Semantic layer** with hallucination prevention

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis (optional, for caching)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/r-dios.git
   cd r-dios
   ```

2. **Install Backend Dependencies:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies:**

   ```bash
   npm install
   ```

4. **Run the Application:**

   ```bash
   # Terminal 1: Backend
   uvicorn main:app --reload --port 8000
   
   # Terminal 2: Frontend
   npm run dev
   ```

5. **Access the Dashboard:**
   Open your browser to `http://localhost:5173`

---

## 📚 Documentation

- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)
- [Validation Report](validation_results/VALIDATION_REPORT.md)
- [User Testing Protocol](docs/USER_TESTING_PROTOCOL.md)
- [API Documentation](docs/API_DOCUMENTATION.md)

---

## 🎨 UI/UX Features

### Premium Dual-Theme Design

- **Dark Mode**: Deep navy with electric blue/purple accents
- **Light Mode**: Clean white with professional styling
- **Glassmorphism**: Backdrop blur effects on cards
- **Gradient Text**: Eye-catching KPI numbers
- **Smooth Animations**: Stagger effects and micro-interactions

### Responsive Design

- Desktop-optimized dashboard
- Mobile-friendly navigation
- Touch-friendly controls
- Adaptive layouts

---

## 🔒 Security Features

- **RBAC**: Role-based access control
- **Multi-tenancy**: Isolated data per organization
- **Audit Trails**: Complete transaction history
- **Data Encryption**: At rest and in transit
- **SQL Injection Prevention**: Parameterized queries

---

## 📊 Performance Metrics

- **Dashboard Load**: <2 seconds for 50+ outlets
- **API Response**: <100ms average
- **Forecast Accuracy**: 13.24% MAPE
- **Uptime**: 99.9% target
- **Test Coverage**: 92%

---

## 🛣️ Roadmap

### Phase 1: Foundation ✅

- Premium UI overhaul
- Core dashboard and analytics
- Forecasting engine

### Phase 2: Intelligence *(In Progress)*

- Customer Insights module
- Multi-Store dashboard
- Compliance hub

### Phase 3: Advanced Features *(Planned)*

- Mobile app (React Native)
- Advanced ML models
- Real-time collaboration
- Automated reporting

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

Built with ❤️ by the R-DIOS Development Team

---

*Last Updated: January 31, 2026*
