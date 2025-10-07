# 🏰 Rise of Kingdoms Bot

Advanced automation bot for Rise of Kingdoms on BlueStacks with human-like behavior patterns.

## ✨ Features

### Core Automation
- **Resource Gathering**: Automatically search and gather food, wood, stone, and gold from the map
- **Troop Training**: Queue troops continuously based on your configuration
- **Building Upgrades**: Auto-upgrade buildings following optimal progression
- **Research**: Automatically start technology research
- **Barbarian Attacks**: Farm barbarians for rewards and experience
- **Troop Healing**: Auto-heal wounded troops in hospital
- **Alliance Help**: Automatically help alliance members
- **Daily Quests**: Complete and collect daily quest rewards
- **Chest Collection**: Auto-collect free chests, VIP chests, and daily rewards

### Advanced Features
- **Human-like Behavior**: Random delays, bezier curve movements, realistic clicking patterns
- **Anti-Detection**: Session randomization, fatigue simulation, random breaks
- **Multi-Resolution Support**: Works with any screen resolution (auto-scaling)
- **Template Matching**: Advanced image recognition for game state detection
- **Smart Task Scheduling**: Intelligent task prioritization and randomization
- **Error Recovery**: Automatic error handling and recovery mechanisms
- **Detailed Logging**: Comprehensive logging system with color-coded output
- **Statistics Tracking**: Track all actions, resources, and performance metrics
- **License System**: Secure license validation and hardware binding

## 🚀 Installation

### Prerequisites
1. **BlueStacks 5** or later installed
2. **Rise of Kingdoms** installed in BlueStacks
3. **ADB enabled** in BlueStacks settings
4. **Valid license key**

### Quick Install (Windows)
1. Download `RoK_Bot_Setup_v1.0.0.exe`
2. Run installer as administrator
3. Follow installation wizard
4. Launch bot and enter license key

### Manual Installation
```bash
# Clone repository
git clone https://github.com/philoh20-crypto/ROK_bot.git
cd rok-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run bot
python bot_core.py
```

## 🔧 Configuration

### Enabling ADB in BlueStacks
1. Open BlueStacks Settings
2. Navigate to Advanced
3. Enable "Android Debug Bridge (ADB)"
4. Note the port number (default: 5555)
5. Restart BlueStacks

### Bot Configuration
The bot can be configured through the GUI:

#### Tasks Tab
- Enable/disable specific tasks
- Configure resource gathering priorities
- Set troop training preferences
- Adjust barbarian attack settings

#### Settings Tab
- Adjust humanization parameters
- Configure session durations
- Set break intervals
- Enable safe mode for extra caution

## 📖 Usage

### First Time Setup
1. Launch the bot
2. Enter your license key when prompted
3. Select BlueStacks device from dropdown
4. Click "Connect"
5. Configure your desired tasks
6. Click "Start Bot"

### Running the Bot
1. Ensure Rise of Kingdoms is open in BlueStacks
2. Start the bot
3. Monitor progress in the Statistics tab
4. Check logs for detailed information

### Stopping the Bot
- Click "Pause" to temporarily pause (resume anytime)
- Click "Stop" to completely stop the bot
- Statistics are automatically saved

## 🛡️ License System

### Activating License
```python
from license_client import LicenseClient

client = LicenseClient()
result = client.activate_license("YOUR-LICENSE-KEY-HERE")

if result["success"]:
    print("License activated successfully!")
else:
    print(f"Activation failed: {result['message']}")
```

### License Types
- **Trial**: 7 days (for testing)
- **Monthly**: 30 days
- **Yearly**: 365 days
- **Lifetime**: 10 years (effectively permanent)

### License Management
- Each license is bound to one device (hardware ID)
- Check license status in GUI: `License Info` button
- Renew before expiration to avoid interruption

## 📊 Statistics & Reporting

### Real-time Statistics
- Total actions performed
- Success rate percentage
- Resources gathered (all types)
- Troops trained (by type)
- Buildings upgraded
- Barbarians defeated
- And much more...

### Export Options
- Excel reports with multiple sheets
- JSON format for data analysis
- Automatic session logs

### Log Files
All logs are saved in the `logs/` directory:
- `session_YYYYMMDD_HHMMSS.log` - Detailed session logs
- `stats_YYYYMMDD_HHMMSS.json` - Session statistics
- `report_YYYYMMDD_HHMMSS.xlsx` - Excel reports

## 🔒 Security & Safety

### Anti-Detection Features
1. **Random Timing**: All actions use randomized delays
2. **Human-like Movement**: Bezier curves for realistic mouse paths
3. **Fatigue Simulation**: Bot gets "slower" over time
4. **Random Breaks**: Unpredictable break patterns
5. **Task Randomization**: Tasks executed in random order
6. **Session Variation**: Each session has different duration

### Safe Mode
Enable in Settings for maximum safety:
- Longer delays between actions
- More conservative task execution
- Extra verification steps
- Reduced automation intensity

## 🛠️ Development

### Project Structure
```
rok_bot/
├── bot_core.py           # Main bot controller & GUI
├── adb_client.py         # ADB communication wrapper
├── adb_utils.py          # Image processing utilities
├── state_machine.py      # Task implementations
├── humanizer.py          # Human behavior simulation
├── session_logger.py     # Logging & statistics
├── license_server.py     # License management (server)
├── license_client.py     # License validation (client)
├── templates/            # Image templates for recognition
├── logs/                 # Log files
├── requirements.txt      # Python dependencies
├── build_exe.sh          # Build script (Linux/Mac)
├── build_exe.spec        # PyInstaller configuration
└── installer.iss         # Inno Setup script (Windows)
```

### Building from Source
```bash
# Linux/Mac
chmod +x build_exe.sh
./build_exe.sh

# Windows
python -m PyInstaller build_exe.spec
```

### Adding Custom Tasks
Create a new task class in `state_machine.py`:

```python
class CustomTask(BaseTask):
    def execute(self) -> bool:
        try:
            logger.info("Executing custom task")
            
            # Your task logic here
            if self.find_and_tap("templates/custom_button.png"):
                self.humanizer.wait_human(1.0)
                return True
            
            return False
        except Exception as e:
            self.logger.log_error("Custom task failed", e)
            return False
```

### Creating Image Templates
1. Take screenshot during gameplay
2. Crop the UI element you want to detect
3. Save as PNG in `templates/` directory
4. Use descriptive filename (e.g., `gather_button.png`)
5. Update template references in task code

## 🐛 Troubleshooting

### Bot Won't Connect
- Ensure BlueStacks is running
- Check ADB is enabled in BlueStacks settings
- Verify ADB port (default: 5037)
- Try restarting BlueStacks

### Template Not Found
- Check template files exist in `templates/` directory
- Verify image matches current game UI
- Adjust threshold parameter (lower = more lenient)
- Take new screenshot if game UI changed

### License Issues
- Verify license key is correct
- Check license expiration date
- Ensure only using on one device
- Contact support for license problems

### Performance Issues
- Close other applications
- Reduce BlueStacks graphics settings
- Enable safe mode
- Increase delay settings

## 📝 Best Practices

1. **Start Slow**: Begin with conservative settings
2. **Monitor Initially**: Watch first few hours of operation
3. **Regular Breaks**: Don't run 24/7
4. **Update Templates**: After game updates, update templates
5. **Check Logs**: Review logs regularly for errors
6. **Vary Schedule**: Don't use same schedule daily
7. **Backup Config**: Save your working configuration

## ⚠️ Disclaimer

This bot is for educational purposes only. Use at your own risk. The developers are not responsible for any account actions taken by game publishers. Always review and comply with the game's Terms of Service.


## 📜 License

Copyright © 2025. All rights reserved.

This software is licensed. Redistribution and commercial use are prohibited without explicit permission.

## 🙏 Credits

- **Pure Python ADB**: For ADB communication
- **OpenCV**: Image processing
- **PyQt5**: GUI framework
- **PyInstaller**: Executable creation

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-05  
**Compatibility**: BlueStacks 5+, Rise of Kingdoms Latest