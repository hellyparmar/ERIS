# Supabase Setup Guide for R-DIOS
## Quick Start - Get Your App Running on Supabase in 10 Minutes

---

## 📋 Prerequisites

- ✅ R-DIOS codebase (your current setup)
- ✅ GitHub account (for Supabase sign up)
- ✅ Your existing local PostgreSQL database

---

## 🚀 Step 1: Create Supabase Account

1. Go to: **https://supabase.com**
2. Click **"Start your project"**
3. Sign up with GitHub (recommended)
4. Verify your email

---

## 🗄️ Step 2: Create Database Project

1. Click **"New Project"**
2. Fill in details:
   ```
   Organization: Create new (or select existing)
   Project Name: r-dios-production
   Database Password: [SAVE THIS!]
   Region: Southeast Asia (Singapore) - closest to India
   ```
3. Click **"Create new project"**
4. Wait ~2 minutes for provisioning

---

## 🔑 Step 3: Get Your Connection Details

### A. Database Connection String

1. Go to **Project Settings** (⚙️ icon bottom left)
2. Click **Database** tab
3. Scroll to **Connection string** → Select **URI** mode
4. Copy the string:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
5. **Replace `[YOUR-PASSWORD]`** with the password you created in Step 2

### B. API Keys (Optional - for advanced features)

1. Go to **Project Settings** → **API** tab
2. Copy:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **anon/public key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

---

## ⚙️ Step 4: Configure Your R-DIOS Project

### Update .env File

```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System
nano .env
```

Add/update these lines:

```env
# Supabase Database
DATABASE_URL=postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres

# Supabase API (optional)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Save and exit (Ctrl+X, Y, Enter)

---

## 🏗️ Step 5: Set Up Database Schema

### Option A: Using Supabase SQL Editor (Recommended)

1. In Supabase Dashboard, go to **SQL Editor**
2. Click **"New query"**
3. Run your migrations one by one:

```sql
-- First, enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Then copy and paste your migration files
-- Start with: migrations/001_create_organizations_stores.sql
```

4. Execute each migration file in order:
   - `001_create_organizations_stores.sql`
   - `002_add_multitenant_columns.sql`
   - `003_enable_row_level_security.sql`
   - `004_gst_schema.sql`

### Option B: Using Command Line

```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

# Run all migrations
for file in migrations/*.sql; do
  psql "$DATABASE_URL" < "$file"
  echo "✅ Completed: $file"
done
```

---

## ✅ Step 6: Test Connection

```bash
# Test database connection
psql "$DATABASE_URL" -c "SELECT version();"

# Should output: PostgreSQL 15.x on ...

# Check tables were created
psql "$DATABASE_URL" -c "\dt"

# Should list: organizations, stores, products, customers, etc.
```

---

## 🔄 Step 7: Restart Your API

```bash
# Kill existing API process
pkill -f uvicorn

# Start with Supabase database
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System
python -m uvicorn api.main:app --reload --port 8000
```

**Expected output:**
```
🌐 Using cloud database: aws-0-ap-southeast-1.pooler.supabase.com
✅ Supabase client initialized
INFO:     Application startup complete.
```

---

## 🧪 Step 8: Verify Everything Works

### A. API Health Check

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "3.0"
}
```

### B. Test Frontend

```bash
# Make sure frontend is running
npm run dev

# Open browser: http://localhost:5173
```

Dashboard should load with data!

---

## 🎛️ Step 9: Supabase Dashboard Features

### Database Management

1. **Table Editor** - View/edit data visually
2. **SQL Editor** - Run custom queries
3. **Database** → **Roles** - Manage users
4. **Database** → **Replication** - Configure backups

### Monitoring

1. **Logs** tab - See all database queries
2. **Reports** tab - Performance metrics
3. **Database** → **Backups** - Daily backups (7-day retention)

---

## 🔒 Step 10: Enable Row-Level Security (RLS)

Your multi-tenant setup uses RLS. Verify it's enabled:

```sql
-- In Supabase SQL Editor:
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Should show: rowsecurity = true for your tables
```

---

## 📦 Optional: Migrate Existing Data

If you have data in local PostgreSQL:

```bash
# 1. Export from local
pg_dump -U petpooja -d rdios_db --data-only --inserts > local_data.sql

# 2. Import to Supabase
psql "$DATABASE_URL" < local_data.sql
```

---

## 🔧 Troubleshooting

### "SSL connection required"
✅ Already handled in `database_postgres.py` - it auto-adds `?sslmode=require`

### "Connection timeout"
- Check your internet connection
- Verify region is correct (Singapore for India)
- Try from different network (not behind restrictive firewall)

### "Permission denied"
```sql
-- Run in SQL Editor:
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### "Migration failed"
- Check migration order (run in sequence: 001, 002, 003, 004)
- Verify no syntax errors in SQL files
- Check Supabase Logs tab for error details

---

## 💰 Pricing (Free Tier Limits)

**Supabase Free Plan:**
- ✅ 500 MB database storage
- ✅ 1 GB file storage
- ✅ 50,000 monthly active users
- ✅ 2 GB bandwidth/month
- ✅ Social OAuth (Google, GitHub, etc.)
- ✅ 7-day backups

**When to upgrade to Pro ($25/mo):**
- Need more than 8 GB database
- Want daily backups (no 7-day limit)
- Need priority support
- Require custom domains

---

## 🎓 Bonus: Supabase Advanced Features

### Authentication (Future)

```python
# Already set up in database_postgres.py
from api.db.database_postgres import supabase_client

# Sign up user
user = supabase_client.auth.sign_up({
    "email": "user@example.com",
    "password": "password123"
})

# Sign in
session = supabase_client.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "password123"
})
```

### Real-time Subscriptions

```python
# Listen to database changes
def handle_change(payload):
    print(f"Change detected: {payload}")

supabase_client.table('products').on('INSERT', handle_change).subscribe()
```

### Storage (for invoice PDFs)

```python
# Upload invoice PDF
supabase_client.storage.from_('invoices').upload(
    'invoice_001.pdf',
    invoice_pdf_bytes
)
```

---

## ✅ Success Checklist

- [x] Created Supabase account
- [x] Created r-dios-production project
- [x] Copied connection string
- [x] Updated .env file
- [x] Ran all migrations
- [x] Tested database connection
- [x] Restarted API successfully
- [x] Frontend loads and displays data
- [x] Row-Level Security enabled

---

## 🎉 You're Done!

Your R-DIOS system is now running on **Supabase cloud database**!

**Next steps:**
- Deploy your API to production (Railway, Render, fly.io)
- Deploy your frontend (Vercel, Netlify)
- Set up custom domain
- Enable Supabase Authentication for users

**Need help?** Check Supabase docs: https://supabase.com/docs
