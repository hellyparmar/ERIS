# Supabase Quick Start - R-DIOS
## Get up and running in 5 minutes!

### 🎯 Current Status
✅ **Supabase support implemented**  
✅ **Configuration files created**  
⏳ **Waiting for your Supabase project**

---

## 🚀 Quick Setup (3 Steps)

### 1. Create Supabase Project (2 minutes)
```
1. Go to: https://supabase.com
2. Click "Start your project" → Sign up with GitHub
3. New Project:
   - Name: r-dios-production
   - Password: [SAVE THIS!]
   - Region: Southeast Asia (Singapore)
4. Wait ~2 minutes for setup
```

### 2. Get Connection String
```
Settings → Database → Connection string (URI mode)

Copy: postgresql://postgres.xxxxx:[PASSWORD]@aws-0...pooler.supabase.com:5432/postgres

Replace [PASSWORD] with your project password!
```

### 3. Update .env File
```bash
nano .env

# Paste your connection string:
DATABASE_URL=postgresql://postgres.xxxxx:YOUR_PASSWORD@aws-0...

# Save: Ctrl+X, Y, Enter
```

---

## ✅ That's It!

Your code will:
- ✅ Auto-detect Supabase (vs local)
- ✅ Auto-add SSL requirement  
- ✅ Use connection pooling
- ✅ Initialize Supabase client

Restart your API and it just works! 🎉

---

## 📚 Full Documentation

See `/home/petpooja/Enterprise Retail Intelligence System/docs/SUPABASE_SETUP.md` for:
- Database migration steps
- Troubleshooting
- Advanced features (Auth, Storage, Real-time)
- Performance tuning

---

## 🧪 Test Connection

```bash
# Restart API with new config
pkill -f uvicorn
python -m uvicorn api.main:app --reload

# Should see:
# 🌐 Using cloud database: aws-0-ap-southeast-1.pooler.supabase.com
# ✅ Supabase client initialized
```

---

## ⚡ Local Development

Keep using local PostgreSQL during development:

```env
# In .env:
DATABASE_URL=postgresql://petpooja:password@localhost:5432/rdios_db

# Code auto-detects local vs cloud!
```

---

**Need help?** Check the full guide: `docs/SUPABASE_SETUP.md`
