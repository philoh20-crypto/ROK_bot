"""
State Machine - Concrete task implementations for Rise of Kingdoms
"""

import time
import random
import logging
from enum import Enum
from typing import Optional, Dict, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


# ==============================
# ENUM DEFINITIONS
# ==============================

class GameState(Enum):
    """Enumerates possible game states."""
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
    """Enumerates all available task types."""
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


# ==============================
# BASE TASK CLASS
# ==============================

class BaseTask:
    """Base class for all game tasks."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.adb = bot.adb
        self.humanizer = bot.humanizer
        self.logger = bot.logger
        self.image_processor = bot.image_processor

    def execute(self) -> bool:
        """Execute the task (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement the execute() method.")

    def find_and_tap(self, template: str, threshold: float = 0.8) -> bool:
        """Find a template and tap it using human-like behavior."""
        screenshot = self.adb.get_screenshot()
        if not screenshot:
            logger.debug(f"[BaseTask] Failed to get screenshot while searching for '{template}'")
            return False

        result = self.image_processor.find_template(screenshot, template, threshold)
        if not result:
            logger.debug(f"[BaseTask] Template not found: {template}")
            return False

        x, y, width, height = result
        tap_x, tap_y = self.humanizer.random_offset(x + width // 2, y + height // 2)
        self.adb.tap(tap_x, tap_y)
        self.humanizer.wait_human(0.5)
        logger.debug(f"[BaseTask] Found and tapped template: {template}")
        return True

    def wait_for_template(self, template: str, timeout: int = 10, threshold: float = 0.8) -> bool:
        """Wait for a template to appear within a timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            screenshot = self.adb.get_screenshot()
            if screenshot and self.image_processor.find_template(screenshot, template, threshold):
                logger.debug(f"[BaseTask] Template appeared: {template}")
                return True
            time.sleep(0.5)
        logger.debug(f"[BaseTask] Timeout waiting for template: {template}")
        return False


# ==============================
# RESOURCE GATHERING
# ==============================

class ResourceGatheringTask(BaseTask):
    """Task to gather resources from the world map."""

    def __init__(self, bot, resource_type: str = "food", troop_count: int = 10000) -> None:
        super().__init__(bot)
        self.resource_type = resource_type
        self.troop_count = troop_count
        self.resource_templates: Dict[str, str] = {
            "food": "templates/food_icon.png",
            "wood": "templates/wood_icon.png",
            "stone": "templates/stone_icon.png",
            "gold": "templates/gold_icon.png",
        }

    def execute(self) -> bool:
        """Perform the resource gathering routine."""
        try:
            logger.info(f"[ResourceGatheringTask] Starting resource gathering: {self.resource_type}")

            if not self._navigate_to_map():
                logger.error("[ResourceGatheringTask] Failed to navigate to world map.")
                return False

            if not self._find_resource_node():
                logger.error(f"[ResourceGatheringTask] Failed to find {self.resource_type} resource node.")
                return False

            if not self._send_gathering_troops():
                logger.error("[ResourceGatheringTask] Failed to send gathering troops.")
                return False

            self.logger.log_gathering_trip(self.resource_type, 300)
            logger.info(f"[ResourceGatheringTask] Resource gathering completed: {self.resource_type}")
            return True

        except Exception as e:
            self.logger.log_error(f"Resource gathering failed for {self.resource_type}", e)
            return False

    def _navigate_to_map(self) -> bool:
        """Navigate to the world map view."""
        if self.find_and_tap("templates/map_button.png"):
            self.humanizer.wait_human(2.0)
            return True
        return False

    def _find_resource_node(self) -> bool:
        """Find and select a resource node."""
        logger.info(f"[ResourceGatheringTask] Searching for {self.resource_type} resource node...")
        if not self.find_and_tap("templates/search_button.png"):
            return False

        self.humanizer.wait_human(1.0)
        template = self.resource_templates.get(self.resource_type)
        if not template:
            logger.warning(f"[ResourceGatheringTask] Unknown resource type: {self.resource_type}")
            return False

        if not self.find_and_tap(template):
            return False

        self.humanizer.wait_human(1.0)
        return self.find_and_tap("templates/resource_node.png")

    def _send_gathering_troops(self) -> bool:
        """Send troops to gather the selected resource."""
        if not self.find_and_tap("templates/gather_button.png"):
            return False

        self.humanizer.wait_human(1.0)

        if not self.find_and_tap("templates/commander_slot.png"):
            return False

        self.humanizer.wait_human(0.5)
        if not self.find_and_tap("templates/confirm_button.png"):
            return False

        self.humanizer.wait_human(2.0)
        logger.info(f"[ResourceGatheringTask] Troops sent to gather {self.resource_type}")
        return True


# ==============================
# TROOP TRAINING
# ==============================

class TroopTrainingTask(BaseTask):
    """Task to train troops in the barracks."""

    def __init__(self, bot, troop_type: str = "infantry", quantity: int = 100) -> None:
        super().__init__(bot)
        self.troop_type = troop_type
        self.quantity = quantity
        self.troop_templates: Dict[str, str] = {
            "infantry": "templates/infantry_icon.png",
            "cavalry": "templates/cavalry_icon.png",
            "archer": "templates/archer_icon.png",
            "siege": "templates/siege_icon.png",
        }

    def execute(self) -> bool:
        """Perform troop training."""
        try:
            logger.info(f"[TroopTrainingTask] Training {self.quantity} {self.troop_type} troops")

            if not self._find_barracks():
                logger.error("[TroopTrainingTask] Failed to access barracks.")
                return False

            if not self._select_troop_type():
                logger.error(f"[TroopTrainingTask] Failed to select troop type: {self.troop_type}")
                return False

            if not self._train_troops():
                logger.error("[TroopTrainingTask] Failed to train troops.")
                return False

            self.logger.log_troop_trained(self.troop_type, self.quantity)
            logger.info(f"[TroopTrainingTask] Troop training completed: {self.quantity} {self.troop_type}")
            return True

        except Exception as e:
            self.logger.log_error(f"Troop training failed for {self.troop_type}", e)
            return False

    def _find_barracks(self) -> bool:
        """Locate and open the barracks."""
        if not self.find_and_tap("templates/barracks.png"):
            return False
        self.humanizer.wait_human(1.5)
        return self.find_and_tap("templates/train_button.png")

    def _select_troop_type(self) -> bool:
        """Select the troop type to train."""
        template = self.troop_templates.get(self.troop_type)
        return bool(template and self.find_and_tap(template))

    def _train_troops(self) -> bool:
        """Train the selected troop type."""
        if not self.find_and_tap("templates/max_button.png"):
            return False
        self.humanizer.wait_human(0.5)
        return self.find_and_tap("templates/train_confirm_button.png")


# ==============================
# BUILDING UPGRADE
# ==============================

class BuildingUpgradeTask(BaseTask):
    """Task to upgrade buildings in the city."""

    def __init__(self, bot, building_name: Optional[str] = None) -> None:
        super().__init__(bot)
        self.building_name = building_name

    def execute(self) -> bool:
        """Perform a building upgrade."""
        try:
            logger.info("[BuildingUpgradeTask] Starting building upgrade task")

            if not self._find_upgradeable_building():
                logger.info("[BuildingUpgradeTask] No buildings available for upgrade.")
                return False

            if not self._upgrade_building():
                logger.error("[BuildingUpgradeTask] Failed to upgrade building.")
                return False

            self.logger.log_building_upgrade(self.building_name or "Unknown")
            logger.info("[BuildingUpgradeTask] Building upgrade completed.")
            return True

        except Exception as e:
            self.logger.log_error("Building upgrade failed", e)
            return False

    def _find_upgradeable_building(self) -> bool:
        """Find a building ready for upgrade."""
        return self.find_and_tap("templates/upgrade_indicator.png") or \
               self.find_and_tap("templates/recommended_button.png")

    def _upgrade_building(self) -> bool:
        """Tap the upgrade button and confirm."""
        if not self.find_and_tap("templates/upgrade_button.png"):
            return False

        self.humanizer.wait_human(1.0)
        if random.random() < 0.3 and self.find_and_tap("templates/use_speedup.png"):
            self.humanizer.wait_human(0.5)

        logger.info("[BuildingUpgradeTask] Building upgrade initiated successfully.")
        return True


# ==============================
# RESEARCH
# ==============================

class ResearchTask(BaseTask):
    """Research technologies in academy."""

    def __init__(self, bot, research_name: Optional[str] = None) -> None:
        super().__init__(bot)
        self.research_name = research_name

    def execute(self) -> bool:
        """Execute research task."""
        try:
            logger.info("[ResearchTask] Starting research task")

            if not self._open_academy():
                logger.error("[ResearchTask] Failed to open academy")
                return False

            if not self._select_research():
                logger.error("[ResearchTask] Failed to select research")
                return False

            if not self._start_research():
                logger.error("[ResearchTask] Failed to start research")
                return False

            self.logger.log_research(self.research_name or "Unknown")
            logger.info("[ResearchTask] Research task completed")
            return True

        except Exception as e:
            self.logger.log_error("Research task failed", e)
            return False

    def _open_academy(self) -> bool:
        """Find and open academy building."""
        if self.find_and_tap("templates/academy.png"):
            self.humanizer.wait_human(1.5)
            return True
        return False

    def _select_research(self) -> bool:
        """Select research technology."""
        if self.find_and_tap("templates/recommended_research.png"):
            self.humanizer.wait_human(1.0)
            return True

        if self.find_and_tap("templates/research_available.png"):
            self.humanizer.wait_human(1.0)
            return True

        return False

    def _start_research(self) -> bool:
        """Start the selected research."""
        if self.find_and_tap("templates/research_button.png"):
            self.humanizer.wait_human(1.0)
            logger.info("[ResearchTask] Research started successfully")
            return True
        return False


# ==============================
# BARBARIAN ATTACK
# ==============================

class BarbarianAttackTask(BaseTask):
    """Attack barbarian camps on world map."""

    def __init__(self, bot, barbarian_level: int = 1, attack_count: int = 5) -> None:
        super().__init__(bot)
        self.barbarian_level = barbarian_level
        self.attack_count = attack_count

    def execute(self) -> bool:
        """Execute barbarian attack task."""
        try:
            logger.info(f"[BarbarianAttackTask] Starting barbarian attack task (Level {self.barbarian_level})")

            attacks_completed = 0
            for attack_index in range(self.attack_count):
                logger.info(f"[BarbarianAttackTask] Barbarian attack {attack_index + 1}/{self.attack_count}")

                if self._attack_barbarian():
                    attacks_completed += 1
                    self.logger.log_barbarian_kill(self.barbarian_level)
                    self.humanizer.wait_human(5.0)  # Wait between attacks
                else:
                    logger.warning(f"[BarbarianAttackTask] Barbarian attack {attack_index + 1} failed")
                    break

                if self.humanizer.should_take_break():
                    self.humanizer.take_break()

            logger.info(f"[BarbarianAttackTask] Barbarian attacks completed: {attacks_completed}/{self.attack_count}")
            return attacks_completed > 0

        except Exception as e:
            self.logger.log_error("Barbarian attack task failed", e)
            return False

    def _attack_barbarian(self) -> bool:
        """Execute single barbarian attack."""
        if not self.find_and_tap("templates/map_button.png"):
            return False
        self.humanizer.wait_human(2.0)

        if not self.find_and_tap("templates/search_button.png"):
            return False
        self.humanizer.wait_human(1.0)

        if not self.find_and_tap("templates/barbarian_filter.png"):
            return False
        self.humanizer.wait_human(1.0)

        level_template = f"templates/barbarian_level_{self.barbarian_level}.png"
        if not self.find_and_tap(level_template):
            return False
        self.humanizer.wait_human(1.0)

        if not self.find_and_tap("templates/barbarian_fort.png"):
            return False
        self.humanizer.wait_human(1.0)

        return self._send_attack_troops()

    def _send_attack_troops(self) -> bool:
        """Send troops to attack barbarian."""
        if not self.find_and_tap("templates/attack_button.png"):
            return False
        self.humanizer.wait_human(1.0)

        if not self.find_and_tap("templates/commander_slot_1.png"):
            return False
        self.humanizer.wait_human(0.5)

        if not self.find_and_tap("templates/commander_slot_2.png"):
            return False
        self.humanizer.wait_human(0.5)

        if not self.find_and_tap("templates/march_button.png"):
            return False
        self.humanizer.wait_human(2.0)

        logger.info("[BarbarianAttackTask] Attack troops sent to barbarian")
        return True


# ==============================
# HEAL TROOPS
# ==============================

class HealTroopsTask(BaseTask):
    """Heal wounded troops in hospital."""

    def execute(self) -> bool:
        """Execute troop healing task."""
        try:
            logger.info("[HealTroopsTask] Starting troop healing task")

            if not self.find_and_tap("templates/hospital.png"):
                logger.info("[HealTroopsTask] Hospital building not found")
                return False

            self.humanizer.wait_human(1.5)

            if self.find_and_tap("templates/heal_all_button.png"):
                self.humanizer.wait_human(1.0)
                if self.find_and_tap("templates/confirm_heal.png"):
                    self.humanizer.wait_human(1.0)
                    logger.info("[HealTroopsTask] Started healing wounded troops")
                    self.logger.log_action("Heal troops", True)
                    return True

            logger.info("[HealTroopsTask] No wounded troops to heal")
            return True  # No healing needed is not an error

        except Exception as e:
            self.logger.log_error("Troop healing task failed", e)
            return False


# ==============================
# ALLIANCE HELP
# ==============================

class AllianceHelpTask(BaseTask):
    """Help alliance members with constructions and research."""

    def execute(self) -> bool:
        """Execute alliance help task."""
        try:
            logger.info("[AllianceHelpTask] Starting alliance help task")

            if not self.find_and_tap("templates/alliance_button.png"):
                return False

            self.humanizer.wait_human(1.5)

            help_count = 0
            max_helps = 50  # Safety limit

            while self.find_and_tap("templates/help_all_button.png"):
                help_count += 1
                self.logger.log_alliance_help()
                self.humanizer.wait_human(0.5)

                if help_count >= max_helps:
                    logger.info(f"[AllianceHelpTask] Reached maximum help limit: {max_helps}")
                    break

            logger.info(f"[AllianceHelpTask] Provided {help_count} alliance helps")
            self.adb.press_back()
            return help_count > 0

        except Exception as e:
            self.logger.log_error("Alliance help task failed", e)
            return False


# ==============================
# CHEST COLLECTION
# ==============================

class CollectChestsTask(BaseTask):
    """Collect free and VIP chests."""

    def execute(self) -> bool:
        """Execute chest collection task."""
        try:
            logger.info("[CollectChestsTask] Starting chest collection task")

            chests_collected = 0

            if self._collect_free_chest():
                chests_collected += 1

            if self._collect_vip_chest():
                chests_collected += 1

            if self._collect_daily_chest():
                chests_collected += 1

            logger.info(f"[CollectChestsTask] Chest collection completed: {chests_collected} chests collected")
            return chests_collected > 0

        except Exception as e:
            self.logger.log_error("Chest collection task failed", e)
            return False

    def _collect_free_chest(self) -> bool:
        """Collect free chest."""
        if not self.find_and_tap("templates/free_chest.png"):
            return False

        self.humanizer.wait_human(2.0)
        if not self.find_and_tap("templates/open_chest.png"):
            return False

        self.humanizer.wait_human(2.0)
        self.logger.log_chest_collected("Free")
        self.adb.press_back()
        return True

    def _collect_vip_chest(self) -> bool:
        """Collect VIP chest."""
        if not self.find_and_tap("templates/vip_chest.png"):
            return False

        self.humanizer.wait_human(2.0)
        if not self.find_and_tap("templates/open_chest.png"):
            return False

        self.humanizer.wait_human(2.0)
        self.logger.log_chest_collected("VIP")
        self.adb.press_back()
        return True

    def _collect_daily_chest(self) -> bool:
        """Collect daily objectives chest."""
        if not self.find_and_tap("templates/daily_objectives.png"):
            return False

        self.humanizer.wait_human(1.5)
        if not self.find_and_tap("templates/claim_reward.png"):
            return False

        self.humanizer.wait_human(1.5)
        self.logger.log_chest_collected("Daily")
        self.adb.press_back()
        return True


# ==============================
# DAILY QUESTS
# ==============================

class DailyQuestsTask(BaseTask):
    """Complete and collect daily quest rewards."""

    def execute(self) -> bool:
        """Execute daily quests collection task."""
        try:
            logger.info("[DailyQuestsTask] Starting daily quests collection task")

            if not self.find_and_tap("templates/quests_button.png"):
                return False

            self.humanizer.wait_human(1.5)

            quests_collected = 0
            max_quests = 20  # Safety limit

            while self.find_and_tap("templates/collect_quest.png"):
                quests_collected += 1
                self.logger.log_quest_completed(f"Quest {quests_collected}")
                self.humanizer.wait_human(0.8)

                if quests_collected >= max_quests:
                    logger.info(f"[DailyQuestsTask] Reached maximum quest collection limit: {max_quests}")
                    break

            logger.info(f"[DailyQuestsTask] Daily quests completed: {quests_collected} rewards collected")
            self.adb.press_back()
            return quests_collected > 0

        except Exception as e:
            self.logger.log_error("Daily quests task failed", e)
            return False
