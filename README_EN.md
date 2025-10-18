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
- 🎮 **PandaPal Go** - educational Breakout/Arkanoid game with math problems
- 🛡️ **24/7 AI Moderation** - protection from inappropriate language and dangerous content
- 📊 **Parental Control** - dashboard with progress analytics
- 🖼️ **Vision API** - analysis of homework photos
- 📚 **Web Scraping** - current materials from educational sites
- 🎯 **Personalization** - adaptation to age (6-18 years) and level
- 🌐 **Modern Web Interface** - responsive design for all devices
- 🔒 **OWASP Top 10 Security** - comprehensive security protection

---

## 🚀 Technology Stack

### Frontend (Website)
- **React 19** + **TypeScript** - modern UI
- **Tailwind CSS** - responsive styles
- **Zustand** - state management
- **Vite** - fast build
- **Web Vitals** - performance monitoring
- **Canvas API** - 2D PandaPal Go game
- **Mobile-First Design** - mobile device optimization

### Backend (Telegram Bot)
- **Python 3.11+** - main language
- **aiogram 3.x** - modern Telegram Bot API library
- **SQLAlchemy 2.0** - ORM for database work
- **Alembic** - database migrations
- **Google Gemini 1.5 Flash** - AI engine
- **Redis** - caching and sessions
- **PostgreSQL** - main database
- **OWASP Security Modules** - cryptography, audit, integrity
- **Fernet Encryption** - sensitive data encryption

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
│   ├── security/               # OWASP security modules
│   │   ├── crypto.py           # Encryption and cryptography
│   │   ├── headers.py          # Security HTTP headers
│   │   ├── integrity.py        # Integrity checks and SSRF
│   │   └── audit_logger.py     # Audit logging
│   ├── models.py              # Database models
│   └── config.py              # Configuration
├── frontend/                   # Website (React)
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/             # Pages
│   │   ├── game/              # PandaPal Go game
│   │   │   ├── core/          # Game engine
│   │   │   ├── entities/      # Game objects
│   │   │   ├── levels/        # Game levels
│   │   │   └── physics/       # Physics and collisions
│   │   └── utils/             # Utilities
│   ├── public/                # Static files
│   └── dist/                  # Build
├── alembic/                   # Database migrations
├── docs/                      # Documentation
├── tests/                     # Tests (188+ tests)
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── security/              # Security tests
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
python -m bot.main
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

### 4. Access to PandaPal Go
After starting the frontend, the game will be available at:
```
http://localhost:5173/play
```

Or on the production website:
```
https://pandapal.ru/play
```

### 5. Environment Variables
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
- **🧪 Testing** - 188+ automated tests
- **🎮 Game Analytics** - PandaPal Go progress tracking
- **🛡️ Security Audit** - logging of all security events

---

## 🛡️ Security

- **🔒 OWASP Top 10 Compliance** - full compliance with security standards
- **🔐 Fernet Encryption** - sensitive data encryption (AES-256 GCM)
- **🛡️ AI Moderation** - automatic content filtering
- **👨‍👩‍👧‍👦 Parental Control** - access settings and monitoring
- **📊 Audit Logging** - masking sensitive data in logs
- **🌐 SSRF Protection** - preventing attacks on internal resources
- **🔒 CSP Headers** - XSS attack protection
- **🛡️ Clickjacking Protection** - preventing embedding in malicious frames
- **✅ Data Integrity** - checksum verification and validation

---

## 🎮 PandaPal Go - Educational Game

**PandaPal Go** is a unique educational game in the Breakout/Arkanoid genre, specially designed for school-age children. The game combines engaging gameplay with mathematical problem solving.

### 🏫 School Locations
- **🏃‍♂️ Gym** - math with sports themes
- **📚 Library** - logic and reading problems
- **🍎 Cafeteria** - math with food and products
- **🎨 Classroom** - general school subjects
- **🌳 Playground** - fun break-time problems

### 🎯 Game Features
- **📱 Mobile optimization** - finger control on phone
- **💻 Desktop support** - mouse control on computer
- **🎵 Sound effects** - pleasant audio feedback
- **🎨 Modern graphics** - clean geometric design
- **📊 Scoring system** - motivation for learning
- **🔄 Progressive difficulty** - adaptation to child's level

### 🎮 Controls
- **Mobile**: Move finger to control paddle
- **Desktop**: Move mouse to control paddle
- **Pause**: Press spacebar or tap screen
- **Start**: Click anywhere on screen

---

## 🎯 Features

### For Children (6-18 years)
- 💬 **Smart Chat** - answers to school curriculum questions
- 🎮 **PandaPal Go** - educational game with math problems
- 📸 **Photo Analysis** - homework help through Vision API
- 🎓 **Adaptive Learning** - personalized explanations
- 🏆 **Achievement System** - motivation for learning
- 🏫 **School Locations** - game in gym, cafeteria, library

### For Parents
- 📊 **Progress Dashboard** - tracking child's success
- ⚙️ **Security Settings** - access and content control
- 📱 **Notifications** - activity reports
- 🔍 **Communication History** - transparency in AI interaction

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
- **Python**: PEP 8, type hints, SOLID principles
- **TypeScript**: ESLint, Prettier
- **Tests**: coverage >80%, 188+ automated tests
- **Security**: OWASP Top 10 compliance
- **Documentation**: update on changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- **📧 Email**: 79516625803@ya.ru
- **💬 Telegram**: [@SavinVE](https://t.me/SavinVE)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/PandaPal/issues)
- **📖 Documentation**: [pandapal.ru/docs](https://pandapal.ru/docs)

---

<div align="center">

**Made with ❤️ for children's education**

[⬆️ Back to top](#-pandapal---ai-assistant-for-childrens-education)

</div>
