# Getting Started with Ethio Tele Trade Bot

Welcome! This guide will get you from zero to a running bot in under 10 minutes.

## What You've Got

A complete, production-ready Telegram bot that buys Telegram groups. Everything is built, tested, and ready to deploy.

## Three Ways to Start

### Option 1: Quick Local Test (5 minutes)

Perfect for: Testing the bot locally before deploying.

```bash
# 1. Install Python 3.11+ (check: python3 --version)

# 2. Clone/download this project
cd ethio-tele-trade-bot

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment template
cp .env.example .env

# 6. Get bot token from @BotFather
# - Open Telegram, search @BotFather
# - Send /newbot and follow instructions
# - Copy your bot token

# 7. Get your admin ID from @userinfobot
# - Open Telegram, search @userinfobot
# - Start chat, copy your ID

# 8. Edit .env file with your values
# Required: BOT_TOKEN, ADMIN_ID, CHANNEL_ID

# 9. Run bot
python bot.py --polling

# 10. Test in Telegram!
# Search for your bot and send /start
```

**Done!** Your bot is running locally.

### Option 2: Deploy to Render (15 minutes)

Perfect for: Production deployment with zero server management.

**Prerequisites:**
- GitHub account
- Render.com account (free)
- Bot token from @BotFather
- Your Telegram admin ID

**Steps:**

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - "New" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - Build: `pip install -r requirements.txt`
     - Start: `python bot.py`

3. **Set Environment Variables** (in Render dashboard)
   ```
   BOT_TOKEN=<from @BotFather>
   ADMIN_ID=<from @userinfobot>
   CHANNEL_ID=@TeleTradeET
   BASE_URL=https://your-service.onrender.com
   DATABASE_URL=sqlite:///data.db
   WEBHOOK_PATH=/webhook
   ```

4. **Set Webhook**
   ```bash
   # After deployment completes
   python3 scripts/set_webhook.py
   ```

5. **Test Your Bot**
   - Open Telegram
   - Search for your bot
   - Send /start

**Done!** Your bot is live on the internet.

### Option 3: Read First, Deploy Later

Perfect for: Understanding what you're deploying.

**Read these in order:**
1. `STRUCTURE.txt` - See what's included (2 min)
2. `QUICKSTART.md` - Rapid deployment guide (3 min)
3. `README.md` - Complete technical documentation (15 min)
4. `DEPLOYMENT.md` - Detailed deployment steps (10 min)

## What Happens Next?

### After Starting the Bot

**For Users:**
1. They send `/start`
2. Select language (English/Amharic)
3. Must join your channel (@TeleTradeET)
4. Can now sell their groups

**For You (Admin):**
1. Users submit groups via `/sell`
2. You receive notifications with screenshots
3. Use `/panel` to review submissions
4. Approve/reject with inline buttons
5. Mark payments as complete

## Key Admin Commands

Once your bot is running, you can:

```
/panel  - View pending submissions (with action buttons)
/stats  - See how many submissions, payments, etc.
/export - Download submissions as CSV
/pause  - Temporarily stop accepting new submissions
```

## Quick Troubleshooting

**Bot not responding?**
- Check BOT_TOKEN is correct
- Verify bot is running (check logs)
- For webhook: check BASE_URL is correct

**Admin commands not working?**
- Verify ADMIN_ID matches your Telegram user ID exactly
- Get your ID from @userinfobot

**"Channel verification failed"?**
- Make sure CHANNEL_ID is correct (with @)
- Channel must be public
- User must actually join the channel

## File Guide

**Start here:**
- `README.md` - Complete documentation
- `QUICKSTART.md` - Fast setup
- `STRUCTURE.txt` - What's in the project

**Deploy with:**
- `.env.example` - Environment variables
- `requirements.txt` - Dependencies
- `render.yaml` - Render config
- `scripts/set_webhook.py` - Webhook setup

**Code structure:**
- `bot.py` - Main entry point
- `handlers/` - All bot commands
- `models/database.py` - Database operations
- `lang/` - English & Amharic translations

## Common First Steps

### 1. Create Your Bot

```bash
# In Telegram:
1. Search @BotFather
2. Send /newbot
3. Name: Ethio Tele Trade Bot
4. Username: YourBotName_bot
5. Copy token
```

### 2. Create Your Channel

```bash
# In Telegram:
1. New Channel
2. Make it public
3. Choose username (e.g., @TeleTradeET)
4. Add your bot as admin
```

### 3. Get Your Admin ID

```bash
# In Telegram:
1. Search @userinfobot
2. Start chat
3. Copy your ID (e.g., 123456789)
```

### 4. Configure Environment

Edit `.env`:
```env
BOT_TOKEN=<paste-token-here>
ADMIN_ID=<paste-id-here>
CHANNEL_ID=@YourChannel
```

### 5. Run

```bash
python bot.py --polling
```

## Understanding the Flow

**User's Journey:**
1. /start → Choose language → Join channel
2. Click "Sell My Group" button
3. Send group link
4. Add bot as admin to their group
5. Bot reads group details automatically
6. Bot calculates and shows price
7. User uploads screenshot proof
8. Waits for admin approval
9. Provides payment details
10. Receives confirmation when paid

**Your Journey (Admin):**
1. Receive notification with group details
2. Click "View Screenshot" to verify
3. Click "Confirm Transfer" if valid
4. User automatically asked for payment info
5. You manually send payment
6. Click "Mark as Paid" in bot
7. User receives confirmation

## Pricing Explained

The bot automatically calculates prices:

- Groups from **2016-2023**: **1000 Birr**
- Groups from **Jan-Apr 2024**: **300 Birr**
- Groups from **May 2024+**: **Not eligible**
- Older/newer: **Manual review**

You can modify this in `utils/price_engine.py`.

## Need Help?

**Quick answers:**
- Check `README.md` for detailed docs
- Check `DEPLOYMENT.md` for deployment issues
- Check `SCREENSHOT_GUIDE.md` to help users

**Common issues:**
- [Deployment issues](#quick-troubleshooting)
- [Bot not responding](#quick-troubleshooting)
- [Admin access issues](#quick-troubleshooting)

## What's Included?

✅ Complete working bot (2,500+ lines of code)
✅ Bilingual (English + Amharic)
✅ Admin dashboard in Telegram
✅ Database with all tables
✅ Security (rate limiting, validation, etc.)
✅ Error handling & logging
✅ Tests for price engine
✅ 7 documentation files
✅ Deployment configs for Render
✅ Helper scripts

## Next Steps

**Just testing?**
→ Follow "Option 1: Quick Local Test" above

**Ready to go live?**
→ Follow "Option 2: Deploy to Render" above

**Want to understand first?**
→ Read `STRUCTURE.txt` then `README.md`

**Need to customize?**
→ Read `PROJECT_SUMMARY.md` for architecture details

## Quick Reference Card

```
📖 Documentation
   README.md          - Main docs (complete guide)
   QUICKSTART.md      - 5-minute setup
   DEPLOYMENT.md      - Deploy to production
   PROJECT_SUMMARY.md - Technical overview
   STRUCTURE.txt      - File structure
   SCREENSHOT_GUIDE.md- User instructions
   CHANGELOG.md       - Version history

🔧 Configuration
   .env.example       - Environment template
   requirements.txt   - Python packages
   render.yaml        - Render config

🤖 Bot Files
   bot.py            - Main entry point
   handlers/         - Command handlers
   models/           - Database layer
   middlewares/      - Request processing
   utils/            - Helper functions
   lang/             - Translations

📝 Scripts
   set_webhook.py    - Set webhook
   unset_webhook.py  - Remove webhook
   get_admin_id.py   - Get admin ID

🧪 Tests
   test_price_engine.py - Price calculation tests
```

## Support

Stuck? Here's where to look:

1. **Bot won't start**: Check .env file, verify BOT_TOKEN
2. **Admin features not working**: Verify ADMIN_ID is exact
3. **Deployment issues**: See DEPLOYMENT.md troubleshooting
4. **User flow questions**: See SCREENSHOT_GUIDE.md
5. **Technical questions**: See README.md or PROJECT_SUMMARY.md

---

## Ready? Let's Go!

**Fastest path** (5 minutes):
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
python bot.py --polling
# Test in Telegram!
```

**Production path** (15 minutes):
1. Push to GitHub
2. Deploy on Render
3. Set environment variables
4. Run `python3 scripts/set_webhook.py`
5. Done!

---

Built with ❤️ for Ethiopian entrepreneurs.

**Version**: 1.0.0 | **Status**: ✅ Production Ready
