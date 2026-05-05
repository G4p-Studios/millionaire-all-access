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
- S: sit or stand when at a seat area
- Enter or Space (at host control panel while standing): open host controls
- Up and Down (inside host panel): navigate controls
- Left and Right (inside host panel): switch between Show Controls and Flow/Presets pages
- Enter or Space (inside host panel): activate selected control
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
- assets/sounds/navigation

Recommended split:

- ui_move, ui_select, ui_back, ui_error, ui_connect, ui_disconnect in assets/sounds/ui
- leave.wav, step.wav, arrive.wav, panel.wav, sitting.wav, and standing.wav in assets/sounds/navigation

Legacy fallback is still supported:

- sounds

If a sound file is present in both places, the game prioritizes assets/sounds.

## Session asset sync (Phase 1)

The lobby now supports Roblox and VP style session asset sync.

- Host source folder: set in Host Game as Session Assets Folder
- Default source folder: assets/session_sync
- Allowed file types: wav, mp3, flac, ogg, png, jpg, jpeg, json
- Client cache folder: temp_assets/<lobby_name>
- Max per-file sync size: 100 MB

How it works:

1. Host selects Session Assets Folder in Host Game, then enters the lobby.
2. Host client publishes a manifest, then uploads each file in chunks with resume by offset.
3. Joining players download missing or changed files in chunks and resume from partial .part files.
4. Players mark themselves ready after sync completes.
5. Host start is blocked until all connected non-host players are ready.

The host can republish at any time using Refresh Session Assets in the host control panel.
Sync calls now include retry with small backoff for transient network failures.

If Session Assets Folder is left blank, the game falls back to assets/session_sync.

Lobby player list now includes Syncing or Ready state.

## Development note

This project is focused on stable accessibility and host usability first. Additional visual presets, richer set customization, and more advanced movement logic are planned.

## Host panel pages

When open, the host control panel has two pages:

- Show Controls: Lights, Music Bed, Sting, Refresh Session Assets, Sync Status, Start Game
- Flow and Presets: Call-Up Target, Call Next Contestant, Move Target To Hot Seat, Quick Switch Preset, Setup Preset, Apply Setup Preset, Save Current As Preset, Import Preset Pack, Delete Selected Preset

Setup presets now apply a full studio state bundle:

- light preset
- music bed preset
- host zone and seated or standing posture
- call-up pointer behavior

Hosts can create and persist custom presets from the panel using Save Current As Preset.
Saved presets are also written as JSON preset pack files in assets/preset_packs and loaded automatically.
Quick Switch Preset changes and applies the next preset in one action.
Import Preset Pack lets hosts bring in a .json preset pack from any folder.
Delete Selected Preset removes the currently selected custom or pack preset, while built-in presets stay protected.
