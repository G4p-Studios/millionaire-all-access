# Hosting Transition Guide

This guide helps hosts who are used to Roblox Studio or Virtual Paradise start hosting quickly in this project.

## Concept mapping

- Roblox or Virtual Paradise studio scene maps to the lobby studio areas in this game.
- Moving around the set uses directional navigation (Arrow keys) across connected studio nodes.
- Each arrival announces landmark, available exits, and nearby key targets.
- Triggering game progress is host-driven, similar to running stages manually in studio tools.

## First hosted session

1. Open the game and select Host Game.
2. Choose your lobby name and port.
3. Set Session Assets Folder to the folder that contains your custom sounds and images.
4. Set Public if you want your lobby listed by the lobby service.
5. Start server.
6. Confirm players are connected in the lobby list.
7. Move around studio areas with Arrow keys to verify your setup cues.
8. Use S to sit or stand when at contestant seating, hot seat, or host control panel.
9. Stand at Host Control Panel and press Enter or Space to open host controls.
10. Press Enter to start once everyone is ready.

The lobby publishes assets automatically from Session Assets Folder when the host joins.
If Session Assets Folder is blank, it falls back to assets/session_sync.
Transfers are chunked and resumable for both host upload and player download.
Sync retries automatically with short backoff on transient network issues.
Files over 100 MB are skipped from session sync.
Players sync them into temp_assets/<lobby_name> and show as Ready when complete.
Game start is blocked until all connected non-host players are Ready.
Short disconnects now attempt automatic reconnect before the session is dropped.
If the active host disconnects, host control is handed off to a connected player.

Use Left and Right while the panel is open to switch pages:

- Show Controls page for lights, music bed, and stings
- Show Controls page includes Refresh Session Assets to republish changes mid-lobby
- Show Controls page includes Sync Status to announce revision, skipped files, and player readiness
- Show Controls page includes Reliability Status to announce active host and reconnect grace timers
- Flow and Presets page for call-up order, explicit Move Target To Hot Seat, and setup presets
- Flow and Presets page includes Quick Switch Preset to cycle and apply the next preset in one action
- Flow and Presets page includes Save Current As Preset for reusable host studio snapshots
- Flow and Presets page includes Import Preset Pack to load .json preset packs from disk
- Flow and Presets page includes Delete Selected Preset to clean up custom or imported presets

Setup presets now apply a full host studio state in one action:

- lights and music bed
- host location and seated or standing posture
- call-up pointer reset or keep behavior

Use Save Current As Preset to capture your current studio setup and reuse it in future sessions.
Saved presets are written as JSON pack files under assets/preset_packs and auto-loaded on startup.
Use Import Preset Pack to bring in packs shared by other hosts.
Use Delete Selected Preset to remove a selected non-built-in preset from your rotation.

## During gameplay

- Read the question aloud or let built-in speech handle prompts.
- Contestants answer with A, B, C, or D.
- From higher tiers, lock-in flow requires a second key press by the contestant, then Enter by the host to reveal.
- Use lifeline keys 1, 2, and 3 as needed.

## Accessibility-first hosting tips

- Keep spoken pacing clear and predictable.
- Use R during gameplay to repeat long questions.
- Announce any custom house rules before pressing Enter to start.
- Keep menu and lobby sounds enabled to provide state feedback.

## Sound organization plan

Store new assets under:

- assets/sounds/game for gameplay beds, stings, and reveal sounds
- assets/sounds/ui for menu navigation and connection cues
- assets/sounds/navigation for lobby set movement cues such as leave, step, arrive, panel, sitting, and standing

Legacy sounds in the sounds folder still load, but new content should be added in assets/sounds.
