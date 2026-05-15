from engine.rules import has_double_end_block


def make_board(size=19):
    return [[0 for _ in range(size)] for _ in range(size)]


def test_single_stone_double_end_block_counts():
    board = make_board()
    # 对手单子在(6,5)，远端(7,5)被己方或任意棋子封住
    board[5][6] = 2
    board[5][7] = 1
    # 当前落子在(5,5)封住近端
    board[5][5] = 1

    assert has_double_end_block(board, 5, 5, 1, 19) is True


def test_not_double_end_block_when_far_end_open():
    board = make_board()
    board[5][6] = 2
    board[5][5] = 1
    # far end (7,5) is empty

    assert has_double_end_block(board, 5, 5, 1, 19) is False


def test_multiple_runs_still_boolean_true_once():
    board = make_board()
    # 横向一段被双端封
    board[9][10] = 2
    board[9][11] = 1
    board[9][9] = 1  # 当前落子

    # 纵向另一段也被双端封（同一落子点另一方向）
    board[8][9] = 2
    board[7][9] = 1

    assert has_double_end_block(board, 9, 9, 1, 19) is True
