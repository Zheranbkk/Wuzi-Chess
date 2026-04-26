from engine.card_effects import CardContext, play_immediate_card
from engine.rules import check_win, clear_matching_lines
from engine.state import GameState


def make_ctx(state: GameState, hand: list[str], player_color: str):
    return CardContext(
        state=state,
        player_hand=hand,
        player_color=player_color,
        all_cards=["定位混淆", "库存补充", "贼不走空"],
        random_choice=lambda cards: cards[0],
        now_ms=lambda: 5000,
        start_tetris=lambda _: None,
        switch_turn=lambda: None,
    )


def test_tetris_activation_consumes_confuse_and_locks_cards():
    state = GameState()
    state.confuse_turns_left = 2
    hand = ["俄罗斯方块！"]

    play_immediate_card("俄罗斯方块！", make_ctx(state, hand, "black"), 0)

    assert state.tetris_mode is True
    assert state.cards_locked is True
    assert state.confuse_turns_left == 1
    assert state.black_has_acted is True


def test_ghost_activation_keeps_confuse_counter_but_locks_cards():
    state = GameState()
    state.confuse_turns_left = 2
    state.board[0][0] = 1
    hand = ["幽灵棋子"]

    play_immediate_card("幽灵棋子", make_ctx(state, hand, "white"), 0)

    assert state.cards_locked is True
    assert state.ghost_start_time == 5000
    # 幽灵棋子不消耗定位混淆回合
    assert state.confuse_turns_left == 2
    assert state.white_has_acted is True


def test_barrier_blocks_win_even_with_five_in_row():
    board = [[0 for _ in range(19)] for _ in range(19)]
    y = 9
    for x in range(2, 7):
        board[y][x] = 1

    # 在连线上放置一个屏障中心，阻断连线
    barriers_centers = [(4, y)]

    assert check_win(board, 4, y, 1, 19, barriers_centers) is False


def test_clear_matching_lines_ignores_ghost_pieces():
    board = [[0 for _ in range(19)] for _ in range(19)]
    for x in range(5):
        board[3][x] = 3  # 幽灵棋子颜色

    changed = clear_matching_lines(board, 19)

    assert changed is False
    assert all(board[3][x] == 3 for x in range(5))


def test_swap_hands_also_consumes_confuse_turn_once():
    state = GameState()
    state.confuse_turns_left = 3
    state.black_hand = ["战术换家", "A"]
    state.white_hand = ["B"]

    play_immediate_card("战术换家", make_ctx(state, state.black_hand, "black"), 0)

    assert state.confuse_turns_left == 2
    assert state.black_hand == ["B"]
    assert state.white_hand == ["A"]
