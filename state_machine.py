"""
State Machine - Concrete task implementations for Rise of Kingdoms
"""
import time
import random
from typing import Optional, List, Dict, Tuple
from enum import Enum
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class GameState(Enum):
    """Game states enumeration"""
    UNKNOWN = "unknown"
    MAIN_MENU = "main_menu"
    CITY_VIEW = "city_view"
    WORLD_MAP = "world_map"
    BATTLE_SCREEN = "battle_screen"
    BUILDING_MENU = "building_menu"
    ALLIANCE_MENU = "alliance_menu"
    VIP_SHOP = "vip_shop"
    INBOX = "inbox"


class TaskType(Enum):
    """Available task types enumeration"""
    GATHER_RESOURCES = "gather_resources"
    TRAIN_TROOPS = "train_troops"
    UPGRADE_BUILDINGS = "upgrade_buildings"
    RESEARCH_TECH = "research_tech"
    ATTACK_BARBARIANS = "attack_barbarians"
    HEAL_TROOPS = "heal_troops"
    COLLECT_RESOURCES = "collect_resources"
    ALLIANCE_HELP = "alliance_help"
    DAILY_QUESTS = "daily_quests"
    COLLECT_CHESTS = "collect_chests"
    VIP_CHESTS = "vip_chests"
    FREE_CHESTS = "free_chests"
    NEW_PLAYER_TUTORIAL = "new_player_tutorial"
    EXPLORE_FOG = "explore_fog"
    GATHER_GEMS = "gather_gems"


class BaseTask:
    """Base class for all game tasks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.adb = bot.adb
        self.humanizer = bot.humanizer
        self.logger = bot.logger
        self.image_processor = bot.image_processor
    
    def execute(self) -> bool:
        """Execute the task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def find_and_tap(self, template: str, threshold: float = 0.8) -> bool:
        """Find template and tap it with human-like behavior"""
        screenshot = self.adb.get_screenshot()
        if not screenshot:
            logger.debug("Failed to get screenshot for template matching")
            return False
        
        result = self.image_processor.find_template(screenshot, template, threshold)
        if result:
            x, y, width, height = result
            tap_x, tap_y = self.humanizer.random_offset(x + width // 2, y + height // 2)
            self.adb.tap(tap_x, tap_y)
            self.humanizer.wait_human(0.5)
            logger.debug(f"Found and tapped template: {template}")
            return True
        
        logger.debug(f"Template not found: {template}")
        return False
    
    def wait_for_template(self, template: str, timeout: int = 10, threshold: float = 0.8) -> bool:
        """Wait for template to appear on screen"""
        start_time = time.time()
        check_interval = 0.5
        
        while time.time() - start_time < timeout:
            screenshot = self.adb.get_screenshot()
            if screenshot:
                result = self.image_processor.find_template(screenshot, template, threshold)
                if result:
                    logger.debug(f"Template appeared: {template}")
                    return True
            
            time.sleep(check_interval)
        
        logger.debug(f"Timeout waiting for template: {template}")
        return False


class ResourceGatheringTask(BaseTask):
    """Gather resources from the world map"""
    
    def __init__(self, bot, resource_type: str = "food", troop_count: int = 10000):
        super().__init__(bot)
        self.resource_type = resource_type
        self.troop_count = troop_count
        
        self.resource_templates = {
            "food": "templates/food_icon.png",
            "wood": "templates/wood_icon.png", 
            "stone": "templates/stone_icon.png",
            "gold": "templates/gold_icon.png"
        }
    
    def execute(self) -> bool:
        """Execute resource gathering task"""
        try:
            logger.info(f"Starting resource gathering: {self.resource_type}")
            
            # Navigate to world map
            if not self._navigate_to_map():
                logger.error("Failed to navigate to world map")
                return False
            
            # Search for resource node
            if not self._find_resource_node():
                logger.error(f"Failed to find {self.resource_type} resource node")
                return False
            
            # Send troops to gather
            if not self._send_gathering_troops():
                logger.error("Failed to send gathering troops")
                return False
            
            self.logger.log_gathering_trip(self.resource_type, 300)
            logger.info(f"Resource gathering completed: {self.resource_type}")
            return True
        
        except Exception as e:
            self.logger.log_error(f"Resource gathering failed for {self.resource_type}", e)
            return False
    
    def _navigate_to_map(self) -> bool:
        """Navigate to world map view"""
        if self.find_and_tap("templates/map_button.png"):
            self.humanizer.wait_human(2.0)
            return True
        return False
    
    def _find_resource_node(self) -> bool:
        """Find and select resource node on map"""
        logger.info(f"Searching for {self.resource_type} resource node...")
        
        # Use search feature to find resources
        if self.find_and_tap("templates/search_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Select specific resource type
            if self.resource_type in self.resource_templates:
                template_path = self.resource_templates[self.resource_type]
                if self.find_and_tap(template_path):
                    self.humanizer.wait_human(1.0)
                    
                    # Tap first available resource node
                    if self.find_and_tap("templates/resource_node.png"):
                        self.humanizer.wait_human(1.0)
                        return True
        
        return False
    
    def _send_gathering_troops(self) -> bool:
        """Send troops to gather resources"""
        # Tap gather button
        if self.find_and_tap("templates/gather_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Select commander
            if self.find_and_tap("templates/commander_slot.png"):
                self.humanizer.wait_human(0.5)
                
                # Confirm troop selection
                if self.find_and_tap("templates/confirm_button.png"):
                    self.humanizer.wait_human(2.0)
                    logger.info(f"Troops sent to gather {self.resource_type}")
                    return True
        
        return False


class TroopTrainingTask(BaseTask):
    """Train troops in barracks"""
    
    def __init__(self, bot, troop_type: str = "infantry", quantity: int = 100):
        super().__init__(bot)
        self.troop_type = troop_type
        self.quantity = quantity
        
        self.troop_templates = {
            "infantry": "templates/infantry_icon.png",
            "cavalry": "templates/cavalry_icon.png", 
            "archer": "templates/archer_icon.png",
            "siege": "templates/siege_icon.png"
        }
    
    def execute(self) -> bool:
        """Execute troop training task"""
        try:
            logger.info(f"Training {self.quantity} {self.troop_type} troops")
            
            # Find and access barracks
            if not self._find_barracks():
                logger.error("Failed to access barracks")
                return False
            
            # Select troop type
            if not self._select_troop_type():
                logger.error(f"Failed to select troop type: {self.troop_type}")
                return False
            
            # Train troops
            if not self._train_troops():
                logger.error("Failed to train troops")
                return False
            
            self.logger.log_troop_trained(self.troop_type, self.quantity)
            logger.info(f"Troop training completed: {self.quantity} {self.troop_type}")
            return True
        
        except Exception as e:
            self.logger.log_error(f"Troop training failed for {self.troop_type}", e)
            return False
    
    def _find_barracks(self) -> bool:
        """Find and access barracks building"""
        if self.find_and_tap("templates/barracks.png"):
            self.humanizer.wait_human(1.5)
            
            # Tap train button
            if self.find_and_tap("templates/train_button.png"):
                self.humanizer.wait_human(1.0)
                return True
        return False
    
    def _select_troop_type(self) -> bool:
        """Select specific troop type to train"""
        if self.troop_type in self.troop_templates:
            template_path = self.troop_templates[self.troop_type]
            if self.find_and_tap(template_path):
                self.humanizer.wait_human(0.8)
                return True
        return False
    
    def _train_troops(self) -> bool:
        """Input quantity and confirm training"""
        # Use max button for quick selection
        if self.find_and_tap("templates/max_button.png"):
            self.humanizer.wait_human(0.5)
            
            # Confirm training initiation
            if self.find_and_tap("templates/train_confirm_button.png"):
                self.humanizer.wait_human(1.0)
                logger.info(f"Started training {self.troop_type} troops")
                return True
        
        return False


class BuildingUpgradeTask(BaseTask):
    """Upgrade buildings in city"""
    
    def __init__(self, bot, building_name: Optional[str] = None):
        super().__init__(bot)
        self.building_name = building_name
    
    def execute(self) -> bool:
        """Execute building upgrade task"""
        try:
            logger.info("Starting building upgrade task")
            
            # Find upgradeable building
            if not self._find_upgradeable_building():
                logger.info("No buildings available for upgrade")
                return False
            
            # Perform upgrade
            if not self._upgrade_building():
                logger.error("Failed to upgrade building")
                return False
            
            self.logger.log_building_upgrade(self.building_name or "Unknown")
            logger.info("Building upgrade completed")
            return True
        
        except Exception as e:
            self.logger.log_error("Building upgrade failed", e)
            return False
    
    def _find_upgradeable_building(self) -> bool:
        """Find building that can be upgraded"""
        # Look for upgrade indicator
        if self.find_and_tap("templates/upgrade_indicator.png"):
            self.humanizer.wait_human(1.0)
            return True
        
        # Try recommended upgrades
        if self.find_and_tap("templates/recommended_button.png"):
            self.humanizer.wait_human(1.0)
            return True
        
        return False
    
    def _upgrade_building(self) -> bool:
        """Tap upgrade button and confirm action"""
        if self.find_and_tap("templates/upgrade_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Optional: Use speedup items (30% chance)
            if random.random() < 0.3:
                if self.find_and_tap("templates/use_speedup.png"):
                    self.humanizer.wait_human(0.5)
            
            logger.info("Building upgrade initiated successfully")
            return True
        
        return False


class ResearchTask(BaseTask):
    """Research technologies in academy"""
    
    def __init__(self, bot, research_name: Optional[str] = None):
        super().__init__(bot)
        self.research_name = research_name
    
    def execute(self) -> bool:
        """Execute research task"""
        try:
            logger.info("Starting research task")
            
            # Open academy building
            if not self._open_academy():
                logger.error("Failed to open academy")
                return False
            
            # Select research
            if not self._select_research():
                logger.error("Failed to select research")
                return False
            
            # Start research
            if not self._start_research():
                logger.error("Failed to start research")
                return False
            
            self.logger.log_research(self.research_name or "Unknown")
            logger.info("Research task completed")
            return True
        
        except Exception as e:
            self.logger.log_error("Research task failed", e)
            return False
    
    def _open_academy(self) -> bool:
        """Find and open academy building"""
        if self.find_and_tap("templates/academy.png"):
            self.humanizer.wait_human(1.5)
            return True
        return False
    
    def _select_research(self) -> bool:
        """Select research technology"""
        # Try recommended research first
        if self.find_and_tap("templates/recommended_research.png"):
            self.humanizer.wait_human(1.0)
            return True
        
        # Fallback to first available research
        if self.find_and_tap("templates/research_available.png"):
            self.humanizer.wait_human(1.0)
            return True
        
        return False
    
    def _start_research(self) -> bool:
        """Start the selected research"""
        if self.find_and_tap("templates/research_button.png"):
            self.humanizer.wait_human(1.0)
            logger.info("Research started successfully")
            return True
        return False


class BarbarianAttackTask(BaseTask):
    """Attack barbarian camps on world map"""
    
    def __init__(self, bot, barbarian_level: int = 1, attack_count: int = 5):
        super().__init__(bot)
        self.barbarian_level = barbarian_level
        self.attack_count = attack_count
    
    def execute(self) -> bool:
        """Execute barbarian attack task"""
        try:
            logger.info(f"Starting barbarian attack task (Level {self.barbarian_level})")
            
            attacks_completed = 0
            for attack_index in range(self.attack_count):
                logger.info(f"Barbarian attack {attack_index + 1}/{self.attack_count}")
                
                if self._attack_barbarian():
                    attacks_completed += 1
                    self.logger.log_barbarian_kill(self.barbarian_level)
                    self.humanizer.wait_human(5.0)  # Wait between attacks
                else:
                    logger.warning(f"Barbarian attack {attack_index + 1} failed")
                    break
                
                # Check for human-like breaks
                if self.humanizer.should_take_break():
                    self.humanizer.take_break()
            
            logger.info(f"Barbarian attacks completed: {attacks_completed}/{self.attack_count}")
            return attacks_completed > 0
        
        except Exception as e:
            self.logger.log_error("Barbarian attack task failed", e)
            return False
    
    def _attack_barbarian(self) -> bool:
        """Execute single barbarian attack"""
        # Navigate to world map
        if not self.find_and_tap("templates/map_button.png"):
            return False
        self.humanizer.wait_human(2.0)
        
        # Search for barbarians
        if self.find_and_tap("templates/search_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Select barbarian filter
            if self.find_and_tap("templates/barbarian_filter.png"):
                self.humanizer.wait_human(1.0)
                
                # Select barbarian level
                level_template = f"templates/barbarian_level_{self.barbarian_level}.png"
                if self.find_and_tap(level_template):
                    self.humanizer.wait_human(1.0)
                    
                    # Tap first barbarian camp
                    if self.find_and_tap("templates/barbarian_fort.png"):
                        self.humanizer.wait_human(1.0)
                        
                        # Send attack
                        return self._send_attack_troops()
        
        return False
    
    def _send_attack_troops(self) -> bool:
        """Send troops to attack barbarian"""
        if self.find_and_tap("templates/attack_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Select commanders
            if self.find_and_tap("templates/commander_slot_1.png"):
                self.humanizer.wait_human(0.5)
                
                if self.find_and_tap("templates/commander_slot_2.png"):
                    self.humanizer.wait_human(0.5)
                    
                    # Send march
                    if self.find_and_tap("templates/march_button.png"):
                        self.humanizer.wait_human(2.0)
                        logger.info("Attack troops sent to barbarian")
                        return True
        
        return False


class HealTroopsTask(BaseTask):
    """Heal wounded troops in hospital"""
    
    def execute(self) -> bool:
        """Execute troop healing task"""
        try:
            logger.info("Starting troop healing task")
            
            # Open hospital building
            if not self.find_and_tap("templates/hospital.png"):
                logger.info("Hospital building not found")
                return False
            
            self.humanizer.wait_human(1.5)
            
            # Heal all wounded troops
            if self.find_and_tap("templates/heal_all_button.png"):
                self.humanizer.wait_human(1.0)
                
                # Confirm healing
                if self.find_and_tap("templates/confirm_heal.png"):
                    self.humanizer.wait_human(1.0)
                    logger.info("Started healing wounded troops")
                    self.logger.log_action("Heal troops", True)
                    return True
            
            logger.info("No wounded troops to heal")
            return True  # Return True as no healing needed is not an error
        
        except Exception as e:
            self.logger.log_error("Troop healing task failed", e)
            return False


class AllianceHelpTask(BaseTask):
    """Help alliance members with constructions and research"""
    
    def execute(self) -> bool:
        """Execute alliance help task"""
        try:
            logger.info("Starting alliance help task")
            
            # Open alliance menu
            if not self.find_and_tap("templates/alliance_button.png"):
                return False
            
            self.humanizer.wait_human(1.5)
            
            # Provide alliance helps
            help_count = 0
            max_helps = 50  # Safety limit
            
            while self.find_and_tap("templates/help_all_button.png"):
                help_count += 1
                self.logger.log_alliance_help()
                self.humanizer.wait_human(0.5)
                
                if help_count >= max_helps:
                    logger.info(f"Reached maximum help limit: {max_helps}")
                    break
            
            logger.info(f"Provided {help_count} alliance helps")
            
            # Return to city view
            self.adb.press_back()
            return help_count > 0
        
        except Exception as e:
            self.logger.log_error("Alliance help task failed", e)
            return False


class CollectChestsTask(BaseTask):
    """Collect free and VIP chests"""
    
    def execute(self) -> bool:
        """Execute chest collection task"""
        try:
            logger.info("Starting chest collection task")
            
            chests_collected = 0
            
            # Collect free chest
            if self._collect_free_chest():
                chests_collected += 1
            
            # Collect VIP chest
            if self._collect_vip_chest():
                chests_collected += 1
            
            # Collect daily objectives chest
            if self._collect_daily_chest():
                chests_collected += 1
            
            logger.info(f"Chest collection completed: {chests_collected} chests collected")
            return chests_collected > 0
        
        except Exception as e:
            self.logger.log_error("Chest collection task failed", e)
            return False
    
    def _collect_free_chest(self) -> bool:
        """Collect free chest"""
        if self.find_and_tap("templates/free_chest.png"):
            self.humanizer.wait_human(2.0)
            
            if self.find_and_tap("templates/open_chest.png"):
                self.humanizer.wait_human(2.0)
                self.logger.log_chest_collected("Free")
                self.adb.press_back()  # Return from chest screen
                return True
        return False
    
    def _collect_vip_chest(self) -> bool:
        """Collect VIP chest"""
        if self.find_and_tap("templates/vip_chest.png"):
            self.humanizer.wait_human(2.0)
            
            if self.find_and_tap("templates/open_chest.png"):
                self.humanizer.wait_human(2.0)
                self.logger.log_chest_collected("VIP")
                self.adb.press_back()
                return True
        return False
    
    def _collect_daily_chest(self) -> bool:
        """Collect daily objectives chest"""
        if self.find_and_tap("templates/daily_objectives.png"):
            self.humanizer.wait_human(1.5)
            
            if self.find_and_tap("templates/claim_reward.png"):
                self.humanizer.wait_human(1.5)
                self.logger.log_chest_collected("Daily")
                self.adb.press_back()
                return True
        return False


class DailyQuestsTask(BaseTask):
    """Complete and collect daily quest rewards"""
    
    def execute(self) -> bool:
        """Execute daily quests collection task"""
        try:
            logger.info("Starting daily quests collection task")
            
            # Open quests menu
            if not self.find_and_tap("templates/quests_button.png"):
                return False
            
            self.humanizer.wait_human(1.5)
            
            # Collect available quest rewards
            quests_collected = 0
            max_quests = 20  # Safety limit
            
            while self.find_and_tap("templates/collect_quest.png"):
                quests_collected += 1
                self.logger.log_quest_completed(f"Quest {quests_collected}")
                self.humanizer.wait_human(0.8)
                
                if quests_collected >= max_quests:
                    logger.info(f"Reached maximum quest collection limit: {max_quests}")
                    break
            
            logger.info(f"Daily quests completed: {quests_collected} rewards collected")
            
            # Return to city view
            self.adb.press_back()
            return quests_collected > 0
        
        except Exception as e:
            self.logger.log_error("Daily quests task failed", e)
            return False


class NewPlayerTutorialTask(BaseTask):
    """Complete new player tutorial automatically"""
    
    def execute(self) -> bool:
        """Execute tutorial completion task"""
        try:
            logger.info("Starting new player tutorial task")
            
            # Check if tutorial is active
            if not self._is_tutorial_active():
                logger.info("No active tutorial found")
                return False
            
            # Follow tutorial prompts
            tutorial_steps = 0
            max_steps = 50  # Safety limit
            
            while tutorial_steps < max_steps:
                # Look for tutorial indicators
                if self.find_and_tap("templates/tutorial_arrow.png"):
                    tutorial_steps += 1
                    self.humanizer.wait_human(1.5)
                    logger.info(f"Tutorial step {tutorial_steps} completed")
                    
                elif self.find_and_tap("templates/tutorial_ok.png"):
                    self.humanizer.wait_human(1.0)
                    
                elif self.find_and_tap("templates/tutorial_next.png"):
                    self.humanizer.wait_human(1.0)
                    
                elif self.find_and_tap("templates/tutorial_claim.png"):
                    self.humanizer.wait_human(1.5)
                    tutorial_steps += 1
                    
                else:
                    # No more tutorial steps found
                    break
                
                # Check if should take break
                if self.humanizer.should_take_break():
                    self.humanizer.take_break()
            
            logger.info(f"Completed {tutorial_steps} tutorial steps")
            self.logger.log_action("New Player Tutorial", True, f"{tutorial_steps} steps")
            return True
        
        except Exception as e:
            self.logger.log_error("Tutorial task failed", e)
            return False
    
    def _is_tutorial_active(self) -> bool:
        """Check if tutorial is currently active"""
        screenshot = self.adb.get_screenshot()
        if not screenshot:
            return False
        
        # Look for tutorial indicators
        indicators = [
            "templates/tutorial_arrow.png",
            "templates/tutorial_finger.png",
            "templates/tutorial_highlight.png"
        ]
        
        for indicator in indicators:
            if self.image_processor.find_template(screenshot, indicator, 0.7):
                return True
        
        return False


class ExploreFogTask(BaseTask):
    """Explore fog of war on the map"""
    
    def execute(self) -> bool:
        """Execute fog exploration task"""
        try:
            logger.info("Starting fog exploration task")
            
            # Navigate to map
            if not self.find_and_tap("templates/map_button.png"):
                return False
            
            self.humanizer.wait_human(2.0)
            
            # Send scouts to explore fog
            scouts_sent = 0
            max_scouts = 3
            
            for scout_index in range(max_scouts):
                if self._send_scout_to_fog():
                    scouts_sent += 1
                    logger.info(f"Scout {scouts_sent}/{max_scouts} sent to explore")
                    self.humanizer.wait_human(2.0)
                else:
                    break
            
            logger.info(f"Sent {scouts_sent} scouts to explore fog")
            self.logger.log_action("Explore Fog", True, f"{scouts_sent} scouts sent")
            
            # Return to city
            self.adb.press_back()
            return scouts_sent > 0
        
        except Exception as e:
            self.logger.log_error("Fog exploration task failed", e)
            return False
    
    def _send_scout_to_fog(self) -> bool:
        """Send a single scout to explore fog"""
        # Look for fog areas on map
        if self.find_and_tap("templates/fog_area.png"):
            self.humanizer.wait_human(1.0)
            
            # Tap scout button
            if self.find_and_tap("templates/scout_button.png"):
                self.humanizer.wait_human(1.0)
                
                # Select commander
                if self.find_and_tap("templates/commander_slot.png"):
                    self.humanizer.wait_human(0.5)
                    
                    # Confirm scout
                    if self.find_and_tap("templates/confirm_button.png"):
                        return True
        
        return False


class GatherGemsTask(BaseTask):
    """Gather gems from gem deposits"""
    
    def execute(self) -> bool:
        """Execute gem gathering task"""
        try:
            logger.info("Starting gem gathering task")
            
            # Navigate to map
            if not self.find_and_tap("templates/map_button.png"):
                return False
            
            self.humanizer.wait_human(2.0)
            
            # Search for gem deposits
            if not self._find_gem_deposit():
                logger.info("No gem deposits found nearby")
                self.adb.press_back()
                return False
            
            # Send troops to gather
            if not self._send_gathering_troops():
                self.adb.press_back()
                return False
            
            logger.info("Successfully sent troops to gather gems")
            self.logger.log_action("Gather Gems", True, "Troops sent")
            self.logger.log_gathering_trip("gems", 180)
            
            return True
        
        except Exception as e:
            self.logger.log_error("Gem gathering task failed", e)
            return False
    
    def _find_gem_deposit(self) -> bool:
        """Find gem deposit on map"""
        logger.info("Searching for gem deposits...")
        
        # Use search feature
        if self.find_and_tap("templates/search_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Select gem filter
            if self.find_and_tap("templates/gem_icon.png"):
                self.humanizer.wait_human(1.0)
                
                # Tap first available gem deposit
                if self.find_and_tap("templates/gem_deposit.png"):
                    self.humanizer.wait_human(1.0)
                    return True
        
        return False
    
    def _send_gathering_troops(self) -> bool:
        """Send troops to gather gems"""
        # Tap gather button
        if self.find_and_tap("templates/gather_button.png"):
            self.humanizer.wait_human(1.0)
            
            # Select commander
            if self.find_and_tap("templates/commander_slot.png"):
                self.humanizer.wait_human(0.5)
                
                # Confirm selection
                if self.find_and_tap("templates/confirm_button.png"):
                    self.humanizer.wait_human(1.5)
                    return True
        
        return False


class BuildingUpgradeTaskEnhanced(BuildingUpgradeTask):
    """Enhanced building upgrade with level targeting"""
    
    def __init__(self, bot, target_level: int = 25, focus_town_hall: bool = True):
        super().__init__(bot)
        self.target_level = target_level
        self.focus_town_hall = focus_town_hall
    
    def execute(self) -> bool:
        """Execute building upgrade with level targeting"""
        try:
            logger.info(f"Building upgrade task (target level: {self.target_level})")
            
            # Check current town hall level
            current_th_level = self._get_town_hall_level()
            
            if current_th_level >= self.target_level:
                logger.info(f"Target level {self.target_level} reached")
                return False
            
            # If focusing on town hall, upgrade it first
            if self.focus_town_hall:
                if self._upgrade_town_hall():
                    return True
            
            # Otherwise upgrade any available building
            if not self._find_upgradeable_building():
                logger.info("No buildings available for upgrade")
                return False
            
            if not self._upgrade_building():
                return False
            
            self.logger.log_building_upgrade(self.building_name or "Unknown")
            return True
        
        except Exception as e:
            self.logger.log_error("Building upgrade task failed", e)
            return False
    
    def _get_town_hall_level(self) -> int:
        """Get current town hall level"""
        try:
            # Tap town hall
            if self.find_and_tap("templates/town_hall.png"):
                self.humanizer.wait_human(1.0)
                
                # Read level from screen (requires OCR or template matching)
                # For now, return 1 as placeholder
                # TODO: Implement level detection
                
                self.adb.press_back()
                return 1
        except Exception:
            return 1
    
    def _upgrade_town_hall(self) -> bool:
        """Specifically upgrade town hall"""
        logger.info("Attempting to upgrade Town Hall")
        
        if self.find_and_tap("templates/town_hall.png"):
            self.humanizer.wait_human(1.5)
            
            if self.find_and_tap("templates/upgrade_button.png"):
                self.humanizer.wait_human(1.0)
                logger.info("Town Hall upgrade initiated")
                self.building_name = "Town Hall"
                return True
            
            self.adb.press_back()
        
        return False