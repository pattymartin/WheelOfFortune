# Wheel of Fortune

This project is a GUI used to host a game of Wheel of Fortune at home.

- [Getting Started](#getting-started)
- [Beginning a Game](#beginning-a-game)
  - [Application Windows](#application-windows)
  - [Creating a Game](#creating-a-game)
  - [Selecting Puzzles](#selecting-puzzles)
  - [Creating Puzzles](#creating-puzzles)
  - [Changing Settings](#changing-settings)
  - [Changing Hotkeys](#changing-hotkeys)
  - [Setting Player Names](#setting-player-names)
- [Gameplay](#gameplay)
  - [Standard Round](#standard-round)
  - [Toss-Up Round](#toss-up-round)
  - [Mystery Round](#mystery-round)
  - [Express Round](#express-round)
  - [Triple Toss-Up](#triple-toss-up)
  - [Speed-Up Round](#speed-up-round)
  - [Final Spin](#final-spin)
  - [Bonus Round](#bonus-round)
- [Acknowledgments](#acknowledgments)

## Getting Started

To make use of this application, you will need your own wheel for your
contestants to spin, and your own puzzles for the contestants to guess.

This project is created with:
* Python 3.7.4
* Kivy 1.11.1 ([Installation instructions](
  https://kivy.org/doc/stable/gettingstarted/installation.html))

With Python and Kivy installed, the application can be launched simply by
running `manager.py` in Python. This must be run from the project's root
directory (the same directory that contains `manager.py`).

## Beginning a Game

### Application Windows

<img align="right" width="50%" src="https://i.imgur.com/pOJ4w3y.gif">

The app opens in 6 separate windows, so that they can be placed on different
screens if desired:

1. Manager Window
2. Puzzleboard Window
3. Used Letters Window
4. Score Window (Player 1)
5. Score Window (Player 2)
6. Score Window (Player 3)

If the manager window is closed, all other windows will also close. Otherwise,
closing a window will have no effect on other windows.

Any window can be made fullscreen by right clicking on the window and clicking
the `Toggle Fullscreen` button.

The puzzleboard and category strip are surrounded by draggable splitters so
that they can be repositioned within the window.

### Creating a Game

<img align="right" width="50%" src="https://i.imgur.com/oNZML47.png">

Click `Select Puzzle` from the manager window, or press `Ctrl`+`O` on the
keyboard, to open the game selection screen. From this screen, you may add
puzzles for as many rounds as you wish.

- The number of rounds can be adjusted by clicking the `+` or `-` buttons.
- Click `Select puzzles` to add puzzles to the game. For each puzzle, you can
  select a round type and a reward for solving the puzzle.
- To save the game to a file, click `Export` at the top of the menu and specify
  a filename.
- To import a game from a file, click `Import` at the top of the menu and
  select a file.

### Selecting Puzzles

<img align="right" width="50%" src="https://i.imgur.com/UEzEBYv.png">

Clicking `Select Puzzle` from the game selection screen will open the puzzle
selection screen. This displays a list of available puzzles.
- Click each puzzle that you wish to select. Puzzles will be added to the game
  in the order that they were selected.
- Click `Export` to save any selected puzzles to a file. Puzzles will be
  written to the file in the order that they were selected.
- Click `Import` to import puzzles from a file.
- Click `Delete All` to delete all saved puzzles.
- Click `X` next to a puzzle's name to delete an individual puzzle.

### Creating Puzzles

<img align="right" width="40%" src="https://i.imgur.com/f6x8j4X.gif">

To create new puzzles, you can type directly into the puzzleboard.

- Click any panel in the puzzleboard window to start typing.
- Press `Ctrl`+`S` to save your puzzle.
- Press `Ctrl`+`O` to open an existing puzzle for editing.

### Setting Player Names

- Select a player by clicking on their score in the manager window, or by
  pressing `1`, `2`, or `3` on the keyboard. Pressing the spacebar will cycle
  through players.
- Enter a name into the text input box labeled `Edit player name`
- Click the `OK` button, or press `Enter` on the keyboard.

### Changing Settings

From the manager window, click the gear icon in the bottom left to open the
settings menu. From here, you can set:
- The amount of time on the final spin timer
- The dollar amounts for each wedge on the wheel
- The price of a vowel
- The minimum reward for solving a puzzle
- The reward for solving a clue
- The dollar amount added to the final spin value

### Changing Hotkeys

There is a button on the left of the settings screen to change the hotkeys.

### Strings and Values

The files `strings.py` and `values.py` contain values used by the application
(text, currency, color values, font sizes, timing information, etc.). This
makes it easy to tweak how the application works, or to make edits for
localization purposes.

## Gameplay

### Standard Round

- To start a player's turn, select the player by clicking on their score, or by
  pressing `1`, `2`, or `3` on the keyboard. Pressing the spacebar will cycle
  through players.
- Wait for the player to spin the wheel.
  - If the wheel lands on a cash wedge, select the value of the wedge in the
    dropdown labeled `Select cash value`. Alternatively, you may type a value
	into the text input box labeled `Enter custom cash value`.
  - If the wheel lands on "Bankrupt", click the `Bankrupt` button or press `0`
    on the keyboard, then select the next player.
  - If the wheel lands on "Lose a Turn", click the `Lose a Turn` button or
    press `9` on the keyboard, then select the next player.
- When the player guesses a letter, press the letter on the keyboard. If
  applicable, the letter will be revealed on the puzzleboard and removed from
  the used letters window.
- Click the `Add Value` button or press `Enter` on the keyboard to award the
  cash value to the player. Changes to the score will be reflected in the
  player's score window.
- If the player wishes to buy a vowel, click the `Buy a Vowel` button or press
  the `-` key on the keyboard to deduct $250 from the player. Then, press the
  letter on the keyboard, just as you would for a consonant.
- The `🚫` button or the `8` key on the keyboard can be pressed at any time to
  play a buzzer sound, indicating an incorrect guess.
- If at any point you wish to manually adjust a player's score, you can add or
  subtract from their score by typing a value into the text input box labeled
  `Adjust score` and then pressing the `-` or `+` buttons to subtract or add
  that amount.
- If the player correctly solves the puzzle, click the `Solve` button or press
  the right arrow key on the keyboard to reveal the puzzle on the puzzleboard.
- At the end of a round, press the `Bank Score` button or press the `=` key on
  the keyboard. This will add the selected player's round total to their game
  total, and then set each player's round total back to zero.

### Toss-Up Round

If each player has their own button to ring in, the buttons should be mapped to
the keyboard keys `1`, `2`, and `3`.

During a Toss-Up Round:
- Click the `Toss-Up` button on the manager window, or press `4` on the
  keyboard, to begin the toss-up.
- Press `1`, `2`, or `3` on the keyboard, or click on a player's score, to ring
  in for that player. If multiple players ring in, only the first player to
  ring in will be selected.
- If the player guesses correctly, click the `Solve` button, or press the right
  arrow key on the keyboard.
- If the player fails to guess correctly, click `Toss-Up` or press `4` to
  resume. The player will be unable to ring in again during the current
  toss-up.

### Mystery Round

The mystery round has not yet been implemented. Currently, a mystery round
behaves the same as a standard round. However, a player's score can still be
manually adjusted if they flip over a mystery wedge.

### Express Round

The express round has not yet been implemented. Currently, an express round
behaves the same as a standard round. However, a player's score can still be
manually adjusted if they land on an express wedge and wish to "hop aboard the
Express".

### Triple Toss-Up

The rounds in a triple toss-up are the same as a regular toss-up, except that
the first two rounds in a triple toss-up play a different sound when the puzzle
is solved.

### Speed-Up Round

- When a Speed-Up Round starts, the `Final Spin Timer` button will appear in
  the top right.
- Click this button, or press the backtick (`` ` ``) key on the keyboard,
  to start or pause the timer.
- When the timer is paused, it can be reset by clicking the `Reset` button or
  pressing `Shift`+`` ` `` on the keyboard.
- When the timer runs out, click the `Final Spin` button or press `4` on the
  keyboard to start the final spin.

### Final Spin

- Spin the wheel. If the wheel does not land on a cash wedge, spin again.
- Select the value of the cash wedge in the dropdown labeled `Select cash
  value`. $1,000 is automatically added to the selected value.
- Starting with the current player, each player takes a turn guessing one
  letter. Vowels are free. Press the guessed letter on the keyboard.
- If the letter is not in the puzzle, the player loses their turn.
- Click the `Add Value` button or press `Enter` on the keyboard to award the
  cash value to the player. The player has until 4 seconds after letters are
  revealed to attempt solve the puzzle. If the player does not solve the
  puzzle, move on to the next player.
- If the player solves the puzzle, click the `Solve` button or press the right
  arrow key on the keyboard.
- After the final spin, any subsequent speed-up rounds will be skipped.

### Bonus Round

<img align="right" width="50%" src="https://i.imgur.com/2hP5cEL.png">

- After the final speed-up round, the player with the highest score moves on to
  the bonus round.
- In the event of a tie, you will be prompted to select a puzzle to use as a
  tiebreaker toss-up to decide which player proceeds to the bonus round. You
  will also have the option to manually select a winner from this screen.
- Click the `Reveal` button next to "RSTLNE" to reveal the given letters on the
  puzzleboard.
- Allow the player to guess another three consonants and a vowel (plus a fourth
  consonant if they have a wild card). Type these letters into the text input
  box underneath "RSTLNE", then click the adjacent `Reveal` button to reveal
  the letters on the puzzleboard.
- If the player solves the puzzle, click the `Solve` button, or press the right
  arrow key on the keyboard.
- If the player fails to solve the puzzle, press the `🚫` button or press the
  `8` key.

## Acknowledgments

This project was created for Marina Sky Vied. They provided guidance for most
of the game mechanics.

Sounds are property of their respective copyright holders.
