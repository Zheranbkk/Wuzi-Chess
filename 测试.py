import pygame
import sys
import os
import random

import os
import sys

# 获取路径
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pygame.init()

#棋盘初始化参数
BOARD_SIZE = 19
board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
CELL_SIZE = 40
GRID_TOP = 100
black_turn = True #黑白回合轮次
winner = 0 #胜利判定 0=目前无人获胜，1=黑胜，2=白胜
again_rect = None
quit_rect = None
all_cards = [
    "两极反转", "定位混淆", "战术核弹", "阴阳屏障",
    "俄罗斯方块！", "幽灵棋子",
    "战术换家", "贼不走空", "库存补充", "回归基本功"
] # 全部卡牌列表
black_hand = []  # 黑方手牌列表
white_hand = []  # 白方手牌列表
black_has_acted = False  # 黑方是否已经行动
white_has_acted = False  # 白方是否已经行动
selected_card = None    # 当前选中的卡牌名（比如“两极反转”）
selected_card_owner = None  # 记录是谁选中的（'black' 或 'white'）
last_card_played = None  # 最近使用的卡牌信息（用于显示）
barriers = []  #阴阳屏障的坐标
barriers_centers = [] #阴阳屏障中心的坐标
confuse_turns_left = 0 #定位混淆剩余轮次
cards_locked = False #回归基本功
card_waiting_target = False #部署类卡牌预设目标
left_hand = white_hand #战术转换家
right_hand = black_hand #战术转换家
forbidden = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)] # 战术核弹禁落区
ghost_mode = False              # 是否正在幽灵状态
ghost_rounds_left = 0          # 幽灵状态剩余回合数
ghost_board_snapshot = []      # 进入幽灵状态前保存的棋盘状态
ghost_recent_moves = []        # 幽灵期间记录的落子 [(x, y, color), ...]
ghost_start_time = None        # 记忆倒计时开始时间
tetris_mode = False #俄罗斯方块模式
tetris_turn = 0                 # 记录轮次（0~5，共6回合）
tetris_current_player = "black"
tetris_active_block = None     # 当前正在操控的方块对象
tetris_last_fall_time = 0      # 上一次下落的时间戳
tetris_fall_interval = 500     # 每0.5秒下落一格
current_shape = None
current_pos = None
tetris_color = None
tetris_blocks_remaining = 7    # 每次总共落6个俄罗斯方块
tetris_shapes = {              # 俄罗斯方块的结构预设
    "square": [(0,0), (1,0), (0,1), (1,1)],
    "L": [(0,0), (0,1), (0,2), (1,2)],
    "cross": [(1,0), (0,1), (1,1), (2,1), (1,2)],
    "line": [(0,0), (0,1), (0,2), (0,3)],
    "Z": [(0,0), (1,0), (1,1), (2,1)],
    "T": [(0,0), (1,0), (2,0), (1,1)],
}
card_descriptions = {
    "两极反转": "选择2×2区域，反转其中黑白棋子颜色",
    "定位混淆": "在接下来的3回合内，双方落子颜色颠倒",
    "战术核弹": "选定1格，清除棋子并禁用该格",
    "阴阳屏障": "选定1格，部署十字形屏障阻断连线",
    "俄罗斯方块！": "进入6回合俄罗斯方块模式，双方操控对方棋子颜色方块，形成5连自动清除",
    "幽灵棋子": "5秒后棋盘上所有棋子变灰6回合，双方进行盲落子",
    "战术换家": "与对方交换全部手牌",
    "贼不走空": "随机偷取对方一张手牌",
    "库存补充": "抽两张新卡牌",
    "回归基本功": "禁用卡牌系统，强制进入纯五子棋阶段"
}
piece_color = None
acting_hand = None
has_acted_flag = None



def switch_turn():
    global black_turn, black_has_acted, white_has_acted
    black_turn = not black_turn
    black_has_acted = False
    white_has_acted = False #落子与出牌逻辑的重置

def update_hand_display_order(): #默认白方手牌列表在左侧，黑方手牌列表在右侧
    global left_hand, right_hand
    left_hand = white_hand
    right_hand = black_hand

def generate_tetris_queue():
    types = ["square", "L", "cross", "long", "Z", "T"]
    queue = random.choices(types, k=6)
    while len(set(queue)) < 3:  # 至少出现3种不同的形状
        queue = random.choices(types, k=6)
    return queue

def generate_next_tetris_block():
    global current_shape, current_pos, tetris_color, tetris_current_player, tetris_turn

    #推进轮次
    tetris_turn += 1

    if tetris_turn >= 7:
        return  # 所有6个方块已用完

    # 设置当前操作者
    if tetris_turn > 0:
        tetris_current_player = "white" if tetris_current_player == "black" else "black"

    # 获取形状类型（从队列中依次取）
    shape_type = random.choice(list(tetris_shapes.keys()))
    current_shape = tetris_shapes.get(shape_type, [(0, 0)])  # fallback 为 1格方块

    # 初始位置设在棋盘中上方
    current_pos = (BOARD_SIZE // 2, 0)

    # 黑方操作白块，白方操作黑块（即 tetris_color 是“棋盘颜色”，不是玩家颜色）
    tetris_color = 2 if tetris_current_player == "black" else 1


def clear_matching_lines(): #俄罗斯方块同色消除检定
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    to_clear = set()

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            color = board[y][x]
            if color not in [1, 2]:
                continue

            for dx, dy in directions:
                temp = [(x, y)]
                for i in range(1, 5):
                    nx = x + dx * i
                    ny = y + dy * i
                    if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == color:
                        temp.append((nx, ny))
                    else:
                        break
                if len(temp) >= 5:
                    to_clear.update(temp)

    for x, y in to_clear:
        board[y][x] = 0

    return len(to_clear) > 0


def handle_card_click(player_hand, player_turn, player_has_acted, player_color):
    global selected_card, selected_card_owner, card_waiting_target, last_card_played
    global confuse_turns_left, black_has_acted, white_has_acted, cards_locked, black_hand, white_hand
    global left_hand, right_hand, ghost_mode, ghost_board_snapshot, ghost_rounds_left, ghost_start_time, ghost_recent_moves
    global tetris_mode, tetris_turn, tetris_active_block, current_shape, current_pos, tetris_color, tetris_current_player
    if cards_locked:
        return
    mouse_x, mouse_y = pygame.mouse.get_pos()

    for idx, card_name in enumerate(player_hand):
        padding = 10
        card_surface = font.render(card_name, True, (255, 255, 255))
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
            if card_name in ["两极反转", "战术核弹", "阴阳屏障"]:
                selected_card = card_name
                selected_card_owner = player_color
                card_waiting_target = True
                return
        #手牌不涉及棋盘部署，即刻生效
            if card_name == "定位混淆":
                confuse_turns_left = 3
                last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 使用了 定位混淆"
                player_hand.pop(idx)  # 打出卡牌

                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True
                if confuse_turns_left > 0:
                    confuse_turns_left -= 1
                switch_turn()
                return
            if card_name == "回归基本功":
                cards_locked = True  # 锁死手牌功能
                last_card_played = "手牌功能已禁用，请落子"
                player_hand.pop(idx)

                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True
                if confuse_turns_left > 0:
                    confuse_turns_left -= 1
                switch_turn()
                return
            if card_name == "贼不走空":
                # 判断目标玩家
                if player_color == "black":
                    opponent_hand = white_hand
                    self_hand = black_hand
                else:
                    opponent_hand = black_hand
                    self_hand = white_hand

                if opponent_hand:
                    stolen_card = random.choice(opponent_hand)
                    opponent_hand.remove(stolen_card)
                    self_hand.append(stolen_card)
                    last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 偷走了对方的一张手牌: {stolen_card}！"
                else:
                    last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 想偷卡牌，但对方手牌为空！"

                player_hand.pop(idx)

                # 设置行动状态
                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True

                # 若混淆回合还在 ➜ 消耗1回合
                if confuse_turns_left > 0:
                    confuse_turns_left -= 1

                switch_turn()
                return
            if card_name == "战术换家":
                # 交换数据
                black_hand, white_hand = white_hand, black_hand

                # 交换显示
                left_hand, right_hand = white_hand, black_hand

                last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 使用了 战术换家：双方交换了全部手牌！"

                player_hand.pop(idx)

                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True

                if confuse_turns_left > 0:
                    confuse_turns_left -= 1

                switch_turn()
                return
            
            if card_name == "库存补充":
                player_hand.pop(idx)  # 移除打出的牌

                # 摸两张牌
                for _ in range(2):
                    player_hand.append(random.choice(all_cards))

                last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 使用了 库存补充，抽取了 2 张手牌"

                # 设置行动状态
                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True

                if confuse_turns_left > 0:
                    confuse_turns_left -= 1

                switch_turn()
                return
            
            if card_name == "幽灵棋子":
                ghost_board_snapshot = [row.copy() for row in board]  # 保存当前棋盘
                ghost_recent_moves = []        # 清空记录
                ghost_start_time = pygame.time.get_ticks()  # 当前时间
                cards_locked = True            # 禁止出牌
                player_hand.pop(idx)

                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True

                last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 使用了 幽灵棋子：请记住棋盘，5秒后将进入幽灵模式！"

                switch_turn()
                return
            
            elif card_name == "俄罗斯方块！":
                tetris_mode = True
                cards_locked = True
                tetris_turn = 0
                tetris_current_player = player_color
                generate_next_tetris_block()  # 初始化第一个方块

                last_card_played = f"{'黑方' if player_color == 'black' else '白方'} 激活了俄罗斯方块模式！"
                player_hand.pop(idx)

                if player_color == 'black':
                    black_has_acted = True
                else:
                    white_has_acted = True

                if confuse_turns_left > 0:
                    confuse_turns_left -= 1

                switch_turn()
                return

            else:
                # 普通立即打出的卡
                last_card_played = f"{'黑方' if player_color == 'black' else '白方'}使用了 {card_name}"
                player_hand.pop(idx)  
                if player_color == "black":
                    black_has_acted = True
                else:
                    white_has_acted = True
                if confuse_turns_left > 0:
                    confuse_turns_left -= 1
                switch_turn()
            break #具体的卡牌选择

def reset_game(): #棋盘初始化
    global board, forbidden, black_hand, white_hand, left_hand, right_hand
    global winner, black_turn, black_has_acted, white_has_acted
    global selected_card, selected_card_owner, card_waiting_target
    global last_card_played, barriers, barriers_centers
    global confuse_turns_left, cards_locked
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]  # 清空棋盘
    forbidden = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]  # 清空禁落区
    black_hand.clear()
    white_hand.clear()

    left_hand = white_hand
    right_hand = black_hand

    winner = 0  # 重置胜负
    black_turn = True  # 黑方先手
    barriers = [] #重置阴阳屏障
    barriers_centers = [] #重置阴阳屏障中心
    confuse_turns_left = 0 #重置定位混淆次数
    cards_locked = False #重置基本功手牌锁定
    black_has_acted = False
    white_has_acted = False
    selected_card = None
    selected_card_owner = None
    card_waiting_target = False
    last_card_played = None


#导入字体
def load_font():
    font_path = os.path.join(BASE_DIR,"ZCOOLKuaiLe-Regular.ttf")
    if os.path.exists(font_path):
        return pygame.font.Font(font_path, 24)
    else:
        return pygame.font.SysFont("Arial", 20)

font = load_font()

#阴阳屏障检定辅助函数
def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def segments_intersect(A, B, C, D):
    # 判断线段 AB 和 CD 是否相交
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


#是否有阴阳屏障阻挡
# 是否有阴阳屏障阻挡
def is_blocked(x1, y1, x2, y2):
    A = (x1 + 0.5, y1 + 0.5)
    B = (x2 + 0.5, y2 + 0.5)

    for cx, cy in barriers_centers:

        # 横线从 (cx - 1 + 0.5, cy + 0.5) 到 (cx + 1 + 0.5, cy + 0.5) 即：(cx - 0.5, cy + 0.5) 到 (cx + 1.5, cy + 0.5)
        H1 = (cx - 0.5, cy + 0.5)
        H2 = (cx + 1.5, cy + 0.5)

        # 纵线从 (cx + 0.5, cy - 0.5) 到 (cx + 0.5, cy + 1.5)
        V1 = (cx + 0.5, cy - 0.5)
        V2 = (cx + 0.5, cy + 1.5)

        if segments_intersect(A, B, H1, H2) or segments_intersect(A, B, V1, V2):
            return True

    return False



#定义胜利条件
def check_win(x, y, color):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 横、竖、斜右下、斜右上

    for dx, dy in directions:
        count = 1

        # 正向
        i = 1
        while True:
            nx = x + dx * i
            ny = y + dy * i
            px = x + dx * (i - 1)
            py = y + dy * (i - 1)

            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if board[ny][nx] == color and not is_blocked(px, py, nx, ny):
                    count += 1
                    i += 1
                else:
                    break
            else:
                break

        # 反向
        i = 1
        while True:
            nx = x - dx * i
            ny = y - dy * i
            px = x - dx * (i - 1)
            py = y - dy * (i - 1)

            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                if board[ny][nx] == color and not is_blocked(px, py, nx, ny):
                    count += 1
                    i += 1
                else:
                    break
            else:
                break

        if count >= 5:
            return True

    return False



#导入棋子素材并缩放至合适大小
BP_img = pygame.image.load(os.path.join(BASE_DIR,"BlackP.png"))
WP_img = pygame.image.load(os.path.join(BASE_DIR,"WhiteP.png"))
GP_img = pygame.image.load(os.path.join(BASE_DIR,"GreyP.png"))
ghostp_img = pygame.image.load(os.path.join(BASE_DIR,"ghostp.png"))
black_sq_img = pygame.image.load(os.path.join(BASE_DIR,"Blacksq.png"))
white_sq_img = pygame.image.load(os.path.join(BASE_DIR,"Whitesq.png"))

BP_img = pygame.transform.scale(BP_img, (CELL_SIZE, CELL_SIZE))
WP_img = pygame.transform.scale(WP_img, (CELL_SIZE, CELL_SIZE))
GP_img = pygame.transform.scale(GP_img, (CELL_SIZE, CELL_SIZE))
ghostp_img = pygame.transform.scale(ghostp_img, (CELL_SIZE, CELL_SIZE))
black_sq_img = pygame.transform.scale(black_sq_img, (CELL_SIZE, CELL_SIZE))
white_sq_img = pygame.transform.scale(white_sq_img, (CELL_SIZE, CELL_SIZE))

#设置窗口尺寸
width, height = 1400,1000
GRID_LEFT = (width - (CELL_SIZE * (BOARD_SIZE - 1))) // 2
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("五子棋")

#主循环
running = True
while running:
    for event in pygame.event.get():
        #俄罗斯方块操作事件
        if tetris_mode and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                # 向左移动
                new_pos = (current_pos[0] - 1, current_pos[1])
                if all(0 <= new_pos[0] + dx < BOARD_SIZE and 0 <= new_pos[1] + dy < BOARD_SIZE and board[new_pos[1] + dy][new_pos[0] + dx] == 0
                    for dx, dy in current_shape):
                    current_pos = new_pos

            elif event.key == pygame.K_RIGHT:
                # 向右移动
                new_pos = (current_pos[0] + 1, current_pos[1])
                if all(0 <= new_pos[0] + dx < BOARD_SIZE and 0 <= new_pos[1] + dy < BOARD_SIZE and board[new_pos[1] + dy][new_pos[0] + dx] == 0
                    for dx, dy in current_shape):
                    current_pos = new_pos

            elif event.key == pygame.K_DOWN:
                # 快速向下一格
                new_pos = (current_pos[0], current_pos[1] + 1)
                if all(0 <= new_pos[0] + dx < BOARD_SIZE and 0 <= new_pos[1] + dy < BOARD_SIZE and board[new_pos[1] + dy][new_pos[0] + dx] == 0
                    for dx, dy in current_shape):
                    current_pos = new_pos
                    tetris_last_fall_time = pygame.time.get_ticks()  # 重置下落计时，避免连续跳跃

            elif event.key == pygame.K_SPACE:
                # 顺时针旋转方块
                rotated_shape = [(dy, -dx) for dx, dy in current_shape]

                # 检查旋转后是否在边界内且不冲突
                valid = True
                for dx, dy in rotated_shape:
                    nx = current_pos[0] + dx
                    ny = current_pos[1] + dy
                    if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == 0):
                        valid = False
                        break

                if valid:
                    current_shape = rotated_shape



        #鼠标点击事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            if tetris_mode:
                continue #在俄罗斯方块模式下跳过所有落子和出牌检定

            mouse_x, mouse_y = pygame.mouse.get_pos()
            #“再来一局”和“退出游戏”的按钮点击
            if winner != 0:
                if again_rect and again_rect.inflate(20, 10).collidepoint(mouse_x, mouse_y):
                    reset_game() #重置游戏
                    pygame.event.clear()
                    continue
                elif quit_rect and quit_rect.inflate(20, 10).collidepoint(mouse_x, mouse_y):
                    running = False #退出游戏
                    continue
            # 检测点击手牌（手牌选中）
            if black_turn:
                handle_card_click(black_hand, True, black_has_acted, "black")
            else:
                handle_card_click(white_hand, True, white_has_acted, "white")


            #两极反转
            if card_waiting_target and selected_card == "两极反转":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE - 1 and 0 <= grid_y < BOARD_SIZE - 1:
                    for dy in range(2):
                        for dx in range(2):
                            nx = grid_x + dx
                            ny = grid_y + dy
                            if board[ny][nx] == 1:
                                board[ny][nx] = 2
                            elif board[ny][nx] == 2:
                                board[ny][nx] = 1

                    # 反转后的胜利检定
                    for y in range(BOARD_SIZE):
                        for x in range(BOARD_SIZE):
                            if board[y][x] != 0:
                                if check_win(x, y, board[y][x]):
                                    winner = board[y][x]  # 1黑胜，2白胜
                    # 消耗手牌
                    if selected_card_owner == "black":
                        if selected_card in black_hand:
                            black_hand.remove(selected_card)
                        black_has_acted = True
                    elif selected_card_owner == "white":
                        if selected_card in white_hand:
                            white_hand.remove(selected_card)
                        white_has_acted = True


                    # 打出提示
                    last_card_played = f"{'黑方' if selected_card_owner == 'black' else '白方'} 使用了 两极反转"

                    # 清除临时状态
                    selected_card = None
                    selected_card_owner = None
                    card_waiting_target = False

                    switch_turn()  # 切换回合
                    continue
            #战术核弹
            if card_waiting_target and selected_card == "战术核弹":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
                    # 移除棋子（如果有的话）
                    board[grid_y][grid_x] = 0
                    # 标记为禁落区域
                    forbidden[grid_y][grid_x] = True

                    # 消耗手牌
                    if selected_card_owner == "black":
                        if selected_card in black_hand:
                            black_hand.remove(selected_card)
                        black_has_acted = True
                    elif selected_card_owner == "white":
                        if selected_card in white_hand:
                            white_hand.remove(selected_card)
                        white_has_acted = True

                    last_card_played = f"{'黑方' if selected_card_owner == 'black' else '白方'} 使用了 战术核弹"

                    # 清除临时状态
                    selected_card = None
                    selected_card_owner = None
                    card_waiting_target = False

                    switch_turn()  # 切换回合
                    continue
            #阴阳屏障
            if card_waiting_target and selected_card == "阴阳屏障":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - GRID_LEFT) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]:  # 上下左右+自己
                        nx = grid_x + dx
                        ny = grid_y + dy
                        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            barriers.append((nx, ny))
                        
                        barriers_centers.append((grid_x,grid_y)) # 单独保存中心点

                    # 消耗手牌
                    if selected_card_owner == "black":
                        if selected_card in black_hand:
                            black_hand.remove(selected_card)
                        black_has_acted = True
                    elif selected_card_owner == "white":
                        if selected_card in white_hand:
                            white_hand.remove(selected_card)
                        white_has_acted = True

                    last_card_played = f"{'黑方' if selected_card_owner == 'black' else '白方'} 使用了 阴阳屏障"

                    # 清除准备状态
                    selected_card = None
                    selected_card_owner = None
                    card_waiting_target = False

                    switch_turn()
                    continue


            #检测点击落子
            mouse_x, mouse_y = pygame.mouse.get_pos()

            if selected_card:  # 如果有选中的卡牌，说明准备出牌（这部分后面会完善）
                pass  # 暂时留空，下一步处理
            else:
                grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
                grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

                if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
                    if board[grid_y][grid_x] == 0 and not forbidden[grid_y][grid_x] and winner == 0:
                        if black_turn and not black_has_acted:
                            piece_color = 2 if confuse_turns_left > 0 else 1
                            acting_hand = black_hand
                            has_acted_flag = "black"

                        elif not black_turn and not white_has_acted:
                            piece_color = 1 if confuse_turns_left > 0 else 2
                            acting_hand = white_hand
                            has_acted_flag = "white"

                        if piece_color is not None:
                            if ghost_mode:
                                ghost_recent_moves.append((grid_x, grid_y, piece_color))
                                board[grid_y][grid_x] = 3
                                ghost_rounds_left -= 1
                            else:
                                board[grid_y][grid_x] = piece_color

                                if check_win(grid_x, grid_y, piece_color):
                                    winner = piece_color

                            if not cards_locked:
                                acting_hand.append(random.choice(all_cards))

                            if has_acted_flag == "black":
                                black_has_acted = True
                            else:
                                white_has_acted = True

                            if confuse_turns_left > 0:
                                confuse_turns_left -= 1

                            switch_turn()
                        
    # 俄罗斯方块下落逻辑
    if tetris_mode and current_shape and current_pos:
        now = pygame.time.get_ticks()
        if now - tetris_last_fall_time > tetris_fall_interval:
            tetris_last_fall_time = now

            # 尝试向下移动
            new_pos = (current_pos[0], current_pos[1] + 1)
            can_fall = True
            for dx, dy in current_shape:
                nx = new_pos[0] + dx
                ny = new_pos[1] + dy
                if ny >= BOARD_SIZE or board[ny][nx] != 0:
                    can_fall = False
                    break

            if can_fall:
                current_pos = new_pos
            else:
                # 方块落到底部，将其写入棋盘
                for dx, dy in current_shape:
                    nx = current_pos[0] + dx
                    ny = current_pos[1] + dy
                    if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                        board[ny][nx] = tetris_color  # 1=黑，2=白

                clear_matching_lines() #清除5个同色俄罗斯方块

                # 切换控制权或退出模式
                if tetris_turn < 6:
                    generate_next_tetris_block()  # 切换下一玩家
                else:
                    tetris_mode = False
                    cards_locked = False  # 恢复出牌
                    last_card_played = "俄罗斯方块阶段结束，恢复普通对局！"

    #幽灵棋子状态进入
    if ghost_start_time and not ghost_mode:
        elapsed = pygame.time.get_ticks() - ghost_start_time
        if elapsed > 5000:
            ghost_mode = True
            ghost_rounds_left = 6
            ghost_start_time = None
            last_card_played = "已进入幽灵棋子模式，持续6回合！"
            ghost_recent_moves.clear()

            # 将当前所有棋子变为灰色，并记录原始颜色
            for y in range(BOARD_SIZE):
                for x in range(BOARD_SIZE):
                    if board[y][x] == 1 or board[y][x] == 2:
                        ghost_recent_moves.append((x, y, board[y][x]))
                        board[y][x] = 3  # 幽灵棋子颜色


    #幽灵模式结束后恢复颜色 + 检查胜负
    if ghost_mode and ghost_rounds_left <= 0:
        ghost_mode = False
        cards_locked = False
        last_card_played = "幽灵棋子效果结束，棋盘恢复！"

        # 恢复棋盘颜色
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                if board[y][x] == 3:
                    board[y][x] = 0
        for x, y, color in ghost_recent_moves:
            board[y][x] = color

        # 检查胜利
        for x, y, color in ghost_recent_moves:
            if check_win(x, y, color):
                winner = color



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
    white_label = font.render("白方", True, (0, 0, 0))
    black_label = font.render("黑方", True, (0, 0, 0))

    # 白方标识
    white_label_pos = (GRID_LEFT - 220, GRID_TOP - 40)
    # 黑方标识
    black_label_pos = (GRID_LEFT + (BOARD_SIZE - 1) * CELL_SIZE + 160, GRID_TOP - 40)

    screen.blit(white_label, white_label_pos)
    screen.blit(black_label, black_label_pos)
    
    # 绘制回合信息
    if black_turn:
        turn_text = font.render("当前轮到：黑方", True, (0, 0, 0))
    else:
        turn_text = font.render("当前轮到：白方", True, (0, 0, 0))

    # 放在屏幕上方居中
    turn_rect = turn_text.get_rect(center=(width // 2, 10))
    screen.blit(turn_text, turn_rect)


    # 显示手牌
    # 获取当前鼠标位置
    mouse_x, mouse_y = pygame.mouse.get_pos()

    hovered_card_name = None 
    # 绘制白方手牌（左边）
    for idx, card_name in enumerate(left_hand):
        card_surface = font.render(card_name, True, (255, 255, 255))
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
    for idx, card_name in enumerate(right_hand):
        card_surface = font.render(card_name, True, (255, 255, 255))
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
    if last_card_played:
        tip_surface = font.render(last_card_played, True, (255, 255, 0))
        tip_rect = tip_surface.get_rect(center=(width // 2, 40))
        screen.blit(tip_surface, tip_rect)

    
    if hovered_card_name and hovered_card_name in card_descriptions:
        desc_text = card_descriptions[hovered_card_name]
        lines = desc_text.split('\n')
        for i, line in enumerate(lines):
            desc_surface = font.render(line, True, (0, 0, 0))
            desc_rect = desc_surface.get_rect(topleft=(50, height - 100 + i * 30))
            screen.blit(desc_surface, desc_rect)

    #生成棋子图像
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if forbidden[y][x]:
                pos_x = GRID_LEFT + x * CELL_SIZE - CELL_SIZE // 2
                pos_y = GRID_TOP + y * CELL_SIZE - CELL_SIZE // 2
                screen.blit(GP_img, (pos_x, pos_y))
            elif board[y][x] == 1:
                pos_x = GRID_LEFT + x * CELL_SIZE - CELL_SIZE // 2
                pos_y = GRID_TOP + y * CELL_SIZE - CELL_SIZE // 2
                if tetris_mode:
                    screen.blit(black_sq_img, (pos_x, pos_y))
                else:
                    screen.blit(BP_img, (pos_x, pos_y))
            elif board[y][x] == 2:
                pos_x = GRID_LEFT + x * CELL_SIZE - CELL_SIZE // 2
                pos_y = GRID_TOP + y * CELL_SIZE - CELL_SIZE // 2
                if tetris_mode:
                    screen.blit(white_sq_img, (pos_x, pos_y))
                else:
                    screen.blit(WP_img, (pos_x, pos_y))
            elif board[y][x] == 3:
                pos_x = GRID_LEFT + x * CELL_SIZE - CELL_SIZE // 2
                pos_y = GRID_TOP + y * CELL_SIZE - CELL_SIZE // 2
                screen.blit(ghostp_img, (pos_x, pos_y))
    
    # 俄罗斯方块绘制
    if tetris_mode and current_shape and current_pos:
        for dx, dy in current_shape:
            block_x = current_pos[0] + dx
            block_y = current_pos[1] + dy
            if 0 <= block_x < BOARD_SIZE and 0 <= block_y < BOARD_SIZE:
                pos_x = GRID_LEFT + block_x * CELL_SIZE - CELL_SIZE // 2
                pos_y = GRID_TOP + block_y * CELL_SIZE - CELL_SIZE // 2
                if tetris_color == 1:
                    screen.blit(black_sq_img, (pos_x, pos_y))
                else:
                    screen.blit(white_sq_img, (pos_x, pos_y))

    #以卡牌施放预选区域绘制
    if card_waiting_target and selected_card == "两极反转":
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
        grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

        if 0 <= grid_x < BOARD_SIZE - 1 and 0 <= grid_y < BOARD_SIZE - 1:
            for dy in range(2):
                for dx in range(2):
                    point_x = GRID_LEFT + (grid_x + dx) * CELL_SIZE
                    point_y = GRID_TOP + (grid_y + dy) * CELL_SIZE
                    pygame.draw.circle(screen, (255, 0, 0), (point_x, point_y), 5)
    if card_waiting_target and selected_card == "战术核弹":
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x = (mouse_x - GRID_LEFT + CELL_SIZE // 2) // CELL_SIZE
        grid_y = (mouse_y - GRID_TOP + CELL_SIZE // 2) // CELL_SIZE

        if 0 <= grid_x < BOARD_SIZE and 0 <= grid_y < BOARD_SIZE:
            point_x = GRID_LEFT + grid_x * CELL_SIZE
            point_y = GRID_TOP + grid_y * CELL_SIZE
            pygame.draw.circle(screen, (255, 0, 0), (point_x, point_y), 5)
    if card_waiting_target and selected_card == "阴阳屏障":
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
    for bx, by in barriers_centers:
        center_x = GRID_LEFT + bx * CELL_SIZE + CELL_SIZE // 2
        center_y = GRID_TOP + by * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.line(screen, (255, 0, 0), (center_x - 1 * CELL_SIZE, center_y), (center_x + 1 * CELL_SIZE, center_y), 3)
        pygame.draw.line(screen, (255, 0, 0), (center_x, center_y - 1 * CELL_SIZE), (center_x, center_y + 1 * CELL_SIZE), 3)

    #回归基本功提示
    if cards_locked:
        warning_text = font.render("手牌功能已禁用，请落子", True, (255, 0, 0))
        warning_rect = warning_text.get_rect(center=(width // 2, GRID_TOP - 30))
        screen.blit(warning_text, warning_rect)

    #胜利后信息显示
    again_button = None
    quit_button = None
    if winner != 0:
        msg = "黑方胜利！" if winner == 1 else "白方胜利！"
        text_surface = font.render(msg, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(width // 2, 40))
        screen.blit(text_surface, text_rect)

    #绘制“再来一局”按钮
        again_surface = font.render("再来一局", True, (255, 255, 255))
        again_rect = again_surface.get_rect(center=(width // 2 - 100, height - 60))
        pygame.draw.rect(screen, (0, 0, 0), again_rect.inflate(20, 10))
        screen.blit(again_surface, again_rect)

    #绘制“退出游戏”按钮
        quit_surface = font.render("退出游戏", True, (255, 255, 255))
        quit_rect = quit_surface.get_rect(center=(width // 2 + 100, height - 60))
        pygame.draw.rect(screen, (0, 0, 0), quit_rect.inflate(20, 10))
        screen.blit(quit_surface, quit_rect)

    pygame.display.flip()


pygame.quit()
sys.exit()
