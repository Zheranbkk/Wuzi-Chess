"""Centralized runtime state for Wuzi Chess (phase 2A)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameState:
    board_size: int = 19

    board: list[list[int]] = field(default_factory=list)
    forbidden: list[list[bool]] = field(default_factory=list)

    black_turn: bool = True
    winner: int = 0
    again_rect: object | None = None
    quit_rect: object | None = None

    black_hand: list[str] = field(default_factory=list)
    white_hand: list[str] = field(default_factory=list)
    black_has_acted: bool = False
    white_has_acted: bool = False

    selected_card: str | None = None
    selected_card_owner: str | None = None
    last_card_played: str | None = None

    barriers: list[tuple[int, int]] = field(default_factory=list)
    barriers_centers: list[tuple[int, int]] = field(default_factory=list)

    confuse_turns_left: int = 0
    cards_locked: bool = False
    card_waiting_target: bool = False

    left_hand: list[str] = field(default_factory=list)
    right_hand: list[str] = field(default_factory=list)

    ghost_mode: bool = False
    ghost_rounds_left: int = 0
    ghost_board_snapshot: list[list[int]] = field(default_factory=list)
    ghost_recent_moves: list[tuple[int, int, int]] = field(default_factory=list)
    ghost_start_time: int | None = None

    tetris_mode: bool = False
    tetris_turn: int = 0
    tetris_current_player: str = "black"
    tetris_active_block: object | None = None
    tetris_last_fall_time: int = 0
    tetris_fall_interval: int = 500
    current_shape: list[tuple[int, int]] | None = None
    current_pos: tuple[int, int] | None = None
    tetris_color: int | None = None
    tetris_blocks_remaining: int = 7

    piece_color: int | None = None
    acting_hand: list[str] | None = None
    has_acted_flag: str | None = None

    def __post_init__(self) -> None:
        if not self.board:
            self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        if not self.forbidden:
            self.forbidden = [[False for _ in range(self.board_size)] for _ in range(self.board_size)]
        if not self.left_hand:
            self.left_hand = self.white_hand
        if not self.right_hand:
            self.right_hand = self.black_hand

    def reset_match(self) -> None:
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.forbidden = [[False for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.black_hand.clear()
        self.white_hand.clear()
        self.left_hand = self.white_hand
        self.right_hand = self.black_hand

        self.black_turn = True
        self.winner = 0
        self.again_rect = None
        self.quit_rect = None
        self.black_has_acted = False
        self.white_has_acted = False

        self.selected_card = None
        self.selected_card_owner = None
        self.last_card_played = None

        self.barriers.clear()
        self.barriers_centers.clear()

        self.confuse_turns_left = 0
        self.cards_locked = False
        self.card_waiting_target = False

        self.ghost_mode = False
        self.ghost_rounds_left = 0
        self.ghost_board_snapshot.clear()
        self.ghost_recent_moves.clear()
        self.ghost_start_time = None

        self.tetris_mode = False
        self.tetris_turn = 0
        self.tetris_current_player = "black"
        self.tetris_active_block = None
        self.tetris_last_fall_time = 0
        self.current_shape = None
        self.current_pos = None
        self.tetris_color = None
        self.tetris_blocks_remaining = 7

        self.piece_color = None
        self.acting_hand = None
        self.has_acted_flag = None
