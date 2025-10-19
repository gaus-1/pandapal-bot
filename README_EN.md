<div align="center">
  <img src="https://raw.githubusercontent.com/gaus-1/pandapal-bot/main/frontend/public/logo.png" alt="PandaPal Logo" width="200"/>

  # 🐼 PandaPal Bot

  **Safe AI Friend for Kids**

  Telegram bot with artificial intelligence, created specifically for educational purposes for children in grades 1-9.

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/PandaPalBot)
  [![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://reactjs.org/)
</div>

## 🎯 About the Project

PandaPal is a smart assistant for children that:
- 🤖 Answers questions using Google Gemini AI
- 🛡️ Filters content for child safety
- 📚 Provides educational materials
- 👨‍👩‍👧‍👦 Allows parents to control activity
- 🎮 Motivates through interactive tasks

## ✨ Key Features

### For Children:
- 💬 **Smart Answers** - AI understands children's questions and answers clearly
- 📖 **Educational Content** - materials for school subjects
- 🏆 **Achievement System** - motivation through progress and rewards
- 🎨 **Interactive Tasks** - interesting exercises and puzzles

### For Parents:
- 👀 **Parental Control** - view child's activity
- ⚙️ **Safety Settings** - flexible filter configuration
- 📊 **Progress Analytics** - reports on successes and interests
- ⏰ **Time Control** - usage restrictions

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Environment Setup
Create `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Fill in required variables:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost/pandapal
SECRET_KEY=your_secret_key_here
```

### 4. Database Setup
```bash
# Apply migrations
alembic upgrade head
```

### 5. Start Bot
```bash
python -m bot.main
```

## 🌐 Web Interface

The project includes a modern website on React + TypeScript:

### Start frontend:
```bash
cd frontend
npm install
npm run dev
```

Website will be available at: `http://localhost:5173`

## 🏗️ Architecture

### Backend (Python)
- **aiogram 3.x** - Telegram Bot API
- **Google Gemini AI** - natural language processing
- **SQLAlchemy** - ORM for database work
- **PostgreSQL** - main database
- **Redis** - caching and sessions
- **Alembic** - database migrations

### Frontend (React + TypeScript)
- **React 18** - user interface
- **TypeScript** - typed JavaScript
- **Tailwind CSS** - styling
- **Vite** - build and development

### Security
- 🔒 **OWASP Top 10** - security standards compliance
- 🛡️ **Content Filtering** - AI message moderation
- 🔐 **Data Encryption** - personal information protection
- 📝 **Audit Logging** - action tracking

## 📁 Project Structure

```
PandaPal/
├── bot/                    # Backend Python
│   ├── handlers/           # Command handlers
│   ├── services/           # Business logic
│   ├── security/           # Security modules
│   ├── database/           # Database models
│   └── monitoring/         # Monitoring and metrics
├── frontend/               # Frontend React
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Pages
│   │   └── config/         # Configuration
├── tests/                  # Tests
├── docs/                   # Documentation
├── scripts/                # Helper scripts
└── alembic/               # Database migrations
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Tests with coverage
pytest --cov=bot

# Load testing
python scripts/load_testing.py --users 20 --duration 60
```

## 📊 Monitoring

- **Prometheus metrics** - `/metrics` endpoint
- **OpenAPI documentation** - `/api-docs`
- **Logging** - structured logs
- **Performance** - response time monitoring

## 🔧 Development

### Pre-commit hooks
```bash
pre-commit install
```

### Code formatting
```bash
# Python
black bot/
isort bot/

# TypeScript
npm run format
```

### Linters
```bash
# Python
flake8 bot/
pylint bot/

# TypeScript
npm run lint
```

## 📚 Documentation

- [Analytics Setup](docs/SETUP/ANALYTICS_SETUP.md)
- [Security](docs/SECURITY/SECURITY_GUIDE.md)
- [API Documentation](docs/api/openapi.yaml)
- [Testing](docs/TESTING/TESTING.md)

## 🤝 Contributing

1. Fork the repository
2. Create a branch for new feature
3. Make changes
4. Add tests
5. Create Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🆘 Support

- 📧 Email: support@pandapal.ru
- 💬 Telegram: [@PandaPalBot](https://t.me/PandaPalBot)
- 🐛 Issues: [GitHub Issues](https://github.com/gaus-1/pandapal-bot/issues)

---

**Made with ❤️ for children and their parents**
