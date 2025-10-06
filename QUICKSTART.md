# 🚀 Quick Start Guide - Rise of Kingdoms Bot

Get up and running in 5 minutes!

## 📋 Prerequisites Checklist

Before you start, make sure you have:

- [ ] BlueStacks 5 installed and running
- [ ] Rise of Kingdoms installed in BlueStacks
- [ ] Valid license key
- [ ] Python 3.8+ (for manual installation)

## ⚡ Fast Setup (Windows Users)

### Step 1: Enable ADB in BlueStacks
1. Open BlueStacks
2. Click the **hamburger menu** (≡) in top-right
3. Go to **Settings** → **Advanced**
4. Scroll down and enable **"Android Debug Bridge (ADB)"**
5. Note the port number (usually 5555)
6. Click **Restart Now**

### Step 2: Install the Bot
1. Download `RoK_Bot_Setup_v1.0.0.exe`
2. Run as **Administrator**
3. Follow the installation wizard
4. Choose installation directory
5. Wait for installation to complete

### Step 3: First Launch
1. Launch **Rise of Kingdoms Bot** from desktop or start menu
2. Enter your **license key** when prompted
3. Click **Activate**
4. Wait for "License activated successfully!" message

### Step 4: Connect to BlueStacks
1. Make sure Rise of Kingdoms is **open** in BlueStacks
2. In the bot, click **"Refresh Devices"**
3. Select your BlueStacks device from dropdown
4. Click **"Connect"**
5. Wait for "Connected to device" message

### Step 5: Configure Tasks
1. Go to **"Tasks Configuration"** tab
2. Check the tasks you want to enable:
   - ✅ Gather Resources (recommended)
   - ✅ Train Troops
   - ✅ Alliance Help
   - ✅ Collect Chests
   - ✅ Daily Quests
3. Click **"Save Settings"**

### Step 6: Start Botting
1. Go back to **"Main Control"** tab
2. Click **"▶️ Start Bot"**
3. Watch the magic happen! 🎉

## 🐧 Manual Installation (Linux/Mac)

```bash
# 1. Clone or download the repository
git clone https://github.com/yourrepo/rok-bot.git
cd rok-bot

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the bot
python bot_core.py
```

## 🎯 Basic Configuration

### Recommended Settings for Beginners

**Tasks to Enable:**
- ✅ Gather Resources
- ✅ Train Troops
- ✅ Alliance Help
- ✅ Collect Chests
- ✅ Daily Quests
- ❌ Attack Barbarians (enable after testing)

**Settings Tab:**
- Min Action Delay: `0.5s` (safer)
- Max Action Delay: `2.0s` (safer)
- Session Duration: `60 minutes`
- Break Duration: `30 minutes`
- ✅ Safe Mode (for first use)

### Resource Gathering Priority
Configure which resources to gather:
- ✅ Food (most important)
- ✅ Wood (very important)
- ✅ Stone (important)
- ⬜ Gold (optional, gather if needed)

### Troop Training
- **Troop Type**: Infantry (fastest to train)
- **Quantity**: 100-200 (adjust based on resources)

## 🔍 Testing Your Setup

### Quick Test Procedure
1. Start the bot with **only** "Alliance Help" enabled
2. Let it run for 5 minutes
3. Check the **Statistics** tab for actions
4. Review **Logs** tab for any errors
5. If successful, enable more tasks!

### What to Watch For
- ✅ Bot finds and clicks buttons
- ✅ No error messages in logs
- ✅ Actions are being logged
- ✅ Statistics are updating

## 🛠️ Troubleshooting Common Issues

### Bot Won't Connect
**Problem**: "No devices found" or connection fails

**Solutions**:
1. Restart BlueStacks
2. Verify ADB is enabled in BlueStacks settings
3. Try different ADB port (5555, 5556, 5557)
4. Run bot as Administrator

### Template Not Found Errors
**Problem**: "Template not found" errors in logs

**Solutions**:
1. Make sure `templates/` folder exists
2. Verify template images are present
3. Game UI may have changed - update templates
4. Try adjusting recognition threshold in Settings

### License Activation Failed
**Problem**: "Invalid license key" or "License expired"

**Solutions**:
1. Double-check license key for typos
2. Verify license hasn't expired
3. Check internet connection (for online validation)
4. Contact support with your order details

### Bot Clicks Wrong Buttons
**Problem**: Bot taps incorrect locations

**Solutions**:
1. Check BlueStacks resolution matches config
2. Update image templates for current game version
3. Increase recognition threshold
4. Enable Safe Mode for more verification

## 📊 Monitoring Your Bot

### Statistics to Track
- **Success Rate**: Should be >80%
- **Total Actions**: Indicates bot is working
- **Resources Gathered**: Check if gathering is effective
- **Errors**: <5 errors per hour is normal

### When to Stop the Bot
- ⚠️ Success rate drops below 50%
- ⚠️ Continuous errors (>10 in a row)
- ⚠️ Game update released
- ⚠️ Unusual behavior detected

## 🎓 Next Steps

Once you're comfortable with basic usage:

1. **Optimize Settings**: Fine-tune delays and intervals
2. **Enable More Tasks**: Add barbarian attacks, research
3. **Create Schedules**: Set up automated sessions
4. **Monitor Statistics**: Track improvements
5. **Join Community**: Share tips and get help

## 💡 Pro Tips

### For Best Results:
1. **Start Conservative**: Begin with longer delays
2. **Run During Off-Peak**: Bot performs better when game is less laggy
3. **Regular Maintenance**: Update templates after game patches
4. **Backup Config**: Save your working configuration
5. **Vary Schedule**: Don't run same pattern daily

### Safety First:
- ✅ Always use Safe Mode initially
- ✅ Monitor first few hours of operation
- ✅ Don't run 24/7
- ✅ Take breaks between sessions
- ✅ Check logs regularly

## 📞 Getting Help

### Before Asking for Help:
1. Check this quick start guide
2. Read the full README.md
3. Review error logs
4. Try troubleshooting steps above

### Support Channels:
- 📧 **Email**: support@example.com
- 💬 **Discord**: [Join Server]
- 📖 **Docs**: [Full Documentation]
- 🐛 **Bug Reports**: [GitHub Issues]

## ✅ Success Checklist

You're ready to bot when:
- [x] BlueStacks running with ADB enabled
- [x] Rise of Kingdoms open and at city view
- [x] Bot connected to device successfully
- [x] License activated and valid
- [x] Tasks configured appropriately
- [x] Safe Mode enabled for first run
- [x] Logs and statistics tabs open for monitoring

---

**Happy Botting! 🎮🤖**

If you run into any issues, don't hesitate to reach out for support. We're here to help!