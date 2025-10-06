"""
Bot Core - Main bot controller and GUI
"""
import sys
import time
import random
from typing import List, Dict, Optional
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import logging

from adb_client import RoKADBClient
from adb_utils import ImageProcessor, CoordinateMapper
from humanizer import HumanBehavior, SessionRandomizer
from session_logger import SessionLogger
from license_client import LicenseClient, display_license_banner
from state_machine import *
from gui_logger import QTextEditLogger, LogViewer, setup_gui_logging, remove_gui_logging

logger = logging.getLogger(__name__)


class BotCore:
    """Main bot controller and orchestrator"""
    
    def __init__(self):
        self.adb = RoKADBClient()
        self.image_processor = ImageProcessor()
        self.coord_mapper = CoordinateMapper()
        self.humanizer = HumanBehavior()
        self.session_randomizer = SessionRandomizer()
        self.logger = SessionLogger()
        self.license_client = LicenseClient()
        
        self.running = False
        self.paused = False
        self.current_task: Optional[TaskType] = None
        
        # Task configuration
        self.enabled_tasks: Dict[TaskType, bool] = {
            TaskType.GATHER_RESOURCES: True,
            TaskType.TRAIN_TROOPS: True,
            TaskType.UPGRADE_BUILDINGS: True,
            TaskType.RESEARCH_TECH: True,
            TaskType.ATTACK_BARBARIANS: False,  # Disabled by default for safety
            TaskType.HEAL_TROOPS: True,
            TaskType.ALLIANCE_HELP: True,
            TaskType.COLLECT_CHESTS: True,
            TaskType.DAILY_QUESTS: True
        }
        
        self.task_settings: Dict[str, Dict] = {
            "gathering": {
                "resource_types": ["food", "wood", "stone", "gold"],
                "troop_count": 10000
            },
            "training": {
                "troop_type": "infantry",
                "quantity": 100
            },
            "barbarians": {
                "level": 1,
                "attack_count": 5
            }
        }
    
    def check_license(self) -> bool:
        """Check if license is valid and show warnings if needed"""
        if not self.license_client.check_and_warn():
            return False
        
        display_license_banner(self.license_client)
        return True
    
    def initialize(self) -> bool:
        """Initialize bot components and connect to device"""
        logger.info("Initializing Rise of Kingdoms Bot...")
        
        # Connect to ADB server
        if not self.adb.connect():
            logger.error("Failed to connect to ADB server")
            return False
        
        # Select available device
        if not self.adb.select_device():
            logger.error("No ADB devices found")
            return False
        
        # Get and set screen resolution for coordinate mapping
        width, height = self.adb.get_screen_resolution()
        self.coord_mapper.set_current_resolution(width, height)
        logger.info(f"Screen resolution detected: {width}x{height}")
        
        # Start game if not already running
        if not self.adb.is_app_running():
            logger.info("Rise of Kingdoms not running, starting application...")
            self.adb.start_app()
            time.sleep(5)  # Wait for app to fully load
        
        logger.info("Bot initialized successfully")
        return True
    
    def start(self):
        """Start the bot main execution loop"""
        if not self.running:
            self.running = True
            self.paused = False
            logger.info("Bot execution started")
            self._run_bot_loop()
    
    def stop(self):
        """Stop the bot and cleanup resources"""
        self.running = False
        logger.info("Bot execution stopped")
        self.logger.close()
    
    def pause(self):
        """Pause bot execution temporarily"""
        self.paused = True
        logger.info("Bot execution paused")
    
    def resume(self):
        """Resume bot execution after pause"""
        self.paused = False
        logger.info("Bot execution resumed")
    
    def _run_bot_loop(self):
        """Main bot execution loop with task scheduling"""
        logger.info("Starting main bot execution loop...")
        
        while self.running:
            try:
                # Check if execution is paused
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Check if session should end based on duration
                if self.session_randomizer.should_end_session():
                    logger.info("Session duration completed, taking break...")
                    delay_seconds = self.session_randomizer.get_next_session_delay()
                    logger.info(f"Next session in {delay_seconds / 60:.1f} minutes")
                    time.sleep(delay_seconds)
                    continue
                
                # Get list of enabled tasks
                tasks = self._get_enabled_tasks()
                
                # Randomize task execution order for human-like behavior
                tasks = self.session_randomizer.randomize_task_order(tasks)
                
                # Execute each task in randomized order
                for task_type in tasks:
                    if not self.running or self.paused:
                        break
                    
                    # Random chance to skip task (simulates human behavior)
                    if self.session_randomizer.should_skip_task(0.1):
                        logger.info(f"Randomly skipping task: {task_type.value}")
                        continue
                    
                    self._execute_task(task_type)
                    
                    # Add human-like delay between tasks
                    self.humanizer.wait_human(random.uniform(5, 15))
                    
                    # Check if human-like break is needed
                    if self.humanizer.should_take_break():
                        self.humanizer.take_break()
                
                # Wait before starting next task cycle
                cycle_delay = random.uniform(60, 180)  # 1-3 minutes between cycles
                logger.info(f"Task cycle completed, waiting {cycle_delay:.0f} seconds...")
                time.sleep(cycle_delay)
            
            except Exception as e:
                self.logger.log_error("Unexpected error in bot main loop", e)
                time.sleep(30)  # Wait before retrying after error
        
        logger.info("Bot main loop ended")
    
    def _get_enabled_tasks(self) -> List[TaskType]:
        """Get list of currently enabled task types"""
        return [task_type for task_type, enabled in self.enabled_tasks.items() if enabled]
    
    def _execute_task(self, task_type: TaskType):
        """Execute a specific task type with error handling"""
        try:
            self.current_task = task_type
            logger.info(f"Executing task: {task_type.value}")
            
            task_instance = self._create_task_instance(task_type)
            if task_instance:
                success = task_instance.execute()
                self.logger.log_action(
                    task_type.value,
                    success,
                    f"Task completed successfully" if success else f"Task execution failed"
                )
            else:
                logger.error(f"Failed to create task instance for: {task_type.value}")
            
            self.current_task = None
        
        except Exception as e:
            self.logger.log_error(f"Task execution error for {task_type.value}", e)
            self.current_task = None
    
    def _create_task_instance(self, task_type: TaskType) -> Optional[BaseTask]:
        """Create appropriate task instance based on task type"""
        if task_type == TaskType.GATHER_RESOURCES:
            resource = random.choice(self.task_settings["gathering"]["resource_types"])
            return ResourceGatheringTask(self, resource)
        
        elif task_type == TaskType.TRAIN_TROOPS:
            return TroopTrainingTask(
                self,
                self.task_settings["training"]["troop_type"],
                self.task_settings["training"]["quantity"]
            )
        
        elif task_type == TaskType.UPGRADE_BUILDINGS:
            return BuildingUpgradeTask(self)
        
        elif task_type == TaskType.RESEARCH_TECH:
            return ResearchTask(self)
        
        elif task_type == TaskType.ATTACK_BARBARIANS:
            return BarbarianAttackTask(
                self,
                self.task_settings["barbarians"]["level"],
                self.task_settings["barbarians"]["attack_count"]
            )
        
        elif task_type == TaskType.HEAL_TROOPS:
            return HealTroopsTask(self)
        
        elif task_type == TaskType.ALLIANCE_HELP:
            return AllianceHelpTask(self)
        
        elif task_type == TaskType.COLLECT_CHESTS:
            return CollectChestsTask(self)
        
        elif task_type == TaskType.DAILY_QUESTS:
            return DailyQuestsTask(self)
        
        return None
    
    def set_task_enabled(self, task_type: TaskType, enabled: bool):
        """Enable or disable specific task type"""
        self.enabled_tasks[task_type] = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"Task {task_type.value} {status}")
    
    def update_task_settings(self, category: str, settings: Dict):
        """Update settings for specific task category"""
        if category in self.task_settings:
            self.task_settings[category].update(settings)
            logger.info(f"Updated settings for category: {category}")


class BotGUI(QMainWindow):
    """PyQt5 GUI interface for bot control and monitoring"""
    
    def __init__(self):
        super().__init__()
        self.bot = BotCore()
        self.bot_thread: Optional[BotThread] = None
        self.gui_logger_handler: Optional[QTextEditLogger] = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface components"""
        self.setWindowTitle("Rise of Kingdoms Bot v1.0")
        self.setGeometry(100, 100, 900, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header section
        header_layout = QHBoxLayout()
        title_label = QLabel("🏰 Rise of Kingdoms Bot")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # License information button
        license_btn = QPushButton("📄 License Info")
        license_btn.clicked.connect(self.show_license_info)
        header_layout.addWidget(license_btn)
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(QLabel(""))  # Spacer
        
        # Tab widget for different sections
        tabs = QTabWidget()
        tabs.addTab(self.create_main_tab(), "Main Control")
        tabs.addTab(self.create_tasks_tab(), "Tasks Configuration")
        tabs.addTab(self.create_settings_tab(), "Settings")
        tabs.addTab(self.create_statistics_tab(), "Statistics")
        tabs.addTab(self.create_logs_tab(), "Logs")
        
        main_layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready to initialize")
        
        # Apply application stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
    
    def create_main_tab(self):
        """Create main control tab with connection and bot controls"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Connection group
        conn_group = QGroupBox("Device Connection")
        conn_layout = QVBoxLayout()
        
        self.device_combo = QComboBox()
        self.refresh_devices_btn = QPushButton("🔄 Refresh Devices")
        self.refresh_devices_btn.clicked.connect(self.refresh_devices)
        self.connect_btn = QPushButton("🔌 Connect to Device")
        self.connect_btn.clicked.connect(self.connect_device)
        
        conn_layout.addWidget(QLabel("Select Device:"))
        conn_layout.addWidget(self.device_combo)
        conn_layout.addWidget(self.refresh_devices_btn)
        conn_layout.addWidget(self.connect_btn)
        conn_group.setLayout(conn_layout)
        
        # Bot control buttons
        control_group = QGroupBox("Bot Control")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Start Bot")
        self.start_btn.clicked.connect(self.start_bot)
        self.start_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("⏸️ Pause Bot")
        self.pause_btn.clicked.connect(self.pause_bot)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹️ Stop Bot")
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        
        # Status display
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Not Connected")
        self.current_task_label = QLabel("Current Task: None")
        self.actions_label = QLabel("Actions Completed: 0")
        self.uptime_label = QLabel("Uptime: 00:00:00")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_task_label)
        status_layout.addWidget(self.actions_label)
        status_layout.addWidget(self.uptime_label)
        status_group.setLayout(status_layout)
        
        # Quick actions
        quick_group = QGroupBox("Quick Actions")
        quick_layout = QHBoxLayout()
        
        self.screenshot_btn = QPushButton("📸 Take Screenshot")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        
        self.restart_game_btn = QPushButton("🔄 Restart Game")
        self.restart_game_btn.clicked.connect(self.restart_game)
        
        quick_layout.addWidget(self.screenshot_btn)
        quick_layout.addWidget(self.restart_game_btn)
        quick_group.setLayout(quick_layout)
        
        # Add all groups to main layout
        layout.addWidget(conn_group)
        layout.addWidget(control_group)
        layout.addWidget(status_group)
        layout.addWidget(quick_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_tasks_tab(self):
        """Create tasks configuration tab with task-specific settings"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Task checkboxes
        tasks_group = QGroupBox("Enabled Tasks")
        tasks_layout = QVBoxLayout()
        
        self.task_checkboxes: Dict[TaskType, QCheckBox] = {}
        for task_type in TaskType:
            checkbox = QCheckBox(task_type.value.replace("_", " ").title())
            checkbox.setChecked(self.bot.enabled_tasks.get(task_type, False))
            checkbox.stateChanged.connect(
                lambda state, t=task_type: self.bot.set_task_enabled(t, state == Qt.Checked)
            )
            self.task_checkboxes[task_type] = checkbox
            tasks_layout.addWidget(checkbox)
        
        tasks_group.setLayout(tasks_layout)
        
        # Gathering settings
        gather_group = QGroupBox("Gathering Settings")
        gather_layout = QFormLayout()
        
        self.resource_checks: Dict[str, QCheckBox] = {}
        for resource in ["food", "wood", "stone", "gold"]:
            check = QCheckBox()
            check.setChecked(True)
            self.resource_checks[resource] = check
            gather_layout.addRow(resource.capitalize() + ":", check)
        
        gather_group.setLayout(gather_layout)
        
        # Training settings
        train_group = QGroupBox("Training Settings")
        train_layout = QFormLayout()
        
        self.troop_type_combo = QComboBox()
        self.troop_type_combo.addItems(["infantry", "cavalry", "archer", "siege"])
        
        self.troop_quantity_spin = QSpinBox()
        self.troop_quantity_spin.setRange(1, 10000)
        self.troop_quantity_spin.setValue(100)
        
        train_layout.addRow("Troop Type:", self.troop_type_combo)
        train_layout.addRow("Quantity:", self.troop_quantity_spin)
        train_group.setLayout(train_layout)
        
        # Barbarian settings
        barb_group = QGroupBox("Barbarian Attack Settings")
        barb_layout = QFormLayout()
        
        self.barb_level_spin = QSpinBox()
        self.barb_level_spin.setRange(1, 50)
        self.barb_level_spin.setValue(1)
        
        self.barb_count_spin = QSpinBox()
        self.barb_count_spin.setRange(1, 20)
        self.barb_count_spin.setValue(5)
        
        barb_layout.addRow("Barbarian Level:", self.barb_level_spin)
        barb_layout.addRow("Attack Count:", self.barb_count_spin)
        barb_group.setLayout(barb_layout)
        
        # Save settings button
        save_btn = QPushButton("💾 Save Task Settings")
        save_btn.clicked.connect(self.save_task_settings)
        
        # Add all groups to layout
        layout.addWidget(tasks_group)
        layout.addWidget(gather_group)
        layout.addWidget(train_group)
        layout.addWidget(barb_group)
        layout.addWidget(save_btn)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_settings_tab(self):
        """Create settings tab with bot behavior configuration"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Humanization settings
        human_group = QGroupBox("Humanization Settings")
        human_layout = QFormLayout()
        
        self.min_delay_spin = QDoubleSpinBox()
        self.min_delay_spin.setRange(0.1, 5.0)
        self.min_delay_spin.setValue(0.3)
        self.min_delay_spin.setSingleStep(0.1)
        
        self.max_delay_spin = QDoubleSpinBox()
        self.max_delay_spin.setRange(0.5, 10.0)
        self.max_delay_spin.setValue(1.5)
        self.max_delay_spin.setSingleStep(0.1)
        
        human_layout.addRow("Minimum Action Delay (s):", self.min_delay_spin)
        human_layout.addRow("Maximum Action Delay (s):", self.max_delay_spin)
        human_group.setLayout(human_layout)
        
        # Session settings
        session_group = QGroupBox("Session Settings")
        session_layout = QFormLayout()
        
        self.session_duration_spin = QSpinBox()
        self.session_duration_spin.setRange(30, 300)
        self.session_duration_spin.setValue(90)
        self.session_duration_spin.setSuffix(" minutes")
        
        self.break_duration_spin = QSpinBox()
        self.break_duration_spin.setRange(10, 180)
        self.break_duration_spin.setValue(30)
        self.break_duration_spin.setSuffix(" minutes")
        
        session_layout.addRow("Session Duration:", self.session_duration_spin)
        session_layout.addRow("Break Duration:", self.break_duration_spin)
        session_group.setLayout(session_layout)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout()
        
        self.safe_mode_check = QCheckBox("Safe Mode (Extra Delays and Precautions)")
        self.safe_mode_check.setChecked(False)
        
        self.screenshot_on_error_check = QCheckBox("Take Screenshot on Errors")
        self.screenshot_on_error_check.setChecked(True)
        
        advanced_layout.addWidget(self.safe_mode_check)
        advanced_layout.addWidget(self.screenshot_on_error_check)
        advanced_group.setLayout(advanced_layout)
        
        # Save settings button
        save_btn = QPushButton("💾 Save General Settings")
        save_btn.clicked.connect(self.save_general_settings)
        
        layout.addWidget(human_group)
        layout.addWidget(session_group)
        layout.addWidget(advanced_group)
        layout.addWidget(save_btn)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_statistics_tab(self):
        """Create statistics tab with session performance data"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Statistics display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        
        # Refresh and export buttons
        refresh_btn = QPushButton("🔄 Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_statistics)
        
        export_btn = QPushButton("📊 Export to Excel")
        export_btn.clicked.connect(self.export_statistics)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        
        layout.addWidget(QLabel("Session Statistics:"))
        layout.addWidget(self.stats_text)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        return tab
    
    def create_logs_tab(self):
        """Create logs tab with console output"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Log display
        self.log_text = LogViewer()
        self.log_text.setReadOnly(True)
        
        # Setup GUI logging
        self.gui_logger_handler = setup_gui_logging(self.log_text)
        
        # Clear logs button
        clear_btn = QPushButton("🗑️ Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        
        layout.addWidget(QLabel("Console Logs:"))
        layout.addWidget(self.log_text)
        layout.addWidget(clear_btn)
        
        tab.setLayout(layout)
        return tab
    
    # Button handler methods
    def refresh_devices(self):
        """Refresh the list of available ADB devices"""
        self.device_combo.clear()
        if self.bot.adb.connect():
            devices = self.bot.adb.get_devices()
            for device in devices:
                self.device_combo.addItem(device.serial)
            device_count = len(devices)
            self.statusBar().showMessage(f"Found {device_count} device(s)")
        else:
            self.statusBar().showMessage("Failed to connect to ADB server")
    
    def connect_device(self):
        """Connect to the selected ADB device"""
        # Check license validity first
        if not self.bot.check_license():
            QMessageBox.critical(self, "License Error", 
                               "Invalid or expired license! Please activate a valid license.")
            return
        
        # Initialize bot and connect to device
        if self.bot.initialize():
            self.start_btn.setEnabled(True)
            self.status_label.setText("Status: Connected to Device")
            self.statusBar().showMessage("Successfully connected to BlueStacks device")
            QMessageBox.information(self, "Connection Success", 
                                  "Successfully connected to BlueStacks device!")
        else:
            QMessageBox.critical(self, "Connection Error", 
                               "Failed to connect to device. Please check your BlueStacks installation.")
    
    def start_bot(self):
        """Start the bot execution"""
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Bot Running")
        
        # Start bot in separate thread
        self.bot_thread = BotThread(self.bot)
        self.bot_thread.start()
        
        self.statusBar().showMessage("Bot execution started")
    
    def pause_bot(self):
        """Pause or resume bot execution"""
        if self.bot.paused:
            self.bot.resume()
            self.pause_btn.setText("⏸️ Pause Bot")
            self.status_label.setText("Status: Bot Running")
            self.statusBar().showMessage("Bot execution resumed")
        else:
            self.bot.pause()
            self.pause_btn.setText("▶️ Resume Bot")
            self.status_label.setText("Status: Bot Paused")
            self.statusBar().showMessage("Bot execution paused")
    
    def stop_bot(self):
        """Stop the bot execution"""
        self.bot.stop()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Bot Stopped")
        self.statusBar().showMessage("Bot execution stopped")
    
    def take_screenshot(self):
        """Take and save a screenshot from the device"""
        screenshot = self.bot.adb.get_screenshot()
        if screenshot:
            filename = f"screenshot_{int(time.time())}.png"
            screenshot.save(filename)
            QMessageBox.information(self, "Screenshot Saved", 
                                  f"Screenshot saved as: {filename}")
        else:
            QMessageBox.warning(self, "Screenshot Failed", 
                              "Failed to capture screenshot from device")
    
    def restart_game(self):
        """Restart the Rise of Kingdoms game"""
        self.bot.adb.stop_app()
        time.sleep(2)  # Wait for app to fully close
        self.bot.adb.start_app()
        self.statusBar().showMessage("Game restarted successfully")
    
    def save_task_settings(self):
        """Save task-specific configuration settings"""
        # Update gathering settings
        resources = [resource for resource, check in self.resource_checks.items() 
                    if check.isChecked()]
        self.bot.task_settings["gathering"]["resource_types"] = resources
        
        # Update training settings
        self.bot.task_settings["training"]["troop_type"] = self.troop_type_combo.currentText()
        self.bot.task_settings["training"]["quantity"] = self.troop_quantity_spin.value()
        
        # Update barbarian settings
        self.bot.task_settings["barbarians"]["level"] = self.barb_level_spin.value()
        self.bot.task_settings["barbarians"]["attack_count"] = self.barb_count_spin.value()
        
        QMessageBox.information(self, "Settings Saved", "Task configuration settings saved successfully!")
    
    def save_general_settings(self):
        """Save general bot behavior settings"""
        self.bot.humanizer.min_action_delay = self.min_delay_spin.value()
        self.bot.humanizer.max_action_delay = self.max_delay_spin.value()
        
        QMessageBox.information(self, "Settings Saved", "General settings saved successfully!")
    
    def refresh_statistics(self):
        """Refresh and display current session statistics"""
        stats = self.bot.logger.get_statistics_summary()
        
        stats_text = f"""
Session ID: {stats['session_id']}
Duration: {stats['duration_formatted']}
Total Actions: {stats['total_actions']:,}
Success Rate: {stats['success_rate_formatted']}

Resources Gathered:
  Food: {stats['resources_gathered']['food']:,}
  Wood: {stats['resources_gathered']['wood']:,}
  Stone: {stats['resources_gathered']['stone']:,}
  Gold: {stats['resources_gathered']['gold']:,}

Troops Trained:
  Infantry: {stats['troops_trained']['infantry']:,}
  Cavalry: {stats['troops_trained']['cavalry']:,}
  Archer: {stats['troops_trained']['archer']:,}
  Siege: {stats['troops_trained']['siege']:,}

Other Activities:
  Buildings Upgraded: {stats['buildings_upgraded']:,}
  Researches Started: {stats['researches_started']:,}
  Barbarians Killed: {stats['barbarians_killed']:,}
  Gathering Trips: {stats['gathering_trips']:,}
  Alliance Helps: {stats['alliance_helps']:,}
  Daily Quests: {stats['daily_quests_completed']:,}
  Chests Collected: {stats['chests_collected']:,}

Issues:
  Errors: {stats['total_errors']:,}
  Warnings: {stats['total_warnings']:,}
"""
        self.stats_text.setText(stats_text)
    
    def export_statistics(self):
        """Export statistics to Excel file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Statistics to Excel", "", "Excel Files (*.xlsx)"
        )
        if filename:
            success = self.bot.logger.export_to_excel(filename)
            if success:
                QMessageBox.information(self, "Export Success", 
                                      f"Statistics exported to: {filename}")
            else:
                QMessageBox.warning(self, "Export Failed", 
                                  "Failed to export statistics to Excel")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.clear_logs()
        self.statusBar().showMessage("Logs cleared")
    
    def show_license_info(self):
        """Display license information dialog"""
        info = self.bot.license_client.get_license_info()
        message = f"""
License Information:

User ID: {info['user_id']}
License Key: {info['license_key']}
Expiration: {info['expires_at']}
Days Remaining: {info['days_remaining']}
Status: {'✅ ACTIVE' if info['is_valid'] else '❌ INACTIVE'}
Hardware ID: {info['hardware_id']}
"""
        QMessageBox.information(self, "License Information", message)
    
    def closeEvent(self, event):
        """Handle application close event with safety checks"""
        if self.bot.running:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Bot is currently running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.bot.stop()
                if self.gui_logger_handler:
                    remove_gui_logging(self.gui_logger_handler)
                event.accept()
            else:
                event.ignore()
        else:
            if self.gui_logger_handler:
                remove_gui_logging(self.gui_logger_handler)
            event.accept()


class BotThread(QThread):
    """QThread for running bot execution in background"""
    
    def __init__(self, bot: BotCore):
        super().__init__()
        self.bot = bot
    
    def run(self):
        """Main thread execution method"""
        self.bot.start()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for consistent look
    
    # Create and show main GUI window
    gui = BotGUI()
    gui.show()
    
    # Start application event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
