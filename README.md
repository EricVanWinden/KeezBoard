# KeezBoard

## Run Digital Keez

The host runs the game server on a PC. Players use a PC or tablet browser on the
same home network. The host takes the first seat and can reorder seats before
starting.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn keezboard.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` on the host. Create a room and share the displayed
LAN invite link or room code. If other devices cannot connect, allow Python
through the host PC's private-network firewall. The host's game state is saved
to `keezboard.sqlite3` in the server's working directory and restored after a
restart.

The server supports one active room and uses display names rather than accounts.
Outside-network play, multiple simultaneous games, and phone-sized screens are
not supported. See [DigitalKeezImplementationSpec.md](docs/DigitalKeezImplementationSpec.md)
for the approved requirements and [KeezBoardRulesEnglish.md](docs/KeezBoardRulesEnglish.md)
for the source rules. If three consecutive deals have no legal moves, the game
stalls and the host can create a new room.
