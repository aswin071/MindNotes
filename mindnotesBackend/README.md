# 🧠 MindNotes Backend API

Django REST API for MindNotes - A mental wellness and productivity application.

---

## 🚀 Quick Start

### Local Development with Docker

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd mindnotesBackend

# 2. Create environment file
cp .env.example .env

# 3. Start all services
docker-compose up --build

# 4. Run migrations
docker-compose exec web python manage.py migrate

# 5. Create superuser
docker-compose exec web python manage.py createsuperuser
```

**Access the API**: http://localhost:8000

---

## 📁 Project Structure

```
mindnotesBackend/
├── api/                    # API versioning
│   └── v1/                # Version 1 endpoints
├── authentication/         # User auth & JWT
├── journals/              # Journal entries
├── focus/                 # Focus sessions
├── prompts/               # AI prompts
├── analytics/             # User analytics
├── moods/                 # Mood tracking
├── subscriptions/         # Subscription management
├── exports/               # Data export
├── core/                  # Core utilities
├── mindnotesBackend/      # Project settings
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Local dev setup
└── requirements.txt       # Python dependencies
```

---

## 🛠️ Tech Stack

- **Framework**: Django 3.2.25 + Django REST Framework
- **Databases**:
  - PostgreSQL (relational data)
  - MongoDB (documents/logs)
- **Cache**: Redis
- **Task Queue**: Celery + Celery Beat
- **Authentication**: JWT (Simple JWT)
- **Server**: Gunicorn
- **Storage**: AWS S3 / Google Cloud Storage (optional)

---

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/token/refresh/` - Refresh JWT token

### Journals
- `GET /api/v1/journals/` - List journals
- `POST /api/v1/journals/` - Create journal
- `GET /api/v1/journals/{id}/` - Get journal
- `PUT /api/v1/journals/{id}/` - Update journal
- `DELETE /api/v1/journals/{id}/` - Delete journal

### Focus Sessions
- `GET /api/v1/focus/` - List focus sessions
- `POST /api/v1/focus/` - Create session
- `GET /api/v1/focus/{id}/` - Get session details

### More endpoints...
See full API documentation at `/api/docs/` (when running)

---

## 🐳 Deployment

### Option 1: Deploy to Railway (Recommended)

**Railway automatically detects and deploys your Dockerfile!**

```bash
# 1. Push to GitHub
git push origin main

# 2. Go to Railway.app
# 3. Create new project from GitHub repo
# 4. Add PostgreSQL and Redis databases
# 5. Set environment variables
# 6. Railway auto-deploys!
```

📖 **Full guide**: See [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)

### Option 2: Local Docker

```bash
docker-compose up -d
```

---

## 🔧 Environment Variables

Required environment variables (see [.env.example](./.env.example)):

```env
SECRET_KEY=your-secret-key
DEBUG=False
POSTGRES_DATABASE=mindnotes
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
MONGODB_URI=mongodb://...
REDIS_URL=redis://...
```

---

## 📦 Services

The Docker setup includes:

| Service | Port | Description |
|---------|------|-------------|
| **web** | 8000 | Django API (Gunicorn) |
| **postgres** | 5432 | PostgreSQL database |
| **mongodb** | 27017 | MongoDB database |
| **redis** | 6379 | Redis cache |
| **celery_worker** | - | Background tasks |
| **celery_beat** | - | Periodic tasks |

---

## 🧪 Testing

```bash
# Run tests
docker-compose exec web python manage.py test

# Run with coverage
docker-compose exec web coverage run --source='.' manage.py test
docker-compose exec web coverage report
```

---

## 📊 Database Management

### Migrations
```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

### Backup & Restore
```bash
# Backup
docker-compose exec web python manage.py dumpdata > backup.json

# Restore
docker-compose exec web python manage.py loaddata backup.json
```

---

## 🔐 Security

- ✅ JWT Authentication
- ✅ CORS configured
- ✅ Environment-based configuration
- ✅ Secret key management
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection

---

## 📈 Performance

- **Redis Caching**: Configured for sessions and query results
- **Connection Pooling**: PostgreSQL and MongoDB
- **Celery**: Async tasks for heavy operations
- **Static Files**: WhiteNoise for efficient serving

---

## 🐛 Troubleshooting

### Service won't start
```bash
docker-compose down -v
docker-compose up --build
```

### Database connection error
```bash
# Check if databases are running
docker-compose ps

# View logs
docker-compose logs postgres
docker-compose logs mongodb
```

### Port already in use
```bash
# Change ports in docker-compose.yml
# Or stop conflicting services
```

---

## 📚 Documentation

- **[DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)** - Detailed Docker & Railway deployment guide
- **[.env.example](./.env.example)** - Environment variables template
- **[requirements.txt](./requirements.txt)** - Python dependencies

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

- **Issues**: Create GitHub issue
- **Email**: your-email@example.com
- **Documentation**: See docs folder

---

## 📄 License

This project is licensed under the MIT License.

---

## 🎯 Roadmap

- [ ] API documentation (Swagger/OpenAPI)
- [ ] WebSocket support for real-time features
- [ ] GraphQL endpoint
- [ ] Rate limiting enhancements
- [ ] Monitoring and logging (Sentry)
- [ ] AWS deployment scripts

---

**Built with ❤️ for mental wellness and productivity**
