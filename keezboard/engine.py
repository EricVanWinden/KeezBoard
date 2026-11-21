from __future__ import annotations

import copy
import secrets
from dataclasses import asdict, dataclass, field
from typing import Any


SUITS = ("hearts", "diamonds", "clubs", "spades")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_EMPTY_DEALS = 3


class GameError(ValueError):
    """A requested room or move violates the game rules."""


@dataclass
class Player:
    id: str
    name: str
    seat: int
    token: str
    pawns: list[int] = field(default_factory=lambda: [-1, -1, -1, -1])
    hand: list[dict[str, str]] = field(default_factory=list)


@dataclass
class GameState:
    code: str
    host_token: str
    host_player_id: str
    status: str
    players: list[Player]
    deal_number: int = 0
    deal_in_cycle: int = 0
    first_seat: int = 0
    current_seat: int = 0
    hand_size: int = 0
    deck: list[dict[str, str]] = field(default_factory=list)
    discard_pile: list[dict[str, str]] = field(default_factory=list)
    winner_player_ids: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)


def new_room(host_name: str) -> GameState:
    name = _validate_name(host_name)
    player_id = secrets.token_urlsafe(9)
    player = Player(
        id=player_id,
        name=name,
        seat=0,
        token=secrets.token_urlsafe(32),
    )
    return GameState(
        code="".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(6)),
        host_token=secrets.token_urlsafe(32),
        host_player_id=player_id,
        status="lobby",
        players=[player],
    )


def add_player(state: GameState, display_name: str) -> Player:
    if state.status != "lobby":
        raise GameError("Players cannot join after the game has started.")
    if len(state.players) >= 8:
        raise GameError("This room already has eight players.")
    name = _validate_name(display_name)
    player = Player(
        id=secrets.token_urlsafe(9),
        name=name,
        seat=len(state.players),
        token=secrets.token_urlsafe(32),
    )
    state.players.append(player)
    return player


def reorder_seats(state: GameState, player_ids: list[str]) -> None:
    if state.status != "lobby":
        raise GameError("Seat order is locked after the game starts.")
    current_ids = {player.id for player in state.players}
    if len(player_ids) != len(current_ids) or set(player_ids) != current_ids:
        raise GameError("Seat order must include every player exactly once.")
    by_id = {player.id: player for player in state.players}
    for seat, player_id in enumerate(player_ids):
        by_id[player_id].seat = seat


def start_game(state: GameState) -> None:
    if state.status != "lobby":
        raise GameError("This room has already started.")
    if not 3 <= len(state.players) <= 8:
        raise GameError("A game needs between three and eight players.")
    state.players.sort(key=lambda player: player.seat)
    state.status = "playing"
    state.deal_number = 0
    state.deal_in_cycle = 0
    state.first_seat = 0
    state.winner_player_ids.clear()
    state.notices.clear()
    _deal_next(state)
    _seek_turn(state, state.first_seat - 1)


def player_for_token(state: GameState, token: str) -> Player | None:
    return next(
        (player for player in state.players if secrets.compare_digest(player.token, token)),
        None,
    )


def controlled_player_ids(state: GameState, player: Player) -> list[str]:
    if not _is_paired(state) or not _all_home(state, player):
        return [player.id]
    partner = _partner(state, player)
    return [partner.id]


def legal_actions(state: GameState, player: Player) -> list[dict[str, Any]]:
    if state.status != "playing" or player.seat != state.current_seat:
        return []
    actions: list[dict[str, Any]] = []
    for card in player.hand:
        actions.extend(_legal_actions_for_card(state, player, card))
    return actions


def play_action(
    state: GameState,
    player: Player,
    requested_action: dict[str, Any],
) -> None:
    if state.status != "playing":
        raise GameError("There is no active game.")
    if player.seat != state.current_seat:
        raise GameError("It is not your turn.")
    card_id = requested_action.get("card_id")
    card = next((item for item in player.hand if item["id"] == card_id), None)
    if card is None:
        raise GameError("That card is not in your hand.")
    options = _legal_actions_for_card(state, player, card)
    if requested_action not in options:
        raise GameError("That move is not legal.")

    _apply_action(state, requested_action)
    player.hand.remove(card)
    state.discard_pile.append(card)
    description = _describe_action(state, player, card, requested_action)
    _add_notice(state, description)

    winner = _find_winner(state)
    if winner:
        state.status = "finished"
        state.winner_player_ids = winner
        names = " and ".join(_player_by_id(state, player_id).name for player_id in winner)
        _add_notice(state, f"{names} won the game.")
        return

    _seek_turn(state, player.seat)


def public_state(
    state: GameState,
    viewer: Player,
    connected_player_ids: set[str],
    host: bool,
) -> dict[str, Any]:
    player_count = len(state.players)
    track_length = player_count * 16
    player_rows: list[dict[str, Any]] = []
    for player in sorted(state.players, key=lambda item: item.seat):
        row: dict[str, Any] = {
            "id": player.id,
            "name": player.name,
            "seat": player.seat,
            "pawns": list(player.pawns),
            "hand_count": len(player.hand),
            "online": player.id in connected_player_ids,
            "is_you": player.id == viewer.id,
            "partner_id": _partner(state, player).id if _is_paired(state) else None,
        }
        if player.id == viewer.id:
            row["hand"] = [dict(card) for card in player.hand]
        player_rows.append(row)

    current = next(
        (player for player in state.players if player.seat == state.current_seat),
        None,
    )
    return {
        "code": state.code,
        "status": state.status,
        "host": host,
        "host_player_id": state.host_player_id,
        "players": player_rows,
        "track_length": track_length,
        "layout": _layout_name(player_count),
        "piece_types": _piece_types(player_count),
        "deal_number": state.deal_number,
        "deal_in_cycle": state.deal_in_cycle,
        "hand_size": state.hand_size,
        "first_player_id": _player_at_seat(state, state.first_seat).id
        if state.status != "lobby"
        else None,
        "current_player_id": current.id if current and state.status == "playing" else None,
        "waiting_for_reconnect": bool(
            current
            and state.status == "playing"
            and current.id not in connected_player_ids
        ),
        "winner_player_ids": list(state.winner_player_ids),
        "notices": list(state.notices[-8:]),
        "legal_actions": legal_actions(state, viewer),
    }


def to_dict(state: GameState) -> dict[str, Any]:
    return asdict(state)


def from_dict(data: dict[str, Any]) -> GameState:
    values = dict(data)
    values["players"] = [Player(**player) for player in values["players"]]
    return GameState(**values)


def _validate_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise GameError("Enter a display name.")
    if len(normalized) > 24:
        raise GameError("Display names must be 24 characters or fewer.")
    return normalized


def _layout_name(player_count: int) -> str:
    if player_count == 4:
        return "four 90-degree pieces"
    if player_count == 6:
        return "four 90-degree and two 180-degree pieces"
    if player_count == 8:
        return "four 90-degree and four 180-degree pieces"
    return "custom"


def _piece_types(player_count: int) -> list[str]:
    if player_count == 4:
        return ["90"] * 4
    if player_count == 6:
        return ["90", "90", "180", "90", "90", "180"]
    if player_count == 8:
        return ["90", "180"] * 4
    return ["custom"] * player_count


def _deal_next(state: GameState) -> None:
    if state.deal_number == 0:
        state.deal_in_cycle = 1
        state.deck = _new_deck(state.deal_number + 1, len(state.players))
        state.discard_pile.clear()
        state.first_seat = 0
        state.hand_size = 5
    elif state.deal_in_cycle == 3:
        state.deal_in_cycle = 1
        state.deck = _new_deck(state.deal_number + 1, len(state.players))
        state.discard_pile.clear()
        state.first_seat = (state.first_seat + 1) % len(state.players)
        state.hand_size = 5
    else:
        state.deal_in_cycle += 1
        state.first_seat = (state.first_seat + 1) % len(state.players)
        state.hand_size = 4
    state.deal_number += 1

    ordered = sorted(state.players, key=lambda item: (item.seat - state.first_seat) % len(state.players))
    for player in state.players:
        player.hand.clear()
    for player in ordered:
        for _ in range(state.hand_size):
            if not state.deck:
                raise RuntimeError("The deal exhausted the deck unexpectedly.")
            player.hand.append(state.deck.pop())

    for player in state.players:
        if not any(card["rank"] in ("A", "K") for card in player.hand):
            state.discard_pile.extend(player.hand)
            player.hand.clear()
            _add_notice(state, f"{player.name} had no Ace or King and discarded their hand.")


def _new_deck(cycle: int, player_count: int) -> list[dict[str, str]]:
    cards = [
        {
            "id": f"{cycle}-{player_index}-{rank}",
            "rank": rank,
            "suit": SUITS[player_index % len(SUITS)],
        }
        for player_index in range(player_count)
        for rank in RANKS
    ]
    secrets.SystemRandom().shuffle(cards)
    return cards


def _seek_turn(state: GameState, after_seat: int) -> None:
    empty_deals = 0
    while state.status == "playing":
        ordered_seats = [
            (after_seat + offset) % len(state.players)
            for offset in range(1, len(state.players) + 1)
        ]
        found = False
        for seat in ordered_seats:
            player = _player_at_seat(state, seat)
            if not player.hand:
                continue
            if not any(_legal_actions_for_card(state, player, card) for card in player.hand):
                state.discard_pile.extend(player.hand)
                player.hand.clear()
                _add_notice(state, f"{player.name} had no legal move; their hand was discarded.")
                continue
            state.current_seat = seat
            found = True
            break
        if found:
            return

        _deal_next(state)
        after_seat = state.first_seat - 1
        empty_deals += 1
        if empty_deals >= MAX_EMPTY_DEALS:
            state.status = "stalled"
            _add_notice(state, "No legal moves are available. The host can create a new room.")
            return


def _legal_actions_for_card(
    state: GameState,
    player: Player,
    card: dict[str, str],
) -> list[dict[str, Any]]:
    rank = card["rank"]
    result: list[dict[str, Any]] = []
    controlled = [
        _player_by_id(state, player_id)
        for player_id in controlled_player_ids(state, player)
    ]

    if rank in ("A", "K"):
        if rank == "A":
            for owner in controlled:
                for pawn_index, position in enumerate(owner.pawns):
                    if position >= 0 and _can_move(state, owner, pawn_index, 1):
                        result.append(
                            {
                                "card_id": card["id"],
                                "type": "move",
                                "moves": [{"player_id": owner.id, "pawn": pawn_index, "steps": 1}],
                            }
                        )
        for owner in controlled:
            for pawn_index, position in enumerate(owner.pawns):
                if position == -1 and _can_setup(state, owner):
                    result.append(
                        {
                            "card_id": card["id"],
                            "type": "setup",
                            "moves": [{"player_id": owner.id, "pawn": pawn_index}],
                        }
                    )
        return result

    if rank == "J":
        for owner in controlled:
            for pawn_index, position in enumerate(owner.pawns):
                if position < 0 or position >= _track_length(state) or _is_protected(state, owner, pawn_index):
                    continue
                for target in state.players:
                    if target.id == owner.id:
                        continue
                    for target_index, target_position in enumerate(target.pawns):
                        if (
                            0 <= target_position < _track_length(state)
                            and not _is_protected(state, target, target_index)
                        ):
                            result.append(
                                {
                                    "card_id": card["id"],
                                    "type": "swap",
                                    "moves": [
                                        {
                                            "player_id": owner.id,
                                            "pawn": pawn_index,
                                            "target_player_id": target.id,
                                            "target_pawn": target_index,
                                        }
                                    ],
                                }
                            )
        return result

    if rank == "7":
        for owner in controlled:
            for pawn_index in range(4):
                if _can_move(state, owner, pawn_index, 7):
                    result.append(
                        {
                            "card_id": card["id"],
                            "type": "move",
                            "moves": [{"player_id": owner.id, "pawn": pawn_index, "steps": 7}],
                        }
                    )
        if _is_paired(state) and _team_pawns_out(state, player) > 1:
            for first_owner in controlled:
                for first_pawn in range(4):
                    for first_steps in range(1, 7):
                        if not _can_move(state, first_owner, first_pawn, first_steps):
                            continue
                        simulated = copy.deepcopy(state)
                        simulated_owner = _player_by_id(simulated, first_owner.id)
                        _apply_move(simulated, simulated_owner, first_pawn, first_steps)
                        simulated_actor = _player_by_id(simulated, player.id)
                        second_owners = [
                            _player_by_id(simulated, player_id)
                            for player_id in controlled_player_ids(simulated, simulated_actor)
                        ]
                        for second_owner in second_owners:
                            for second_pawn in range(4):
                                if (second_owner.id, second_pawn) == (first_owner.id, first_pawn):
                                    continue
                                second_steps = 7 - first_steps
                                if _can_move(simulated, second_owner, second_pawn, second_steps):
                                    after_split = copy.deepcopy(simulated)
                                    _apply_move(
                                        after_split,
                                        _player_by_id(after_split, second_owner.id),
                                        second_pawn,
                                        second_steps,
                                    )
                                    if _team_pawns_out(
                                        after_split,
                                        _player_by_id(after_split, player.id),
                                    ) == 0:
                                        continue
                                    result.append(
                                        {
                                            "card_id": card["id"],
                                            "type": "split",
                                            "moves": [
                                                {
                                                    "player_id": first_owner.id,
                                                    "pawn": first_pawn,
                                                    "steps": first_steps,
                                                },
                                                {
                                                    "player_id": second_owner.id,
                                                    "pawn": second_pawn,
                                                    "steps": second_steps,
                                                },
                                            ],
                                        }
                                    )
        return result

    if rank == "4":
        step_count = -4
    elif rank == "Q":
        step_count = 12
    else:
        step_count = int(rank)

    for owner in controlled:
        for pawn_index in range(4):
            if _can_move(state, owner, pawn_index, step_count):
                result.append(
                    {
                        "card_id": card["id"],
                        "type": "move",
                        "moves": [
                            {"player_id": owner.id, "pawn": pawn_index, "steps": step_count}
                        ],
                    }
                )
    return result


def _can_setup(state: GameState, player: Player) -> bool:
    start = (player.seat * 16) % _track_length(state)
    return not any(
        0 <= position < _track_length(state)
        and _global_position(other, position, state) == start
        for other in state.players
        for position in other.pawns
    )


def _can_move(state: GameState, player: Player, pawn_index: int, steps: int) -> bool:
    position = player.pawns[pawn_index]
    if position < 0 or steps == 0:
        return False
    track_length = _track_length(state)
    if steps < 0:
        if position >= track_length:
            return False
        for distance in range(1, -steps + 1):
            progress = (position - distance) % track_length
            global_position = _global_position(player, progress, state)
            if _protected_occupant(state, global_position, player.id, pawn_index):
                return False
        return True

    target = position + steps
    if target > track_length + 3:
        return False
    for distance in range(1, steps + 1):
        progress = position + distance
        if progress < track_length:
            global_position = _global_position(player, progress, state)
            if _protected_occupant(state, global_position, player.id, pawn_index):
                return False
        elif _home_occupied(state, player, progress, player.id, pawn_index):
            return False
    return True


def _apply_action(state: GameState, action: dict[str, Any]) -> None:
    for move in action["moves"]:
        owner = _player_by_id(state, move["player_id"])
        if action["type"] == "setup":
            owner.pawns[move["pawn"]] = 0
        elif action["type"] == "swap":
            target = _player_by_id(state, move["target_player_id"])
            _apply_swap(state, owner, move["pawn"], target, move["target_pawn"])
        else:
            _apply_move(state, owner, move["pawn"], move["steps"])


def _apply_move(state: GameState, player: Player, pawn_index: int, steps: int) -> None:
    track_length = _track_length(state)
    position = player.pawns[pawn_index]
    target = (position + steps) % track_length if steps < 0 else position + steps
    if target < track_length:
        global_target = _global_position(player, target, state)
        for other in state.players:
            for index, other_position in enumerate(other.pawns):
                if (
                    other.id != player.id or index != pawn_index
                ) and 0 <= other_position < track_length:
                    if _global_position(other, other_position, state) == global_target:
                        other.pawns[index] = -1
    player.pawns[pawn_index] = target


def _apply_swap(
    state: GameState,
    first_player: Player,
    first_pawn: int,
    second_player: Player,
    second_pawn: int,
) -> None:
    first_position = first_player.pawns[first_pawn]
    second_position = second_player.pawns[second_pawn]
    first_global = _global_position(first_player, first_position, state)
    second_global = _global_position(second_player, second_position, state)
    track_length = _track_length(state)
    first_player.pawns[first_pawn] = (second_global - first_player.seat * 16) % track_length
    second_player.pawns[second_pawn] = (first_global - second_player.seat * 16) % track_length


def _find_winner(state: GameState) -> list[str]:
    if not _is_paired(state):
        return [
            player.id
            for player in state.players
            if _all_home(state, player)
        ][:1]
    for player in state.players:
        partner = _partner(state, player)
        if _all_home(state, player) and _all_home(state, partner):
            return [player.id, partner.id]
    return []


def _team_pawns_out(state: GameState, player: Player) -> int:
    teammates = _team_members(state, player)
    track_length = _track_length(state)
    return sum(
        position < track_length
        for teammate in teammates
        for position in teammate.pawns
    )


def _all_home(state: GameState, player: Player) -> bool:
    track_length = _track_length(state)
    return all(position >= track_length for position in player.pawns)


def _team_members(state: GameState, player: Player) -> list[Player]:
    if not _is_paired(state):
        return [player]
    partner = _partner(state, player)
    return [player, partner]


def _is_paired(state: GameState) -> bool:
    return len(state.players) >= 4 and len(state.players) % 2 == 0


def _partner(state: GameState, player: Player) -> Player:
    offset = len(state.players) // 2
    return _player_at_seat(state, (player.seat + offset) % len(state.players))


def _track_length(state: GameState) -> int:
    return len(state.players) * 16


def _global_position(player: Player, progress: int, state: GameState) -> int:
    return (player.seat * 16 + progress) % _track_length(state)


def _is_protected(state: GameState, player: Player, pawn_index: int) -> bool:
    return player.pawns[pawn_index] == 0


def _protected_occupant(
    state: GameState,
    global_position: int,
    excluded_player_id: str,
    excluded_pawn: int,
) -> bool:
    for player in state.players:
        for pawn_index, position in enumerate(player.pawns):
            if (
                player.id != excluded_player_id or pawn_index != excluded_pawn
            ) and position == 0 and _global_position(player, position, state) == global_position:
                return True
    return False


def _home_occupied(
    state: GameState,
    player: Player,
    home_position: int,
    excluded_player_id: str,
    excluded_pawn: int,
) -> bool:
    for other in state.players:
        for pawn_index, position in enumerate(other.pawns):
            if (
                other.id != excluded_player_id or pawn_index != excluded_pawn
            ) and other.id == player.id and position == home_position:
                return True
    return False


def _player_at_seat(state: GameState, seat: int) -> Player:
    normalized_seat = seat % len(state.players)
    return next(player for player in state.players if player.seat == normalized_seat)


def _player_by_id(state: GameState, player_id: str) -> Player:
    return next(player for player in state.players if player.id == player_id)


def _describe_action(
    state: GameState,
    player: Player,
    card: dict[str, str],
    action: dict[str, Any],
) -> str:
    if action["type"] == "setup":
        move = action["moves"][0]
        owner = _player_by_id(state, move["player_id"])
        return f"{player.name} played {card['rank']} to set up {owner.name}'s pawn {move['pawn'] + 1}."
    if action["type"] == "swap":
        move = action["moves"][0]
        target = _player_by_id(state, move["target_player_id"])
        return f"{player.name} swapped a pawn with {target.name} using a Jack."
    if action["type"] == "split":
        return f"{player.name} split a Seven across two pawns."
    move = action["moves"][0]
    owner = _player_by_id(state, move["player_id"])
    return f"{player.name} played {card['rank']} and moved {owner.name}'s pawn {move['pawn'] + 1}."


def _add_notice(state: GameState, message: str) -> None:
    state.notices.append(message)
    del state.notices[:-20]
