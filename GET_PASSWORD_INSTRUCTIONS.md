# 🔑 GET YOUR SUPABASE DATABASE PASSWORD

## CRITICAL: You need to add your database password to `.env` file

### Step 1: Get Your Password from Supabase Dashboard

1. **Go to Supabase Dashboard**:
   ```
   https://supabase.com/dashboard/project/ihraowxbduhlichzszgk/settings/database
   ```

2. **Find "Database password" section**

3. **Copy the password** (or reset if you forgot it)

### Step 2: Update `.env` File

Open `.env` and replace this line:
```
DB_PASSWORD=YOUR_DATABASE_PASSWORD_HERE
```

With your actual password:
```
DB_PASSWORD=your_actual_password_here
```

### Step 3: Test Connection

Run the test script:
```bash
python test_supabase_connection.py
```

---

## ⚠️ IMPORTANT NOTES

### Why You Need the Database Password:

1. **Your code uses `psycopg2.connect()`** - This is direct PostgreSQL connection
2. **The SUPABASE_KEY (anon key) is for REST API only** - Cannot be used with psycopg2
3. **Direct database access requires the database password**

### What We've Already Configured:

✅ **DB_HOST**: `db.ihraowxbduhlichzszgk.supabase.co`  
✅ **DB_PORT**: `5432`  
✅ **DB_NAME**: `postgres`  
✅ **DB_USER**: `postgres`  
❌ **DB_PASSWORD**: **YOU NEED TO ADD THIS**

### Connection String Format:

```
postgresql://postgres:[YOUR-PASSWORD]@db.ihraowxbduhlichzszgk.supabase.co:5432/postgres
```

---

## 🚀 After Adding Password

Once you add the password, your API will connect to:
- ✅ Company Supabase database (not your local PostgreSQL)
- ✅ All 6 tables: locations, news_balanced_corpus_1, location_insights, price_trends, unified_data_DataType_Raghu, location_costs
- ✅ Direct SQL queries with full PostgreSQL features (CTEs, JOINs, PostGIS)

---

## 🔍 How to Find Password in Supabase

### Option 1: Database Settings Page
1. Go to: Settings → Database
2. Look for "Connection string" or "Database password"
3. Click "Show" or "Reveal" to see the password

### Option 2: Connection Pooler Settings
1. Go to: Settings → Database → Connection Pooler
2. Look for connection details
3. Password should be visible there

### Option 3: Reset Password
If you can't find it:
1. Go to: Settings → Database
2. Click "Reset database password"
3. Copy the new password immediately
4. Update `.env` file

---

## ❓ Still Having Issues?

If you cannot access the database password:
1. Contact your Supabase project admin
2. They need to share the database password with you
3. Or they can add you as a project member with database access

---

**Once you have the password, update `.env` and run the test script!**
