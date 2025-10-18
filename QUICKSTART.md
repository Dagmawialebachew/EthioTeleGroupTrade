# Quick Start Guide

Get your Ethio Tele Trade Bot running in 5 minutes!

## 1. Get Your Bot Token

1. Open Telegram
2. Search for [@BotFather](https://t.me/BotFather)
3. Send `/newbot`
4. Follow instructions to create bot
5. Copy the bot token (looks like: `123456:ABC-DEF1234...`)

## 2. Get Your Admin ID

1. Open Telegram
2. Search for [@userinfobot](https://t.me/userinfobot)
3. Start the bot
4. Copy your user ID (looks like: `123456789`)

## 3. Create Your Channel

1. Create a new Telegram channel (e.g., @TeleTradeET)
2. Make it public
3. Copy the username (e.g., @TeleTradeET)

## 4. Setup Locally

```bash
# Clone and navigate to project
cd ethio-tele-trade-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

## 5. Configure .env

Edit `.env` file:

```env
BOT_TOKEN=your-bot-token-here
ADMIN_ID=your-user-id-here
CHANNEL_ID=@YourChannel
DATABASE_URL=sqlite:///data.db
LOG_CHANNEL_ID=your-user-id-here
BASE_URL=https://yourservice.onrender.com
WEBHOOK_PATH=/webhook
```

## 6. Run Locally

```bash
python bot.py --polling
```

Bot is now running! Open Telegram and test it.

## 7. Deploy to Render (Production)

1. Push code to GitHub
2. Go to [Render](https://render.com)
3. Create new Web Service
4. Connect GitHub repo
5. Set environment variables (same as .env)
6. Set `BASE_URL` to your Render service URL
7. Deploy!

## 8. Set Webhook

After deployment:

```bash
python scripts/set_webhook.py
```

## Done!

Your bot is live! Test by sending `/start` to your bot.

## Troubleshooting

**Bot not responding?**
- Check bot token is correct
- Verify Render service is running
- Check webhook is set: `python scripts/set_webhook.py`

**Admin commands not working?**
- Verify ADMIN_ID matches your Telegram user ID
- Check case-sensitive commands

**Users can't verify channel join?**
- Make channel public
- Add bot as admin to channel
- Check CHANNEL_ID format: @YourChannel

## Need Help?

Check the full [README.md](README.md) for detailed documentation.
