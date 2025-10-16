# 🚂 Railway Deployment Setup

## ✅ Files Created for Railway

Your project is now configured for Railway deployment with:

- ✅ **Procfile** - Tells Railway how to run your Django app
- ✅ **runtime.txt** - Specifies Python 3.10.12
- ✅ **requirements.txt** - Python dependencies
- ✅ **nixpacks.toml** - Build configuration
- ✅ **mindnotesBackend/Dockerfile** - Docker support (alternative)

---

## 🚀 Railway Deployment Steps

### 1. Go to Railway Dashboard

Your project: **MindNotes**
URL: https://railway.app/project/your-project-id

### 2. Configure Service Settings

Click on your **MindNotes** service → **Settings**:

#### Start Command (if auto-detection fails):
```bash
cd mindnotesBackend && gunicorn mindnotesBackend.wsgi:application --bind 0.0.0.0:$PORT
```

#### Root Directory (if needed):
```
mindnotesBackend
```

### 3. Set Environment Variables

Go to **Variables** tab and add:

#### Required Variables:
```env
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
PORT=8000

# PostgreSQL (Railway auto-provides these as DATABASE_URL)
POSTGRES_DATABASE=${PGDATABASE}
POSTGRES_HOST=${PGHOST}
POSTGRES_PORT=${PGPORT}
POSTGRES_USER=${PGUSER}
POSTGRES_PASSWORD=${PGPASSWORD}

# MongoDB (Use MongoDB Atlas free tier)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/mindnotes?retryWrites=true&w=majority
MONGODB_DB_NAME=mindnotes
MONGODB_HOST=cluster.mongodb.net
MONGODB_PORT=27017
MONGODB_USER=your_username
MONGODB_PASSWORD=your_password

# Redis (Railway auto-provides REDIS_URL)
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# CORS - Add your frontend URL
FRONTEND_URL=http://localhost:5173
CORS_ALLOW_ALL=False

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
```

#### Generate SECRET_KEY:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Add Database Services

#### PostgreSQL:
1. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically links it to your service

#### Redis:
1. Click **"+ New"** → **"Database"** → **"Redis"**
2. Railway automatically links it to your service

#### MongoDB:
Use **MongoDB Atlas** (Railway doesn't offer free MongoDB):
1. Go to https://cloud.mongodb.com
2. Create free cluster (512MB)
3. Create database user
4. Get connection string
5. Add to Railway environment variables

### 5. Deploy

Railway will automatically deploy when you push to GitHub:

```bash
git add .
git commit -m "Configure Railway deployment"
git push origin main
```

### 6. Run Migrations

After deployment, run migrations using Railway CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Run migrations
railway run python mindnotesBackend/manage.py migrate

# Create superuser
railway run python mindnotesBackend/manage.py createsuperuser
```

---

## 🔍 Troubleshooting

### Issue: "SECRET_KEY not set"
**Solution**: Add `SECRET_KEY` to Railway environment variables

### Issue: "ALLOWED_HOSTS"
**Solution**: Already configured for `.railway.app` and `.onrender.com` domains

### Issue: Build fails
**Solution**: Check logs in Railway dashboard. Common issues:
- Missing environment variables
- Python version mismatch
- Requirements.txt issues

### Issue: "Can't connect to database"
**Solution**:
- Verify PostgreSQL service is running
- Check environment variables are set: `PGHOST`, `PGDATABASE`, etc.
- Railway auto-provides `DATABASE_URL` - we parse it in settings

### Issue: Static files not loading
**Solution**:
```bash
railway run python mindnotesBackend/manage.py collectstatic --noinput
```

---

## 📋 Environment Variable Checklist

Before deploying, ensure these are set in Railway:

- [ ] `SECRET_KEY` (generated)
- [ ] `DEBUG=False`
- [ ] `MONGODB_URI` (from MongoDB Atlas)
- [ ] `FRONTEND_URL` (your frontend domain)
- [ ] PostgreSQL variables (auto-provided by Railway)
- [ ] Redis variables (auto-provided by Railway)

---

## 🌐 Your API URLs

After deployment, your API will be available at:

- **Railway URL**: `https://your-service-name.railway.app`
- **API Base**: `https://your-service-name.railway.app/api/v1/`
- **Admin Panel**: `https://your-service-name.railway.app/admin/`

Share the Railway URL with your frontend team!

---

## 💡 Tips

1. **Monitor Usage**: Railway free tier has $5/month credit
2. **Logs**: View real-time logs in Railway dashboard
3. **Auto-Deploy**: Every git push triggers deployment
4. **Rollback**: Use Railway dashboard to rollback to previous deployments
5. **Custom Domain**: Add in Settings → Domains

---

## 🆘 Need Help?

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **View Logs**: Railway Dashboard → Your Service → Deployments → Logs

---

**Your backend is ready for Railway! 🎉**
