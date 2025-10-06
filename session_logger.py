"""
Session Logger - Track bot activities, statistics, and generate reports
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from colorlog import ColoredFormatter


class BotStatistics:
    """Track and manage bot performance statistics."""

    def __init__(self):
        self.session_start = datetime.now()
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0

        # Task-specific counters
        self.resources_gathered = {"food": 0, "wood": 0, "stone": 0, "gold": 0}
        self.troops_trained = {"infantry": 0, "cavalry": 0, "archer": 0, "siege": 0}
        self.buildings_upgraded = 0
        self.researches_started = 0
        self.barbarians_killed = 0
        self.gathering_trips = 0
        self.alliance_helps = 0
        self.daily_quests_completed = 0
        self.chests_collected = 0

        # Error tracking
        self.errors: list[Dict[str, Any]] = []
        self.warnings: list[Dict[str, Any]] = []


class SessionLogger:
    """Comprehensive logging and statistics tracking for bot activities."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.stats = BotStatistics()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Setup file logging paths
        self.log_file = self.log_dir / f"session_{self.session_id}.log"
        self.stats_file = self.log_dir / f"stats_{self.session_id}.json"

        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Session logger initialized with ID: {self.session_id}")

    def _setup_logging(self) -> None:
        """Setup colored console logging and file logging."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Console handler with color
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)-8s - %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    # ----------------------------
    # Logging Methods
    # ----------------------------

    def log_action(self, action: str, success: bool = True, details: str = "") -> None:
        """Log a bot action with success/failure status."""
        self.stats.total_actions += 1

        if success:
            self.stats.successful_actions += 1
            self.logger.info(f"✓ {action} - {details}")
        else:
            self.stats.failed_actions += 1
            self.logger.warning(f"✗ {action} failed - {details}")

    def log_resource_gathered(self, resource_type: str, amount: int) -> None:
        """Log resource gathering activity."""
        if resource_type in self.stats.resources_gathered:
            self.stats.resources_gathered[resource_type] += amount
            self.logger.info(f"Gathered {amount:,} {resource_type}")
        else:
            self.logger.warning(f"Unknown resource type: {resource_type}")

    def log_troop_trained(self, troop_type: str, count: int) -> None:
        """Log troop training activity."""
        if troop_type in self.stats.troops_trained:
            self.stats.troops_trained[troop_type] += count
            self.logger.info(f"Trained {count:,} {troop_type} troops")
        else:
            self.logger.warning(f"Unknown troop type: {troop_type}")

    def log_building_upgrade(self, building_name: str, level: Optional[int] = None) -> None:
        """Log building upgrade with optional level information."""
        self.stats.buildings_upgraded += 1
        level_info = f" to level {level}" if level else ""
        self.logger.info(f"Upgraded {building_name}{level_info}")

    def log_research(self, research_name: str) -> None:
        """Log research initiation."""
        self.stats.researches_started += 1
        self.logger.info(f"Research started: {research_name}")

    def log_barbarian_kill(self, level: int) -> None:
        """Log barbarian defeat."""
        self.stats.barbarians_killed += 1
        self.logger.info(f"Defeated barbarian level {level}")

    def log_gathering_trip(self, resource: str, duration: int) -> None:
        """Log gathering trip completion."""
        self.stats.gathering_trips += 1
        self.logger.info(f"Gathering trip completed: {resource} (Duration: {duration}s)")

    def log_alliance_help(self) -> None:
        """Log alliance help provided."""
        self.stats.alliance_helps += 1
        self.logger.debug("Alliance help provided")

    def log_chest_collected(self, chest_type: str) -> None:
        """Log chest collection."""
        self.stats.chests_collected += 1
        self.logger.info(f"Collected {chest_type} chest")

    def log_quest_completed(self, quest_name: str) -> None:
        """Log quest completion."""
        self.stats.daily_quests_completed += 1
        self.logger.info(f"Quest completed: {quest_name}")

    def log_error(self, error_msg: str, exception: Optional[Exception] = None) -> None:
        """Log error with optional exception details."""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "message": error_msg,
            "exception_type": type(exception).__name__ if exception else None,
            "exception_details": str(exception) if exception else None,
        }
        self.stats.errors.append(error_data)

        if exception:
            self.logger.error(f"{error_msg}: {exception}")
        else:
            self.logger.error(error_msg)

    def log_warning(self, warning_msg: str) -> None:
        """Log warning message."""
        warning_data = {"timestamp": datetime.now().isoformat(), "message": warning_msg}
        self.stats.warnings.append(warning_data)
        self.logger.warning(warning_msg)

    # ----------------------------
    # Statistics Methods
    # ----------------------------

    def get_session_duration(self) -> timedelta:
        """Get current session duration."""
        return datetime.now() - self.stats.session_start

    def get_success_rate(self) -> float:
        """Calculate action success rate percentage."""
        total = self.stats.total_actions
        return (self.stats.successful_actions / total * 100.0) if total else 0.0

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get comprehensive statistics summary."""
        duration = self.get_session_duration()
        success_rate = self.get_success_rate()

        return {
            "session_id": self.session_id,
            "session_start": self.stats.session_start.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration).split(".")[0],
            "total_actions": self.stats.total_actions,
            "successful_actions": self.stats.successful_actions,
            "failed_actions": self.stats.failed_actions,
            "success_rate": round(success_rate, 2),
            "success_rate_formatted": f"{success_rate:.2f}%",
            "resources_gathered": self.stats.resources_gathered.copy(),
            "troops_trained": self.stats.troops_trained.copy(),
            "buildings_upgraded": self.stats.buildings_upgraded,
            "researches_started": self.stats.researches_started,
            "barbarians_killed": self.stats.barbarians_killed,
            "gathering_trips": self.stats.gathering_trips,
            "alliance_helps": self.stats.alliance_helps,
            "daily_quests_completed": self.stats.daily_quests_completed,
            "chests_collected": self.stats.chests_collected,
            "total_errors": len(self.stats.errors),
            "total_warnings": len(self.stats.warnings),
        }

    def save_statistics(self) -> None:
        """Save statistics to JSON file."""
        try:
            summary = self.get_statistics_summary()
            summary["errors"] = self.stats.errors
            summary["warnings"] = self.stats.warnings

            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Statistics saved to {self.stats_file}")
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")

    # ----------------------------
    # Output & Export
    # ----------------------------

    def print_summary(self) -> None:
        """Print formatted session summary to console."""
        summary = self.get_statistics_summary()

        print("\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Session ID: {summary['session_id']}")
        print(f"Duration: {summary['duration_formatted']}")
        print(f"Total Actions: {summary['total_actions']:,}")
        print(f"Success Rate: {summary['success_rate_formatted']}")

        print("\nResources Gathered:")
        for res, amt in summary["resources_gathered"].items():
            if amt > 0:
                print(f"  {res.capitalize():<8}: {amt:>10,}")

        print("\nTroops Trained:")
        for troop, count in summary["troops_trained"].items():
            if count > 0:
                print(f"  {troop.capitalize():<8}: {count:>10,}")

        print("\nOther Activities:")
        activities = [
            ("Buildings Upgraded", summary["buildings_upgraded"]),
            ("Researches Started", summary["researches_started"]),
            ("Barbarians Killed", summary["barbarians_killed"]),
            ("Gathering Trips", summary["gathering_trips"]),
            ("Alliance Helps", summary["alliance_helps"]),
            ("Daily Quests", summary["daily_quests_completed"]),
            ("Chests Collected", summary["chests_collected"]),
        ]
        for name, count in activities:
            if count > 0:
                print(f"  {name:<20}: {count:>8,}")

        print("\nIssues:")
        print(f"  Errors: {summary['total_errors']:>8,}")
        print(f"  Warnings: {summary['total_warnings']:>6,}")
        print("=" * 60 + "\n")

    def export_to_excel(self, filename: Optional[str] = None) -> bool:
        """Export statistics to Excel file with multiple sheets."""
        if filename is None:
            filename = self.log_dir / f"report_{self.session_id}.xlsx"

        try:
            with pd.ExcelWriter(filename, engine="openpyxl") as writer:
                summary_data = self.get_statistics_summary()
                flat_summary = {
                    k: v for k, v in summary_data.items() if not isinstance(v, dict)
                }

                pd.DataFrame([flat_summary]).to_excel(writer, sheet_name="Summary", index=False)
                pd.DataFrame(
                    list(summary_data["resources_gathered"].items()),
                    columns=["Resource", "Amount"],
                ).to_excel(writer, sheet_name="Resources", index=False)

                pd.DataFrame(
                    list(summary_data["troops_trained"].items()),
                    columns=["Troop Type", "Count"],
                ).to_excel(writer, sheet_name="Troops", index=False)

                if self.stats.errors:
                    pd.DataFrame(self.stats.errors).to_excel(writer, sheet_name="Errors", index=False)
                if self.stats.warnings:
                    pd.DataFrame(self.stats.warnings).to_excel(writer, sheet_name="Warnings", index=False)

            self.logger.info(f"Excel report exported to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export to Excel: {e}")
            return False

    # ----------------------------
    # Cleanup
    # ----------------------------

    def close(self) -> None:
        """Close logger and save final statistics."""
        self.save_statistics()
        self.print_summary()
        self.logger.info("Session logger closed successfully")

        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
