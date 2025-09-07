# 💰 Enhanced Expense & Budget Bot

A comprehensive Telegram bot for tracking expenses, managing budgets, and building financial habits through gamification. Built with Django and pyTelegramBotAPI.

## 🚀 Features

### 💱 Multi-Currency Support
- Support for 10+ major currencies (USD, EUR, GBP, ETB, JPY, CAD, AUD, CHF, CNY, INR)
- Real-time exchange rate conversion using forex-python
- Automatic currency caching for improved performance
- Set your preferred default currency

### 🔥 Streak System & Rewards
- Daily streak tracking based on expense/income logging
- Earn money rewards for maintaining streaks
- Increasing multipliers for longer streaks (up to 5x for 35+ day streaks)
- Track total earnings from streak rewards

### 📊 Comprehensive Reports
- **Daily, Weekly, Monthly, and Yearly reports**
- Visual pie charts showing expense breakdown by category
- Income vs expenses analysis
- Net worth tracking over time
- Category-based spending insights

### 📁 Smart Categorization
- 11 pre-defined expense categories with emojis:
  - 🍔 Food & Dining
  - 🚗 Transportation
  - 🏠 Housing
  - 🛒 Shopping
  - 💊 Healthcare
  - 🎬 Entertainment
  - 📚 Education
  - ⚡ Utilities
  - 👕 Clothing
  - ✈️ Travel
  - 💳 Other

### 💰 Financial Tracking
- Track expenses and income
- Manage debts and loans
- Budget monitoring (ready for future enhancements)
- Multi-currency transaction support

### ⚙️ Enhanced User Experience
- Intuitive keyboard navigation
- Rich text formatting with emojis
- Comprehensive error handling
- Settings panel for customization
- Backward compatibility with existing commands

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Telegram Bot Token

### 1. Clone the Repository
```bash
git clone <repository-url>
cd expense-budget-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the project root with the following variables:

```env
SECRET_KEY=your_django_secret_key
BOT_TOKEN=your_telegram_bot_token
PGDATABASE=your_database_name
PGUSER=your_database_user
PGPASSWORD=your_database_password
PGHOST=your_database_host
WEB_HOOK_URL=your_webhook_url
```

### 4. Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Initialize default categories
python setup_enhanced_bot.py
```

### 5. Run the Bot
```bash
# Development
python manage.py runserver

# Production (with webhook)
python manage.py set_webhook
```

## 📱 Usage

### Getting Started
1. Start a conversation with your bot on Telegram
2. Send `/start` to begin
3. Share your contact when prompted
4. Start tracking your finances!

### Main Commands

#### 📊 Reports
- **Daily Report**: View today's financial summary
- **Weekly Report**: 7-day financial overview
- **Monthly Report**: 30-day comprehensive analysis
- **Yearly Report**: Annual financial review

#### 🔥 Streaks
- View your current streak count
- Check available rewards
- Claim streak rewards
- Track total earnings from streaks

#### ⚙️ Settings
- Change default currency
- Configure timezone
- Update personal information

#### 📁 Categories
- View all available expense categories
- See category descriptions and emojis

### Legacy Commands (Still Supported)
- `/start` - Start the bot
- `/spends` - Show spending analysis (last 30 days)
- `/earnings` - Show income analysis (last 30 days)
- `/debts` - Show debt summary
- `/owes` - Show money owed to you

## 🏗️ Architecture

### Models
- **User**: Enhanced with currency, timezone, and streak tracking
- **Expense**: Proper expense tracking with categories and currency
- **Income**: Income tracking with currency support
- **Owe**: Debt/loan management with currency support
- **Streak**: Streak tracking and reward management
- **CurrencyRate**: Exchange rate caching
- **ExpenseCategory**: Pre-defined expense categories
- **Budget**: Budget tracking (ready for future use)

### Key Components
- **bot/bot.py**: Main bot logic and handlers
- **bot/models.py**: Database models
- **bot/utils.py**: Utility functions for currency, streaks, etc.
- **bot/diagrams.py**: Chart generation for reports
- **core/settings.py**: Django configuration

## 🔧 Development

### Project Structure
```
expense-budget-bot/
├── bot/
│   ├── models.py          # Database models
│   ├── bot.py            # Main bot logic
│   ├── utils.py          # Utility functions
│   ├── diagrams.py       # Chart generation
│   └── management/
│       └── commands/     # Django management commands
├── core/
│   ├── settings.py       # Django settings
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI application
├── requirements.txt      # Python dependencies
├── setup_enhanced_bot.py # Setup script
└── ENHANCED_FEATURES.md  # Detailed feature documentation
```

### Adding New Features
1. Create new models in `bot/models.py`
2. Add handlers in `bot/bot.py`
3. Create utility functions in `bot/utils.py`
4. Update migrations: `python manage.py makemigrations`
5. Apply migrations: `python manage.py migrate`

### Testing
```bash
# Run Django tests
python manage.py test

# Test bot functionality
python manage.py run_bot
```

## 🚀 Deployment

### Vercel Deployment
The project is configured for Vercel deployment with:
- `vercel.json`: Vercel configuration
- PostgreSQL database support
- Webhook integration for Telegram

### Environment Variables for Production
```env
SECRET_KEY=your_production_secret_key
BOT_TOKEN=your_production_bot_token
PGDATABASE=your_production_database
PGUSER=your_production_user
PGPASSWORD=your_production_password
PGHOST=your_production_host
WEB_HOOK_URL=https://your-app.vercel.app/webhook/
```

## 📊 API Reference

### Bot Commands
| Command | Description | Parameters |
|---------|-------------|------------|
| `/start` | Initialize bot | None |
| `/spends` | Show spending analysis | None |
| `/earnings` | Show income analysis | None |
| `/debts` | Show debt summary | None |
| `/owes` | Show money owed | None |

### Callback Queries
| Callback | Description | Data Format |
|----------|-------------|-------------|
| `report_*` | Generate report | `report_daily/weekly/monthly/yearly` |
| `claim_reward` | Claim streak reward | None |
| `change_currency` | Change default currency | None |
| `currency_*` | Select currency | `currency_USD/EUR/etc` |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check the `ENHANCED_FEATURES.md` for detailed documentation
2. Review the error messages in the bot
3. Check your environment variables
4. Ensure all dependencies are installed

## 🔮 Future Enhancements

- Budget setting and tracking
- Investment tracking
- Bill reminders and notifications
- Financial goals and targets
- Export to CSV/PDF
- Multi-language support
- Advanced analytics and insights
- Integration with banking APIs

## 📈 Changelog

### v2.0.0 - Enhanced Features
- ✅ Multi-currency support with real-time exchange rates
- ✅ Streak system with monetary rewards
- ✅ Comprehensive reporting (daily, weekly, monthly, yearly)
- ✅ Enhanced expense categorization
- ✅ Improved user interface and experience
- ✅ Better error handling and validation
- ✅ Modular code structure for scalability

### v1.0.0 - Initial Release
- Basic expense and income tracking
- Simple debt management
- Basic reporting with pie charts
- User authentication via contact sharing

---

**Built with ❤️ using Django, pyTelegramBotAPI, and modern web technologies**