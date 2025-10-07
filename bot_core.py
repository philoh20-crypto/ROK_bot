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


class ADBConnectionThread(QThread):
    """Thread for ADB connection to prevent GUI freezing"""
    connection_result = pyqtSignal(bool, str)  # success, message
    devices_found = pyqtSignal(list)  # list of devices
    
    def __init__(self, adb_client, action="connect"):
        super().__init__()
        self.adb_client = adb_client
        self.action = action
        self.device_serial = None
    
    def run(self):
        """Execute ADB connection operations in separate thread"""
        try:
            if self.action == "connect":
                success = self.adb_client.connect()
                if success:
                    self.connection_result.emit(True, "Connected to ADB server")
                else:
                    self.connection_result.emit(False, "Failed to connect to ADB server")
            
            elif self.action == "refresh_devices":
                if not self.adb_client.client:
                    self.adb_client.connect()
                devices = self.adb_client.get_devices()
                self.devices_found.emit(devices)
            
            elif self.action == "select_device":
                success = self.adb_client.select_device(self.device_serial)
                if success:
                    self.connection_result.emit(True, f"Connected to device {self.device_serial}")
                else:
                    self.connection_result.emit(False, "Failed to connect to device")
        
        except Exception as e:
            self.connection_result.emit(False, f"Error: {str(e)}")


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
        
        # Task configuration with detailed settings
        self.enabled_tasks: Dict[TaskType, bool] = {
            TaskType.GATHER_RESOURCES: True,
            TaskType.TRAIN_TROOPS: True,
            TaskType.UPGRADE_BUILDINGS: True,
            TaskType.RESEARCH_TECH: True,
            TaskType.ATTACK_BARBARIANS: False,
            TaskType.HEAL_TROOPS: True,
            TaskType.ALLIANCE_HELP: True,
            TaskType.COLLECT_CHESTS: True,
            TaskType.DAILY_QUESTS: True,
            TaskType.NEW_PLAYER_TUTORIAL: False,
            TaskType.EXPLORE_FOG: False,
            TaskType.GATHER_GEMS: False
        }
        
        self.task_settings: Dict[str, Dict] = {
            "gathering": {
                "resource_types": ["food", "wood", "stone", "gold"],
                "troop_count": 10000,
                "gather_gems": False
            },
            "training": {
                "troop_type": "infantry",
                "quantity": 100,
                "continuous": True
            },
            "buildings": {
                "target_level": 25,
                "focus_town_hall": True,
                "upgrade_priority": ["town_hall", "academy", "barracks", "training_grounds"]
            },
            "barbarians": {
                "level": 1,
                "attack_count": 5
            },
            "exploration": {
                "explore_fog": False,
                "max_scouts": 3
            },
            "tutorial": {
                "auto_complete": False,
                "skip_animations": True
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
        
        elif task_type == TaskType.NEW_PLAYER_TUTORIAL:
            return NewPlayerTutorialTask(self)
        
        elif task_type == TaskType.EXPLORE_FOG:
            return ExploreFogTask(self)
        
        elif task_type == TaskType.GATHER_GEMS:
            return GatherGemsTask(self)
        
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
        self.update_timer: Optional[QTimer] = None
        self.adb_thread: Optional[ADBConnectionThread] = None
        self.init_ui()
        self.setup_logging()
        self.setup_timers()
    
    def setup_logging(self):
        """Setup GUI logging system"""
        self.gui_logger_handler = setup_gui_logging(self.log_viewer)
        logger.info("GUI logging system initialized")
    
    def setup_timers(self):
        """Setup periodic update timers"""
        # Timer for updating statistics and status
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize user interface components"""
        self.setWindowTitle("Rise of Kingdoms Bot v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header section
        header_layout = QHBoxLayout()
        title_label = QLabel("🏰 Rise of Kingdoms Bot")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # License information button
        license_btn = QPushButton("📄 License Info")
        license_btn.setMinimumSize(120, 40)
        license_btn.clicked.connect(self.show_license_info)
        header_layout.addWidget(license_btn)
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(QLabel(""))  # Spacer
        
        # Create main content with tasks and logs side by side
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Control and Tasks
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Connection group
        conn_group = self.create_connection_group()
        left_layout.addWidget(conn_group)
        
        # Control buttons
        control_group = self.create_control_group()
        left_layout.addWidget(control_group)
        
        # Status display
        status_group = self.create_status_group()
        left_layout.addWidget(status_group)
        
        # Tasks configuration
        tasks_group = self.create_tasks_group()
        left_layout.addWidget(tasks_group)
        
        left_layout.addStretch()
        
        # Right side - Logs
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        log_label = QLabel("📋 Bot Logs")
        log_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        right_layout.addWidget(log_label)
        
        self.log_viewer = LogViewer()
        right_layout.addWidget(self.log_viewer)
        
        # Log control buttons
        log_buttons = QHBoxLayout()
        clear_logs_btn = QPushButton("🗑️ Clear")
        clear_logs_btn.setMinimumHeight(35)
        clear_logs_btn.clicked.connect(self.clear_logs)
        
        save_logs_btn = QPushButton("💾 Save")
        save_logs_btn.setMinimumHeight(35)
        save_logs_btn.clicked.connect(self.save_logs)
        
        log_buttons.addWidget(clear_logs_btn)
        log_buttons.addWidget(save_logs_btn)
        log_buttons.addStretch()
        
        right_layout.addLayout(log_buttons)
        
        # Add to splitter
        content_splitter.addWidget(left_widget)
        content_splitter.addWidget(right_widget)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(content_splitter)
        
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
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #2c3e50;
            }
            QLabel {
                color: #2c3e50;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                min-height: 25px;
            }
        """)
    
    def create_connection_group(self):
        """Create connection control group"""
        conn_group = QGroupBox("🔌 Connection")
        conn_layout = QVBoxLayout()
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumHeight(35)
        
        btn_layout = QHBoxLayout()
        
        self.refresh_devices_btn = QPushButton("🔄 Refresh")
        self.refresh_devices_btn.setMinimumSize(100, 45)
        self.refresh_devices_btn.clicked.connect(self.refresh_devices)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setMinimumSize(100, 45)
        self.connect_btn.clicked.connect(self.connect_device)
        self.connect_btn.setEnabled(False)
        
        btn_layout.addWidget(self.refresh_devices_btn)
        btn_layout.addWidget(self.connect_btn)
        
        conn_layout.addWidget(QLabel("BlueStacks Device:"))
        conn_layout.addWidget(self.device_combo)
        conn_layout.addLayout(btn_layout)
        conn_group.setLayout(conn_layout)
        
        return conn_group
    
    def create_control_group(self):
        """Create bot control group"""
        control_group = QGroupBox("🎮 Bot Control")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ START")
        self.start_btn.setMinimumSize(120, 60)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.start_btn.clicked.connect(self.start_bot)
        self.start_btn.setEnabled(False)
        
        self.pause_btn = QPushButton("⏸️ PAUSE")
        self.pause_btn.setMinimumSize(120, 60)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.pause_btn.clicked.connect(self.pause_bot)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹️ STOP")
        self.stop_btn.setMinimumSize(120, 60)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        
        return control_group
    
    def create_status_group(self):
        """Create status display group"""
        status_group = QGroupBox("📊 Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        
        self.current_task_label = QLabel("Current Task: None")
        self.current_task_label.setStyleSheet("font-size: 13px;")
        
        self.actions_label = QLabel("Actions: 0")
        self.actions_label.setStyleSheet("font-size: 13px;")
        
        self.uptime_label = QLabel("Uptime: 00:00:00")
        self.uptime_label.setStyleSheet("font-size: 13px;")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_task_label)
        status_layout.addWidget(self.actions_label)
        status_layout.addWidget(self.uptime_label)
        status_group.setLayout(status_layout)
        
        return status_group
    
    def create_tasks_group(self):
        """Create tasks configuration group"""
        tasks_group = QGroupBox("⚙️ Task Configuration")
        tasks_layout = QVBoxLayout()
        
        # Scroll area for tasks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        self.task_checkboxes: Dict[TaskType, QCheckBox] = {}
        
        # Basic tasks
        basic_label = QLabel("Basic Tasks:")
        basic_label.setStyleSheet("font-weight: bold; color: #2980b9;")
        scroll_layout.addWidget(basic_label)
        
        basic_tasks = [
            (TaskType.GATHER_RESOURCES, "Gather Resources"),
            (TaskType.TRAIN_TROOPS, "Train Troops"),
            (TaskType.UPGRADE_BUILDINGS, "Upgrade Buildings"),
            (TaskType.RESEARCH_TECH, "Research Technology"),
            (TaskType.HEAL_TROOPS, "Heal Troops"),
            (TaskType.ALLIANCE_HELP, "Alliance Help"),
            (TaskType.COLLECT_CHESTS, "Collect Chests"),
            (TaskType.DAILY_QUESTS, "Daily Quests"),
        ]
        
        for task_type, label in basic_tasks:
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.bot.enabled_tasks.get(task_type, False))
            checkbox.setStyleSheet("font-size: 12px;")
            checkbox.stateChanged.connect(
                lambda state, t=task_type: self.bot.set_task_enabled(t, state == Qt.Checked)
            )
            self.task_checkboxes[task_type] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll_layout.addSpacing(10)
        
        # Advanced tasks
        advanced_label = QLabel("Advanced Tasks:")
        advanced_label.setStyleSheet("font-weight: bold; color: #8e44ad;")
        scroll_layout.addWidget(advanced_label)
        
        advanced_tasks = [
            (TaskType.ATTACK_BARBARIANS, "Attack Barbarians"),
            (TaskType.NEW_PLAYER_TUTORIAL, "New Player Tutorial"),
            (TaskType.EXPLORE_FOG, "Explore Fog"),
            (TaskType.GATHER_GEMS, "Gather Gems"),
        ]
        
        for task_type, label in advanced_tasks:
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.bot.enabled_tasks.get(task_type, False))
            checkbox.setStyleSheet("font-size: 12px;")
            checkbox.stateChanged.connect(
                lambda state, t=task_type: self.bot.set_task_enabled(t, state == Qt.Checked)
            )
            self.task_checkboxes[task_type] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll_layout.addStretch()
        
        # Building upgrade config
        scroll_layout.addSpacing(15)
        building_label = QLabel("Building Settings:")
        building_label.setStyleSheet("font-weight: bold; color: #16a085;")
        scroll_layout.addWidget(building_label)
        
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Target Level:"))
        self.target_level_spin = QSpinBox()
        self.target_level_spin.setRange(1, 25)
        self.target_level_spin.setValue(self.bot.task_settings["buildings"]["target_level"])
        level_layout.addWidget(self.target_level_spin)
        scroll_layout.addLayout(level_layout)
        
        self.focus_th_check = QCheckBox("Focus on Town Hall")
        self.focus_th_check.setChecked(self.bot.task_settings["buildings"]["focus_town_hall"])
        scroll_layout.addWidget(self.focus_th_check)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        
        tasks_layout.addWidget(scroll)
        
        # Save button
        save_btn = QPushButton("💾 Save Configuration")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_task_settings)
        tasks_layout.addWidget(save_btn)
        
        tasks_group.setLayout(tasks_layout)
        return tasks_group
    
    def refresh_devices(self):
        """Refresh the list of available ADB devices using thread"""
        self.refresh_devices_btn.setEnabled(False)
        self.refresh_devices_btn.setText("⏳ Refreshing...")
        self.statusBar().showMessage("Connecting to ADB server...")
        
        self.adb_thread = ADBConnectionThread(self.bot.adb, "refresh_devices")
        self.adb_thread.devices_found.connect(self.on_devices_found)
        self.adb_thread.connection_result.connect(self.on_connection_result)
        self.adb_thread.finished.connect(lambda: self.refresh_devices_btn.setEnabled(True))
        self.adb_thread.start()
    
    def on_devices_found(self, devices):
        """Handle devices found signal"""
        self.device_combo.clear()
        for device in devices:
            self.device_combo.addItem(device.serial)
        
        if devices:
            self.connect_btn.setEnabled(True)
            self.statusBar().showMessage(f"Found {len(devices)} device(s)")
            logger.info(f"Found {len(devices)} BlueStacks device(s)")
        else:
            self.connect_btn.setEnabled(False)
            self.statusBar().showMessage("No devices found")
            logger.warning("No devices found. Is BlueStacks running with ADB enabled?")
        
        self.refresh_devices_btn.setText("🔄 Refresh")
    
    def on_connection_result(self, success, message):
        """Handle connection result signal"""
        if success:
            self.statusBar().showMessage(message)
            logger.info(message)
        else:
            self.statusBar().showMessage(message)
            logger.error(message)
            QMessageBox.warning(self, "Connection Error", message)
    
    def connect_device(self):
        """Connect to selected device using thread"""
        selected_serial = self.device_combo.currentText()
        if not selected_serial:
            QMessageBox.warning(self, "No Device", "Please select a device first")
            return
        
        # Check license validity first
        if not self.bot.check_license():
            QMessageBox.critical(self, "License Error", 
                               "Invalid or expired license! Please activate a valid license.")
            return
        
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("⏳ Connecting...")
        self.statusBar().showMessage("Connecting to device...")
        
        self.adb_thread = ADBConnectionThread(self.bot.adb, "select_device")
        self.adb_thread.device_serial = selected_serial
        self.adb_thread.connection_result.connect(self.on_device_connected)
        self.adb_thread.finished.connect(lambda: self.connect_btn.setEnabled(True))
        self.adb_thread.start()
    
    def on_device_connected(self, success, message):
        """Handle device connection result"""
        self.connect_btn.setText("🔌 Connect")
        
        if success:
            # Get screen resolution
            width, height = self.bot.adb.get_screen_resolution()
            self.bot.coord_mapper.set_current_resolution(width, height)
            logger.info(f"Screen resolution: {width}x{height}")
            
            # Start app if not running
            if not self.bot.adb.is_app_running():
                logger.info("Starting Rise of Kingdoms...")
                self.bot.adb.start_app()
            
            self.start_btn.setEnabled(True)
            self.status_label.setText("Status: Connected ✓")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
            self.statusBar().showMessage(message)
            logger.info("Bot ready to start!")
            QMessageBox.information(self, "Success", "Connected to BlueStacks successfully!")
        else:
            self.status_label.setText("Status: Connection Failed ✗")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
            self.statusBar().showMessage(message)
            QMessageBox.critical(self, "Error", message)
    
    def start_bot(self):
        """Start the bot execution"""
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Running")
        
        # Start bot in separate thread
        self.bot_thread = BotThread(self.bot)
        self.bot_thread.start()
        
        self.statusBar().showMessage("Bot execution started")
    
    def pause_bot(self):
        """Pause or resume bot execution"""
        if self.bot.paused:
            self.bot.resume()
            self.pause_btn.setText("⏸️ PAUSE")
            self.status_label.setText("Status: Running")
            self.statusBar().showMessage("Bot execution resumed")
        else:
            self.bot.pause()
            self.pause_btn.setText("▶️ RESUME")
            self.status_label.setText("Status: Paused")
            self.statusBar().showMessage("Bot execution paused")
    
    def stop_bot(self):
        """Stop the bot execution"""
        self.bot.stop()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
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
        # Update building settings
        self.bot.task_settings["buildings"]["target_level"] = self.target_level_spin.value()
        self.bot.task_settings["buildings"]["focus_town_hall"] = self.focus_th_check.isChecked()
        
        logger.info("Task configuration saved")
        QMessageBox.information(self, "Settings Saved", "Task configuration settings saved successfully!")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_viewer.clear_logs()
        self.statusBar().showMessage("Logs cleared")
    
    def save_logs(self):
        """Save logs to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Logs", "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_viewer.toPlainText())
                QMessageBox.information(self, "Success", f"Logs saved to {filename}")
                logger.info(f"Logs saved to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save logs: {e}")
    
    def update_status(self):
        """Update status labels periodically"""
        if self.bot.running:
            # Update current task
            if self.bot.current_task:
                task_name = self.bot.current_task.value.replace("_", " ").title()
                self.current_task_label.setText(f"Current Task: {task_name}")
            else:
                self.current_task_label.setText("Current Task: Idle")
            
            # Update action count
            total_actions = self.bot.logger.stats.total_actions
            self.actions_label.setText(f"Actions: {total_actions}")
            
            # Update uptime
            duration = self.bot.logger.get_session_duration()
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
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
                if self.update_timer:
                    self.update_timer.stop()
                event.accept()
            else:
                event.ignore()
        else:
            if self.gui_logger_handler:
                remove_gui_logging(self.gui_logger_handler)
            if self.update_timer:
                self.update_timer.stop()
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