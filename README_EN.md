# 🐼 PandaPal — Safe AI Assistant for Schoolchildren

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![React](https://img.shields.io/badge/React-19+-61DAFB.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4.svg)
![AI](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-4285F4.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **Safe Telegram bot powered by Google Gemini AI for adaptive learning of schoolchildren grades 1–11**

[🔗 Try the bot](https://t.me/PandaPalBot) • [🌐 Website](https://pandapal.ru) • [📚 Documentation](https://github.com/gaus-1/pandapal-bot/wiki)

[🇷🇺 Русский](README.md) | [🇺🇸 English](README_EN.md)

</div>

---

## ✨ What PandaPal Can Do

### 🎯 **Core Features**

#### ✅ **AI Learning Assistant**
- Answers questions on all school subjects
- Explains complex topics in simple language
- Solves problems with detailed explanations
- Provides hints instead of ready answers
- Voice message support (OpenAI Whisper)

#### ✅ **Content Safety**
- 5-level moderation system
- Filters forbidden topics (politics, violence, 18+, drugs)
- Contextual message analysis
- Age-appropriate content adaptation
- Image analysis with moderation

#### ✅ **Smart Memory**
- **Complete chat history** (no limits)
- Personalized responses based on history
- API token rotation for stable operation
- Response caching for fast performance

#### ✅ **Homework Help**
- 9 subjects (math, Russian, physics, chemistry, etc.)
- 4 types of assistance (solve, explain, check, hint)
- Specialized prompts for each subject
- Interactive keyboards for easy navigation

#### ✅ **User Profile**
- Age tracking (6-18 years)
- Grade tracking (1-11)
- Response adaptation to student level
- Support for types: child, parent, teacher

#### ✅ **Monitoring & Analytics**
- Message and activity statistics
- Learning progress tracking
- Parental control (basic version)
- Engagement system (automatic reminders)

#### ✅ **Automatic Reminders** 🆕
- Weekly reminders for inactive users
- Age personalization (4 message variants)
- Smart task scheduler (Monday 10:00)
- Anti-spam protection (max 1/week)

#### ✅ **Child Safety** 🆕
- Send location to parents with one button
- Links to 3 maps (Yandex, Google, 2GIS)
- Interactive map in Telegram
- Coordinates NOT saved (GDPR compliant)
- Works only with linked parent

#### ✅ **24/7 Operation** 🆕
- Keep Alive service prevents Render sleep
- Automatic API token rotation
- Stable operation without breaks
- Real-time system monitoring

---

## 🚀 Quick Start

### 📋 **Requirements**
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (for frontend)
- Telegram Bot Token ([get here](https://t.me/BotFather))
- Google Gemini API Key ([get here](https://ai.google.dev/))

### 1️⃣ **Clone**
```bash
git clone https://github.com/gaus-1/pandapal-bot.git
cd pandapal-bot
```

### 2️⃣ **Setup Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3️⃣ **Environment Variables**

Create `.env` in project root:
```env
# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/pandapal

# Telegram
TELEGRAM_BOT_TOKEN=your_token_from_BotFather

# Google Gemini AI (main token)
GEMINI_API_KEY=your_key_from_google

# Additional tokens for rotation (comma-separated)
GEMINI_API_KEYS=key2,key3,key4,key5,key6,key7,key8,key9,key10

# AI Settings
GEMINI_MODEL=gemini-1.5-flash
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=8192
AI_RATE_LIMIT_PER_MINUTE=999999
DAILY_MESSAGE_LIMIT=999999
CHAT_HISTORY_LIMIT=999999

# Security
SECRET_KEY=random_string_minimum_32_characters
CONTENT_FILTER_LEVEL=5
FORBIDDEN_TOPICS=politics,violence,weapons,drugs,extremism,terrorism

# Server settings
WEBHOOK_DOMAIN=pandapal-bot.onrender.com
PORT=10000
KEEP_ALIVE=true
```

### 4️⃣ **Initialize Database**
```bash
# Create tables
alembic upgrade head

# Or direct initialization
python -c "from bot.database import init_db; init_db()"
```

### 5️⃣ **Run**

**Locally (Polling mode):**
```bash
python main.py
```

**Production (Webhook mode):**
```bash
export WEBHOOK_DOMAIN=pandapal-bot.onrender.com
export PORT=10000
python web_server.py
```

**Via Docker Compose:**
```bash
docker-compose up --build
```

---

## 🫧 Example: How PandaPal Works

Here's how PandaPal helps a child with math homework:

```python
# Example dialogue with PandaPal
class PandaPalChat:
    def __init__(self):
        self.ai_service = GeminiAIService()
        self.moderator = ContentModerator()

    async def help_with_math(self, problem: str, user_age: int):
        # Question moderation
        if not self.moderator.is_safe(problem):
            return "I can't help with this question. Let's solve a math problem instead!"

        # Generate age-appropriate response
        response = await self.ai_service.generate_response(
            f"Solve this math problem for {user_age} years old: {problem}",
            user_age=user_age
        )
        return response

# Usage
panda = PandaPalChat()
answer = await panda.help_with_math("2+2=?", 8)
print(answer)  # "2+2=4! Let's check: you have 2 apples and get 2 more..."
```

---

## 🏗️ Architecture

PandaPal consists of three main components:

### 🐍 **Backend (Python)**
- **Telegram Bot API** — message handling
- **Google Gemini AI** — response generation
- **PostgreSQL** — data storage
- **Moderation** — 5-level safety system

### ⚛️ **Frontend (React)**
- **Landing Page** — information website
- **PWA** — mobile application
- **Responsive Design** — adaptation for all devices

### 🎮 **PandaPal Go (In Development)**
- **3D Game Engine** — Three.js + React
- **Panda Companion** — virtual friend
- **Educational Quests** — AI-generated tasks

---

## 🚀 Deployment

### **Render.com (Production - Webhook)**

**1. Create PostgreSQL Database:**
- Copy External Database URL

**2. Create Web Service:**
- Repository: `https://github.com/gaus-1/pandapal-bot`
- Branch: `main`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python web_server.py`

**3. Environment Variables:**
```
DATABASE_URL=postgresql://... (from step 1)
TELEGRAM_BOT_TOKEN=your_token
GEMINI_API_KEY=your_main_key
GEMINI_API_KEYS=key2,key3,key4,key5,key6,key7,key8,key9,key10
GEMINI_MODEL=gemini-1.5-flash
WEBHOOK_DOMAIN=pandapal-bot.onrender.com
PORT=10000
KEEP_ALIVE=true
```

**4. Deploy:**
- Render automatically deploys on push to main
- Webhook will be set automatically
- Bot will work in 2-3 minutes

---

## 🧪 Testing

### **Backend Tests**
```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=bot --cov-report=html

# Only unit tests
pytest tests/unit/ -v
```

**Current coverage:** 35.23% (152 tests, all real)

### **Frontend Tests**
```bash
cd frontend

# All tests
npm test

# Responsiveness
npm test -- src/test/responsive.test.tsx

# Coverage
npm run test:coverage
```

**Frontend coverage:** 13/13 responsiveness tests ✅

---

## 🔒 Security

### **Content Moderation (5 Levels)**

1. **Level 1:** Simple forbidden words (50+ patterns)
2. **Level 2:** Regex for SQL Injection, XSS
3. **Level 3:** Contextual analysis (advanced moderation)
4. **Level 4:** Gemini Safety Settings (BLOCK_MEDIUM_AND_ABOVE)
5. **Level 5:** Post-moderation of AI responses

### **Data Protection**
- ✅ No passwords stored (Telegram authorization)
- ✅ All secrets in `.env` (not in code)
- ✅ PostgreSQL with encryption
- ✅ HTTPS for all requests
- ✅ CSP headers on frontend

### **Parental Control**
- Child activity monitoring
- Logging all interactions
- Suspicious activity warnings (in development)

---

## 🛠️ Technology Stack

### **Backend**
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Main language |
| aiogram | 3.15.0 | Telegram Bot API |
| Google Gemini AI | 1.5 Flash | Language Model |
| OpenAI Whisper | latest | Speech recognition |
| SQLAlchemy | 2.0.36 | ORM for PostgreSQL |
| Alembic | 1.13.2 | Database migrations |
| Pydantic | 2.9.2 | Validation and settings |
| Loguru | 0.7.3 | Logging |
| aiohttp | 3.10.11 | Async HTTP server |
| Sentry | 2.18.0 | Error monitoring |

### **Frontend**
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 19.1.1 | UI library |
| TypeScript | 5.6+ | Typing |
| Vite | 6.0+ | Bundler |
| Tailwind CSS | 3.4+ | Styling |
| Vitest | 2.1.9 | Testing |

### **DevOps & Infrastructure**
- **Render.com** — Hosting (Web Service + PostgreSQL)
- **GitHub Actions** — CI/CD Pipeline
- **Docker** — Containerization
- **PostgreSQL 14+** — Database
- **Nginx** — Web server for frontend

---

## 📊 Project Statistics

### **Codebase**
- **Python:** ~4,500+ lines
- **TypeScript/React:** ~1,500 lines
- **Tests:** 152 real tests (no mocks) - all passed ✅
- **Handlers:** 10 routers
- **Services:** 15 services
- **Models:** 10 database tables

### **Functionality**
- ✅ **Working:** 85% (AI, moderation, voice, reminders, location, 24/7)
- 🚧 **In Development:** 10% (gamification, teachers)
- 📋 **Planned:** 5% (extended analytics)

---

## 🗺️ Roadmap 2025

### **Q1 2025 (October-December)**
- [x] ✅ Basic AI chat with Gemini 1.5 Flash
- [x] ✅ Content moderation (5 levels)
- [x] ✅ User profiles
- [x] ✅ Complete message history
- [x] ✅ Homework help (9 subjects)
- [x] ✅ Webhook for production (stable 24/7)
- [x] ✅ Professional project structure
- [x] ✅ Voice messages (OpenAI Whisper)
- [x] ✅ Automatic user reminders
- [x] ✅ Task scheduler (weekly campaigns)
- [x] ✅ Improved navigation (all buttons work)
- [x] ✅ Location sending to parents (child safety)
- [x] ✅ API token rotation for stable operation
- [x] ✅ Keep Alive service for 24/7 operation
- [x] ✅ 152 real tests (100% passing)
- [ ] 🚧 Achievement system (UI ready, logic in development)
- [ ] 🚧 Parental control UI
- [ ] 📋 Teacher functionality

### **Q2 2025 (January-March) - Planned**
- [ ] Complete gamification system
- [ ] Assignment generation and checking (AI)
- [ ] Educational quizzes
- [ ] Learning time control
- [ ] Email reports for parents
- [ ] Mobile application (PWA)

### **Q3 2025 (April-June) - Planned**
- [ ] Integration with electronic diaries
- [ ] API for third-party services
- [ ] Extended analytics (ML)
- [ ] Voice assistant (Speech-to-Text)
- [ ] Group class support

---

## ✅ Status

PandaPal launched in October 2025 as a safe AI assistant for children.

🎮 **In Development:** PandaPal Go — 3D educational game with panda companion

🚀 PandaPal has new features every week! Make sure to ⭐ star and 👀 watch this repository to stay updated.

---

## 🤝 Contributing

We welcome community contributions! Read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### **How to Help:**
1. 🐛 Report a bug ([Issues](https://github.com/gaus-1/pandapal-bot/issues))
2. 💡 Suggest a new feature
3. 🔧 Fix a bug (Pull Request)
4. 📝 Improve documentation
5. ⭐ Star the project

### **Development Process:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License © 2025 PandaPal Team

You are free to use, modify and distribute this project.

---

## 🌟 Support the Project

If PandaPal helped your child — give ⭐ to the project!

### **Contact**
- 📧 Email: v81158847@gmail.com
- 🐛 Issues: [github.com/gaus-1/pandapal-bot/issues](https://github.com/gaus-1/pandapal-bot/issues)
- 💬 Telegram: [@PandaPalBot](https://t.me/PandaPalBot)

---

<div align="center">

![GitHub last commit](https://img.shields.io/github/last-commit/gaus-1/pandapal-bot)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/gaus-1/pandapal-bot)
![GitHub repo size](https://img.shields.io/github/repo-size/gaus-1/pandapal-bot)

**Status:** 🟢 Active Development
**Version:** 1.0.0-beta
**Last Update:** October 2025

---

<p align="center">
  <b>Made with ❤️ and 🐼 for safe children's learning</b><br>
  <i>PandaPal — learning can be interesting and safe!</i>
</p>

</div>
