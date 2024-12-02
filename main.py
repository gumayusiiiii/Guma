from flask import Flask, render_template, request, jsonify
import enum
from api.api import generate_game_start, judge_story_step, generate_branch_options, generate_story, generate_end
from rag.rag_handler import Database

app = Flask(__name__)

class State(enum.Enum):
    START = 0
    STORY = 1
    BRANCH = 2
    END = 3

class Game:
    def __init__(self):
        self.sm = State.START
        self.db = Database()
        self.style = ""
        self.background = ""
        self.story_intro = ""
        self.player_task = ""
        self.branch_depth = 0
        self.choices_made = 0

    def format_branch_option(self, option_text):
        if ". " in option_text:
            parts = option_text.split(". ", 1)
            if parts[0].isdigit():
                return parts[1]
        return option_text

    def handle_branch_options(self, raw_options):
        options = []
        for opt in raw_options:
            if ". " in opt:
                main_parts = opt.split(". 1.")
                if len(main_parts) > 1:
                    options.append(self.format_branch_option(main_parts[0]))
                else:
                    options.append(self.format_branch_option(opt))
            else:
                options.append(opt)
        return options[:4]

    def judge_next_step(self):
        MAX_BRANCH_DEPTH = 3
        MAX_CHOICES = 5

        if self.choices_made >= MAX_CHOICES:
            return "End"

        if self.branch_depth >= MAX_BRANCH_DEPTH:
            self.branch_depth = 0
            return "Progress"

        if self.sm == State.START:
            return "Branch"
        elif self.sm == State.STORY:
            return "Branch"
        else:
            return "Progress"

game = Game()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.json
    game.sm = State.START
    game.branch_depth = 0
    game.choices_made = 0

    game.race = data.get('race')
    game.profession = data.get('profession')
    game.background = data.get('background')
    game.style = data.get('style')

    if game.style == "Clash of Kingdoms":
        game.style = "Clash of Kingdoms; Features: Focuses on strategy, intrigue, and interpersonal interaction..."
    elif game.style == "Ancient Ruins":
        game.style = "Ancient Ruins; Features: Classic adventure style..."
    elif game.style == "Cosmic Horror":
        game.style = "Cosmic Horror; Features: Emphasizes fear of the unknown..."
    elif game.style == "Lighthearted Fantasy Adventure":
        game.style = "Lighthearted Fantasy Adventure; Features: Lighthearted and fun..."

    game.info = {
        "race": game.race,
        "profession": game.profession,
        "background": game.background,
        "style": game.style
    }

    game.story_intro, game.player_task = generate_game_start(game.info)

    game.db.set_race(game.race)
    game.db.set_profession(game.profession)
    game.db.set_style(game.style)
    game.db.set_background(game.background)
    game.db.set_intro(game.story_intro)
    game.db.set_task(game.player_task)

    next_step = game.judge_next_step()
    if next_step == "Progress":
        game.sm = State.STORY
    elif next_step == "Branch":
        game.sm = State.BRANCH
    elif next_step == "End":
        game.sm = State.END

    return jsonify({
        'status': 'success',
        'story_intro': game.story_intro,
        'player_task': game.player_task,
        'next_state': game.sm.name
    })

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.json
    current_state = game.sm
    response_data = {'status': 'success'}

    try:
        if current_state == State.BRANCH:
            game.branch_depth += 1
            game.choices_made += 1

            # 记录玩家选择
            player_choice = data.get('choice', '')
            if player_choice:
                game.db.set_current_choice(player_choice)  # 设置当前选择
                game.db.append_log(f"Player choice: {player_choice}")

            # 首先生成基于选择的故事段落
            if player_choice:
                story_stream = generate_story(game.db.get_context())
                story_text = ""
                if story_stream:
                    for chunk in story_stream:
                        if hasattr(chunk.choices[0].delta, 'content'):
                            story_text += chunk.choices[0].delta.content or ""

                if story_text:
                    game.db.append_story_segment(story_text)
                    response_data['story'] = story_text

            # 然后生成新的分支选项
            intro, *options = generate_branch_options(game.db.get_context())
            options = game.handle_branch_options(options)

            while len(options) < 4:
                options.append("Continue exploring")

            game.db.append_log(f"Branch choices: {', '.join(options)}")

            response_data.update({
                'intro': intro,
                'options': options
            })

        elif current_state == State.STORY:
            story_stream = generate_story(game.db.get_context())
            story_text = ""

            if story_stream:
                for chunk in story_stream:
                    if hasattr(chunk.choices[0].delta, 'content'):
                        story_text += chunk.choices[0].delta.content or ""

            if story_text:
                game.db.append_story_segment(story_text)
                game.db.append_log(f"Story segment: {story_text}")
                response_data.update({
                    'story': story_text
                })

        elif current_state == State.END:
            end_stream = generate_end(game.db.get_context())
            end_text = ""

            if end_stream:
                for chunk in end_stream:
                    if hasattr(chunk.choices[0].delta, 'content'):
                        end_text += chunk.choices[0].delta.content or ""

            if end_text:
                game.db.append_story_segment(end_text)
                game.db.append_log(f"Ending: {end_text}")
                game.db.save_data()

            game.branch_depth = 0
            game.choices_made = 0
            game.sm = State.START

            response_data.update({
                'ending': end_text
            })

        next_step = game.judge_next_step()
        if next_step == "Progress":
            game.sm = State.STORY
        elif next_step == "Branch":
            game.sm = State.BRANCH
        elif next_step == "End":
            game.sm = State.END

        response_data['next_state'] = game.sm.name
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in make_move: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)