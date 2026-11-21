from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from keezboard import engine
from keezboard.engine import GameError, add_player, legal_actions, new_room, play_action
from keezboard.storage import StateStore


def build_state(player_count: int) -> engine.GameState:
    state = new_room("Player 1")
    for number in range(2, player_count + 1):
        add_player(state, f"Player {number}")
    state.status = "playing"
    state.current_seat = 0
    state.players.sort(key=lambda player: player.seat)
    return state


def make_card(card_id: str, rank: str) -> dict[str, str]:
    return {"id": card_id, "rank": rank, "suit": "hearts"}


class GameEngineTests(unittest.TestCase):
    def test_start_requires_three_players_and_seven_succeeds(self) -> None:
        state = build_state(2)
        state.status = "lobby"
        with self.assertRaisesRegex(GameError, "between three and eight"):
            engine.start_game(state)

        add_player(state, "Player 3")
        draw_order = [
            make_card(f"card-{index}", "A" if index in (0, 5, 10) else "2")
            for index in range(39)
        ]
        with patch("keezboard.engine._new_deck", return_value=list(reversed(draw_order))):
            engine.start_game(state)
        self.assertEqual(state.status, "playing")
        self.assertEqual(state.deal_number, 1)
        self.assertEqual(state.hand_size, 5)

    def test_deals_five_four_four_and_rotates_the_first_seat(self) -> None:
        state = build_state(4)
        draw_order = []
        for index in range(52):
            rank = "A" if index in (0, 5, 10, 15) else "2"
            draw_order.append(make_card(f"card-{index}", rank))
        ordered_deck = list(reversed(draw_order))

        with patch(
            "keezboard.engine._new_deck",
            side_effect=lambda *args: ordered_deck.copy(),
        ):
            engine._deal_next(state)
            self.assertEqual([len(player.hand) for player in state.players], [5, 5, 5, 5])
            self.assertEqual((state.hand_size, state.first_seat), (5, 0))

            for player in state.players:
                player.hand.clear()
            engine._deal_next(state)
            self.assertEqual((state.hand_size, state.first_seat), (4, 1))

            for player in state.players:
                player.hand.clear()
            engine._deal_next(state)
            self.assertEqual((state.hand_size, state.first_seat), (4, 2))

            for player in state.players:
                player.hand.clear()
            engine._deal_next(state)
            self.assertEqual((state.hand_size, state.first_seat), (5, 3))

    def test_deck_has_one_thirteen_card_suit_set_per_player(self) -> None:
        for player_count in range(3, 9):
            with self.subTest(player_count=player_count):
                deck = engine._new_deck(1, player_count)
                self.assertEqual(len(deck), 13 * player_count)
                self.assertTrue(
                    all(
                        sum(card["rank"] == rank for card in deck) == player_count
                        for rank in engine.RANKS
                    )
                )
                expected_suits = Counter(
                    engine.SUITS[index % len(engine.SUITS)]
                    for index in range(player_count)
                )
                self.assertEqual(
                    Counter(card["suit"] for card in deck),
                    Counter({suit: count * 13 for suit, count in expected_suits.items()}),
                )

    def test_public_board_dimensions_cover_every_supported_player_count(self) -> None:
        expected_layouts = {
            3: "custom",
            4: "four 90-degree pieces",
            5: "custom",
            6: "four 90-degree and two 180-degree pieces",
            7: "custom",
            8: "four 90-degree and four 180-degree pieces",
        }
        expected_pieces = {
            3: ["custom"] * 3,
            4: ["90"] * 4,
            5: ["custom"] * 5,
            6: ["90", "90", "180", "90", "90", "180"],
            7: ["custom"] * 7,
            8: ["90", "180"] * 4,
        }
        for player_count, layout in expected_layouts.items():
            with self.subTest(player_count=player_count):
                state = build_state(player_count)
                view = engine.public_state(state, state.players[0], set(), False)
                self.assertEqual(view["track_length"], player_count * 16)
                self.assertEqual(view["layout"], layout)
                self.assertEqual(view["piece_types"], expected_pieces[player_count])
                self.assertTrue(all(len(player.pawns) == 4 for player in state.players))

    def test_odd_games_have_no_partners_and_even_seats_pair_oppositely(self) -> None:
        odd = build_state(3)
        even = build_state(6)
        odd_view = engine.public_state(odd, odd.players[0], set(), False)
        even_view = engine.public_state(even, even.players[1], set(), False)

        self.assertTrue(all(player["partner_id"] is None for player in odd_view["players"]))
        self.assertEqual(
            even_view["players"][1]["partner_id"],
            even.players[4].id,
        )

    def test_move_captures_an_unprotected_pawn_but_cannot_pass_a_protected_start(self) -> None:
        state = build_state(3)
        mover, _, opponent = state.players
        mover.pawns[0] = 5
        opponent.pawns[0] = (8 - opponent.seat * 16) % 48
        card = make_card("three", "3")
        mover.hand = [card]

        capture = next(action for action in legal_actions(state, mover) if action["card_id"] == "three")
        play_action(state, mover, capture)
        self.assertEqual(mover.pawns[0], 8)
        self.assertEqual(opponent.pawns[0], -1)

        state = build_state(3)
        mover = state.players[2]
        protected = state.players[0]
        state.current_seat = mover.seat
        mover.pawns[0] = 15
        protected.pawns[0] = 0
        mover.hand = [make_card("ace", "A")]
        actions = legal_actions(state, mover)
        self.assertFalse(
            any(
                action["type"] == "move"
                and action["moves"][0]["player_id"] == mover.id
                and action["moves"][0]["pawn"] == 0
                for action in actions
            )
        )

    def test_home_lane_blocks_overshoot_and_occupied_home_cells(self) -> None:
        state = build_state(3)
        player = state.players[0]
        player.pawns[0] = 47
        player.hand = [make_card("seven", "7")]
        actions = legal_actions(state, player)
        self.assertFalse(
            any(
                action["moves"][0]["pawn"] == 0
                and action["moves"][0]["steps"] == 7
                for action in actions
            )
        )

        player.pawns[0] = 46
        player.pawns[1] = 48
        player.hand = [make_card("two", "2")]
        self.assertFalse(
            any(
                action["moves"][0]["pawn"] == 0
                for action in legal_actions(state, player)
            )
        )

    def test_split_seven_forces_the_partner_after_the_last_own_pawn_enters_home(self) -> None:
        state = build_state(4)
        player = state.players[0]
        partner = state.players[2]
        player.pawns = [62, 65, 66, 67]
        partner.pawns[0] = 5
        partner.pawns[1:] = [65, 66, 67]
        player.hand = [make_card("seven", "7")]

        splits = [
            action
            for action in legal_actions(state, player)
            if action["type"] == "split"
            and action["moves"][0]["player_id"] == player.id
            and action["moves"][0]["pawn"] == 0
            and action["moves"][0]["steps"] == 2
        ]
        self.assertTrue(splits)
        self.assertTrue(all(action["moves"][1]["player_id"] == partner.id for action in splits))
        self.assertTrue(all(action["moves"][1]["steps"] == 5 for action in splits))

        partner.pawns = [64, 65, 66, 67]
        self.assertFalse(
            any(action["type"] == "split" for action in legal_actions(state, player))
        )

    def test_split_seven_cannot_finish_the_team(self) -> None:
        state = build_state(4)
        player = state.players[0]
        partner = state.players[2]
        player.pawns = [62, 65, 66, 67]
        partner.pawns = [59, 65, 66, 67]
        player.hand = [make_card("seven", "7")]

        self.assertFalse(
            any(
                action["type"] == "split"
                and [move["steps"] for move in action["moves"]] == [2, 5]
                for action in legal_actions(state, player)
            )
        )

    def test_jack_cannot_swap_a_pawn_on_its_protected_start(self) -> None:
        state = build_state(3)
        player = state.players[0]
        opponent = state.players[1]
        player.pawns[0] = 0
        opponent.pawns[0] = 4
        player.hand = [make_card("jack", "J")]

        self.assertFalse(
            any(
                action["type"] == "swap"
                and action["moves"][0]["player_id"] == player.id
                and action["moves"][0]["pawn"] == 0
                for action in legal_actions(state, player)
            )
        )

    def test_no_legal_move_discards_the_whole_hand_and_notifies(self) -> None:
        state = build_state(3)
        stuck, next_player, _ = state.players
        stuck.pawns = [0, 1, 2, 3]
        stuck.hand = [make_card("king", "K")]
        next_player.hand = [make_card("ace", "A")]

        engine._seek_turn(state, 2)

        self.assertEqual(stuck.hand, [])
        self.assertEqual(state.current_seat, next_player.seat)
        self.assertTrue(any("no legal move" in notice for notice in state.notices))

    def test_final_pawn_home_ends_a_paired_game(self) -> None:
        state = build_state(4)
        player = state.players[0]
        partner = state.players[2]
        player.pawns = [63, 65, 66, 67]
        partner.pawns = [64, 65, 66, 67]
        player.hand = [make_card("ace", "A")]
        action = next(
            action
            for action in legal_actions(state, player)
            if action["moves"][0]["pawn"] == 0
        )

        play_action(state, player, action)

        self.assertEqual(state.status, "finished")
        self.assertEqual(set(state.winner_player_ids), {player.id, partner.id})

    def test_final_pawn_home_ends_an_odd_game(self) -> None:
        state = build_state(3)
        player = state.players[0]
        player.pawns = [47, 49, 50, 51]
        player.hand = [make_card("ace", "A")]
        action = next(
            action
            for action in legal_actions(state, player)
            if action["moves"][0]["pawn"] == 0
        )

        play_action(state, player, action)

        self.assertEqual(state.status, "finished")
        self.assertEqual(state.winner_player_ids, [player.id])

    def test_private_state_contains_only_viewers_hand(self) -> None:
        state = build_state(3)
        state.players[0].hand = [make_card("private-a", "A")]
        state.players[1].hand = [make_card("private-k", "K")]

        viewer_state = engine.public_state(state, state.players[0], set(), False)

        self.assertEqual(viewer_state["players"][0]["hand"][0]["id"], "private-a")
        self.assertNotIn("hand", viewer_state["players"][1])
        self.assertNotIn("private-k", str(viewer_state))

    def test_room_state_round_trips_through_sqlite(self) -> None:
        state = build_state(3)
        state.players[0].hand = [make_card("saved", "A")]
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "game.sqlite3")
            store.initialize()
            store.save(state)
            restored = store.load()

        self.assertIsNotNone(restored)
        self.assertEqual(restored.code, state.code)
        self.assertEqual(restored.players[0].hand, state.players[0].hand)
        self.assertEqual(restored.players[0].pawns, state.players[0].pawns)


if __name__ == "__main__":
    unittest.main()
