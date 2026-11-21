# Digital Keez Implementation Spec

Status: Implemented 2026-11-16 (approved by the user on 2026-11-16)

- Work item: PBI "implement digital KeezBoard" (ID and URL unavailable; hobby project)
- Requirements: [DigitalKeezRequirements.md](DigitalKeezRequirements.md) (developer-confirmed current on 2026-11-16; no Boards ID or URL supplied)
- Rules baseline: [KeezBoardRulesEnglish.md](KeezBoardRulesEnglish.md)

## Scope

Build a complete, playable browser version of Keez for 3–8 players. The host runs the server on a PC, and players connect using PC or tablet browsers on the same home network.

Playing from outside the home network, phone support, multiple simultaneous games, and user accounts are out of scope for the first version. The host PC must remain available during play; saved state must allow the game to resume after a server restart.

## Implementation decisions

1. Run a single Python server on the host PC and serve a lightweight HTML/CSS/JavaScript client to the home network.
2. Use FastAPI for the server and WebSockets to propagate room and game-state changes to connected browsers.
3. Store the single active game's state locally in SQLite and save state changes automatically.
4. Keep game rules and room state authoritative on the server. Each browser view displays only the cards belonging to that player.
5. Use mainstream PC and tablet browsers; do not design for phone-sized screens.
6. The host occupies a player seat when creating a room.

## Functional requirements

### Room and seating

- The host starts the server from a CLI or IDE and creates one private room.
- The host joins the game as the first player; the host's seat can be reordered before starting.
- The room code and invite link are available for the host to share using their own email app. The link includes the host PC's local network address and room code.
- A player with the invite can claim an open seat without host approval, using a display name only.
- The game supports 3–8 players. The host may reorder seats before starting and decides when to start. Seat order is locked after start.
- For even player counts, opposite seats are partners. For odd counts, players compete individually.
- Turn order follows the seating order. The first player rotates for each new deal.

### Board

- Each player has 16 track positions, 4 home positions, and 4 waiting positions.
- Four players use four 90-degree pieces.
- Six players use four 90-degree pieces and two 180-degree pieces.
- Eight players use four 90-degree pieces and four 180-degree pieces.
- Three, five, and seven player games use custom layouts with the same per-player positions.

### Deck and dealing

- At the start of each three-deal cycle, create a combined deck with one 13-card suit set per player. Repeat suits for player counts above four.
- Shuffle the complete deck before dealing.
- Deal 5 cards per player, then 4, then 4. After the third deal, collect and reshuffle the cards for the next cycle.
- A player with no Ace or King at the start of a deal discards their whole hand and waits for the next deal.

### Rules and moves

- Enforce the card effects, movement, setup, capture, and home-entry rules in the rules baseline, subject to these agreed clarifications:
  - A pawn must move the exact number of spaces to enter home.
  - Pawns cannot pass a pawn on its protected starting space or jump over a pawn already home.
  - A starting-space pawn cannot be captured or swapped. A move onto an occupied protected starting space is blocked.
  - Only one pawn may occupy a space. Landing on a space occupied by an own, teammate, or unprotected opponent pawn sends the pawn already there to waiting; the moving pawn takes the space.
  - In an odd-player game, a Seven cannot be split; it may move one pawn seven spaces.
  - In an even-player game, a Seven may be split across two pawns when both parts are legal. If a player's final pawn enters home while their partner still has pawns out, the remainder must be moved by the partner. A Seven cannot be split to move the team's final remaining pawn home.
  - In an odd-player game, a Jack may swap the player's pawn with an opponent's pawn, subject to the existing protected-space restrictions.
- When a player has no legal move, automatically discard their remaining hand and notify them.
- An odd-player game ends when a player gets all four of their pawns home. A paired game ends when the team achieves the win condition in the rules baseline.

### Connectivity, privacy, and recovery

- Invite links and room codes work only for players on the same home network.
- Each browser instance displays only that player's cards. This is display-level privacy; someone using the same computer may inspect another browser tab.
- If a player disconnects, play continues until that player's turn, then waits for reconnection.
- Save room and game state automatically. After a server restart, restore the room code, players, seats, cards, and current turn so the game can resume.

## Acceptance criteria

1. **AC1 — Start and join:** The host starts the Python server from a CLI or IDE and creates a room. From PC and tablet browsers on the same home network, 3–8 players can join through the room code or LAN link using display names, without accounts or host approval.
2. **AC2 — Lobby:** The host can reorder seats and start the game. The game cannot start with fewer than 3 or more than 8 players. Seat order is locked after start, and opposite seats are partners in even-player games.
3. **AC3 — Board layouts:** Every supported player count renders 16 track, 4 home, and 4 waiting positions per player. The 4-, 6-, and 8-player layouts use the specified pieces; 3-, 5-, and 7-player layouts are custom and navigable.
4. **AC4 — Deck and dealing:** Before play, the server creates one 13-card suit set per player, repeats suits as needed, and shuffles the combined deck. It deals 5, 4, and 4 cards per player over three deals, rotates the first player each deal, then collects and reshuffles the cards.
5. **AC5 — Rules enforcement:** The server rejects illegal moves and enforces the documented rules and agreed clarifications, including exact home entry, protected starting spaces, captures, and Seven behavior.
6. **AC6 — No legal move:** When a player has no legal move, the server automatically discards that player's remaining hand and notifies them.
7. **AC7 — Victory:** An odd-player game ends when a player gets all four pawns home. A paired game ends when the team achieves the documented win condition.
8. **AC8 — Card privacy:** Each browser instance displays only its player's cards.
9. **AC9 — Disconnect and resume:** A disconnected player can reconnect; their turn waits if they have not returned by the time it is due. After a server restart, the game resumes with its room code, players, cards, seats, and current turn.
10. **AC10 — Device and network scope:** The game works in current mainstream PC and tablet browsers on the home network. Phone-sized screens and access from outside the home network are not required.

## Verification record

- **AC1:** Browser/API smoke covered room creation, host seating, joining by room code, and LAN invite generation. A separate physical PC or tablet on the home network was not available for testing.
- **AC2:** Unit tests cover the minimum player count and opposite-seat partnerships. Browser/API smoke covered host authorization, seat reordering, and starting a game.
- **AC3:** Unit tests verify the layout and piece composition for 3–8 players. Browser rendering checks counted 16 track, 4 home, and 4 waiting positions per player for every supported count. Standard layouts use circular sectors with a 1:2 angular-width ratio for 90- and 180-degree pieces; odd counts use equal custom sectors. The 768px viewport was checked.
- **AC4:** Unit tests cover deck composition, suit repetition, deal sizes, and first-seat rotation.
- **AC5:** Unit tests cover capture, protected starting spaces, exact home entry, Seven splitting, partner handoff, and Jack restrictions.
- **AC6:** Unit test covers automatic hand discard and notification when no legal move exists.
- **AC7:** Unit tests cover both individual and paired victories.
- **AC8:** Unit test confirms that public state contains only the viewer's hand; browser/API smoke checked private state.
- **AC9:** Unit test covers SQLite round-tripping. Browser/API smoke covered reconnect, LAN invite recovery, and state restoration after a server restart.
- **AC10:** Chromium browser checks covered gameplay and a 768px tablet-sized viewport. Testing from a separate physical device remains outstanding.
- **Commands:** `python -m unittest discover -s tests -v` (15 tests), `python -m compileall -q keezboard tests`, and `node --check keezboard\static\app.js` passed.

## Deferred and out of scope

- Playing from outside the home network (separate PBI).
- Phone support.
- Multiple simultaneous games.
- User accounts.

## Amendments

- 2026-11-16: Clarified that the host automatically occupies the first player seat when creating a room, per developer decision.
- 2026-11-16: Per developer confirmation, standard 4/6/8-player layouts render 90- and 180-degree pieces as circular track sectors with a 1:2 angular-width ratio.
