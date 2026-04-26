from engine.rules import check_win, clear_matching_lines


def make_board(size=19):
    return [[0 for _ in range(size)] for _ in range(size)]


def test_check_win_horizontal_without_barrier():
    board = make_board()
    y = 10
    for x in range(3, 8):
        board[y][x] = 1

    assert check_win(board, 5, y, 1, 19, []) is True


def test_check_win_blocked_by_barrier():
    board = make_board()
    y = 10
    for x in range(3, 8):
        board[y][x] = 1

    barriers_centers = [(5, y)]
    assert check_win(board, 5, y, 1, 19, barriers_centers) is False


def test_clear_matching_lines_clears_five_in_row():
    board = make_board()
    y = 2
    for x in range(0, 5):
        board[y][x] = 2

    changed = clear_matching_lines(board, 19)

    assert changed is True
    assert all(board[y][x] == 0 for x in range(0, 5))
