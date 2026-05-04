# Hosting Transition Guide

This guide helps hosts who are used to Roblox Studio or Virtual Paradise start hosting quickly in this project.

## Concept mapping

- Roblox or Virtual Paradise studio scene maps to the lobby studio areas in this game.
- Moving around the set is done with Left and Right in the lobby.
- Triggering game progress is host-driven, similar to running stages manually in studio tools.

## First hosted session

1. Open the game and select Host Game.
2. Choose your lobby name and port.
3. Set Session Assets Folder to the folder that contains your custom sounds and images.
4. Set Public if you want your lobby listed by the lobby service.
5. Start server.
6. Confirm players are connected in the lobby list.
7. Move around studio areas with Left and Right to verify your setup cues.
8. Use S to sit or stand when at contestant seating, hot seat, or host control panel.
9. Stand at Host Control Panel and press Enter or Space to open host controls.
10. Press Enter to start once everyone is ready.

The lobby publishes assets automatically from Session Assets Folder when the host joins.
If Session Assets Folder is blank, it falls back to assets/session_sync.
Players sync them into temp_assets/<lobby_name> and show as Ready when complete.
Game start is blocked until all connected non-host players are Ready.

Use Left and Right while the panel is open to switch pages:

- Show Controls page for lights, music bed, and stings
- Flow and Presets page for call-up order, explicit Move Target To Hot Seat, and setup presets

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
