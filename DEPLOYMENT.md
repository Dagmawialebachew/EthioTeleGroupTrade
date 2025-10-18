# Deployment Checklist

Complete guide for deploying Ethio Tele Trade Bot to production on Render.

## Pre-Deployment Checklist

### 1. Bot Setup
- [ ] Created bot via @BotFather
- [ ] Saved bot token securely
- [ ] Set bot name: Ethio Tele Trade Bot
- [ ] Set bot username: @EthioTeleTradeBot
- [ ] Set bot description
- [ ] Set bot about text
- [ ] Uploaded bot profile picture (optional)

### 2. Channel Setup
- [ ] Created Telegram channel
- [ ] Made channel public
- [ ] Set channel username (e.g., @TeleTradeET)
- [ ] Added bot as admin to channel
- [ ] Posted welcome message

### 3. Admin Setup
- [ ] Got admin user ID from @userinfobot
- [ ] Tested admin ID is correct
- [ ] Created log channel (optional)
- [ ] Added bot to log channel as admin

### 4. Code Preparation
- [ ] All code committed to Git
- [ ] .env in .gitignore
- [ ] requirements.txt up to date
- [ ] README.md complete
- [ ] Tests passing: `python3 tests/test_price_engine.py`

## Render Deployment Steps

### Step 1: Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit - Ethio Tele Trade Bot"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Verify email

### Step 3: Create Web Service

1. Click "New +" → "Web Service"
2. Connect GitHub repository
3. Select your repo

### Step 4: Configure Service

**Basic Settings:**
- **Name**: `ethio-tele-trade-bot` (or your choice)
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Root Directory**: (leave empty)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`

**Advanced Settings:**
- **Instance Type**: Free (or upgrade as needed)
- **Auto-Deploy**: Yes

### Step 5: Environment Variables

Click "Environment" tab and add:

| Key | Value | Notes |
|-----|-------|-------|
| `BOT_TOKEN` | Your bot token | From @BotFather |
| `ADMIN_ID` | Your user ID | From @userinfobot |
| `CHANNEL_ID` | @TeleTradeET | Your channel username |
| `DATABASE_URL` | sqlite:///data.db | SQLite database path |
| `LOG_CHANNEL_ID` | Your log channel ID | Optional |
| `BASE_URL` | https://your-service.onrender.com | Your Render service URL |
| `WEBHOOK_PATH` | /webhook | Webhook endpoint |
| `PORT` | 8080 | Port for web service |

**Important**: Update `BASE_URL` after getting your Render URL!

### Step 6: Deploy

1. Click "Create Web Service"
2. Wait for build to complete (2-3 minutes)
3. Check logs for errors
4. Copy your service URL

### Step 7: Update BASE_URL

1. Go back to Environment Variables
2. Update `BASE_URL` with your actual Render URL
3. Save changes (triggers re-deploy)

### Step 8: Set Webhook

After deployment completes:

```bash
# Update .env locally with your Render URL
BASE_URL=https://your-actual-service.onrender.com

# Run webhook script
python3 scripts/set_webhook.py
```

Expected output:
```
✅ Webhook set successfully to: https://your-service.onrender.com/webhook

Webhook Info:
URL: https://your-service.onrender.com/webhook
Pending updates: 0
```

### Step 9: Verify Deployment

**Health Check:**
```bash
curl https://your-service.onrender.com/health
```

Expected: `OK`

**Webhook Info:**
```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

Check:
- `url` matches your service
- `pending_update_count` is 0
- `last_error_date` is empty

**Test Bot:**
1. Open Telegram
2. Search for @EthioTeleTradeBot
3. Send `/start`
4. Verify language selection appears
5. Complete full user flow

## Post-Deployment Tasks

### 1. Setup Monitoring

**UptimeRobot (Recommended):**
1. Go to [uptimerobot.com](https://uptimerobot.com)
2. Create free account
3. Add new monitor:
   - **Type**: HTTP(S)
   - **URL**: `https://your-service.onrender.com/health`
   - **Name**: Ethio Tele Trade Bot
   - **Interval**: 5 minutes
4. Add alert contacts (email/SMS)

This keeps your Render service awake and alerts you if it goes down.

### 2. Test All Flows

- [ ] Language selection (English + Amharic)
- [ ] Channel join verification
- [ ] Sell flow (complete end-to-end)
- [ ] Screenshot upload
- [ ] Admin panel commands
- [ ] Admin approval flow
- [ ] Payment info collection
- [ ] Payment completion
- [ ] Rejection flow
- [ ] My Submissions
- [ ] Support menu
- [ ] FAQ menu

### 3. Admin Testing

- [ ] `/panel` shows submissions
- [ ] View screenshot works
- [ ] Confirm transfer works
- [ ] Reject with reason works
- [ ] Mark as paid works
- [ ] `/stats` shows correct data
- [ ] `/export` generates CSV
- [ ] `/pause` pauses submissions

### 4. Error Testing

- [ ] Invalid group link
- [ ] Bot not admin in group
- [ ] Invalid username format
- [ ] Invalid image upload
- [ ] Unknown commands
- [ ] Rate limiting works
- [ ] Errors logged to LOG_CHANNEL_ID

## Render Persistence Setup

Render free tier doesn't include persistent disk by default. For production:

### Option 1: Upgrade to Paid Plan
- Persistent disk included
- Database survives restarts
- Recommended for production

### Option 2: External Database
Replace SQLite with PostgreSQL:

1. Add to Render:
   - New PostgreSQL database
   - Copy connection string

2. Update environment:
   ```
   DATABASE_URL=postgresql://user:pass@host/db
   ```

3. Update code:
   - Replace aiosqlite with asyncpg
   - Update database.py

## Troubleshooting

### Webhook Not Working

**Check webhook status:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Reset webhook:**
```bash
python3 scripts/unset_webhook.py
python3 scripts/set_webhook.py
```

**Common issues:**
- BASE_URL doesn't match Render URL
- Service is sleeping (setup UptimeRobot)
- Port mismatch (check PORT env var)

### Bot Not Responding

**Check Render logs:**
1. Go to Render dashboard
2. Click your service
3. Click "Logs" tab
4. Look for Python errors

**Common issues:**
- Missing environment variables
- Database connection error
- Bot token invalid
- Channel ID incorrect

### Database Issues

**Check database file:**
```bash
# In Render shell
ls -la data.db
```

**Reset database:**
- Delete data.db
- Restart service (auto-creates new DB)
- WARNING: Loses all data!

### Admin Commands Not Working

**Verify admin ID:**
1. Message @userinfobot
2. Check ADMIN_ID env var matches exactly
3. Redeploy if changed

### Language Issues

**Check language files:**
```bash
ls -la lang/
cat lang/lang_en.json
cat lang/lang_am.json
```

**Verify JSON format:**
```bash
python3 -m json.tool lang/lang_en.json
python3 -m json.tool lang/lang_am.json
```

## Maintenance

### Regular Checks

**Daily:**
- Check bot is responding
- Review admin panel for new submissions
- Process pending payments

**Weekly:**
- Check Render logs for errors
- Review stats: `/stats`
- Export data: `/export`
- Check UptimeRobot reports

**Monthly:**
- Update dependencies: `pip install -U -r requirements.txt`
- Test full user flow
- Backup database
- Review pricing logic

### Updates and Rollbacks

**Deploy updates:**
```bash
git add .
git commit -m "Update: description"
git push
```

Render auto-deploys on push.

**Rollback:**
1. Go to Render dashboard
2. Click "Deploys" tab
3. Find previous working deploy
4. Click "Redeploy"

### Database Backups

**Manual backup:**
1. Go to Render dashboard
2. Click "Shell" tab
3. Run:
   ```bash
   cat data.db | base64
   ```
4. Save output to file locally
5. Decode when needed: `base64 -d`

**Automated backup (recommended):**
- Use external storage (S3, Google Drive)
- Schedule daily exports
- Keep 30 days of backups

## Scaling Considerations

When bot grows:

1. **Upgrade Render Plan**
   - More RAM/CPU
   - Persistent disk
   - Better performance

2. **External Database**
   - PostgreSQL on Render
   - Better for concurrent users
   - Easier backups

3. **Redis for FSM**
   - Replace MemoryStorage
   - Survives restarts
   - Better for scaling

4. **Multiple Workers**
   - Horizontal scaling
   - Load balancing
   - High availability

## Security Checklist

- [ ] All secrets in environment variables
- [ ] .env not in Git
- [ ] Bot token not exposed
- [ ] Admin commands restricted
- [ ] Rate limiting enabled
- [ ] Input validation on all user data
- [ ] No SQL injection vulnerabilities
- [ ] File upload size limits
- [ ] Error messages don't leak info

## Go-Live Checklist

- [ ] All tests passing
- [ ] Webhook set correctly
- [ ] UptimeRobot configured
- [ ] Admin tested all flows
- [ ] Error logging working
- [ ] Database persistent
- [ ] Backup strategy in place
- [ ] Documentation complete
- [ ] Support channel ready

## Success Metrics

Track these KPIs:

- Total submissions
- Conversion rate (submissions → paid)
- Average processing time
- User satisfaction
- Error rate
- Uptime percentage

Use `/stats` command and analytics tools to monitor.

---

**Ready to go live?** Follow this checklist step-by-step and you'll have a production-ready bot!
