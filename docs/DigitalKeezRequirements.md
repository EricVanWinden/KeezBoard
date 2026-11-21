# Digital Keez Requirements

## Purpose

Create a browser-based digital version of Keez for private games with friends and family. The existing [KeezBoardRulesEnglish.md](KeezBoardRulesEnglish.md) remains the source of truth for card effects and movement rules, except where this document specifies different player counts, game modes, or board layouts.

## Players and game modes

- Support 3–8 players.
- With an even number of players, play in pairs. Players opposite one another in the seating order are partners.
- With an odd number of players, play individually. The first player to get all four of their own pawns home wins.
- In paired games, follow the existing rules for helping a partner and winning as a team.
- The host sets the seating order before starting. This determines partners in paired games and turn order. The host may change the order before the game starts; the order is locked after the start.
- The host chooses when to start, once 3–8 players have joined.
- The first player rotates for each new deal.

## Board and cards

- Each player has 16 track positions, 4 home positions, and 4 waiting positions.
- Board layouts:
  - 4 players: four 90-degree pieces.
  - 6 players: four 90-degree pieces and two 180-degree pieces.
  - 8 players: four 90-degree pieces and four 180-degree pieces.
  - Odd player counts: generate a custom layout.
- At the start of each three-deal cycle, create a combined deck with one 13-card suit set per player (for example, hearts or spades), repeating suits for games with five or more players. Shuffle the full deck, then deal 5 cards per player, followed by 4 and 4. Collect and reshuffle all cards after the third deal. The deck contains 13 times the number of players.

## Rooms and networking

- The first version runs on the host's PC and is available only to devices on the same home network.
- The host starts the Python server from a command line or IDE. No third-party hosting service is planned for the first version.
- Support one active game at a time.
- The host creates a private room and shares its room code or link using their own email app. A link should include the host PC's local network address and room code. Anyone with the invitation can join an open seat; host approval is not required.
- Players join using a display name only; accounts are not required.
- Playing from outside the home network is deferred to a separate PBI.

## Client, privacy, and recovery

- Support browsers on PCs and tablets. Phone-sized screens are out of scope because the board would be too small.
- Each browser instance displays only that player's cards. This is display-level privacy; someone using the same computer could still view another player's tab.
- If a player disconnects, play continues until their turn and then waits for them to reconnect.
- Save game state automatically on the host PC and allow the game to resume after a server interruption.

## Technology direction

Use a Python server with a browser client, building on the host's Python experience. The approved [DigitalKeezImplementationSpec.md](DigitalKeezImplementationSpec.md) selects FastAPI, WebSockets, and SQLite. Godot is not recommended for the browser-first requirement; TypeScript remains an alternative but would require learning more new tooling.

## Out of scope for the first version

- Internet play from outside the home network.
- Phone support.
- Multiple simultaneous games.
- User accounts.
