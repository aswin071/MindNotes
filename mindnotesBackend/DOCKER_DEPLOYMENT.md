# 🐳 Docker Deployment Guide - MindNotes Backend

This guide covers deploying your Dockerized Django backend both **locally** and on **Railway**.

---

## 📦 What's Included

Your Docker setup includes:
- **Django Backend** (Gunicorn)
- **PostgreSQL** Database
- **MongoDB** Database
- **Redis** Cache
- **Celery Worker** (Background tasks)
- **Celery Beat** (Periodic tasks)

---

## 🚀 Quick Start - Local Development

### Prerequisites
- Docker installed (https://docs.docker.com/get-docker/)
- Docker Compose installed

### 1. Clone and Setup

```bash
cd mindnotesBackend
cp .env.example .env
# Edit .env file with your settings
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 3. Run Migrations

```bash
# Run Django migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 4. Access Your Application

- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **PostgreSQL**: localhost:5432
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

---

## 🛠️ Common Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery_worker
```

### Stop Services
```bash
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v
```

### Restart Services
```bash
docker-compose restart

# Restart specific service
docker-compose restart web
```

### Execute Commands
```bash
# Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Collect static files
docker-compose exec web python manage.py collectstatic
```

### View Running Containers
```bash
docker-compose ps
```

---

## 🌐 Deploy to Railway with Docker

Railway automatically detects and uses your Dockerfile!

### Step 1: Prepare for Railway

Make sure these files exist:
- ✅ `Dockerfile` (already created)
- ✅ `.dockerignore` (already created)
- ✅ `requirements.txt` (already exists)

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Add Docker support"
git push origin main
```

### Step 3: Create Railway Project

1. Go to **https://railway.app**
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your **MindNotes** repository
5. Railway will **automatically detect your Dockerfile**

### Step 4: Add Services on Railway

#### A. Add PostgreSQL
- Click **"+ New"** → **"Database"** → **"PostgreSQL"**
- Railway auto-generates `DATABASE_URL`

#### B. Add Redis
- Click **"+ New"** → **"Database"** → **"Redis"**
- Railway auto-generates `REDIS_URL`

#### C. Add MongoDB
Use **MongoDB Atlas** (free tier):
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster (512MB)
3. Get connection string
4. Add to Railway environment variables

### Step 5: Configure Environment Variables

In Railway Dashboard → Your Service → **Variables**:

```env
# Required
SECRET_KEY=your-secret-key-here
DEBUG=False
RAILWAY_ENVIRONMENT=production
PORT=8000

# PostgreSQL (Railway auto-provides DATABASE_URL)
POSTGRES_DATABASE=${PGDATABASE}
POSTGRES_HOST=${PGHOST}
POSTGRES_PORT=${PGPORT}
POSTGRES_USER=${PGUSER}
POSTGRES_PASSWORD=${PGPASSWORD}

# MongoDB (from Atlas)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/mindnotes
MONGODB_DB_NAME=mindnotes
MONGODB_HOST=cluster.mongodb.net
MONGODB_PORT=27017
MONGODB_USER=your_user
MONGODB_PASSWORD=your_password

# Redis (Railway auto-provides REDIS_URL)
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# CORS
FRONTEND_URL=https://your-frontend.vercel.app
CORS_ALLOW_ALL=False

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
```

**Note:** Railway automatically provides:
- `DATABASE_URL` for PostgreSQL
- `REDIS_URL` for Redis
- You can reference them with `${DATABASE_URL}` syntax

### Step 6: Deploy

Railway automatically deploys! Monitor the build in the dashboard.

### Step 7: Run Migrations (Railway CLI)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser
```

---

## 🔧 Railway Docker Configuration

### Update Dockerfile for Railway (Optional)

If you need to bind to Railway's dynamic PORT:

```dockerfile
# At the end of Dockerfile, replace CMD with:
CMD gunicorn mindnotesBackend.wsgi:application --bind 0.0.0.0:$PORT --workers 3
```

Our Dockerfile already handles this correctly!

### Add Celery Worker Service (Optional)

To run Celery on Railway:

1. **Duplicate your service**
2. Name it **"celery-worker"**
3. Override the **Start Command** in Settings:
   ```
   celery -A mindnotesBackend worker --loglevel=info
   ```
4. Add same environment variables

---

## 📊 Monitoring & Debugging

### Check Service Health
```bash
# Local
docker-compose ps

# Railway
railway status
```

### View Logs
```bash
# Local
docker-compose logs -f web

# Railway
railway logs
```

### Database Access
```bash
# Local PostgreSQL
docker-compose exec postgres psql -U postgres -d mindnotes

# Local MongoDB
docker-compose exec mongodb mongosh -u admin -p admin123

# Railway
railway run python manage.py dbshell
```

---

## 🔒 Production Best Practices

### 1. Security
- ✅ Use strong `SECRET_KEY`
- ✅ Set `DEBUG=False` in production
- ✅ Don't commit `.env` file
- ✅ Use environment variables for all secrets

### 2. Static Files
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 3. Database Backups

**Local:**
```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U postgres mindnotes > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres mindnotes < backup.sql

# MongoDB backup
docker-compose exec mongodb mongodump --out /tmp/backup
```

**Railway:**
```bash
# Export data
railway run python manage.py dumpdata > backup.json

# Import data
railway run python manage.py loaddata backup.json
```

---

## 🐛 Troubleshooting

### Issue: "Port already in use"
```bash
# Stop conflicting services
docker-compose down
# Or change ports in docker-compose.yml
```

### Issue: "Database connection refused"
```bash
# Wait for database to be ready
docker-compose up -d postgres mongodb redis
sleep 10
docker-compose up web
```

### Issue: "Static files not loading"
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Issue: Railway build fails
1. Check build logs in Railway dashboard
2. Verify `Dockerfile` syntax
3. Ensure all dependencies in `requirements.txt`
4. Check environment variables are set

### Issue: "No module named 'mindnotesBackend'"
```bash
# Ensure WORKDIR is correct in Dockerfile
# Should be: WORKDIR /app
```

---

## 📈 Scaling on Railway

Railway makes scaling easy:

1. **Vertical Scaling**: Increase RAM/CPU in service settings
2. **Horizontal Scaling**: Add more instances (paid plans)
3. **Auto-scaling**: Available in Railway Pro

---

## 💰 Cost Management

### Free Tier Limits
- **Railway**: $5 credit/month
- **MongoDB Atlas**: 512MB free forever
- **Total**: Enough for development

### Monitor Usage
- Railway Dashboard → Your project → **Metrics**
- Check daily/monthly usage
- Set up usage alerts

---

## 🔄 CI/CD Pipeline

Railway auto-deploys on git push:

```bash
# Make changes
git add .
git commit -m "Update backend"
git push origin main

# Railway automatically:
# 1. Detects changes
# 2. Builds Docker image
# 3. Deploys new version
# 4. Zero-downtime deployment
```

---

## 📚 Additional Resources

- **Docker Docs**: https://docs.docker.com
- **Railway Docs**: https://docs.railway.app
- **Django Production**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Gunicorn**: https://docs.gunicorn.org

---

## 🎯 Next Steps

1. ✅ Test locally with Docker Compose
2. ✅ Push to GitHub
3. ✅ Deploy to Railway
4. ✅ Configure environment variables
5. ✅ Run migrations
6. ✅ Share API URL with frontend team
7. ✅ Monitor and optimize

---

## 🆘 Need Help?

- **Railway Discord**: https://discord.gg/railway
- **Railway Support**: https://railway.app/help
- **GitHub Issues**: Create issue in your repo

---

**Your Dockerized backend is production-ready! 🎉**
