"""
thunder_typer.py
================
雷霆打字戰機 — 第一階段
結合「垂直捲軸射擊（雷霆戰機）」與「打字測驗（ZType）」的桌面遊戲。

技術要點：
  - OOP 架構：Enemy、Bullet、Game 三個類別
  - 介面：Canvas（主畫面）、ttk.Progressbar（HP）、Label（分數/Combo）
  - 遊戲迴圈：root.after()，禁用 time.sleep() 與 while True
  - 輸入：root.bind("<KeyPress>") 全域攔截，不使用 Entry
  - 核心機制：目標鎖定（Target Locking）
"""

import tkinter as tk
from tkinter import ttk
import random
import string

# ══════════════════════════════════════════════════════════════════════════════
#  遊戲全域常數
# ══════════════════════════════════════════════════════════════════════════════

CANVAS_W      = 620          # Canvas 寬度（像素）
CANVAS_H      = 700          # Canvas 高度（像素）
FPS_MS        = 33           # 主迴圈間隔毫秒（約 30 FPS）
ENEMY_SPEED   = 0.9          # 敵機每幀下移的像素數
SPAWN_MS      = 2800         # 敵機生成間隔毫秒（初始值，難度提升後會縮短）
MAX_ENEMIES   = 9            # 畫面同時最多存在的敵機數
BULLET_SPEED  = 14           # 子彈每幀上移的像素數
MAX_HP        = 100          # 玩家最大生命值
DAMAGE        = 22           # 敵機抵達底部時對玩家造成的傷害
CHAR_W        = 7            # Courier 11pt 每字元估算寬度（px），用於文字定位

# ── 英文單字庫 ─────────────────────────────────────────────────────────────────
WORDS = [
    # 4 字母
    "able","acid","aged","also","apex","arch","army","atom",
    "back","barn","beam","bird","blue","bold","bond","bred",
    "cage","calm","cave","chin","chip","claw","clay","clue",
    "damp","dare","dark","data","dawn","deal","deck","dome",
    "echo","edge","emit","epic","even","evil","exam","exit",
    # 5 字母
    "alpha","blaze","brave","brick","cable","chase","chess",
    "chord","clash","cloud","cobra","coral","crane","crisp","crown",
    "delta","depth","digit","dingo","disco","draft","drain","drift",
    "eagle","early","earth","eight","elite","ember","epoch","error",
    "fable","faith","false","fault","feast","fever","fifth","fixed",
    "flame","flash","flint","flood","flora","focus","force","forge",
    "frost","globe","grace","grade","grain","grand","grant","grasp",
    "grave","graze","greed","green","greet","grind","groan","guard",
    "hazel","heavy","heist","helix","honor","horse","hover","human",
    "humid","haste","hyper","ideal","index","indie","infer","intel",
    "ivory","jewel","joint","joker","judge","juice","karma","knife",
    "laser","layer","learn","legal","lemma","level","light","limit",
    "logic","lunar","magic","maple","march","marsh","match","maxim",
    "merge","metal","might","mimic","minor","minus","model","motor",
    "nexus","night","ninja","noble","noise","north","novel","nymph",
    "oasis","ocean","onset","order","orbit","other","outer","oxide",
    "panel","paper","patch","pause","pearl","phase","pilot","pixel",
    "pixel","place","plain","plane","plant","plaza","pluck","plumb",
    "polar","power","press","prism","probe","prone","proxy","pulse",
    "quest","quick","quiet","quota","quote","radar","radix","rally",
    "range","rapid","ratio","razor","reach","realm","relay","relic",
    "remix","renew","repel","reset","ridge","risky","rival","river",
    "robot","rocky","rouge","round","route","royal","ruled","runes",
    "sabre","scale","scope","scout","seize","servo","seven","shade",
    "sigma","skate","skill","slave","slice","slide","slope","smoke",
    "snake","solar","solid","solve","sonar","sound","south","spark",
    "spawn","speed","spell","spend","spire","spoke","spore","sport",
    "spray","squad","stack","staff","stage","stake","stall","stamp",
    "stand","stark","start","state","stave","steal","steel","steep",
    "stern","stick","sting","stock","stomp","stone","store","storm",
    "story","stove","strap","straw","stray","strip","strum","strut",
    "stuck","study","style","surge","swamp","swarm","sweep","swept",
    "swift","sword","swirl","syrup","tango","taunt","tempo","tense",
    "tiger","tight","tilde","timer","titan","token","topaz","torch",
    "total","tower","trace","track","trade","trail","train","trait",
    "tramp","trash","trawl","triad","tribe","trick","trill","troop",
    "trove","truce","truly","trump","trunk","trust","truth","turbo",
    "tweak","twirl","twist","ultra","unity","until","upper","usher",
    "valor","valve","vault","venom","vexed","viral","virus","visor",
    "vista","vital","vixen","voter","viper","vortex","waves","weave",
    "wedge","whirl","wield","witch","witty","xenon","yacht","yield",
    "young","zoned","zones","zooms","zesty","zebra",
]

# 去重，確保單字唯一
WORDS = list(set(WORDS))


# ══════════════════════════════════════════════════════════════════════════════
#  Enemy（敵機）類別
# ══════════════════════════════════════════════════════════════════════════════

class Enemy:
    """
    代表一台帶有英文單字的敵機。

    包含：
      - 矩形幾何圖形（Canvas.create_rectangle）
      - 已輸入部分的黃色文字（anchor="w"）
      - 未輸入部分的白色文字（anchor="w"）
      - 鎖定狀態的外框高亮效果
    """

    # 敵機顏色設定（常數）
    COLOR_FILL    = "#BB2020"   # 矩形填色
    COLOR_OUTLINE = "#FF5555"   # 矩形外框（未鎖定）
    COLOR_LOCKED  = "#FFFF00"   # 矩形外框（鎖定中）
    COLOR_TYPED   = "#FFE033"   # 已輸入字元顏色（黃色）
    COLOR_REMAIN  = "#E8E8E8"   # 未輸入字元顏色（白色）

    def __init__(self, canvas: tk.Canvas, word: str, x: int):
        """
        初始化敵機。

        參數：
            canvas  -- 目標 Canvas 物件
            word    -- 此敵機對應的英文單字
            x       -- 水平中心位置（pixel）
        """
        self.canvas = canvas
        self.word   = word          # 完整英文單字
        self.typed  = 0             # 已正確輸入的字元數
        self.x      = float(x)     # 中心 X（使用浮點數，累積移動更精確）
        self.y      = 20.0          # 中心 Y（從頂部開始）
        self.alive  = True

        # 矩形尺寸：依單字長度動態計算寬度
        self._hw = max(len(word) * 5 + 22, 40)  # 半寬
        self._hh = 15                             # 半高

        # 文字整體居中所需的起始 X
        self._txt_start_x = x - len(word) * CHAR_W / 2
        self._txt_y       = self.y - self._hh - 14   # 文字在矩形上方

        # ── 建立 Canvas 圖形元素 ─────────────────────────────────
        # 敵機矩形（紅色）
        self._rect = canvas.create_rectangle(
            x - self._hw, self.y - self._hh,
            x + self._hw, self.y + self._hh,
            fill=self.COLOR_FILL,
            outline=self.COLOR_OUTLINE,
            width=2,
        )
        # 已輸入部分（黃色，向左對齊）
        self._typed_txt = canvas.create_text(
            self._txt_start_x, self._txt_y,
            text="",
            fill=self.COLOR_TYPED,
            font=("Courier", 11, "bold"),
            anchor="w",
        )
        # 未輸入部分（白色，向左對齊，緊接在已輸入後方）
        self._remain_txt = canvas.create_text(
            self._txt_start_x, self._txt_y,
            text=word,
            fill=self.COLOR_REMAIN,
            font=("Courier", 11, "bold"),
            anchor="w",
        )

    # ── 私有：更新分色文字顯示 ────────────────────────────────────────────────
    def _refresh_text(self):
        """
        依 self.typed 數量重新計算並更新兩段文字的內容與位置。
        已輸入部分 = 黃色，未輸入部分 = 白色，兩者緊密拼接。
        """
        typed_str  = self.word[:self.typed]          # 已打的前綴
        remain_str = self.word[self.typed:]          # 尚未打的後綴
        remain_x   = self._txt_start_x + self.typed * CHAR_W  # 後綴起點

        self.canvas.itemconfig(self._typed_txt,  text=typed_str)
        self.canvas.itemconfig(self._remain_txt, text=remain_str)
        # 後綴文字 X 座標右移（已輸入字元的寬度）
        self.canvas.coords(self._remain_txt, remain_x, self._txt_y)

    # ── 公開：每幀向下移動 ────────────────────────────────────────────────────
    def move_down(self):
        """將敵機（矩形＋兩段文字）統一向下移動 ENEMY_SPEED 像素。"""
        self.y       += ENEMY_SPEED
        self._txt_y  += ENEMY_SPEED
        # Canvas.move() 可同步移動指定 item
        self.canvas.move(self._rect,       0, ENEMY_SPEED)
        self.canvas.move(self._typed_txt,  0, ENEMY_SPEED)
        self.canvas.move(self._remain_txt, 0, ENEMY_SPEED)

    # ── 公開：嘗試輸入字元 ────────────────────────────────────────────────────
    def try_type(self, char: str) -> bool:
        """
        嘗試輸入一個字元。
        若與當前期望字元相符則 typed +1、刷新顯示並回傳 True，否則回傳 False。
        """
        if self.typed < len(self.word) and self.word[self.typed] == char:
            self.typed += 1
            self._refresh_text()
            return True
        return False

    # ── 公開：狀態查詢 ────────────────────────────────────────────────────────
    def is_done(self) -> bool:
        """回傳單字是否已完整輸入完畢。"""
        return self.typed == len(self.word)

    def first_char_matches(self, char: str) -> bool:
        """
        目標鎖定判斷：尚未開始輸入（typed == 0）且首字母符合時回傳 True。
        僅用於無鎖定目標時搜尋可攻擊的敵機。
        """
        return self.typed == 0 and bool(self.word) and self.word[0] == char

    # ── 公開：鎖定視覺效果 ────────────────────────────────────────────────────
    def set_locked(self, locked: bool):
        """鎖定時外框變成亮黃色且加粗，解鎖時還原。"""
        if locked:
            self.canvas.itemconfig(self._rect,
                                   outline=self.COLOR_LOCKED, width=3)
        else:
            self.canvas.itemconfig(self._rect,
                                   outline=self.COLOR_OUTLINE, width=2)

    # ── 公開：銷毀（Canvas.delete） ───────────────────────────────────────────
    def destroy(self):
        """
        呼叫 Canvas.delete() 移除此敵機的所有圖形與文字元素，
        並將 alive 標記為 False。
        """
        self.canvas.delete(self._rect)
        self.canvas.delete(self._typed_txt)
        self.canvas.delete(self._remain_txt)
        self.alive = False


# ══════════════════════════════════════════════════════════════════════════════
#  Bullet（子彈）類別
# ══════════════════════════════════════════════════════════════════════════════

class Bullet:
    """
    玩家發射的子彈（藍綠色橢圓）。
    發射時記錄目標位置，計算方向單位向量（dx, dy），
    每幀沿該方向移動 BULLET_SPEED 像素，而非只往正上方飛。
    """

    def __init__(self, canvas: tk.Canvas,
                 sx: float, sy: float,
                 tx: float, ty: float):
        """
        參數：
            canvas      -- 目標 Canvas
            sx, sy      -- 子彈起始座標（砲口位置）
            tx, ty      -- 目標座標（鎖定敵機的中心）
        """
        self.canvas = canvas
        self.x      = float(sx)
        self.y      = float(sy)
        self.alive  = True

        # ── 計算方向單位向量 ──────────────────────────────────
        import math
        dx = tx - sx
        dy = ty - sy
        dist = math.hypot(dx, dy)   # 起點到目標的距離

        if dist == 0:
            # 目標與砲口重疊（理論上不會發生），預設垂直向上
            self._vx, self._vy = 0.0, -1.0
        else:
            # 正規化為單位向量，乘以速度
            self._vx = (dx / dist) * BULLET_SPEED
            self._vy = (dy / dist) * BULLET_SPEED

        # 子彈圖形（細長橢圓，方向感較強）
        self._oval = canvas.create_oval(
            sx - 3, sy - 5, sx + 3, sy + 5,
            fill="#00FFCC", outline="",
        )

    def move(self):
        """每幀沿方向向量移動；飛出畫面四邊後自動銷毀。"""
        self.x += self._vx
        self.y += self._vy
        self.canvas.move(self._oval, self._vx, self._vy)
        # 超出畫面任意方向則銷毀
        if self.y < 0 or self.y > CANVAS_H or self.x < 0 or self.x > CANVAS_W:
            self.destroy()

    def destroy(self):
        """移除子彈的 Canvas 元素。"""
        self.canvas.delete(self._oval)
        self.alive = False


# ══════════════════════════════════════════════════════════════════════════════
#  Game（遊戲主控制器）類別
# ══════════════════════════════════════════════════════════════════════════════

class Game:
    """
    遊戲主控制器。

    負責：
      1. 建構所有 UI Widget（Canvas、Progressbar、Label）
      2. 繪製玩家戰機
      3. 綁定全域鍵盤事件（不使用 Entry）
      4. 敵機生成排程
      5. 主遊戲迴圈（使用 after()）
      6. 目標鎖定（Target Locking）邏輯
      7. 分數、Combo、HP 管理
    """

    def __init__(self, root: tk.Tk):
        self.root = root

        # ── 遊戲狀態變數 ──────────────────────────────────────
        self.score      = 0        # 當前分數
        self.combo      = 0        # 當前 Combo 連擊數
        self.max_combo  = 0        # 本局最高 Combo
        self.hp         = MAX_HP   # 玩家當前生命值
        self.game_over  = False    # 遊戲是否已結束

        # ── 物件列表 ──────────────────────────────────────────
        self.enemies = []          # 畫面上所有存活的 Enemy 實例
        self.bullets = []          # 畫面上所有存活的 Bullet 實例
        self.locked  = None        # 目前被鎖定的 Enemy（None = 未鎖定）

        # ── 玩家座標（固定在底部中央） ────────────────────────
        self._px = CANVAS_W // 2
        self._py = CANVAS_H - 40

        # ── 初始化 ────────────────────────────────────────────
        self._build_ui()        # 建立所有 Widget
        self._draw_player()     # 繪製玩家戰機
        self._bind_keys()       # 綁定鍵盤事件

        # 使用 after() 啟動敵機生成與遊戲迴圈（不使用 while/sleep）
        self.root.after(800,    self._spawn_enemy)
        self.root.after(FPS_MS, self._game_loop)

    # ══════════════════════════════════════════════════════════════════════════
    #  UI 建構
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """建立視窗的所有 Widget（使用 Canvas、Label、ttk.Progressbar）。"""
        self.root.configure(bg="#07071A")

        # ── 頂部資訊列（Frame） ───────────────────────────────
        top = tk.Frame(self.root, bg="#07071A")
        top.pack(fill=tk.X, padx=14, pady=(8, 3))

        # 分數：靜態標題 Label + 動態數值 Label
        tk.Label(top, text="SCORE",
                 bg="#07071A", fg="#445566",
                 font=("Courier", 8, "bold")).pack(side=tk.LEFT)

        self._score_var = tk.StringVar(value="0")
        tk.Label(top, textvariable=self._score_var,
                 bg="#07071A", fg="#FFFFFF",
                 font=("Courier", 14, "bold"),
                 width=8, anchor="w").pack(side=tk.LEFT, padx=(3, 18))

        # Combo：靜態標題 Label + 動態數值 Label
        tk.Label(top, text="COMBO",
                 bg="#07071A", fg="#445566",
                 font=("Courier", 8, "bold")).pack(side=tk.LEFT)

        self._combo_var = tk.StringVar(value="×0")
        self._combo_lbl = tk.Label(top, textvariable=self._combo_var,
                                   bg="#07071A", fg="#FFEE44",
                                   font=("Courier", 14, "bold"),
                                   width=6, anchor="w")
        self._combo_lbl.pack(side=tk.LEFT, padx=(3, 0))

        # HP 進度條（右側）
        hp_frame = tk.Frame(top, bg="#07071A")
        hp_frame.pack(side=tk.RIGHT)

        tk.Label(hp_frame, text="HP",
                 bg="#07071A", fg="#445566",
                 font=("Courier", 8, "bold")).pack(side=tk.LEFT, padx=(0, 5))

        # 設定 ttk 樣式（顏色、槽色）
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("hp.Horizontal.TProgressbar",
                         troughcolor="#111128",
                         background="#22DD66",
                         bordercolor="#223344",
                         lightcolor="#22DD66",
                         darkcolor="#22DD66")

        self._hp_var = tk.IntVar(value=MAX_HP)
        self._hp_bar = ttk.Progressbar(
            hp_frame,
            variable=self._hp_var,
            maximum=MAX_HP,
            length=170,
            style="hp.Horizontal.TProgressbar",
            mode="determinate",
        )
        self._hp_bar.pack(side=tk.LEFT)

        # ── 主遊戲 Canvas ─────────────────────────────────────
        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_W, height=CANVAS_H,
            bg="#080820",
            highlightthickness=1,
            highlightbackground="#1A2A40",
        )
        self.canvas.pack(padx=14, pady=(2, 2))

        # 繪製靜態背景元素（星點裝飾）
        self._draw_starfield()

        # 玩家飛行跑道分隔線（虛線）
        self.canvas.create_line(
            0, CANVAS_H - 65, CANVAS_W, CANVAS_H - 65,
            fill="#151530", width=1, dash=(5, 5)
        )

        # ── 底部提示文字 Label ────────────────────────────────
        self._hint_lbl = tk.Label(
            self.root,
            text="輸入首字母 → 鎖定敵機（黃框）→ 連續輸入完整單字 → 擊毀！  錯字則 Combo 歸零",
            bg="#07071A", fg="#2A3A4A",
            font=("Courier", 8),
        )
        self._hint_lbl.pack(pady=(0, 7))

    def _draw_starfield(self):
        """在 Canvas 上隨機繪製靜態星點，製造太空背景感。"""
        random.seed(42)   # 固定種子確保背景每次相同
        for _ in range(120):
            sx = random.randint(0, CANVAS_W)
            sy = random.randint(0, CANVAS_H - 80)
            # 隨機亮度（三種）
            brightness = random.choice(["#1A1A38", "#222244", "#2A2A55"])
            r = random.choice([1, 1, 1, 2])
            self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r,
                                    fill=brightness, outline="")
        random.seed()     # 恢復隨機狀態

    # ══════════════════════════════════════════════════════════════════════════
    #  玩家戰機繪製
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_player(self):
        """
        使用 Canvas 幾何圖形（矩形、多邊形、橢圓）拼合玩家戰機外觀。
        所有元素都加上 tag="player" 方便統一管理。
        """
        cx, cy = self._px, self._py

        # 噴射火焰（最底層，先畫）
        self.canvas.create_polygon(
            cx - 8,  cy + 20,
            cx,      cy + 36,
            cx + 8,  cy + 20,
            fill="#FF6600", outline="", tags="player"
        )
        # 火焰內芯（亮色）
        self.canvas.create_polygon(
            cx - 4,  cy + 20,
            cx,      cy + 28,
            cx + 4,  cy + 20,
            fill="#FFCC00", outline="", tags="player"
        )

        # 左翼
        self.canvas.create_polygon(
            cx - 14, cy - 6,
            cx - 40, cy + 20,
            cx - 14, cy + 20,
            fill="#0A5588", outline="", tags="player"
        )
        # 右翼
        self.canvas.create_polygon(
            cx + 14, cy - 6,
            cx + 40, cy + 20,
            cx + 14, cy + 20,
            fill="#0A5588", outline="", tags="player"
        )

        # 機身（矩形）
        self.canvas.create_rectangle(
            cx - 13, cy - 24,
            cx + 13, cy + 20,
            fill="#1177CC", outline="#44AAFF", width=2, tags="player"
        )

        # 砲管
        self.canvas.create_rectangle(
            cx - 4, cy - 38,
            cx + 4, cy - 24,
            fill="#33CCFF", outline="", tags="player"
        )

        # 砲口（小圓）
        self.canvas.create_oval(
            cx - 5, cy - 44,
            cx + 5, cy - 36,
            fill="#88EEFF", outline="", tags="player"
        )

        # 駕駛艙（橢圓）
        self.canvas.create_oval(
            cx - 8, cy - 18,
            cx + 8, cy - 4,
            fill="#88DDFF", outline="#AAEEFF", tags="player"
        )

        # 左翼端燈（裝飾小點）
        self.canvas.create_oval(
            cx - 42, cy + 18, cx - 38, cy + 22,
            fill="#FF3333", outline="", tags="player"
        )
        # 右翼端燈
        self.canvas.create_oval(
            cx + 38, cy + 18, cx + 42, cy + 22,
            fill="#FF3333", outline="", tags="player"
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  鍵盤事件綁定
    # ══════════════════════════════════════════════════════════════════════════

    def _bind_keys(self):
        """
        對根視窗（root）進行全域鍵盤攔截。
        不使用 Entry，直接用 bind("<KeyPress>") 截取所有鍵盤輸入。
        """
        self.root.bind("<KeyPress>", self._on_key)

    def _on_key(self, event: tk.Event):
        """
        ╔═══════════════════════════════════════════════════════════════╗
        ║              目標鎖定機制（Target Locking）                    ║
        ╠═══════════════════════════════════════════════════════════════╣
        ║  狀態一：無鎖定目標（self.locked is None）                     ║
        ║    → 遍歷所有敵機，比對其「首字母」                             ║
        ║    → 首個符合者被「鎖定」（set_locked(True)），後續輸入專屬     ║
        ║                                                               ║
        ║  狀態二：有鎖定目標（self.locked is not None）                  ║
        ║    → 所有按鍵輸入僅對鎖定敵機生效                               ║
        ║    → 單字完成（is_done()）→ 摧毀（destroy()）→ 解鎖           ║
        ║    → 按鍵錯誤 → Combo 歸零                                     ║
        ╚═══════════════════════════════════════════════════════════════╝
        """
        if self.game_over:
            return

        # 只處理 a-z 英文小寫字母
        ch = event.char.lower()
        if ch not in string.ascii_lowercase:
            return

        # ── 狀態一：尚未鎖定任何敵機 ──────────────────────────
        if self.locked is None:
            for enemy in self.enemies:
                if enemy.alive and enemy.first_char_matches(ch):
                    # 找到首字母符合的敵機 → 鎖定
                    self.locked = enemy
                    enemy.set_locked(True)
                    enemy.try_type(ch)          # 輸入第一個字元
                    self._fire_bullet()         # 發射子彈
                    # 邊緣情況：單字只有一個字元，立即完成
                    if enemy.is_done():
                        self._kill_enemy(enemy)
                        self.locked = None
                    break   # 只鎖定第一個符合目標，後續忽略

        # ── 狀態二：已有鎖定目標 ──────────────────────────────
        else:
            # 防禦：鎖定目標已被外部清除（例如碰底銷毀）
            if not self.locked.alive:
                self.locked = None
                return

            hit = self.locked.try_type(ch)   # 嘗試輸入字元
            if hit:
                self._fire_bullet()
                if self.locked.is_done():
                    # 單字完整輸入完畢 → 摧毀並解鎖
                    self._kill_enemy(self.locked)
                    self.locked = None
            else:
                # 輸入錯誤 → Combo 斷鏈
                self._break_combo()

    # ══════════════════════════════════════════════════════════════════════════
    #  子彈
    # ══════════════════════════════════════════════════════════════════════════

    def _fire_bullet(self):
        """
        在玩家砲口位置建立一顆子彈。
        若有鎖定敵機，子彈朝敵機當前位置發射（含 X 分量）；
        否則垂直向上（備用）。
        """
        sx = float(self._px)     # 砲口 X
        sy = float(self._py - 38)  # 砲口 Y（砲管頂端）

        if self.locked and self.locked.alive:
            # 目標：鎖定敵機的即時中心座標
            tx, ty = self.locked.x, self.locked.y
        else:
            # 無鎖定目標：垂直向上
            tx, ty = sx, sy - 500.0

        b = Bullet(self.canvas, sx, sy, tx, ty)
        self.bullets.append(b)

    # ══════════════════════════════════════════════════════════════════════════
    #  敵機摧毀與計分
    # ══════════════════════════════════════════════════════════════════════════

    def _kill_enemy(self, enemy: Enemy):
        """
        摧毀指定敵機：
          1. Combo +1
          2. 依單字長度與 Combo 計算得分
          3. 更新 Label 顯示
          4. 顯示飄字動畫
          5. 呼叫 Enemy.destroy()（內部執行 Canvas.delete）
          6. 從 self.enemies 移除
        """
        self.combo     += 1
        self.max_combo  = max(self.max_combo, self.combo)

        # 得分公式：單字字元數 × 10 × Combo 係數（每 4 連擊提升一級）
        multiplier = self.combo // 4 + 1
        pts        = len(enemy.word) * 10 * multiplier
        self.score += pts

        # 更新分數 Label
        self._score_var.set(f"{self.score:,}")

        # 更新 Combo Label 並依連擊數變換顏色
        self._combo_var.set(f"×{self.combo}")
        if self.combo >= 12:
            self._combo_lbl.config(fg="#FF3333")   # 高 Combo：紅色
        elif self.combo >= 6:
            self._combo_lbl.config(fg="#FF8800")   # 中 Combo：橙色
        else:
            self._combo_lbl.config(fg="#FFEE44")   # 低 Combo：黃色

        # 飄字動畫（在敵機位置顯示得分）
        self._popup(enemy.x, enemy.y, f"+{pts}")

        # 摧毀 Canvas 元素（Canvas.delete 在 Enemy.destroy() 內部執行）
        enemy.destroy()

        # 從列表移除已死亡敵機
        self.enemies = [e for e in self.enemies if e.alive]

    def _popup(self, x: float, y: float, text: str):
        """建立一個向上飄動的得分文字並以 after() 驅動動畫。"""
        tid = self.canvas.create_text(
            x, y,
            text=text,
            fill="#FFE033",
            font=("Courier", 13, "bold"),
        )
        # 啟動飄字動畫（共 18 幀，每幀間隔 35ms）
        self._animate_popup(tid, 18)

    def _animate_popup(self, tid: int, frames_left: int):
        """
        遞迴使用 after() 執行飄字動畫。
        每幀向上移動 2px，幀數耗盡後呼叫 Canvas.delete 移除。
        （絕對不使用 time.sleep 或 while 迴圈）
        """
        if frames_left <= 0:
            self.canvas.delete(tid)
            return
        self.canvas.move(tid, 0, -2)
        self.root.after(35, lambda: self._animate_popup(tid, frames_left - 1))

    # ══════════════════════════════════════════════════════════════════════════
    #  Combo 管理
    # ══════════════════════════════════════════════════════════════════════════

    def _break_combo(self):
        """Combo 斷鏈：歸零並恢復預設顏色。"""
        self.combo = 0
        self._combo_var.set("×0")
        self._combo_lbl.config(fg="#FFEE44")

    # ══════════════════════════════════════════════════════════════════════════
    #  HP 管理
    # ══════════════════════════════════════════════════════════════════════════

    def _take_damage(self, dmg: int):
        """
        玩家受到傷害：
          - 扣除 HP 並更新 ttk.Progressbar
          - 依 HP 比例動態改變進度條顏色
          - HP 歸零時觸發遊戲結束
        """
        self.hp = max(0, self.hp - dmg)
        self._hp_var.set(self.hp)

        # 依剩餘 HP 比例更新進度條顏色
        ratio = self.hp / MAX_HP
        style = ttk.Style()
        if ratio <= 0.25:
            # 低血量：紅色警示
            style.configure("hp.Horizontal.TProgressbar",
                             background="#DD2211",
                             lightcolor="#DD2211",
                             darkcolor="#DD2211")
        elif ratio <= 0.55:
            # 中血量：橙色提示
            style.configure("hp.Horizontal.TProgressbar",
                             background="#FF9900",
                             lightcolor="#FF9900",
                             darkcolor="#FF9900")
        else:
            # 高血量：綠色
            style.configure("hp.Horizontal.TProgressbar",
                             background="#22DD66",
                             lightcolor="#22DD66",
                             darkcolor="#22DD66")

        if self.hp <= 0:
            self._end_game()

    # ══════════════════════════════════════════════════════════════════════════
    #  敵機生成（排程）
    # ══════════════════════════════════════════════════════════════════════════

    def _spawn_enemy(self):
        """
        在畫面頂部隨機水平位置生成一台帶有英文單字的敵機。
        使用 after() 自我排程，生成間隔隨分數提升而縮短（難度遞增）。
        """
        if self.game_over:
            return   # 遊戲結束後停止生成

        # 未達上限才生成
        if len(self.enemies) < MAX_ENEMIES:
            word   = random.choice(WORDS)
            margin = 70    # 左右留邊，避免文字超出 Canvas
            x      = random.randint(margin, CANVAS_W - margin)
            enemy  = Enemy(self.canvas, word, x)
            self.enemies.append(enemy)

        # 動態計算下次生成間隔（難度漸增，最短不低於 1000ms）
        next_ms = max(1000, SPAWN_MS - self.score // 8)
        self.root.after(next_ms, self._spawn_enemy)

    # ══════════════════════════════════════════════════════════════════════════
    #  主遊戲迴圈
    # ══════════════════════════════════════════════════════════════════════════

    def _game_loop(self):
        """
        使用 after() 非同步驅動的主遊戲迴圈（約 30 FPS）。
        嚴格禁用 time.sleep() 或 while True，所有更新在此方法內完成。

        每幀執行：
          1. 移動所有敵機（Y 軸下移）
          2. 檢查敵機是否抵達底部（觸發傷害）
          3. 移動所有子彈（Y 軸上移）
          4. 清理死亡物件
          5. 排程下一幀
        """
        if self.game_over:
            return   # 遊戲結束後停止迴圈

        # ── 更新敵機 ──────────────────────────────────────────
        dead_enemies = []
        for enemy in self.enemies:
            if not enemy.alive:
                dead_enemies.append(enemy)
                continue

            enemy.move_down()   # 向下移動一個速度單位

            # 檢查是否到達玩家防線
            if enemy.y >= CANVAS_H - 65:
                # 解除鎖定（若此敵機正被鎖定）
                if self.locked is enemy:
                    self.locked = None
                self._take_damage(DAMAGE)   # 玩家受傷
                self._break_combo()         # Combo 斷鏈
                enemy.destroy()             # 使用 Canvas.delete 銷毀元素
                dead_enemies.append(enemy)

        # 移除已死亡敵機
        self.enemies = [e for e in self.enemies
                        if e not in dead_enemies and e.alive]

        # ── 更新子彈 ──────────────────────────────────────────
        for bullet in self.bullets:
            if bullet.alive:
                bullet.move()

        # 移除已消失的子彈
        self.bullets = [b for b in self.bullets if b.alive]

        # ── 排程下一幀（after() 非阻塞） ──────────────────────
        self.root.after(FPS_MS, self._game_loop)

    # ══════════════════════════════════════════════════════════════════════════
    #  遊戲結束
    # ══════════════════════════════════════════════════════════════════════════

    def _end_game(self):
        """顯示遊戲結束畫面，停止所有後續更新。"""
        self.game_over = True
        cx = CANVAS_W // 2

        # 暗色遮罩矩形（模擬半透明效果）
        self.canvas.create_rectangle(
            70, 200, CANVAS_W - 70, 500,
            fill="#05050F", outline="#CC2222", width=3
        )

        # GAME OVER 大標題
        self.canvas.create_text(
            cx, 270,
            text="GAME OVER",
            fill="#FF2222",
            font=("Courier", 40, "bold"),
        )

        # 最終分數
        self.canvas.create_text(
            cx, 340,
            text=f"SCORE    {self.score:,}",
            fill="#FFFFFF",
            font=("Courier", 18, "bold"),
        )

        # 最高 Combo
        self.canvas.create_text(
            cx, 380,
            text=f"MAX COMBO   ×{self.max_combo}",
            fill="#FFEE44",
            font=("Courier", 14),
        )

        # 重啟提示
        self.canvas.create_text(
            cx, 450,
            text="[ 關閉視窗後重新執行以再來一局 ]",
            fill="#334455",
            font=("Courier", 10),
        )


# ══════════════════════════════════════════════════════════════════════════════
#  程式進入點
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """建立 Tkinter 根視窗並啟動遊戲。"""
    root = tk.Tk()
    root.title("⚡ 雷霆打字戰機  Thunder Typer  Phase 1 ⚡")
    root.resizable(False, False)

    # 啟動遊戲（Game.__init__ 內部會呼叫 after() 啟動迴圈）
    Game(root)

    # 進入 Tkinter 事件迴圈（阻塞在此，所有更新由 after() 驅動）
    root.mainloop()


if __name__ == "__main__":
    main()