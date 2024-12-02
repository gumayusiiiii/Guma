import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI(api_key=os.getenv('API_KEY'), base_url=os.getenv('BASE_URL'))

def generate_game_start(info):
    try:
        prompt = f"""
        As a creative DND game master, craft an engaging opening story and quest.

        Character Info:
        - Race: {info['race']}
        - Class: {info['profession']}
        - Background: {info['background']}
        - Game Style: {info['style']}

        Provide:
        1. Opening Description (200-250 words):
           - Vividly introduce character and situation
           - Create unique world atmosphere and environment
           - Hint at potential conflicts and crises
           - Include sensory details and emotional elements
           - Reflect character's unique background

        2. Initial Quest (80-100 words):
           - Connect closely with character background
           - Provide clear and compelling motivation
           - Hint at larger conflicts and future developments
           - Include challenging and dramatic elements
           - Reflect game style characteristics

        Format:
        - Split with "Quest:"
        - Maintain narrative coherence
        - Emphasize dramatic conflict
        """

        logger.debug("Sending game start request")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a storyteller skilled in creating dramatic tension and emotional resonance."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",
            temperature=0.8
        )

        story = response.choices[0].message.content
        parts = story.split("Quest:") if "Quest:" in story else [story, "Embark on this unknown adventure and discover your destiny."]
        return parts[0].strip(), parts[1].strip()
    except Exception as e:
        logger.error(f"Error generating game start: {str(e)}")
        return "Your adventure begins...", "Explore this unknown world"

def generate_story(context, story_requirements=None):
    try:
        if story_requirements is None:
            story_requirements = {}

        prompt = f"""
        Continue this gripping narrative.

        Context:
        {context}

        Story Phase: {story_requirements.get('current_phase', 'STORY')}
        Branch Depth: {story_requirements.get('branch_depth', 0)}
        Choices Made: {story_requirements.get('choices_made', 0)}

        Requirements:
        1. Create a dramatic scene (200-250 words)
        2. Include:
           - Vivid environmental descriptions
           - Character's internal thoughts
           - Engaging plot developments
           - Emotional turns or escalating conflicts
           - References to previous choices
        3. Maintain tight narrative pacing
        4. Set up the next choice point
        5. Add sensory details for immersion
        """

        return client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a game master focused on creating dramatic tension and emotional depth."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",
            stream=True,
            temperature=0.8
        )
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        return None

def generate_branch_options(context, story_requirements=None):
    try:
        if story_requirements is None:
            story_requirements = {}

        prompt = f"""
        Generate a dramatic scene setup and 4 thought-provoking options.

        Context:
        {context}

        Story Phase: {story_requirements.get('current_phase', 'BRANCH')}
        Branch Depth: {story_requirements.get('branch_depth', 0)}
        Choices Made: {story_requirements.get('choices_made', 0)}

        Format response as:
        [3-4 tension-filled sentences describing the scene, highlighting current predicament and risks]
        1. [Action option with consequences - 30-40 words hinting at potential impacts]
        2. [Action option with consequences - 30-40 words hinting at potential impacts]
        3. [Action option with consequences - 30-40 words hinting at potential impacts]
        4. [Action option with consequences - 30-40 words hinting at potential impacts]

        Each option must:
        - Begin with a strong action verb
        - Include potential consequences and impacts
        - Reflect character's background and abilities
        - Create dramatic tension
        - Present different approaches (combat, stealth, diplomacy, magic, etc.)
        - Connect to previous choices
        - Include emotional or strategic stakes

        Example option format:
        "Infiltrate the back alley, using your knowledge of thieves' signs to avoid guard patrols that might raise the alarm. This could reveal unexpected allies, but might also lead you into an ambush."
        """

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a game master focused on creating deep and dramatic choices."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()
        parts = content.split("\n")

        if len(parts) < 5:
            logger.warning("Insufficient options generated, using defaults")
            return (
                "Tension rises as you face a crucial decision...",
                "Scout the surroundings carefully, seeking signs of danger that might reveal critical information. Your caution could uncover hidden opportunities, but might cost precious time.",
                "Charge forward with weapons ready, your bold action could rally allies but might also alert enemies. Time is of the essence, choose wisely.",
                "Search for an alternative path, using your experience to find hidden opportunities. This might avoid direct conflict but could demand unexpected sacrifices.",
                "Observe the situation patiently, gathering intelligence that might provide tactical advantages. This could expose enemy weaknesses but gives them time to prepare."
            )

        intro = parts[0]
        choices = []
        for part in parts[1:]:
            if ". " in part:
                choice = part.split(". ", 1)[1]
                choices.append(choice)

        while len(choices) < 4:
            default_choices = [
                "Analyze the situation thoroughly using your expertise, seeking overlooked advantages. This requires time but might reveal decisive opportunities.",
                "Take a calculated risk that could turn the tide. Success would bring great advantage, while failure might lead to deeper crisis.",
                "Draw upon your unique background to find an unexpected solution. This might open new paths but could expose your identity.",
                "Trust your instincts and adapt to changing circumstances. Flexibility might create miracles, but lack of preparation carries its own risks."
            ]
            choices.extend(default_choices[len(choices):])
        choices = choices[:4]

        return intro, *choices

    except Exception as e:
        logger.error(f"Error generating branch options: {str(e)}")
        return (
            "A critical moment demands your decision...",
            "Carefully analyze the situation, seeking tactical advantages you might exploit. Your professional intuition could reveal a breakthrough.",
            "Take decisive action, knowing your choice will have lasting consequences. Time is short, but actions need careful consideration.",
            "Seek an alternative approach that plays to your unique abilities. Perhaps there's an unexpected solution waiting to be found.",
            "Prepare yourself to adapt as circumstances change. Staying alert might help you seize fleeting opportunities."
        )

def generate_end(context):
    try:
        logger.debug("Generating ending")
        prompt = f"""
        Create a satisfying and depth-filled ending.

        Context:
        {context}

        Requirements:
        1. Write a complete ending (300-400 words):
           - Summarize key choices and their impacts
           - Resolve major conflicts
           - Provide emotional satisfaction
           - Match story tone
           - Create sense of closure
           - Reflect character growth or change
           - Hint at future possibilities
           - Echo opening themes
        """

        return client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a storyteller skilled in creating endings with depth and emotional resonance."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",
            stream=True
        )
    except Exception as e:
        logger.error(f"Error generating ending: {str(e)}")
        return None

def judge_story_step(context):
    try:
        logger.debug("Judging next story step")
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an experienced DND game master"},
                {"role": "user", "content": f"Based on the current context, answer only 'End' or 'Continue':\n{context}"}
            ],
            model="gpt-4"
        )
        result = response.choices[0].message.content.strip()
        logger.debug(f"Story step judgment: {result}")
        return result
    except Exception as e:
        logger.error(f"Error judging story step: {str(e)}")
        return "Continue"