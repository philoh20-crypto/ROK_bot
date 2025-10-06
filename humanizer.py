"""
Humanizer - Adds human-like behavior patterns to bot actions
"""
import time
import random
import numpy as np
from typing import Tuple, List, Callable, Optional
from faker import Faker
import logging

logger = logging.getLogger(__name__)
fake = Faker()


class HumanBehavior:
    """Simulate human-like interaction patterns and timing."""
    
    def __init__(self):
        self.last_action_time = time.time()
        self.action_count = 0
        self.session_start = time.time()
        
        # Human timing parameters (in seconds)
        self.min_action_delay = 0.3
        self.max_action_delay = 1.5
        self.fatigue_factor = 0.0
        
        # Break patterns
        self.actions_before_break = random.randint(50, 100)
        self.break_duration_range = (30, 120)  # seconds
        self.break_probability = 0.01  # 1% chance per action after threshold

    def human_delay(self, base_delay: float = 1.0, variance: float = 0.3) -> float:
        """
        Calculate human-like delay with Gaussian distribution.
        """
        # Gaussian randomness, bounded within limits
        delay = np.random.normal(base_delay, base_delay * variance)
        delay = max(self.min_action_delay, min(self.max_action_delay, delay))

        # Add fatigue effect (slows actions over time)
        delay += self.fatigue_factor * 0.5
        return delay

    def wait_human(self, base_delay: float = 1.0, variance: float = 0.3):
        """
        Wait with human-like timing patterns.
        """
        delay = self.human_delay(base_delay, variance)
        time.sleep(delay)
        
        self.action_count += 1
        self.last_action_time = time.time()

        # Fatigue increases gradually with session length
        session_duration = time.time() - self.session_start
        self.fatigue_factor = min(2.0, session_duration / 3600)  # Max 2x slower after 1 hour

    def should_take_break(self) -> bool:
        """Determine if bot should take a human-like break."""
        if self.action_count >= self.actions_before_break:
            logger.info("Taking scheduled human-like break...")
            return True
        
        if self.action_count > 30 and random.random() < self.break_probability:
            logger.info("Taking random spontaneous break...")
            return True
        
        return False

    def take_break(self):
        """Take a break for a random duration and reset counters."""
        duration = random.uniform(*self.break_duration_range)
        logger.info(f"Taking break for {duration:.1f} seconds")
        time.sleep(duration)
        
        # Reset session counters
        self.action_count = 0
        self.actions_before_break = random.randint(50, 100)
        self.fatigue_factor = 0.0
        logger.debug("Break completed, counters reset.")

    def random_offset(self, x: int, y: int, max_radius: int = 5) -> Tuple[int, int]:
        """
        Add small random offset to coordinates to simulate imperfect human clicking.
        """
        return (x + random.randint(-max_radius, max_radius),
                y + random.randint(-max_radius, max_radius))

    def bezier_curve(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        num_points: int = 20
    ) -> List[Tuple[int, int]]:
        """
        Generate Bezier curve path for human-like movement.
        """
        ctrl1_x = start[0] + random.randint(-50, 50)
        ctrl1_y = start[1] + random.randint(-50, 50)
        ctrl2_x = end[0] + random.randint(-50, 50)
        ctrl2_y = end[1] + random.randint(-50, 50)
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            x = ((1 - t)**3 * start[0] +
                 3 * (1 - t)**2 * t * ctrl1_x +
                 3 * (1 - t) * t**2 * ctrl2_x +
                 t**3 * end[0])
            y = ((1 - t)**3 * start[1] +
                 3 * (1 - t)**2 * t * ctrl1_y +
                 3 * (1 - t) * t**2 * ctrl2_y +
                 t**3 * end[1])
            points.append((int(x), int(y)))
        
        logger.debug(f"Generated Bezier curve with {len(points)} points.")
        return points

    def human_swipe(
        self,
        swipe_func: Callable,
        start: Tuple[int, int],
        end: Tuple[int, int],
        base_duration: int = 500
    ):
        """
        Perform human-like swipe using Bezier curve and natural timing.
        """
        start = self.random_offset(*start, max_radius=10)
        end = self.random_offset(*end, max_radius=10)
        duration = int(base_duration * random.uniform(0.8, 1.2))
        
        swipe_func(*start, *end, duration)
        self.wait_human(0.5, 0.2)

    def random_idle_action(self, tap_func: Callable, screen_size: Tuple[int, int]):
        """
        Perform random idle actions to mimic human unpredictability.
        """
        actions = [
            lambda: self._random_tap(tap_func, screen_size),
            lambda: self._random_swipe(tap_func, screen_size),
            lambda: time.sleep(random.uniform(1, 3))
        ]
        random.choice(actions)()
        logger.debug("Performed random idle action.")

    def _random_tap(self, tap_func: Callable, screen_size: Tuple[int, int]):
        """Perform a random tap within safe screen bounds."""
        margin = 100
        x = random.randint(margin, screen_size[0] - margin)
        y = random.randint(margin, screen_size[1] - margin)
        tap_func(x, y)
        logger.debug(f"Random tap at ({x}, {y}).")

    def _random_swipe(self, swipe_func: Callable, screen_size: Tuple[int, int]):
        """Perform a random swipe within safe bounds."""
        margin = 200
        x1 = random.randint(margin, screen_size[0] - margin)
        y1 = random.randint(margin, screen_size[1] - margin)
        x2 = max(margin, min(screen_size[0] - margin, x1 + random.randint(-200, 200)))
        y2 = max(margin, min(screen_size[1] - margin, y1 + random.randint(-200, 200)))
        
        swipe_func(x1, y1, x2, y2)
        logger.debug(f"Random swipe from ({x1}, {y1}) to ({x2}, {y2}).")


class RandomNameGenerator:
    """Generate random names for accounts, alliances, and cities."""
    
    @staticmethod
    def generate_username(style: str = "mixed") -> str:
        """Generate a random username in the given style."""
        if style == "fantasy":
            prefixes = ["Dark", "Shadow", "Storm", "Iron", "Blood", "Fire", "Ice", "Dragon"]
            suffixes = ["Slayer", "Hunter", "Warrior", "Lord", "King", "Knight", "Mage", "Rider"]
            return f"{random.choice(prefixes)}{random.choice(suffixes)}{random.randint(1, 999)}"
        
        if style == "military":
            ranks = ["General", "Captain", "Major", "Colonel", "Commander", "Marshal"]
            name = fake.last_name()
            return f"{random.choice(ranks)}{name}{random.randint(1, 99)}"
        
        if style == "modern":
            return f"{fake.user_name()}{random.randint(1, 9999)}"
        
        # Mixed: pick one style randomly
        return RandomNameGenerator.generate_username(random.choice(["fantasy", "military", "modern"]))

    @staticmethod
    def generate_alliance_name() -> str:
        """Generate a random alliance name."""
        prefixes = [
            "The", "Order of", "Kingdom of", "Empire of", "Legion of",
            "Brotherhood of", "Alliance of", "Union of"
        ]
        themes = [
            "Dragons", "Phoenix", "Titans", "Legends", "Heroes",
            "Warriors", "Knights", "Immortals", "Conquerors", "Champions"
        ]
        return f"{random.choice(prefixes)} {random.choice(themes)}"

    @staticmethod
    def generate_city_name() -> str:
        """Generate a random city name."""
        return fake.city().replace(" ", "") + str(random.randint(1, 999))


class SessionRandomizer:
    """Randomize session lengths and task order to avoid detection."""
    
    def __init__(self):
        self.session_duration = random.uniform(1800, 7200)  # 30 min – 2 hr
        self.session_start = time.time()
        self.min_session_duration = 1200  # 20 min minimum

    def should_end_session(self) -> bool:
        """Determine if session should end based on time and randomness."""
        elapsed = time.time() - self.session_start

        if elapsed >= self.session_duration:
            logger.info("Session duration completed.")
            return True
        
        if elapsed > self.min_session_duration and random.random() < 0.05:
            logger.info("Random early session end.")
            return True
        
        return False

    def get_next_session_delay(self) -> float:
        """Return random delay before next session (seconds)."""
        return random.uniform(600, 7200)  # 10 min – 2 hr

    def randomize_task_order(self, tasks: List[str]) -> List[str]:
        """Shuffle task execution order."""
        tasks_copy = tasks.copy()
        random.shuffle(tasks_copy)
        logger.debug(f"Randomized task order: {tasks_copy}")
        return tasks_copy

    def should_skip_task(self, skip_probability: float = 0.1) -> bool:
        """Randomly skip tasks to mimic human inconsistency."""
        should_skip = random.random() < skip_probability
        if should_skip:
            logger.debug("Randomly skipping task.")
        return should_skip


class TypingSimulator:
    """Simulate human typing with delays and typos."""
    
    @staticmethod
    def typing_delay() -> float:
        """Return realistic typing delay between keystrokes."""
        return random.uniform(0.15, 0.35)

    @staticmethod
    def add_typos(text: str, error_rate: float = 0.05) -> str:
        """Add realistic typing mistakes to text."""
        if error_rate <= 0:
            return text
            
        result = []
        for char in text:
            if random.random() < error_rate:
                if random.random() < 0.5:
                    result.extend([char, char])  # Double press
                else:
                    result.append(random.choice('abcdefghijklmnopqrstuvwxyz'))
            else:
                result.append(char)
        return ''.join(result)

    @staticmethod
    def simulate_typing(text: str, callback: Callable[[str], None], error_rate: float = 0.02):
        """Simulate typing text with realistic timing and mistakes."""
        text_with_errors = TypingSimulator.add_typos(text, error_rate)
        
        for char in text_with_errors:
            callback(char)
            time.sleep(TypingSimulator.typing_delay())
