# BolsaV2 - Complete Project

## ✅ What's Included

### Backend (Python/FastAPI)
- FastAPI application with async support
- SQLAlchemy models (Users, Assets, Quotes, Portfolios, Operations, Results)
- Alembic migrations
- Authentication with sessions
- Argon2 password hashing
- Docker containerization

### Frontend (React/TypeScript)
- React 18 with TypeScript
- Vite build tool
- Tailwind CSS
- Zustand state management
- Login and Dashboard pages
- Docker + Nginx

### DevOps
- Docker Compose orchestration
- GitHub Actions CI/CD
- Installation script
- Makefile commands

## 🚀 Quick Start

```bash
chmod +x install.sh
./install.sh
```

Then access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📝 Default Login

Username: admin (or what you entered)
Password: admin123 (or what you entered)

## 🔧 Commands

```bash
make build   # Build images
make up      # Start services
make down    # Stop services
make logs    # View logs
```

## 📦 What to Add

This is a minimal working version. For full features, you can add:
- More API endpoints (portfolios, operations, quotes)
- Additional frontend pages
- Handsontable integration
- Recharts for analytics
- Import/export functionality
- More comprehensive tests

## 🔐 Security Notes

- Change SECRET_KEY in production
- Use strong passwords
- Enable HTTPS in production
- Update Finnhub API key

## 📄 License

MIT License
