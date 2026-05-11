"""Core rule utilities that can be tested independently of pygame."""

from __future__ import annotations

from typing import Iterable


def ccw(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def is_blocked(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    barriers_centers: Iterable[tuple[int, int]],
) -> bool:
    a = (x1 + 0.5, y1 + 0.5)
    b = (x2 + 0.5, y2 + 0.5)

    for cx, cy in barriers_centers:
        h1 = (cx - 0.5, cy + 0.5)
        h2 = (cx + 1.5, cy + 0.5)
        v1 = (cx + 0.5, cy - 0.5)
        v2 = (cx + 0.5, cy + 1.5)

        if segments_intersect(a, b, h1, h2) or segments_intersect(a, b, v1, v2):
            return True

    return False


def check_win(
    board: list[list[int]],
    x: int,
    y: int,
    color: int,
    board_size: int,
    barriers_centers: Iterable[tuple[int, int]],
) -> bool:
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for dx, dy in directions:
        count = 1

        i = 1
        while True:
            nx = x + dx * i
            ny = y + dy * i
            px = x + dx * (i - 1)
            py = y + dy * (i - 1)

            if 0 <= nx < board_size and 0 <= ny < board_size:
                if board[ny][nx] == color and not is_blocked(px, py, nx, ny, barriers_centers):
                    count += 1
                    i += 1
                else:
                    break
            else:
                break

        i = 1
        while True:
            nx = x - dx * i
            ny = y - dy * i
            px = x - dx * (i - 1)
            py = y - dy * (i - 1)

            if 0 <= nx < board_size and 0 <= ny < board_size:
                if board[ny][nx] == color and not is_blocked(px, py, nx, ny, barriers_centers):
                    count += 1
                    i += 1
                else:
                    break
            else:
                break

        if count >= 5:
            return True

    return False


def clear_matching_lines(board: list[list[int]], board_size: int) -> bool:
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    to_clear: set[tuple[int, int]] = set()

    for y in range(board_size):
        for x in range(board_size):
            color = board[y][x]
            if color not in [1, 2]:
                continue

            for dx, dy in directions:
                temp = [(x, y)]
                for i in range(1, 5):
                    nx = x + dx * i
                    ny = y + dy * i
                    if 0 <= nx < board_size and 0 <= ny < board_size and board[ny][nx] == color:
                        temp.append((nx, ny))
                    else:
                        break
                if len(temp) >= 5:
                    to_clear.update(temp)

    for x, y in to_clear:
        board[y][x] = 0

    return len(to_clear) > 0
