import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.race = ""
        self.profession = ""
        self.style = ""
        self.background = ""
        self.intro = ""
        self.task = ""
        self.log = []
        self.current_choice = ""
        self.story_segments = []
        self.story_phase = "OPENING"

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.saves_dir = os.path.join(self.base_dir, 'saves')
        if not os.path.exists(self.saves_dir):
            try:
                os.makedirs(self.saves_dir)
                logger.info(f"Created saves directory at {self.saves_dir}")
            except Exception as e:
                logger.error(f"Failed to create saves directory: {e}")

    def set_race(self, race):
        self.race = race
        logger.debug(f"Set race to: {race}")

    def set_profession(self, profession):
        self.profession = profession
        logger.debug(f"Set profession to: {profession}")

    def set_style(self, style):
        self.style = style
        logger.debug(f"Set style to: {style}")

    def set_background(self, background):
        self.background = background
        logger.debug(f"Set background to: {background}")

    def set_intro(self, intro):
        self.intro = intro
        logger.debug("Story introduction set")

    def set_task(self, task):
        self.task = task
        logger.debug("Main quest task set")

    def set_current_choice(self, choice):
        self.current_choice = choice
        logger.debug(f"Current choice set to: {choice}")

    def set_story_phase(self, phase):
        self.story_phase = phase
        logger.debug(f"Story phase set to: {phase}")

    def append_log(self, text):
        self.log.append(text)
        logger.debug(f"Added to log: {text}")

    def append_story_segment(self, segment):
        if segment and segment.strip():
            self.story_segments.append(segment.strip())
            logger.debug("New story segment added")

    def get_context(self):
        recent_story = "\n".join(self.story_segments[-5:]) if self.story_segments else ""
        recent_logs = "\n".join(self.log[-3:]) if self.log else ""

        context = f"""
Character Information:
Race: {self.race}
Class: {self.profession}
Background: {self.background}
Story Style: {self.style}

Story Introduction:
{self.intro}

Main Quest:
{self.task}

Current Story Phase: {self.story_phase}

Recent Story Progress:
{recent_story}

Recent Actions:
{recent_logs}

Current Choice: {self.current_choice}
"""
        logger.debug("Context generated successfully")
        return context.strip()

    def save_data(self):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            data = {
                "race": self.race,
                "profession": self.profession,
                "style": self.style,
                "background": self.background,
                "intro": self.intro,
                "task": self.task,
                "story_phase": self.story_phase,
                "log": self.log,
                "story_segments": self.story_segments,
                "current_choice": self.current_choice,
                "timestamp": timestamp
            }

            filename = os.path.join(self.saves_dir, f"game_{timestamp}.json")

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            logger.info(f"Game saved successfully to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return False

    def load_data(self, filename):
        try:
            filepath = os.path.join(self.saves_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.race = data.get('race', '')
            self.profession = data.get('profession', '')
            self.style = data.get('style', '')
            self.background = data.get('background', '')
            self.intro = data.get('intro', '')
            self.task = data.get('task', '')
            self.story_phase = data.get('story_phase', 'OPENING')
            self.log = data.get('log', [])
            self.story_segments = data.get('story_segments', [])
            self.current_choice = data.get('current_choice', '')

            logger.info(f"Game loaded successfully from {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return False