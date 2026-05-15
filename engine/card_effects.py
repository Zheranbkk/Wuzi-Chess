"""Card executor registry (phase 2B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.state import GameState
from engine.i18n import translate


@dataclass
class CardContext:
    state: GameState
    player_hand: list[str]
    player_color: str
    all_cards: list[str]
    random_choice: Callable[[list[str]], str]
    now_ms: Callable[[], int]
    start_tetris: Callable[[str], None]
    switch_turn: Callable[[], None]
    tr: Callable[[str], str]


def _actor_label(player_color: str) -> str:
    return "label.black" if player_color == "black" else "label.white"


def _set_acted(state: GameState, player_color: str) -> None:
    if player_color == "black":
        state.black_has_acted = True
    else:
        state.white_has_acted = True


def _consume_confuse_and_switch(state: GameState, switch_turn: Callable[[], None]) -> None:
    if state.confuse_turns_left > 0:
        state.confuse_turns_left -= 1
    switch_turn()


def _play_then_finish(ctx: CardContext, idx: int) -> None:
    ctx.player_hand.pop(idx)
    _set_acted(ctx.state, ctx.player_color)
    _consume_confuse_and_switch(ctx.state, ctx.switch_turn)


def _card_confuse(ctx: CardContext, idx: int) -> None:
    ctx.state.confuse_turns_left = 3
    ctx.state.last_card_played = translate(ctx.state.language, "tip.used_confuse", actor=ctx.tr(_actor_label(ctx.player_color)))
    _play_then_finish(ctx, idx)


def _card_lock_cards(ctx: CardContext, idx: int) -> None:
    ctx.state.cards_locked = True
    ctx.state.last_card_played = translate(ctx.state.language, "tip.used_lock")
    _play_then_finish(ctx, idx)


def _card_steal(ctx: CardContext, idx: int) -> None:
    if ctx.player_color == "black":
        opponent_hand = ctx.state.white_hand
        self_hand = ctx.state.black_hand
    else:
        opponent_hand = ctx.state.black_hand
        self_hand = ctx.state.white_hand

    if opponent_hand:
        stolen_card = ctx.random_choice(opponent_hand)
        opponent_hand.remove(stolen_card)
        self_hand.append(stolen_card)
        ctx.state.last_card_played = translate(ctx.state.language, "tip.steal_success", actor=ctx.tr(_actor_label(ctx.player_color)), card=ctx.tr(f"card.{stolen_card}"))
    else:
        ctx.state.last_card_played = translate(ctx.state.language, "tip.steal_fail", actor=ctx.tr(_actor_label(ctx.player_color)))

    _play_then_finish(ctx, idx)


def _card_swap_hands(ctx: CardContext, idx: int) -> None:
    # 先从出牌者手牌中移除，再交换，避免移除错误目标手牌
    ctx.player_hand.pop(idx)
    ctx.state.black_hand, ctx.state.white_hand = ctx.state.white_hand, ctx.state.black_hand
    ctx.state.left_hand, ctx.state.right_hand = ctx.state.white_hand, ctx.state.black_hand
    ctx.state.last_card_played = translate(ctx.state.language, "tip.swap_hands", actor=ctx.tr(_actor_label(ctx.player_color)))

    _set_acted(ctx.state, ctx.player_color)
    _consume_confuse_and_switch(ctx.state, ctx.switch_turn)


def _card_restock(ctx: CardContext, idx: int) -> None:
    ctx.player_hand.pop(idx)
    for _ in range(2):
        ctx.player_hand.append(ctx.random_choice(ctx.all_cards))

    ctx.state.last_card_played = translate(ctx.state.language, "tip.restock", actor=ctx.tr(_actor_label(ctx.player_color)))
    _set_acted(ctx.state, ctx.player_color)
    _consume_confuse_and_switch(ctx.state, ctx.switch_turn)


def _card_ghost(ctx: CardContext, idx: int) -> None:
    ctx.state.ghost_board_snapshot = [row.copy() for row in ctx.state.board]
    ctx.state.ghost_recent_moves = []
    ctx.state.ghost_start_time = ctx.now_ms()
    ctx.state.cards_locked = True
    ctx.player_hand.pop(idx)

    _set_acted(ctx.state, ctx.player_color)
    ctx.state.last_card_played = translate(ctx.state.language, "tip.ghost_prepare", actor=ctx.tr(_actor_label(ctx.player_color)))
    ctx.switch_turn()


def _card_tetris(ctx: CardContext, idx: int) -> None:
    ctx.state.tetris_mode = True
    ctx.state.cards_locked = True
    ctx.state.tetris_turn = 0
    ctx.state.tetris_current_player = ctx.player_color
    ctx.start_tetris(ctx.player_color)

    ctx.state.last_card_played = translate(ctx.state.language, "tip.tetris_activate", actor=ctx.tr(_actor_label(ctx.player_color)))
    _play_then_finish(ctx, idx)


def _card_default(ctx: CardContext, idx: int, card_name: str) -> None:
    ctx.state.last_card_played = translate(
        ctx.state.language,
        "tip.card_used",
        actor=ctx.tr(_actor_label(ctx.player_color)),
        card=ctx.tr(f"card.{card_name}"),
    )
    _play_then_finish(ctx, idx)


CARD_EFFECT_HANDLERS: dict[str, Callable[[CardContext, int], None]] = {
    "定位混淆": _card_confuse,
    "回归基本功": _card_lock_cards,
    "贼不走空": _card_steal,
    "战术换家": _card_swap_hands,
    "库存补充": _card_restock,
    "幽灵棋子": _card_ghost,
    "俄罗斯方块！": _card_tetris,
}


DEPLOY_CARDS = {"两极反转", "战术核弹", "阴阳屏障"}


def play_immediate_card(card_name: str, ctx: CardContext, idx: int) -> bool:
    handler = CARD_EFFECT_HANDLERS.get(card_name)
    if handler is not None:
        handler(ctx, idx)
        return True

    _card_default(ctx, idx, card_name)
    return True
