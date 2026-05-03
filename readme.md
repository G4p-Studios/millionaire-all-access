# Who Wants To Be A Millionaire - Accessible online game for Windows

This project is an accessible multiplayer game show platform inspired by community-hosted Millionaire games on Roblox and Virtual Paradise.

The goal is to support blind and sighted hosts and players with equal quality gameplay, clear keyboard controls, and studio-style hosting flow.

## Current status

The game is in active development and currently includes:

- Multiplayer host and join flow
- Spoken accessibility output across menu, lobby, and gameplay
- Core Millionaire question loop with lifelines
- Studio zone movement in lobby with keyboard and audio feedback
- A question screen layout closer to classic Millionaire styling

## Host quick start

1. Launch the game.
2. Choose Host Game.
3. Set Lobby Name, Port, Host Name, and Public option.
4. Select Start Server.
5. Wait for players to join in the lobby.
6. Press Enter in the lobby to start the game.

You can also open the in-game Host Quick Start screen from the main menu.

## Keyboard controls

### Menu

- Up and Down: navigate items
- Enter: select item
- Escape: return to main menu from submenus

### Lobby

- Left and Right: move between studio areas
- Tab: move to next studio area
- H: repeat lobby controls
- Enter (host only): start game
- Escape: leave session

### Gameplay

- A, B, C, D: choose answer
- Press selected answer key again (from question 6 onward): lock in
- Enter (after lock-in): reveal answer
- 1, 2, 3: use lifelines
- R: repeat question
- W: walk away

## Sound assets layout

The loader now supports both legacy and new paths.

Preferred structure:

- assets/sounds/game
- assets/sounds/ui

Legacy fallback is still supported:

- sounds

If a sound file is present in both places, the game prioritizes assets/sounds.

## Development note

This project is focused on stable accessibility and host usability first. Additional visual presets, richer set customization, and more advanced movement logic are planned.
