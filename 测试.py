import pygame
import sys
import os
import random

import os
import sys
from engine.cards import ALL_CARDS, CARD_DESCRIPTIONS
from engine.card_effects import CardContext, DEPLOY_CARDS, play_immediate_card
from engine.i18n import translate
from engine.rules import check_win, clear_matching_lines, has_double_end_block
from engine.state import GameState

# 获取路径
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pygame.init()

#棋盘初始化参数
BOARD_SIZE = 19
CELL_SIZE = 40
GRID_TOP = 100
all_cards = ALL_CARDS # 全部卡牌列表
state = GameState(board_size=BOARD_SIZE)
tetris_shapes = {              # 俄罗斯方块的结构预设
    "square": [(0,0), (1,0), (0,1), (1,1)],
    "L": [(0,0), (0,1), (0,2), (1,2)],
    "cross": [(1,0), (0,1), (1,1), (2,1), (1,2)],
    "line": [(0,0), (0,1), (0,2), (0,3)],
    "Z": [(0,0), (1,0), (1,1), (2,1)],
    "T": [(0,0), (1,0), (2,0), (1,1)],
}
card_descriptions = CARD_DESCRIPTIONS


def tr(key, **kwargs):
    return translate(state.language, key, **kwargs)



def switch_turn():
    state.black_turn = not state.black_turn
    state.black_has_acted = False
    state.white_has_acted = False #落子与出牌逻辑的重置

def update_hand_display_order(): #默认白方手牌列表在左侧，黑方手牌列表在右侧
    state.left_hand = state.white_hand
    state.right_hand = state.black_hand

def generate_tetris_queue():
    types = ["square", "L", "cross", "long", "Z", "T"]
    queue = random.choices(types, k=6)
    while len(set(queue)) < 3:  # 至少出现3种不同的形状
        queue = random.choices(types, k=6)
    return queue

def generate_next_tetris_block():
    #推进轮次
    state.tetris_turn += 1

    if state.tetris_turn >= 7:
        return  # 所有6个方块已用完

    # 设置当前操作者
    if state.tetris_turn > 0:
        state.tetris_current_player = "white" if state.tetris_current_player == "black" else "black"

    # 获取形状类型（从队列中依次取）
    shape_type = random.choice(list(tetris_shapes.keys()))
    state.current_shape = tetris_shapes.get(shape_type, [(0, 0)])  # fallback 为 1格方块

    # 初始位置设在棋盘中上方
    state.current_pos = (BOARD_SIZE // 2, 0)

    # 黑方操作白块，白方操作黑块（即 state.tetris_color 是“棋盘颜色”，不是玩家颜色）
    state.tetris_color = 2 if state.tetris_current_player == "black" else 1


def handle_card_click(player_hand, player_turn, player_has_acted, player_color):
    if state.cards_locked:
        return
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for idx, card_name in enumerate(player_hand):
        padding = 10
        card_surface = font.render(tr(f"card.{card_name}"), True, (255, 255, 255))
        text_rect = card_surface.get_rect()
        box_width = text_rect.width + padding * 2
        box_height = text_rect.height + padding * 2

        if player_color == "white":
            card_x = GRID_LEFT - 150
            card_y = GRID_TOP + idx * (box_height + 10)
        else:
            card_x = GRID_LEFT + (BOARD_SIZE - 1) * CELL_SIZE + 50
            card_y = GRID_TOP + idx * (box_height + 10)

        card_rect = pygame.Rect(card_x, card_y, box_width, box_height)

        if card_rect.collidepoint(mouse_x, mouse_y) and not player_has_acted and player_turn:
        #手牌涉及棋盘部署元素
            if card_name in DEPLOY_CARDS:
                state.selected_card = card_name
                state.selected_card_owner = player_color
                state.card_waiting_target = True
                return
            # 执行即时卡牌（由注册表分发）
            card_ctx = CardContext(
                state=state,
                player_hand=player_hand,
                player_color=player_color,
                all_cards=all_cards,
                random_choice=random.choice,
                now_ms=pygame.time.get_ticks,
                start_tetris=lambda _: generate_next_tetris_block(),
                switch_turn=switch_turn,
                tr=tr,
            )
            play_immediate_card(card_name, card_ctx, idx)
            return

def reset_game(): #棋盘初始化
    state.reset_match()


#导入字体
def load_font():
    # 1) 优先使用随项目分发的本地中文字体
    local_font_paths = [
        os.path.join(BASE_DIR, "ZCOOLKuaiLe-Regular.ttf"),
        os.path.join(BASE_DIR, "assets", "fonts", "ZCOOLKuaiLe-Regular.ttf"),
        os.path.join(BASE_DIR, "assets", "fonts", "NotoSansSC-Regular.otf"),
        os.path.join(BASE_DIR, "assets", "fonts", "SourceHanSansSC-Regular.otf"),
    ]
    for font_path in local_font_paths:
        if os.path.exists(font_path):
            return pygame.font.Font(font_path, 24)

    # 2) 尝试系统常见中文字体（跨平台候选链）
    #    注意：SysFont 仅按名称匹配，若系统无此字体会回退到默认字体
    preferred_system_fonts = [
        "PingFang SC",
        "Heiti SC",
        "Hiragino Sans GB",
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "WenQuanYi Zen Hei",
    ]
    for font_name in preferred_system_fonts:
        try:
            matched = pygame.font.match_font(font_name)
            if matched:
                return pygame.font.Font(matched, 24)
        except pygame.error:
            continue

    # 3) 最后才使用通用 fallback（可能不含中文字形）
    return pygame.font.SysFont("Arial", 20)

font = load_font()


def choose_language():
    temp_screen = pygame.display.set_mode((700, 280))
    chooser_font = pygame.font.SysFont(None, 40)
    title_font = pygame.font.SysFont(None, 36)
    english_btn = pygame.Rect(90, 130, 220, 70)
    chinese_btn = pygame.Rect(390, 130, 220, 70)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if english_btn.collidepoint(x, y):
                    return "en"
                if chinese_btn.collidepoint(x, y):
                    return "zh-CN"

        temp_screen.fill((235, 220, 180))
        title = title_font.render("Select Language / 选择语言", True, (0, 0, 0))
        temp_screen.blit(title, title.get_rect(center=(350, 70)))
        pygame.draw.rect(temp_screen, (20, 20, 20), english_btn)
        pygame.draw.rect(temp_screen, (20, 20, 20), chinese_btn)
        en_text = chooser_font.render("English", True, (255, 255, 255))
        zh_text = chooser_font.render("简体中文", True, (255, 255, 255))
        temp_screen.blit(en_text, en_text.get_rect(center=english_btn.center))
        temp_screen.blit(zh_text, zh_text.get_rect(center=chinese_btn.center))
        pygame.display.flip()

def load_scaled_image_or_none(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
    except pygame.error:
        return None


# 导入棋子素材（缺失时自动降级为纯绘制）
BP_img = load_scaled_image_or_none("BlackP.png")
WP_img = load_scaled_image_or_none("WhiteP.png")
GP_img = load_scaled_image_or_none("GreyP.png")
ghostp_img = load_scaled_image_or_none("ghostp.png")
black_sq_img = load_scaled_image_or_none("Blacksq.png")
white_sq_img = load_scaled_image_or_none("Whitesq.png")
assets_fallback_mode = any(img is None for img in [BP_img, WP_img, GP_img, ghostp_img, black_sq_img, white_sq_img])


def draw_piece_with_fallback(surface, board_x, board_y, piece_type):
    pos_x = GRID_LEFT + board_x * CELL_SIZE - CELL_SIZE // 2
    pos_y = GRID_TOP + board_y * CELL_SIZE - CELL_SIZE // 2
    center = (GRID_LEFT + board_x * CELL_SIZE, GRID_TOP + board_y * CELL_SIZE)
    radius = CELL_SIZE // 2 - 2

    if piece_type == "forbidden":
        if GP_img:
            surface.blit(GP_img, (pos_x, pos_y))
        else:
            pygame.draw.circle(surface, (150, 150, 150), center, radius)
            pygame.draw.line(surface, (90, 90, 90), (center[0] - 8, center[1] - 8), (center[0] + 8, center[1] + 8), 2)
            pygame.draw.line(surface, (90, 90, 90), (center[0] - 8, center[1] + 8), (center[0] + 8, center[1] - 8), 2)
        return

    if piece_type == "black":
        if black_sq_img and state.tetris_mode:
            surface.blit(black_sq_img, (pos_x, pos_y))
        elif BP_img:
            surface.blit(BP_img, (pos_x, pos_y))
        else:
            pygame.draw.circle(surface, (0, 0, 0), center, radius)
        return

    if piece_type == "white":
        if white_sq_img and state.tetris_mode:
            surface.blit(white_sq_img, (pos_x, pos_y))
        elif WP_img:
            surface.blit(WP_img, (pos_x, pos_y))
        else:
            pygame.draw.circle(surface, (245, 245, 245), center, radius)
            pygame.draw.circle(surface, (60, 60, 60), center, radius, 1)
        return

    if piece_type == "ghost":
        if ghostp_img:
            surface.blit(ghostp_img, (pos_x, pos_y))
        else:
            pygame.draw.circle(surface, (170, 170, 170), center, radius)

#设置窗口尺寸
width, height = 1400,1000
GRID_LEFT = (width - (CELL_SIZE * (BOARD_SIZE - 1))) // 2
screen = pygame.display.set_mode((width, height))
state.language = choose_language()
pygame.display.set_mode((width, height))
screen = pygame.display.get_surface()
pygame.display.set_caption(tr("window.title"))

#主循环
running = True
while running:
    for event in pygame.event.get():
        #俄罗斯方块操作事件
        if state.tetris_mode and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                # 向左移动
                new_pos = (state.current_pos[0] - 1, state.current_pos[1])
                if all(0 <= new_pos[0] + dx < BOARD_SIZE and 0 <= new_pos[1] + dy < BOARD_SIZE and state.board[new_pos[1] + dy][new_pos[0] + dx] == 0
                    for dx, dy in state.current_shape):
                    state.current_pos = new_pos

            elif event.key == pygame.K_RIGHT:
                # 向右移动
                new_pos = (state.current_pos[0] + 1, state.current_pos[1])
                if all(0 <= new_pos[0] + dx < BOARD_SIZE and 0 <= new_pos[1] + dy < BOARD_SIZE and state.board[new_pos[1] + dy][new_pos[0] + dx] == 0
                    for dx, dy in state.current_shape):
                    state.current_pos = new_pos

            elif event.key == pygame.K_DOWN:
                # 快速向下一格
                new_pos = (state.current_pos[0], state.current_pos[1] + 1)
                if all(0 <= new_pos[0] + dx < BOARD_SIZE and 0 <= new_pos[1] + dy < BOARD_SIZE and state.board[new_pos[1] + dy][new_pos[0] + dx] == 0
                    for dx, dy in state.current_shape):
                    state.current_pos = new_pos
                    state.tetris_last_fall_time = pygame.time.get_ticks()  # 重置下落计时，避免连续跳跃

            elif event.key == pygame.K_SPACE:
                # 顺时针旋转方块
                rotated_shape = [(dy, -dx) for dx, dy in state.current_shape]

                # 检查旋转后是否在边界内且不冲突
                valid = True
                for dx, dy in rotated_shape:
                    nx = state.current_pos[0] + dx
                    ny = state.current_pos[1] + dy
                    if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and state.board[ny][nx] == 0):
                        valid = False
                        break

                if valid:
                    state.current_shape = rotated_shape



        #鼠标点击事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state.tetris_mode:
                continue #在俄罗斯方块模式下跳过所有落子和出牌检定

            mouse_x, mouse_y = pygame.mouse.get_pos()
            #“再来一局”和“退出游戏”的按钮点击
            if state.winner != 0:
                if state.again_rect and state.again_rect.inflate(20, 10).collidepoint(mouse_x, mouse_y):
                    reset_game() #重置游戏
                    pygame.event.clear()
                    continue
                elif state.quit_rect and state.quit_rect.inflate(20, 10).collidepoint(mouse_x, mouse_y):
                    running = False #退出游戏
                    continue
            # 检测点击手牌（手牌选中）
            if state.black_turn:
                handle_card_click(state.black_hand, True, state.black_has_acted, "black")
            else:
                handle_card_click(state.white_hand, True, state.white_has_acted, "white")


            #两极反转
            if state.card_waiting_target and state.selected_card == "两极反转":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE - 1 and 0 <= grid_y < BOARD_SIZE - 1:
                    for dy in range(2):
                        for dx in range(2):
                            nx = grid_x + dx
                            ny = grid_y + dy
                            if state.board[ny][nx] == 1:
                                state.board[ny][nx] = 2
                            elif state.board[ny][nx] == 2:
                                state.board[ny][nx] = 1

                    # 反转后的胜利检定
                    for y in range(BOARD_SIZE):
                        for x in range(BOARD_SIZE):
                            if state.board[y][x] != 0:
                                if check_win(state.board, x, y, state.board[y][x], BOARD_SIZE, state.barriers_centers):
                                    state.winner = state.board[y][x]  # 1黑胜，2白胜
                    # 消耗手牌
                    if state.selected_card_owner == "black":
                        if state.selected_card in state.black_hand:
                            state.black_hand.remove(state.selected_card)
                        state.black_has_acted = True
                    elif state.selected_card_owner == "white":
                        if state.selected_card in state.white_hand:
                            state.white_hand.remove(state.selected_card)
                        state.white_has_acted = True


                    # 打出提示
                    state.last_card_played = tr('tip.used_polarity', actor=tr('label.black') if state.selected_card_owner == 'black' else tr('label.white'))

                    # 清除临时状态
                    state.selected_card = None
                    state.selected_card_owner = None
                    state.card_waiting_target = False

                    switch_turn()  # 切换回合
                    continue
            #战术核弹
            if state.card_waiting_target and state.selected_card == "战术核弹":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
                    # 移除棋子（如果有的话）
                    state.board[grid_y][grid_x] = 0
                    # 标记为禁落区域
                    state.forbidden[grid_y][grid_x] = True

                    # 消耗手牌
                    if state.selected_card_owner == "black":
                        if state.selected_card in state.black_hand:
                            state.black_hand.remove(state.selected_card)
                        state.black_has_acted = True
                    elif state.selected_card_owner == "white":
                        if state.selected_card in state.white_hand:
                            state.white_hand.remove(state.selected_card)
                        state.white_has_acted = True

                    state.last_card_played = tr('tip.used_nuke', actor=tr('label.black') if state.selected_card_owner == 'black' else tr('label.white'))

                    # 清除临时状态
                    state.selected_card = None
                    state.selected_card_owner = None
                    state.card_waiting_target = False

                    switch_turn()  # 切换回合
                    continue
            #阴阳屏障
            if state.card_waiting_target and state.selected_card == "阴阳屏障":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - GRID_LEFT) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:  # 上下左右+自己
                        nx = grid_x + dx
                        ny = grid_y + dy
                        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            state.barriers.append((nx, ny))
                        
                        state.barriers_centers.append((grid_x,grid_y)) # 单独保存中心点

                    # 消耗手牌
                    if state.selected_card_owner == "black":
                        if state.selected_card in state.black_hand:
                            state.black_hand.remove(state.selected_card)
                        state.black_has_acted = True
                    elif state.selected_card_owner == "white":
                        if state.selected_card in state.white_hand:
                            state.white_hand.remove(state.selected_card)
                        state.white_has_acted = True

                    state.last_card_played = tr('tip.used_barrier', actor=tr('label.black') if state.selected_card_owner == 'black' else tr('label.white'))

                    # 清除准备状态
                    state.selected_card = None
                    state.selected_card_owner = None
                    state.card_waiting_target = False

                    switch_turn()
                    continue


            #检测点击落子
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if state.selected_card:  # 如果有选中的卡牌，说明准备出牌（这部分后面会完善）
                pass  # 暂时留空，下一步处理
            else:
                grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
                    if state.board[grid_y][grid_x] == 0 and not state.forbidden[grid_y][grid_x] and state.winner == 0:
                        if state.black_turn and not state.black_has_acted:
                            state.piece_color = 2 if state.confuse_turns_left > 0 else 1
                            state.acting_hand = state.black_hand
                            state.has_acted_flag = "black"

                        elif not state.black_turn and not state.white_has_acted:
                            state.piece_color = 1 if state.confuse_turns_left > 0 else 2
                            state.acting_hand = state.white_hand
                            state.has_acted_flag = "white"

                        if state.piece_color is not None:
                            if state.ghost_mode:
                                state.ghost_recent_moves.append((grid_x, grid_y, state.piece_color))
                                state.board[grid_y][grid_x] = 3
                                state.ghost_rounds_left -= 1
                            else:
                                state.board[grid_y][grid_x] = state.piece_color

                                if check_win(state.board, grid_x, grid_y, state.piece_color, BOARD_SIZE, state.barriers_centers):
                                    state.winner = state.piece_color

                            if has_double_end_block(state.board, grid_x, grid_y, state.piece_color, BOARD_SIZE):
                                state.acting_hand.append(random.choice(all_cards))

                            if state.has_acted_flag == "black":
                                state.black_has_acted = True
                            else:
                                state.white_has_acted = True

                            if state.confuse_turns_left > 0:
                                state.confuse_turns_left -= 1

                            switch_turn()
                        
    # 俄罗斯方块下落逻辑
    if state.tetris_mode and state.current_shape and state.current_pos:
        now = pygame.time.get_ticks()
        if now - state.tetris_last_fall_time > state.tetris_fall_interval:
            state.tetris_last_fall_time = now

            # 尝试向下移动
            new_pos = (state.current_pos[0], state.current_pos[1] + 1)
            can_fall = True
            for dx, dy in state.current_shape:
                nx = new_pos[0] + dx
                ny = new_pos[1] + dy
                if ny >= BOARD_SIZE or state.board[ny][nx] != 0:
                    can_fall = False
                    break

            if can_fall:
                state.current_pos = new_pos
            else:
                # 方块落到底部，将其写入棋盘
                for dx, dy in state.current_shape:
                    nx = state.current_pos[0] + dx
                    ny = state.current_pos[1] + dy
                    if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                        state.board[ny][nx] = state.tetris_color  # 1=黑，2=白

                clear_matching_lines(state.board, BOARD_SIZE) #清除5个同色俄罗斯方块

                # 切换控制权或退出模式
                if state.tetris_turn < 6:
                    generate_next_tetris_block()  # 切换下一玩家
                else:
                    state.tetris_mode = False
                    state.cards_locked = False  # 恢复出牌
                    state.last_card_played = tr("tip.tetris_end")

    #幽灵棋子状态进入
    if state.ghost_start_time and not state.ghost_mode:
        elapsed = pygame.time.get_ticks() - state.ghost_start_time
        if elapsed > 5000:
            state.ghost_mode = True
            state.ghost_rounds_left = 6
            state.ghost_start_time = None
            state.last_card_played = tr("tip.ghost_active")
            state.ghost_recent_moves.clear()

            # 将当前所有棋子变为灰色，并记录原始颜色
            for y in range(BOARD_SIZE):
                for x in range(BOARD_SIZE):
                    if state.board[y][x] == 1 or state.board[y][x] == 2:
                        state.ghost_recent_moves.append((x, y, state.board[y][x]))
                        state.board[y][x] = 3  # 幽灵棋子颜色


    #幽灵模式结束后恢复颜色 + 检查胜负
    if state.ghost_mode and state.ghost_rounds_left <= 0:
        state.ghost_mode = False
        state.cards_locked = False
        state.last_card_played = tr("tip.ghost_end")

        # 恢复棋盘颜色
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                if state.board[y][x] == 3:
                    state.board[y][x] = 0
        for x, y, color in state.ghost_recent_moves:
            state.board[y][x] = color

        # 检查胜利
        for x, y, color in state.ghost_recent_moves:
            if check_win(state.board, x, y, color, BOARD_SIZE, state.barriers_centers):
                state.winner = color



    if event.type == pygame.QUIT:
        running = False

    #棋盘绘制
    screen.fill((235,220,180))
    for i in range(BOARD_SIZE):
        #x轴
        pygame.draw.line(
            screen,(0,0,0),
            (GRID_LEFT, GRID_TOP + i*CELL_SIZE),
            (GRID_LEFT + (BOARD_SIZE - 1) * CELL_SIZE, GRID_TOP + i * CELL_SIZE), 1
            )
        #y轴
        pygame.draw.line(
            screen, (0,0,0),
            (GRID_LEFT + i * CELL_SIZE, GRID_TOP),
            (GRID_LEFT + i * CELL_SIZE, GRID_TOP + (BOARD_SIZE - 1) * CELL_SIZE), 1
        )

    # 绘制对白方和黑方的提示
    white_label = font.render(tr("label.white"), True, (0, 0, 0))
    black_label = font.render(tr("label.black"), True, (0, 0, 0))

    # 白方标识
    white_label_pos = (GRID_LEFT - 220, GRID_TOP - 40)
    # 黑方标识
    black_label_pos = (GRID_LEFT + (BOARD_SIZE - 1) * CELL_SIZE + 160, GRID_TOP - 40)

    screen.blit(white_label, white_label_pos)
    screen.blit(black_label, black_label_pos)
    
    # 绘制回合信息
    if state.black_turn:
        turn_text = font.render(tr("turn.black"), True, (0, 0, 0))
    else:
        turn_text = font.render(tr("turn.white"), True, (0, 0, 0))

    # 放在屏幕上方居中
    turn_rect = turn_text.get_rect(center=(width // 2, 10))
    screen.blit(turn_text, turn_rect)


    # 显示手牌
    # 获取当前鼠标位置
    mouse_x, mouse_y = pygame.mouse.get_pos()

    hovered_card_name = None 
    # 绘制白方手牌（左边）
    for idx, card_name in enumerate(state.left_hand):
        card_surface = font.render(tr(f"card.{card_name}"), True, (255, 255, 255))
        text_rect = card_surface.get_rect()
        padding = 10
        box_width = text_rect.width + padding * 2
        box_height = text_rect.height + padding * 2
        card_x = GRID_LEFT - 180
        card_y = GRID_TOP + idx * (box_height + 10)

        card_rect = pygame.Rect(card_x, card_y, box_width, box_height)

        if card_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, (80, 80, 80), card_rect)  # 灰色内部
            hovered_card_name = card_name #显示悬停卡牌名
        else:
            pygame.draw.rect(screen, (0, 0, 0), card_rect)      # 黑色内部

        pygame.draw.rect(screen, (255, 255, 255), card_rect, 2)  # 白色边框
        screen.blit(card_surface, (card_x + padding, card_y + padding))

    # 绘制黑方手牌（右边）
    for idx, card_name in enumerate(state.right_hand):
        card_surface = font.render(tr(f"card.{card_name}"), True, (255, 255, 255))
        text_rect = card_surface.get_rect()
        padding = 10
        box_width = text_rect.width + padding * 2
        box_height = text_rect.height + padding * 2
        card_x = GRID_LEFT + (BOARD_SIZE - 1) * CELL_SIZE + 50
        card_y = GRID_TOP + idx * (box_height + 10)

        card_rect = pygame.Rect(card_x, card_y, box_width, box_height)

        if card_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, (80, 80, 80), card_rect)
            hovered_card_name = card_name #显示悬停卡牌名
        else:
            pygame.draw.rect(screen, (0, 0, 0), card_rect)

        pygame.draw.rect(screen, (255, 255, 255), card_rect, 2)
        screen.blit(card_surface, (card_x + padding, card_y + padding))

    # 显示最近使用的卡牌提示
    if state.last_card_played:
        tip_surface = font.render(state.last_card_played, True, (255, 255, 0))
        tip_rect = tip_surface.get_rect(center=(width // 2, 40))
        screen.blit(tip_surface, tip_rect)

    
    if hovered_card_name and hovered_card_name in card_descriptions:
        desc_text = tr(card_descriptions[hovered_card_name])
        lines = desc_text.split('\n')
        for i, line in enumerate(lines):
            desc_surface = font.render(line, True, (0, 0, 0))
            desc_rect = desc_surface.get_rect(topleft=(50, height - 100 + i * 30))
            screen.blit(desc_surface, desc_rect)

    #生成棋子图像
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if state.forbidden[y][x]:
                draw_piece_with_fallback(screen, x, y, "forbidden")
            elif state.board[y][x] == 1:
                draw_piece_with_fallback(screen, x, y, "black")
            elif state.board[y][x] == 2:
                draw_piece_with_fallback(screen, x, y, "white")
            elif state.board[y][x] == 3:
                draw_piece_with_fallback(screen, x, y, "ghost")
    
    # 俄罗斯方块绘制
    if state.tetris_mode and state.current_shape and state.current_pos:
        for dx, dy in state.current_shape:
            block_x = state.current_pos[0] + dx
            block_y = state.current_pos[1] + dy
            if 0 <= block_x < BOARD_SIZE and 0 <= block_y < BOARD_SIZE:
                pos_x = GRID_LEFT + block_x * CELL_SIZE - CELL_SIZE // 2
                pos_y = GRID_TOP + block_y * CELL_SIZE - CELL_SIZE // 2
                if state.tetris_color == 1:
                    if black_sq_img:
                        screen.blit(black_sq_img, (pos_x, pos_y))
                    else:
                        pygame.draw.rect(screen, (0, 0, 0), (pos_x, pos_y, CELL_SIZE, CELL_SIZE))
                else:
                    if white_sq_img:
                        screen.blit(white_sq_img, (pos_x, pos_y))
                    else:
                        pygame.draw.rect(screen, (245, 245, 245), (pos_x, pos_y, CELL_SIZE, CELL_SIZE))
                        pygame.draw.rect(screen, (60, 60, 60), (pos_x, pos_y, CELL_SIZE, CELL_SIZE), 1)

    #以卡牌施放预选区域绘制
    if state.card_waiting_target and state.selected_card == "两极反转":
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
        grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

        if 0 <= grid_x < BOARD_SIZE - 1 and 0 <= grid_y < BOARD_SIZE - 1:
            for dy in range(2):
                for dx in range(2):
                    point_x = GRID_LEFT + (grid_x + dx) * CELL_SIZE
                    point_y = GRID_TOP + (grid_y + dy) * CELL_SIZE
                    pygame.draw.circle(screen, (255, 0, 0), (point_x, point_y), 5)
    if state.card_waiting_target and state.selected_card == "战术核弹":
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
        grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

        if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
            point_x = GRID_LEFT + grid_x * CELL_SIZE
            point_y = GRID_TOP + grid_y * CELL_SIZE
            pygame.draw.circle(screen, (255, 0, 0), (point_x, point_y), 5)
    if state.card_waiting_target and state.selected_card == "阴阳屏障":
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
        grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

        if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
            center_x = GRID_LEFT + grid_x * CELL_SIZE + CELL_SIZE // 2
            center_y = GRID_TOP + grid_y * CELL_SIZE + CELL_SIZE // 2

            # 横向红线
            pygame.draw.line(screen, (255, 0, 0), (center_x - 1 * CELL_SIZE, center_y), (center_x + 1 * CELL_SIZE, center_y), 3)
            # 纵向红线
            pygame.draw.line(screen, (255, 0, 0), (center_x, center_y - 1 * CELL_SIZE), (center_x, center_y + 1 * CELL_SIZE), 3)

    #绘制阴阳屏障
    for bx, by in state.barriers_centers:
        center_x = GRID_LEFT + bx * CELL_SIZE + CELL_SIZE // 2
        center_y = GRID_TOP + by * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.line(screen, (255, 0, 0), (center_x - 1 * CELL_SIZE, center_y), (center_x + 1 * CELL_SIZE, center_y), 3)
        pygame.draw.line(screen, (255, 0, 0), (center_x, center_y - 1 * CELL_SIZE), (center_x, center_y + 1 * CELL_SIZE), 3)

    #回归基本功提示
    if state.cards_locked:
        warning_text = font.render(tr("warning.cards_locked"), True, (255, 0, 0))
        warning_rect = warning_text.get_rect(center=(width // 2, GRID_TOP - 30))
        screen.blit(warning_text, warning_rect)

    if assets_fallback_mode:
        fallback_text = font.render(tr("warning.fallback_assets"), True, (120, 60, 0))
        fallback_rect = fallback_text.get_rect(center=(width // 2, height - 20))
        screen.blit(fallback_text, fallback_rect)

    #胜利后信息显示
    again_button = None
    quit_button = None
    if state.winner != 0:
        msg = tr("result.black_win") if state.winner == 1 else tr("result.white_win")
        text_surface = font.render(msg, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(width // 2, 40))
        screen.blit(text_surface, text_rect)

    #绘制“再来一局”按钮
        again_surface = font.render(tr("button.play_again"), True, (255, 255, 255))
        state.again_rect = again_surface.get_rect(center=(width // 2 - 100, height - 60))
        pygame.draw.rect(screen, (0, 0, 0), state.again_rect.inflate(20, 10))
        screen.blit(again_surface, state.again_rect)

    #绘制“退出游戏”按钮
        quit_surface = font.render(tr("button.quit"), True, (255, 255, 255))
        state.quit_rect = quit_surface.get_rect(center=(width // 2 + 100, height - 60))
        pygame.draw.rect(screen, (0, 0, 0), state.quit_rect.inflate(20, 10))
        screen.blit(quit_surface, state.quit_rect)

    pygame.display.flip()


pygame.quit()
sys.exit()
