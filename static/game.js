$(document).ready(function() {
    const RACES = ["Human", "Elf", "Dwarf", "Dragonborn", "Orc", "Tiefling", 
                   "Monk", "Berserker", "Shapeshifter", 
                   "Deep One Warlock", "Mad Oracle"];
    const PROFESSIONS = ["Warrior", "Mage", "Druid", "Rogue (Assassin)", "Ranger", "Warlock"];
    const BACKGROUNDS = ["Exiled Noble", "Cursed One", "Banished Scholar", "Merchant", "Chosen One", "Mercenary"];
    const STYLES = ["Clash of Kingdoms", "Ancient Ruins", "Cosmic Horror", "Lighthearted Fantasy Adventure"];

    let gameState = {
        race: '',
        profession: '',
        background: '',
        style: ''
    };

    function showCharacterCreation() {
        $('#game-board').html(`
            <div class="character-creation">
                <h2>Create Your Character</h2>
                <div class="selection-group">
                    <label>Choose Race:</label>
                    <select id="race-select">
                        ${RACES.map(race => `<option value="${race}">${race}</option>`).join('')}
                    </select>
                </div>
                <div class="selection-group">
                    <label>Choose Profession:</label>
                    <select id="profession-select">
                        ${PROFESSIONS.map(prof => `<option value="${prof}">${prof}</option>`).join('')}
                    </select>
                </div>
                <div class="selection-group">
                    <label>Choose Background:</label>
                    <select id="background-select">
                        ${BACKGROUNDS.map(bg => `<option value="${bg}">${bg}</option>`).join('')}
                    </select>
                </div>
                <div class="selection-group">
                    <label>Choose Game Style:</label>
                    <select id="style-select">
                        ${STYLES.map(style => `<option value="${style}">${style}</option>`).join('')}
                    </select>
                </div>
                <button id="create-character">Begin Adventure</button>
            </div>
        `);
    }

    $('#start-game').click(function() {
        console.log('Starting game');
        showCharacterCreation();
    });

    $(document).on('click', '#create-character', function() {
        console.log('Creating character');
        gameState.race = $('#race-select').val();
        gameState.profession = $('#profession-select').val();
        gameState.background = $('#background-select').val();
        gameState.style = $('#style-select').val();

        console.log('Game state:', gameState);

        $.ajax({
            url: '/start_game',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(gameState),
            success: function(response) {
                console.log('Game start response:', response);
                if(response.status === 'success') {
                    showGameInterface(response);
                }
            },
            error: function(xhr, status, error) {
                console.error('Game start error:', error);
                showError('Unable to start game. Please try again.');
            }
        });
    });

    function showGameInterface(data) {
        $('#game-board').html(`
            <div id="game-content">
                <div id="story-area">
                    <div class="story-text">${data.story_intro}</div>
                    <div class="task-text">${data.player_task}</div>
                </div>
                <div id="game-history"></div>
                <div id="action-area"></div>
            </div>
        `);

        if(data.next_state === 'BRANCH') {
            makeMove({ type: 'branch' });
        } else {
            handleGameState(data.next_state);
        }
    }

    function handleGameState(state) {
        console.log('Handling state:', state);
        if(state === 'STORY') {
            makeMove({ type: 'story' });
        } else if(state === 'BRANCH') {
            makeMove({ type: 'branch' });
        } else if(state === 'END') {
            makeMove({ type: 'end' });
        }
    }

    function makeMove(data) {
        console.log('Making move:', data);
        $('.option-btn').prop('disabled', true);

        const requestData = {
            type: data.type,
            choice: data.choice || ''
        };

        $.ajax({
            url: '/make_move',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requestData),
            success: function(response) {
                console.log('Move response:', response);
                if(response.status === 'success') {
                    if(response.story) {
                        showStory(response);
                    }
                    if(response.intro && response.options) {
                        showBranchOptions(response);
                    }
                    if(response.ending) {
                        showGameEnd(response.ending);
                        return;
                    }

                    $('.option-btn').prop('disabled', false);

                    if(response.next_state) {
                        setTimeout(() => {
                            if(response.next_state !== 'BRANCH') {
                                handleGameState(response.next_state);
                            }
                        }, 1000);
                    }
                }
            },
            error: function(xhr, status, error) {
                console.error('Move execution error:', error);
                showError('Operation failed, please try again: ' + error);
                $('.option-btn').prop('disabled', false);
            }
        });
    }

    function showBranchOptions(data) {
        console.log('Showing options:', data);
        if(!data.intro || !data.options) {
            console.error('Invalid branch data');
            showError('Unable to load options');
            return;
        }

        $('#action-area').empty().html(`
            <div class="branch-options">
                <div class="branch-intro">${data.intro}</div>
                <div class="options-list">
                    ${data.options.map((option, index) => 
                        `<button class="option-btn" data-choice="${encodeURIComponent(option)}">${option}</button>`
                    ).join('')}
                </div>
            </div>
        `);

        $('.option-btn').off('click').on('click', function() {
            const choice = decodeURIComponent($(this).data('choice'));
            console.log('Selected option:', choice);
            makeChoice(choice);
        });
    }

    function makeChoice(choice) {
        console.log('Making choice:', choice);
        $('.option-btn').prop('disabled', true);

        $('#game-history').append(`
            <div class="player-choice">You chose: ${choice}</div>
        `);

        makeMove({
            type: 'branch',
            choice: choice
        });
    }

    function showStory(data) {
        if(data.story) {
            $('#game-history').append(`
                <div class="story-segment">${data.story}</div>
            `);
            $('#game-history').scrollTop($('#game-history')[0].scrollHeight);
        }
    }

    function showGameEnd(ending) {
        $('#game-board').html(`
            <div class="game-end">
                <h2>Adventure Complete</h2>
                <div class="ending-text">${ending || ''}</div>
                <button id="restart-game" class="medieval-btn">Start New Adventure</button>
            </div>
        `);

        $('#restart-game').click(function() {
            location.reload();
        });
    }

    function showError(message) {
        $('#action-area').append(`
            <div class="error-message">
                ${message}
                <button class="medieval-btn" onclick="location.reload()">Restart</button>
            </div>
        `);
    }
});