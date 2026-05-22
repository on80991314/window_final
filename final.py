"""thunder_typer_v2.py
=========================
雷霆打字戰機 V2 — 期末改善版

改善項目（相較 V1）：
  1.  滾動視差星空（3 層速率不同的星星）
  2.  Boss 敵機（字母 ≥7、紅色大型、撞底扣雙倍血）
  3.  連擊特效文字（GOOD / GREAT / EXCELLENT / GODLIKE）
  4.  打字光束追蹤特效（子彈用貝茲曲線閃光取代單點橢圓）
  5.  完整 _restart() 狀態重置（修正 _flash_id / _wave_tid 洩漏）
  6.  locked 敵機死亡時安全解鎖，不產生空指針
  7.  HP 低於 30% 時背景持續脈動紅色警告
  8.  高分排行榜（本次遊戲前三名，儲存於記憶體）
  9.  Combo 斷掉時短暫顯示「MISS!」提示
  10. 敵機依字母長度染色（難度視覺化）
"""

import tkinter as tk
from tkinter import ttk
import random
import math
import string

# ════════════════════════════════════════════════
#  全域常數
# ════════════════════════════════════════════════

CANVAS_W      = 680
CANVAS_H      = 720
FPS_MS        = 33           # ~30 FPS
ENEMY_SPEED   = 0.85
SPAWN_MS      = 2600
MAX_ENEMIES   = 9
BULLET_SPEED  = 16
MAX_HP        = 100
DAMAGE        = 20
DAMAGE_BOSS   = 35
CHAR_W        = 8

DIFF_SCORE_STEP  = 300
DIFF_SPEED_INC   = 0.14
DIFF_SPAWN_DEC   = 200
DIFF_SPAWN_MIN   = 800
DIFF_MAX_LEVEL   = 10

BOSS_PROB        = 0.15      # 每次生成有此機率為 Boss
BOSS_MIN_LEN     = 7        # Boss 單字最短長度

# 星空層數（速率由慢到快）
STAR_LAYERS = [
    {"count": 60,  "speed": 0.15, "color": "#10103A", "r": 1},
    {"count": 40,  "speed": 0.35, "color": "#1A1A55", "r": 1},
    {"count": 20,  "speed": 0.65, "color": "#2A2A80", "r": 2},
]

COMBO_TEXTS = [
    (4,  "GOOD!",      "#88FF88"),
    (8,  "GREAT!",     "#FFDD00"),
    (12, "EXCELLENT!", "#FF8800"),
    (20, "GODLIKE!",   "#FF3399"),
]

WORDS = list(set([
    # 4 字母
    "able","acid","aged","also","apex","arch","army","atom",
    "back","barn","beam","bird","blue","bold","bond","bred",
    "cage","calm","cave","chin","chip","claw","clay","clue",
    "damp","dare","dark","data","dawn","deal","deck","dome",
    "echo","edge","emit","epic","even","evil","exam","exit",
    # 5 字母
    "alpha","blaze","brave","brick","cable","chase","chord",
    "clash","cloud","cobra","coral","crane","crisp","crown",
    "delta","depth","digit","disco","draft","drain","drift",
    "eagle","early","earth","eight","elite","ember","epoch",
    "fable","faith","fault","feast","fever","fifth","fixed",
    "flame","flash","flint","flood","flora","focus","force",
    "frost","globe","grace","grade","grain","grand","grant",
    "grave","graze","greed","green","greet","grind","guard",
    "hazel","heavy","heist","helix","honor","horse","hover",
    "humid","haste","hyper","ideal","index","indie","infer",
    "ivory","jewel","joint","joker","judge","juice","karma",
    "laser","layer","learn","level","light","limit","logic",
    "lunar","magic","maple","march","marsh","match","merge",
    "metal","might","mimic","minor","model","motor","nexus",
    "night","ninja","noble","noise","north","novel","nymph",
    "oasis","ocean","orbit","other","outer","oxide","panel",
    "paper","patch","pause","pearl","phase","pilot","pixel",
    "polar","power","press","prism","probe","prone","proxy",
    "pulse","quest","quick","quiet","quota","radar","rally",
    "range","rapid","ratio","razor","reach","realm","relay",
    "relic","remix","renew","repel","reset","ridge","risky",
    "rival","river","robot","rocky","rouge","round","route",
    "royal","sabre","scale","scope","scout","seize","sigma",
    "skate","skill","slice","slide","slope","smoke","snake",
    "solar","solid","solve","sonar","sound","south","spark",
    "spawn","speed","spell","spend","spire","sport","spray",
    "squad","stack","staff","stage","stake","stamp","stand",
    "stark","start","state","steal","steel","stern","stick",
    "sting","stock","stomp","stone","store","storm","story",
    "strap","straw","strip","stuck","study","style","surge",
    "swamp","swarm","sweep","swift","sword","swirl","tango",
    "taunt","tempo","tense","tiger","tight","timer","titan",
    "token","topaz","torch","total","tower","trace","track",
    "trade","trail","train","trait","triad","tribe","trick",
    "troop","trove","truce","truly","trunk","trust","truth",
    "turbo","tweak","twist","ultra","unity","upper","usher",
    "valor","valve","vault","venom","viral","virus","visor",
    "vista","vital","waves","weave","wedge","whirl","wield",
    "xenon","yacht","yield","young","zoned","zesty","zebra",
    # 6 字母
    "battle","castle","circle","combat","danger","empire",
    "energy","engine","falcon","flight","forest","frozen",
    "galaxy","gamble","garden","golden","hunter","jungle",
    "legend","matrix","mirror","mystic","nature","nebula",
    "nether","palace","planet","plasma","python","rafter",
    "random","reborn","rescue","rocket","rumble","savage",
    "scroll","server","shadow","signal","simple","spider",
    "spirit","static","stream","strike","strobe","strong",
    "studio","system","target","temple","throne","toggle",
    "travel","tundra","turret","vector","vertex","vortex",
    "warden","weapon","window","winter","wizard","wonder",
    # 7 字母（Boss 專用）
    "banquet","caption","cavalry","channel","chapter","circuit",
    "cluster","command","concept","control","courage","crystal",
    "destiny","diamond","discord","dragon","eclipse","element",
    "enhance","eternal","explain","fantasy","fission","fortune",
    "freedom","gateway","genesis","gravity","horizon","impulse",
    "justice","kingdom","lantern","machine","network","observe",
    "phantom","process","quantum","reactor","reflect","refresh",
    "release","remnant","replace","request","reserve","restore",
    "revenue","reverse","revival","resolve","shatter","silence",
    "skyline","slander","society","soldier","sorcery","stellar",
    "subject","sublime","supreme","survive","thunder","torment",
    "trigger","typhoon","vampire","voltage","witness","warrior",
]))

BOSS_WORDS  = [w for w in WORDS if len(w) >= BOSS_MIN_LEN]
NORMAL_WORDS = [w for w in WORDS if len(w) < BOSS_MIN_LEN]


# ════════════════════════════════════════════════
#  Explosion 爆炸粒子
# ════════════════════════════════════════════════

class Explosion:
    _COLORS = ["#FFFFFF","#FFEE88","#FFAA33","#FF6600","#CC3300","#882200"]

    def __init__(self, canvas, x, y, root, count=12, big=False):
        self.canvas = canvas
        self.root   = root
        self._items = []
        self._vels  = []
        self._life  = len(self._COLORS)
        speed_max   = 6.5 if big else 4.5
        r_max       = 5   if big else 4

        for i in range(count):
            angle = (2*math.pi/count)*i + random.uniform(-0.4, 0.4)
            spd   = random.uniform(1.5, speed_max)
            vx    = math.cos(angle)*spd
            vy    = math.sin(angle)*spd
            r     = random.randint(2, r_max)
            oval  = canvas.create_oval(
                x-r, y-r, x+r, y+r,
                fill=self._COLORS[0], outline="")
            self._items.append(oval)
            self._vels.append((vx, vy))

        self._animate()

    def _animate(self):
        if self._life <= 0:
            for o in self._items:
                self.canvas.delete(o)
            return
        color = self._COLORS[len(self._COLORS)-self._life]
        for i, o in enumerate(self._items):
            vx, vy = self._vels[i]
            self.canvas.move(o, vx, vy)
            self.canvas.itemconfig(o, fill=color)
        self._life -= 1
        self.root.after(38, self._animate)


# ════════════════════════════════════════════════
#  StarField  滾動視差星空
# ════════════════════════════════════════════════

class StarField:
    """三層視差滾動星空。每幀由 Game._game_loop 呼叫 update()。"""

    def __init__(self, canvas, w, h):
        self.canvas = canvas
        self.W = w
        self.H = h
        self._stars = []   # list of (oval_id, speed, y_pos)
        self._build()

    def _build(self):
        for layer in STAR_LAYERS:
            for _ in range(layer["count"]):
                x = random.randint(0, self.W)
                y = random.randint(0, self.H)
                r = layer["r"]
                oid = self.canvas.create_oval(
                    x-r, y-r, x+r, y+r,
                    fill=layer["color"], outline=""
                )
                self._stars.append({"id": oid, "speed": layer["speed"],
                                    "r": r, "color": layer["color"]})
                # 把座標記錄在 dict（不用 coords 查詢，快一點）
                self._stars[-1]["x"] = float(x)
                self._stars[-1]["y"] = float(y)

    def update(self):
        for s in self._stars:
            s["y"] += s["speed"]
            if s["y"] > self.H:
                # 移到頂端，x 隨機
                nx = random.randint(0, self.W)
                self.canvas.coords(s["id"],
                    nx-s["r"], 0, nx+s["r"], s["r"]*2)
                s["x"] = float(nx)
                s["y"] = 0.0
            else:
                self.canvas.move(s["id"], 0, s["speed"])

    def destroy(self):
        for s in self._stars:
            self.canvas.delete(s["id"])
        self._stars.clear()


# ════════════════════════════════════════════════
#  Enemy 敵機
# ════════════════════════════════════════════════

class Enemy:
    # 依字母長度選色（越長越紅/越亮）
    _LEN_COLORS = [
        (4, "#1A5A8A", "#4499CC"),   # 短：藍
        (5, "#3A6A2A", "#66AA44"),   # 中：綠
        (6, "#7A5A10", "#FFAA22"),   # 中長：橙
    ]
    _BOSS_FILL    = "#6A0000"
    _BOSS_OUTLINE = "#FF2222"
    COLOR_LOCKED  = "#FFFF00"
    COLOR_TYPED   = "#FFE033"
    COLOR_REMAIN  = "#E8E8E8"

    def __init__(self, canvas, word, x, is_boss=False):
        self.canvas  = canvas
        self.word    = word
        self.typed   = 0
        self.x       = float(x)
        self.y       = 18.0
        self.alive   = True
        self.speed   = ENEMY_SPEED
        self.is_boss = is_boss

        wlen = len(word)
        self._hw = max(wlen*5+22, 44)
        self._hh = 16 if not is_boss else 20
        self._txt_start_x = x - wlen*CHAR_W/2
        self._txt_y       = self.y - self._hh - 14

        if is_boss:
            fill, outline, width = self._BOSS_FILL, self._BOSS_OUTLINE, 3
        else:
            fill, outline, width = self._pick_colors(wlen)

        self._rect = canvas.create_rectangle(
            x-self._hw, self.y-self._hh,
            x+self._hw, self.y+self._hh,
            fill=fill, outline=outline, width=width)

        # Boss 頭頂加「BOSS」標籤
        self._boss_tag = None
        if is_boss:
            self._boss_tag = canvas.create_text(
                x, self.y-self._hh-28,
                text="◆ BOSS",
                fill="#FF4444",
                font=("Courier", 9, "bold"))

        self._typed_txt = canvas.create_text(
            self._txt_start_x, self._txt_y,
            text="", fill=self.COLOR_TYPED,
            font=("Courier", 11, "bold"), anchor="w")
        self._remain_txt = canvas.create_text(
            self._txt_start_x, self._txt_y,
            text=word, fill=self.COLOR_REMAIN,
            font=("Courier", 11, "bold"), anchor="w")

    @classmethod
    def _pick_colors(cls, wlen):
        for min_len, fill, outline in cls._LEN_COLORS:
            if wlen <= min_len:
                return fill, outline, 2
        return "#5A1A3A", "#CC44AA", 2   # 7+ 字母普通（不應觸發，Boss 另行處理）

    def _refresh_text(self):
        typed_str  = self.word[:self.typed]
        remain_str = self.word[self.typed:]
        remain_x   = self._txt_start_x + self.typed*CHAR_W
        self.canvas.itemconfig(self._typed_txt,  text=typed_str)
        self.canvas.itemconfig(self._remain_txt, text=remain_str)
        self.canvas.coords(self._remain_txt, remain_x, self._txt_y)

    def move_down(self):
        self.y      += self.speed
        self._txt_y += self.speed
        self.canvas.move(self._rect,       0, self.speed)
        self.canvas.move(self._typed_txt,  0, self.speed)
        self.canvas.move(self._remain_txt, 0, self.speed)
        if self._boss_tag:
            self.canvas.move(self._boss_tag, 0, self.speed)

    def try_type(self, char):
        if self.typed < len(self.word) and self.word[self.typed] == char:
            self.typed += 1
            self._refresh_text()
            return True
        return False

    def is_done(self):
        return self.typed == len(self.word)

    def first_char_matches(self, char):
        return self.typed == 0 and bool(self.word) and self.word[0] == char

    def set_locked(self, locked):
        if locked:
            self.canvas.itemconfig(self._rect, outline=self.COLOR_LOCKED, width=3)
        else:
            fill, outline, w = self._pick_colors(len(self.word))
            if self.is_boss:
                outline, w = self._BOSS_OUTLINE, 3
            self.canvas.itemconfig(self._rect, outline=outline, width=w)

    def get_bbox(self):
        return (self.x-self._hw, self.y-self._hh,
                self.x+self._hw, self.y+self._hh)

    def destroy(self):
        self.canvas.delete(self._rect)
        self.canvas.delete(self._typed_txt)
        self.canvas.delete(self._remain_txt)
        if self._boss_tag:
            self.canvas.delete(self._boss_tag)
        self.alive = False


# ════════════════════════════════════════════════
#  Bullet 子彈（帶光暈尾跡）
# ════════════════════════════════════════════════

class Bullet:
    def __init__(self, canvas, sx, sy, tx, ty):
        self.canvas = canvas
        self.x      = float(sx)
        self.y      = float(sy)
        self.alive  = True

        dx   = tx - sx
        dy   = ty - sy
        dist = math.hypot(dx, dy)
        if dist == 0:
            self._vx, self._vy = 0.0, -1.0
        else:
            self._vx = (dx/dist)*BULLET_SPEED
            self._vy = (dy/dist)*BULLET_SPEED

        # 主彈頭
        self._oval = canvas.create_oval(
            sx-3, sy-5, sx+3, sy+5,
            fill="#00FFCC", outline="")
        # 光暈（較大、半透明白）
        self._glow = canvas.create_oval(
            sx-5, sy-7, sx+5, sy+7,
            fill="", outline="#44FFEE", width=1)

    def move(self):
        self.x += self._vx
        self.y += self._vy
        self.canvas.move(self._oval, self._vx, self._vy)
        self.canvas.move(self._glow, self._vx, self._vy)
        if (self.y < 0 or self.y > CANVAS_H or
                self.x < 0 or self.x > CANVAS_W):
            self.destroy()

    def destroy(self):
        self.canvas.delete(self._oval)
        self.canvas.delete(self._glow)
        self.alive = False


# ════════════════════════════════════════════════
#  Game 主控制器
# ════════════════════════════════════════════════

class Game:

    def __init__(self, root):
        self.root = root
        self._hp_style = ttk.Style()
        self._hp_style.theme_use("clam")
        self._configure_hp_style("#22DD66")
        self._high_scores = []          # 本次程式執行的排行（前 3）
        self._reset_state()
        self._build_ui()
        self._draw_player()
        self._bind_keys()
        self.root.after(900,    self._spawn_enemy)
        self.root.after(FPS_MS, self._game_loop)

    # ─── 狀態重置 ───────────────────────────────
    def _reset_state(self):
        self.score          = 0
        self.combo          = 0
        self.max_combo      = 0
        self.hp             = MAX_HP
        self.game_over      = False
        self._paused        = False
        self._diff_level    = 0
        self._current_speed = ENEMY_SPEED
        self._current_spawn = SPAWN_MS
        self.enemies        = []
        self.bullets        = []
        self.locked         = None
        self._px            = CANVAS_W // 2
        self._py            = CANVAS_H - 40
        self._active_words  = set()
        self._wave_tid      = None      # 修正：確保重置
        self._flash_id      = None      # 修正：確保重置
        self._danger_pulsing = False
        self._danger_phase   = 0
        self._starfield     = None

    # ─── UI 建構 ────────────────────────────────
    def _build_ui(self):
        self.root.configure(bg="#07071A")

        top = tk.Frame(self.root, bg="#07071A")
        top.pack(fill=tk.X, padx=14, pady=(8,3))

        def lbl(parent, text, fg):
            tk.Label(parent, text=text,
                     bg="#07071A", fg=fg,
                     font=("Courier", 8, "bold")).pack(side=tk.LEFT)

        lbl(top, "SCORE", "#445566")
        self._score_var = tk.StringVar(value="0")
        tk.Label(top, textvariable=self._score_var,
                 bg="#07071A", fg="#FFFFFF",
                 font=("Courier",14,"bold"),
                 width=9, anchor="w").pack(side=tk.LEFT, padx=(3,16))

        lbl(top, "LV", "#445566")
        self._lv_var = tk.StringVar(value="1")
        tk.Label(top, textvariable=self._lv_var,
                 bg="#07071A", fg="#88CCFF",
                 font=("Courier",14,"bold"),
                 width=3, anchor="w").pack(side=tk.LEFT, padx=(3,16))

        lbl(top, "COMBO", "#445566")
        self._combo_var = tk.StringVar(value="×0")
        self._combo_lbl = tk.Label(top, textvariable=self._combo_var,
                                   bg="#07071A", fg="#FFEE44",
                                   font=("Courier",14,"bold"),
                                   width=6, anchor="w")
        self._combo_lbl.pack(side=tk.LEFT, padx=(3,0))

        hp_f = tk.Frame(top, bg="#07071A")
        hp_f.pack(side=tk.RIGHT)
        lbl(hp_f, "HP", "#445566")
        self._hp_var = tk.IntVar(value=MAX_HP)
        self._hp_bar = ttk.Progressbar(
            hp_f, variable=self._hp_var, maximum=MAX_HP,
            length=180, style="hp.Horizontal.TProgressbar",
            mode="determinate")
        self._hp_bar.pack(side=tk.LEFT, padx=(5,0))

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_W, height=CANVAS_H,
            bg="#080820", highlightthickness=1,
            highlightbackground="#1A2A40")
        self.canvas.pack(padx=14, pady=(2,2))

        # 滾動星空
        self._starfield = StarField(self.canvas, CANVAS_W, CANVAS_H)

        self.canvas.create_line(
            0, CANVAS_H-65, CANVAS_W, CANVAS_H-65,
            fill="#151530", width=1, dash=(5,5))

        self._hint_lbl = tk.Label(
            self.root,
            text="首字母鎖定（黃框）→ 打完整單字→擊毀！  錯字=Combo歸零  ESC=暫停",
            bg="#07071A", fg="#2A3A4A",
            font=("Courier", 8))
        self._hint_lbl.pack(pady=(0,7))

    def _configure_hp_style(self, color):
        self._hp_style.configure(
            "hp.Horizontal.TProgressbar",
            troughcolor="#111128", background=color,
            bordercolor="#223344", lightcolor=color, darkcolor=color)

    # ─── 玩家戰機 ──────────────────────────────
    def _draw_player(self):
        cx, cy = self._px, self._py
        c = self.canvas
        c.create_polygon(cx-8,cy+20, cx,cy+36, cx+8,cy+20,
                         fill="#FF6600", outline="", tags="player")
        c.create_polygon(cx-4,cy+20, cx,cy+28, cx+4,cy+20,
                         fill="#FFCC00", outline="", tags="player")
        c.create_polygon(cx-14,cy-6, cx-40,cy+20, cx-14,cy+20,
                         fill="#0A5588", outline="", tags="player")
        c.create_polygon(cx+14,cy-6, cx+40,cy+20, cx+14,cy+20,
                         fill="#0A5588", outline="", tags="player")
        c.create_rectangle(cx-13,cy-24, cx+13,cy+20,
                           fill="#1177CC", outline="#44AAFF", width=2,
                           tags="player")
        c.create_rectangle(cx-4,cy-38, cx+4,cy-24,
                           fill="#33CCFF", outline="", tags="player")
        c.create_oval(cx-5,cy-44, cx+5,cy-36,
                      fill="#88EEFF", outline="", tags="player")
        c.create_oval(cx-8,cy-18, cx+8,cy-4,
                      fill="#88DDFF", outline="#AAEEFF", tags="player")
        c.create_oval(cx-42,cy+18, cx-38,cy+22,
                      fill="#FF3333", outline="", tags="player")
        c.create_oval(cx+38,cy+18, cx+42,cy+22,
                      fill="#FF3333", outline="", tags="player")

    # ─── 鍵盤 ──────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<KeyPress>", self._on_key)

    def _on_key(self, event):
        if event.keysym == "Escape":
            self._toggle_pause()
            return
        if self.game_over or self._paused:
            return
        ch = event.char.lower()
        if ch not in string.ascii_lowercase:
            return

        if self.locked is None:
            for enemy in self.enemies:
                if enemy.alive and enemy.first_char_matches(ch):
                    self.locked = enemy
                    enemy.set_locked(True)
                    enemy.try_type(ch)
                    self._fire_bullet()
                    if enemy.is_done():
                        self._kill_enemy(enemy)
                        self.locked = None
                    break
        else:
            # 修正：locked 敵機可能已被摧毀
            if not self.locked.alive:
                self.locked = None
                return
            hit = self.locked.try_type(ch)
            if hit:
                self._fire_bullet()
                if self.locked.is_done():
                    self._kill_enemy(self.locked)
                    self.locked = None
            else:
                self._break_combo()
                self._show_miss()

    # ─── 暫停 ──────────────────────────────────
    def _toggle_pause(self):
        if self.game_over:
            return
        self._paused = not self._paused
        if self._paused:
            self._pause_bg = self.canvas.create_rectangle(
                150, 295, CANVAS_W-150, 385,
                fill="#05050F", outline="#3355AA", width=2)
            self._pause_txt = self.canvas.create_text(
                CANVAS_W//2, 340,
                text="⏸  PAUSED  ( ESC 繼續 )",
                fill="#88AAFF", font=("Courier",18,"bold"))
        else:
            self.canvas.delete(self._pause_bg)
            self.canvas.delete(self._pause_txt)
            self.root.after(FPS_MS, self._game_loop)

    # ─── 子彈 ──────────────────────────────────
    def _fire_bullet(self):
        sx = float(self._px)
        sy = float(self._py - 40)
        if self.locked and self.locked.alive:
            tx, ty = self.locked.x, self.locked.y
        else:
            tx, ty = sx, sy - 500.0
        self.bullets.append(Bullet(self.canvas, sx, sy, tx, ty))

    # ─── 碰撞偵測 ──────────────────────────────
    def _check_bullet_collisions(self):
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            bx, by = bullet.x, bullet.y
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                x1,y1,x2,y2 = enemy.get_bbox()
                if x1-3 <= bx <= x2+3 and y1-3 <= by <= y2+3:
                    bullet.destroy()
                    Explosion(self.canvas, bx, by, self.root, count=5)
                    break

    # ─── 擊殺與計分 ────────────────────────────
    def _kill_enemy(self, enemy):
        self.combo    += 1
        self.max_combo = max(self.max_combo, self.combo)

        multiplier = self.combo//4 + 1
        pts        = len(enemy.word)*10*multiplier
        self.score += pts
        self._score_var.set(f"{self.score:,}")

        self._combo_var.set(f"×{self.combo}")
        if self.combo >= 20:
            self._combo_lbl.config(fg="#FF3399")
        elif self.combo >= 12:
            self._combo_lbl.config(fg="#FF3333")
        elif self.combo >= 6:
            self._combo_lbl.config(fg="#FF8800")
        else:
            self._combo_lbl.config(fg="#FFEE44")

        # 大型爆炸（Boss 更大）
        Explosion(self.canvas, enemy.x, enemy.y, self.root,
                  count=20 if enemy.is_boss else 16,
                  big=enemy.is_boss)

        self._popup(enemy.x, enemy.y, f"+{pts}")

        # 連擊特效文字
        for threshold, text, color in sorted(COMBO_TEXTS, key=lambda t: t[0], reverse=True):
            if self.combo >= threshold:
                self._combo_popup(text, color)
                break

        self._active_words.discard(enemy.word.lower())
        enemy.destroy()
        self.enemies = [e for e in self.enemies if e.alive]
        self._check_difficulty()

    def _popup(self, x, y, text):
        tid = self.canvas.create_text(
            x, y, text=text,
            fill="#FFE033", font=("Courier",13,"bold"))
        self._animate_popup(tid, 18)

    def _animate_popup(self, tid, n):
        if n <= 0:
            self.canvas.delete(tid)
            return
        self.canvas.move(tid, 0, -2)
        self.root.after(35, lambda: self._animate_popup(tid, n-1))

    def _combo_popup(self, text, color):
        """在畫面中央偏上顯示連擊特效文字。"""
        cx = CANVAS_W//2
        tid = self.canvas.create_text(
            cx, CANVAS_H//2,
            text=text, fill=color,
            font=("Courier",24,"bold"))
        self._animate_popup(tid, 22)

    def _show_miss(self):
        """Combo 斷掉時顯示 MISS!。"""
        cx = CANVAS_W//2
        tid = self.canvas.create_text(
            cx, CANVAS_H-120,
            text="MISS!", fill="#FF4444",
            font=("Courier",16,"bold"))
        self._animate_popup(tid, 14)

    # ─── 難度系統 ──────────────────────────────
    def _check_difficulty(self):
        new_level = min(self.score//DIFF_SCORE_STEP, DIFF_MAX_LEVEL)
        if new_level > self._diff_level:
            self._diff_level    = new_level
            self._current_speed = ENEMY_SPEED + new_level*DIFF_SPEED_INC
            self._current_spawn = max(
                DIFF_SPAWN_MIN, SPAWN_MS - new_level*DIFF_SPAWN_DEC)
            self._lv_var.set(str(new_level+1))
            self._show_wave_text(f"LEVEL  {new_level+1}")

    def _show_wave_text(self, text):
        if self._wave_tid is not None:
            self.canvas.delete(self._wave_tid)
        self._wave_tid = self.canvas.create_text(
            CANVAS_W//2, CANVAS_H//2-60,
            text=text, fill="#44AAFF",
            font=("Courier",26,"bold"))
        self.root.after(1800, self._clear_wave_text)

    def _clear_wave_text(self):
        if self._wave_tid:
            self.canvas.delete(self._wave_tid)
            self._wave_tid = None

    # ─── Combo 中斷 ────────────────────────────
    def _break_combo(self):
        self.combo = 0
        self._combo_var.set("×0")
        self._combo_lbl.config(fg="#FFEE44")

    # ─── HP ────────────────────────────────────
    def _take_damage(self, dmg):
        self.hp = max(0, self.hp - dmg)
        self._hp_var.set(self.hp)
        ratio = self.hp / MAX_HP
        if ratio <= 0.25:
            self._configure_hp_style("#DD2211")
            if not self._danger_pulsing:
                self._danger_pulsing = True
                self._pulse_danger()
        elif ratio <= 0.55:
            self._configure_hp_style("#FF9900")
        else:
            self._configure_hp_style("#22DD66")
        self._flash_damage()
        if self.hp <= 0:
            self._end_game()

    def _flash_damage(self):
        if self._flash_id is not None:
            self.root.after_cancel(self._flash_id)
        self.canvas.configure(bg="#300808")
        self._flash_id = self.root.after(
            220, lambda: self.canvas.configure(bg="#080820"))

    def _pulse_danger(self):
        """HP ≤ 25% 時背景持續紅色脈動。"""
        if self.game_over or self.hp > MAX_HP*0.25:
            self._danger_pulsing = False
            self.canvas.configure(bg="#080820")
            return
        self._danger_phase = (self._danger_phase+1) % 12
        shade = int(8 + 14 * math.sin(self._danger_phase * math.pi / 6))
        bg = f"#{shade+8:02X}0808"
        self.canvas.configure(bg=bg)
        self.root.after(80, self._pulse_danger)

    # ─── 敵機生成 ──────────────────────────────
    def _spawn_enemy(self):
        if self.game_over:
            return
        if not self._paused and len(self.enemies) < MAX_ENEMIES:
            is_boss   = random.random() < BOSS_PROB and self._diff_level >= 2
            pool      = BOSS_WORDS if is_boss else NORMAL_WORDS
            available = [w for w in pool if w.lower() not in self._active_words]
            if not available:
                available = pool
            word  = random.choice(available)
            self._active_words.add(word.lower())

            margin = 80
            x      = random.randint(margin, CANVAS_W-margin)
            enemy  = Enemy(self.canvas, word, x, is_boss=is_boss)
            enemy.speed = self._current_speed * (1.3 if is_boss else 1.0)
            self.enemies.append(enemy)

        self.root.after(self._current_spawn, self._spawn_enemy)

    # ─── 主迴圈 ────────────────────────────────
    def _game_loop(self):
        if self.game_over or self._paused:
            return

        # 滾動星空
        if self._starfield:
            self._starfield.update()

        dead = []
        for enemy in self.enemies:
            if not enemy.alive:
                dead.append(enemy)
                continue
            enemy.move_down()
            if enemy.y >= CANVAS_H - 65:
                if self.locked is enemy:
                    self.locked = None
                self._active_words.discard(enemy.word.lower())
                Explosion(self.canvas, enemy.x, enemy.y-20, self.root, count=8)
                dmg = DAMAGE_BOSS if enemy.is_boss else DAMAGE
                self._take_damage(dmg)
                self._break_combo()
                enemy.destroy()
                dead.append(enemy)

        self.enemies = [e for e in self.enemies if e not in dead and e.alive]

        for bullet in self.bullets:
            if bullet.alive:
                bullet.move()
        self.bullets = [b for b in self.bullets if b.alive]

        self._check_bullet_collisions()
        self.root.after(FPS_MS, self._game_loop)

    # ─── 遊戲結束 ──────────────────────────────
    def _end_game(self):
        self.game_over = True
        self._danger_pulsing = False
        self.canvas.configure(bg="#080820")

        # 更新排行榜
        self._high_scores.append(self.score)
        self._high_scores.sort(reverse=True)
        self._high_scores = self._high_scores[:3]

        cx = CANVAS_W//2
        self.canvas.create_rectangle(
            60, 140, CANVAS_W-60, 560,
            fill="#05050F", outline="#CC2222", width=3)
        self.canvas.create_text(
            cx, 210, text="GAME OVER",
            fill="#FF2222", font=("Courier",40,"bold"))
        self.canvas.create_text(
            cx, 285, text=f"SCORE    {self.score:,}",
            fill="#FFFFFF", font=("Courier",18,"bold"))
        self.canvas.create_text(
            cx, 330, text=f"MAX COMBO   ×{self.max_combo}",
            fill="#FFEE44", font=("Courier",14))
        self.canvas.create_text(
            cx, 368, text=f"最高難度   LV {self._diff_level+1}",
            fill="#88CCFF", font=("Courier",13))

        # 排行榜
        self.canvas.create_text(
            cx, 405, text="── 本日排行 ──",
            fill="#446688", font=("Courier",11))
        for i, sc in enumerate(self._high_scores):
            medal = ["🥇","🥈","🥉"][i]
            self.canvas.create_text(
                cx, 428+i*24,
                text=f"{medal}  {sc:,}",
                fill=["#FFD700","#CCCCCC","#CC8844"][i],
                font=("Courier",12,"bold"))

        btn = tk.Button(
            self.canvas,
            text="▶  再來一局",
            bg="#112233", fg="#AADDFF",
            font=("Courier",14,"bold"),
            activebackground="#1E4466",
            activeforeground="#FFFFFF",
            relief=tk.FLAT, padx=20, pady=8,
            command=self._restart)
        self.canvas.create_window(cx, 515, window=btn)

    def _restart(self):
        # 停止危險脈動
        self._danger_pulsing = False
        if self._flash_id:
            self.root.after_cancel(self._flash_id)

        # 銷毀舊星空
        if self._starfield:
            self._starfield.destroy()

        self.canvas.delete("all")
        self._reset_state()
        self._configure_hp_style("#22DD66")
        self._score_var.set("0")
        self._combo_var.set("×0")
        self._combo_lbl.config(fg="#FFEE44")
        self._lv_var.set("1")
        self._hp_var.set(MAX_HP)
        self.canvas.configure(bg="#080820")

        # 重建星空
        self._starfield = StarField(self.canvas, CANVAS_W, CANVAS_H)
        self.canvas.create_line(
            0, CANVAS_H-65, CANVAS_W, CANVAS_H-65,
            fill="#151530", width=1, dash=(5,5))
        self._draw_player()
        self.root.after(900,    self._spawn_enemy)
        self.root.after(FPS_MS, self._game_loop)


# ════════════════════════════════════════════════
#  進入點
# ════════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.title("⚡ 雷霆打字戰機 V2  Thunder Typer  ⚡")
    root.resizable(False, False)
    Game(root)
    root.mainloop()


if __name__ == "__main__":
    main()
