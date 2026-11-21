from __future__ import annotations

import asyncio
import secrets
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from keezboard.engine import (
    GameError,
    GameState,
    Player,
    add_player,
    new_room,
    player_for_token,
    play_action,
    public_state,
    reorder_seats,
    start_game,
)
from keezboard.storage import StateStore


class CreateRoomRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=24)


class JoinRoomRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=24)
    player_token: str | None = None


class SeatOrderRequest(BaseModel):
    player_ids: list[str]


class MoveRequest(BaseModel):
    action: dict[str, Any]


class Connections:
    def __init__(self) -> None:
        self._players: dict[WebSocket, str] = {}

    def add(self, websocket: WebSocket, player_id: str) -> None:
        self._players[websocket] = player_id

    def remove(self, websocket: WebSocket) -> None:
        self._players.pop(websocket, None)

    def online_ids(self) -> set[str]:
        return set(self._players.values())

    async def broadcast(self, state: GameState) -> None:
        disconnected: list[WebSocket] = []
        online = self.online_ids()
        for websocket, player_id in list(self._players.items()):
            viewer = next(
                (player for player in state.players if player.id == player_id),
                None,
            )
            if viewer is None:
                disconnected.append(websocket)
                continue
            host = viewer.id == state.host_player_id
            try:
                await websocket.send_json(
                    public_state(state, viewer, online, host)
                )
            except (RuntimeError, WebSocketDisconnect):
                disconnected.append(websocket)
        for websocket in disconnected:
            self.remove(websocket)


store = StateStore()
connections = Connections()
mutation_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.initialize()
    app.state.game = store.load()
    yield


app = FastAPI(title="Digital Keez", lifespan=lifespan)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/rooms", status_code=201)
async def create_room(body: CreateRoomRequest, request: Request) -> dict[str, Any]:
    async with mutation_lock:
        current: GameState | None = request.app.state.game
        if current is not None and current.status not in ("finished", "stalled"):
            raise HTTPException(
                status_code=409,
                detail="A room is already active. Join it or finish the current game first.",
            )
        try:
            state = new_room(body.display_name)
        except GameError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        request.app.state.game = state
        store.save(state)
    await connections.broadcast(state)
    host_player = next(player for player in state.players if player.id == state.host_player_id)
    return {
        "state": _view_state(state, host_player, host=True),
        "player_token": host_player.token,
        "host_token": state.host_token,
        "invite_url": _invite_url(state.code, request),
    }


@app.post("/api/rooms/{code}/join")
async def join_room(code: str, body: JoinRoomRequest, request: Request) -> dict[str, Any]:
    async with mutation_lock:
        state = _get_game(request, code)
        player = player_for_token(state, body.player_token or "") if body.player_token else None
        if player is None:
            try:
                player = add_player(state, body.display_name)
            except GameError as error:
                raise HTTPException(status_code=400, detail=str(error)) from error
            store.save(state)
        elif player.name != body.display_name.strip():
            raise HTTPException(status_code=400, detail="That reconnect token belongs to another display name.")
    await connections.broadcast(state)
    return {
        "state": _view_state(state, player, host=player.id == state.host_player_id),
        "player_token": player.token,
        "invite_url": _invite_url(state.code, request),
    }


@app.get("/api/rooms/{code}/state")
async def get_state(
    code: str,
    request: Request,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
) -> dict[str, Any]:
    state = _get_game(request, code)
    player = _player_from_token(state, player_token)
    result = _view_state(state, player, host=player.id == state.host_player_id)
    result["invite_url"] = _invite_url(state.code, request)
    return result


@app.put("/api/rooms/{code}/seats")
async def update_seats(
    code: str,
    body: SeatOrderRequest,
    request: Request,
    host_token: str | None = Header(default=None, alias="X-Host-Token"),
) -> dict[str, Any]:
    async with mutation_lock:
        state = _get_game(request, code)
        _require_host(state, host_token)
        try:
            reorder_seats(state, body.player_ids)
        except GameError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        store.save(state)
    await connections.broadcast(state)
    viewer = next(player for player in state.players if player.id == state.host_player_id)
    return _view_state(state, viewer, host=True)


@app.post("/api/rooms/{code}/start")
async def begin_game(
    code: str,
    request: Request,
    host_token: str | None = Header(default=None, alias="X-Host-Token"),
) -> dict[str, Any]:
    async with mutation_lock:
        state = _get_game(request, code)
        _require_host(state, host_token)
        try:
            start_game(state)
        except GameError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        store.save(state)
    await connections.broadcast(state)
    viewer = next(player for player in state.players if player.id == state.host_player_id)
    return _view_state(state, viewer, host=True)


@app.post("/api/rooms/{code}/move")
async def move(
    code: str,
    body: MoveRequest,
    request: Request,
    player_token: str | None = Header(default=None, alias="X-Player-Token"),
) -> dict[str, Any]:
    async with mutation_lock:
        state = _get_game(request, code)
        player = _player_from_token(state, player_token)
        if player.id not in connections.online_ids():
            raise HTTPException(status_code=409, detail="Reconnect to the game before taking a turn.")
        try:
            play_action(state, player, body.action)
        except GameError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        store.save(state)
    await connections.broadcast(state)
    return _view_state(state, player, host=player.id == state.host_player_id)


@app.websocket("/ws/{code}")
async def websocket_state(websocket: WebSocket, code: str) -> None:
    state: GameState | None = websocket.app.state.game
    if state is None or state.code != code.upper():
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        player_token = await asyncio.wait_for(websocket.receive_text(), timeout=10)
    except WebSocketDisconnect:
        return
    except TimeoutError:
        await websocket.close(code=1008)
        return
    player = player_for_token(state, player_token)
    if player is None:
        await websocket.close(code=1008)
        return

    connections.add(websocket, player.id)
    await connections.broadcast(state)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connections.remove(websocket)
        await connections.broadcast(state)


def _get_game(request: Request, code: str) -> GameState:
    state: GameState | None = request.app.state.game
    if state is None or state.code != code.upper():
        raise HTTPException(status_code=404, detail="Room not found.")
    return state


def _player_from_token(state: GameState, token: str | None) -> Player:
    player = player_for_token(state, token or "")
    if player is None:
        raise HTTPException(status_code=401, detail="A valid player token is required.")
    return player


def _require_host(state: GameState, token: str | None) -> None:
    if token is None or not secrets.compare_digest(token, state.host_token):
        raise HTTPException(status_code=403, detail="Only the host can manage this room.")


def _view_state(state: GameState, viewer: Player, host: bool) -> dict[str, Any]:
    return public_state(state, viewer, connections.online_ids(), host)


def _invite_url(code: str, request: Request) -> str:
    port = request.url.port or 8000
    return f"http://{_lan_address()}:{port}/?room={code}"


def _lan_address() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 80))
            return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
