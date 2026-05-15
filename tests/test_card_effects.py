from engine.card_effects import CardContext, play_immediate_card
from engine.state import GameState


class FakeClock:
    def __init__(self, now: int = 1234):
        self.now = now

    def __call__(self):
        return self.now


def test_restock_draws_two_cards_and_switches_turn():
    state = GameState()
    state.black_turn = True
    hand = ["库存补充"]
    state.black_hand = hand
    switch_called = {"count": 0}

    def switch_turn():
        switch_called["count"] += 1

    ctx = CardContext(
        state=state,
        player_hand=hand,
        player_color="black",
        all_cards=["定位混淆", "贼不走空"],
        random_choice=lambda cards: cards[0],
        now_ms=FakeClock(),
        start_tetris=lambda _: None,
        switch_turn=switch_turn,
        tr=lambda k: k,
    )

    play_immediate_card("库存补充", ctx, 0)

    assert len(hand) == 2
    assert switch_called["count"] == 1
    assert state.black_has_acted is True


def test_ghost_card_locks_cards_and_sets_timer():
    state = GameState()
    hand = ["幽灵棋子"]
    state.white_hand = hand
    state.board[0][0] = 1
    switch_called = {"count": 0}

    def switch_turn():
        switch_called["count"] += 1

    clock = FakeClock(9876)
    ctx = CardContext(
        state=state,
        player_hand=hand,
        player_color="white",
        all_cards=[],
        random_choice=lambda cards: cards[0],
        now_ms=clock,
        start_tetris=lambda _: None,
        switch_turn=switch_turn,
        tr=lambda k: k,
    )

    play_immediate_card("幽灵棋子", ctx, 0)

    assert state.cards_locked is True
    assert state.ghost_start_time == 9876
    assert switch_called["count"] == 1
    assert state.white_has_acted is True


def test_swap_hands_consumes_card_before_swap():
    state = GameState()
    state.black_hand = ["战术换家", "A"]
    state.white_hand = ["B"]

    ctx = CardContext(
        state=state,
        player_hand=state.black_hand,
        player_color="black",
        all_cards=[],
        random_choice=lambda cards: cards[0],
        now_ms=FakeClock(),
        start_tetris=lambda _: None,
        switch_turn=lambda: None,
        tr=lambda k: k,
    )

    play_immediate_card("战术换家", ctx, 0)

    assert "战术换家" not in state.white_hand
    assert state.black_hand == ["B"]
    assert state.white_hand == ["A"]
