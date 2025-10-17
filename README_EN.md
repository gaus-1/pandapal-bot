# 🐼 PandaPal - AI Assistant for Children's Education

<div align="center">

![PandaPal Logo](frontend/public/logo.png)

**Safe and intelligent AI assistant for schoolchildren aged 6-18**

[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-19.1-61dafb)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[🤖 Telegram Bot](https://t.me/PandaPalBot) • [🌐 Website](https://pandapal.ru) • [📚 Documentation](https://pandapal.ru/docs)

**English** | [Русский](README.md)

</div>

---

## 🌟 What is PandaPal?

**PandaPal** is an educational platform with artificial intelligence, created specifically for children and teenagers. We combine modern AI technologies, gamification, and strict security standards to make learning engaging and safe.

### 🎯 Key Features

- 🤖 **AI Assistant based on Google Gemini 1.5 Flash** - answers questions, explains complex topics
- 🛡️ **24/7 AI Moderation** - protection from inappropriate language and dangerous content
- 📊 **Parental Control** - dashboard with progress analytics
- 🖼️ **Vision API** - analysis of homework photos
- 📚 **Web Scraping** - current materials from educational sites
- 🎯 **Personalization** - adaptation to age (6-18 years) and level
- 🌐 **Modern Web Interface** - responsive design for all devices

---

## 🚀 Technology Stack

### Frontend (Website)
- **React 19** + **TypeScript** - modern UI
- **Tailwind CSS** - responsive styles
- **Zustand** - state management
- **Vite** - fast build
- **Web Vitals** - performance monitoring

### Backend (Telegram Bot)
- **Python 3.11+** - main language
- **aiogram 3.x** - modern Telegram Bot API library
- **SQLAlchemy 2.0** - ORM for database work
- **Alembic** - database migrations
- **Google Gemini 1.5 Flash** - AI engine
- **Redis** - caching and sessions
- **PostgreSQL** - main database

### DevOps & Deployment
- **Docker** - containerization
- **Render.com** - hosting
- **GitHub Actions** - CI/CD
- **Nginx** - web server

---

## 🏗️ Project Architecture

```
PandaPal/
├── bot/                        # Telegram Bot (Python)
│   ├── handlers/               # Command handlers
│   ├── services/               # Business logic
│   ├── keyboards/              # Keyboards
│   ├── models.py              # Database models
│   └── config.py              # Configuration
├── frontend/                   # Website (React)
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/             # Pages
│   │   ├── security/          # Security
│   │   └── utils/             # Utilities
│   ├── public/                # Static files
│   └── dist/                  # Build
├── alembic/                   # Database migrations
├── docs/                      # Documentation
├── tests/                     # Tests
└── scripts/                   # Utilities
```

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/PandaPal.git
cd PandaPal
```

### 2. Backend Setup (Telegram Bot)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp env.template .env
# Edit .env file with your tokens

# Apply migrations
alembic upgrade head

# Run bot
python main.py
```

### 3. Frontend Setup (Website)
```bash
cd frontend

# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build
```

### 4. Environment Variables
Create `.env` file in project root:
```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-domain.com/webhook

# Google AI
GOOGLE_API_KEY=your_google_api_key

# Database
DATABASE_URL=postgresql://user:password@localhost/pandapal

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your_secret_key_here
```

---

## 📊 Monitoring and Analytics

- **📈 Usage Analytics** - detailed user statistics
- **🔒 Security** - suspicious activity monitoring
- **⚡ Performance** - Core Web Vitals, response time
- **🧪 Testing** - 139+ automated tests

---

## 🛡️ Security

- **AI Moderation** - automatic content filtering
- **Parental Control** - access settings and monitoring
- **Data Protection** - encryption and secure storage
- **CSP Headers** - XSS attack protection
- **Clickjacking Protection** - preventing embedding in malicious frames

---

## 🎯 Features

### For Children (6-18 years)
- 💬 **Smart Chat** - answers to school curriculum questions
- 📸 **Photo Analysis** - homework help through Vision API
- 🎓 **Adaptive Learning** - personalized explanations
- 🏆 **Achievement System** - motivation for learning

### For Parents
- 📊 **Progress Dashboard** - tracking child's success
- ⚙️ **Security Settings** - access and content control
- 📱 **Notifications** - activity reports
- 🔍 **Communication History** - transparency in AI interaction

### For Teachers
- 📚 **Educational Materials** - current information
- 🎯 **Personalization** - adaptation to different levels
- 📈 **Analytics** - understanding student needs

---

## 🌐 Deployment

### Render.com (Recommended)
1. Connect GitHub repository
2. Configure environment variables
3. Automatic deployment on every push

### Docker
```bash
# Build image
docker build -t pandapal .

# Run container
docker run -p 8000:8000 pandapal
```

---

## 🤝 Contributing

We welcome contributions to PandaPal development!

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Code Standards
- **Python**: PEP 8, type hints
- **TypeScript**: ESLint, Prettier
- **Tests**: coverage >80%
- **Documentation**: update on changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **📧 Email**: support@pandapal.ru
- **💬 Telegram**: [@PandaPalSupport](https://t.me/PandaPalSupport)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/PandaPal/issues)
- **📖 Documentation**: [pandapal.ru/docs](https://pandapal.ru/docs)

---

<div align="center">

**Made with ❤️ for children's education**

[⬆️ Back to top](#-pandapal---ai-assistant-for-childrens-education)

</div>
