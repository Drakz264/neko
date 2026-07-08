#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐱 Neko — a focus companion for ADHD brains
════════════════════════════════════════════
A calm cat that lives on your desktop and works alongside you as a "body
double": it visibly focuses with you, shows time as a ring, rewards every
finished block right away, and suggests active breaks — cooperative, never
punishing.

Controls
────────
• Left-click (short)    → park a thought (Feature 2)
• Left-click + drag     → carry the cat around
• Double-click          → pet it (hearts!)
• Right-click           → menu (start focus, interval, ADHD extras, …)
• ESC                   → quit

Research basis (see comments below):
  1) Body doubling  2) external timer vs. time blindness
  3) instant micro-rewards  4) task chunking  5) active breaks
  + anti-freeze start (activation), thought parking lot (impulse control),
    gentle breathing start (transitions)

Python standard library only. Sound optional via `afplay` (macOS).
"""
import tkinter as tk
import math
import random
import platform
import json
import os
import time
import datetime
import subprocess


# ── Colors ───────────────────────────────────────────────────────────────────
C_BODY   = '#1e1e1e'
C_SHADE  = '#0d0d0d'
C_BELLY  = '#c8a070'
C_PINK   = '#ffaacc'
C_EYE    = '#77ee77'
C_WHITE  = '#ffffff'

# HUD colors
C_FOCUS  = '#5fd6a6'   # calm green = focus
C_WRAP   = '#ffc368'   # amber      = wrap-up (last 2 min)
C_BREAK  = '#8fb8ff'   # soft blue  = break
C_TRACK  = '#3a3a3c'   # ring background
C_MUTE   = '#9a9aa0'   # muted text
C_GOLD   = '#ffcf6b'

CONFETTI_COLORS = ['#ff6b6b', '#ffd166', '#6bcb77', '#4d96ff', '#c77dff', '#ff9e6b']

# ── Text: active breaks (movement + novelty through rotation) ────────────────
BREAK_TIPS = [
    'Stand up & stretch properly 🙆',
    'Grab a glass of water 💧',
    'Look out the window, into the distance 👀',
    'Take a few steps around 🚶',
    'Roll your shoulders slowly 🔄',
    'Take three deep breaths 🌬️',
    'Close your eyes & relax for a moment 😌',
    'Pet the cat & breathe 😸',
]

# ── Text: dopamine menu (instant mini-reward after a block) ──────────────────
DOPAMINE_IDEAS = [
    'Reward: stretch it out 🙆',
    'Reward: a sip of water 💧',
    'Reward: 2 min of your favorite song 🎵',
    'Reward: look out the window 🪟',
    'Reward: a piece of chocolate 🍫',
    'Reward: pet the cat 😸',
    'Reward: three deep breaths 🌬️',
    'Reward: shake it out & loosen up 🕺',
]

# ── FEATURE 1: anti-freeze — tiny 2-min starter tasks (activation) ───────────
# Lower the activation energy: make the first step ridiculously small so that
# ADHD start-paralysis is overcome. Rotating (novelty).
ANTIFREEZE_TASKS = [
    'Just open the file and type the title',
    'Just write 3 sentences — however bad',
    'Just open the book and read one page',
    'Just write the first step on a sticky note',
    'Just clear your desk a little',
    'Just read the task out loud',
    'Just start the tiniest possible piece for 5 minutes',
    'Just put pen & paper down and begin',
]

# Context-aware anti-freeze: pick a 2-min starter that fits the task. Matched by
# keywords in what you typed (German + English). First match wins; else generic.
ANTIFREEZE_CATEGORIES = [
    ('study', [
        'study', 'studying', 'learn', 'learning', 'revise', 'revision', 'exam',
        'test', 'quiz', 'read', 'reading', 'chapter', 'lecture', 'notes',
        'flashcard', 'homework', 'math', 'maths', 'physics', 'chemistry',
        'biology', 'history', 'vocab', 'vocabulary', 'geology',
        'lernen', 'prüfung', 'klausur', 'üben', 'lesen', 'kapitel', 'vorlesung',
        'hausaufgabe', 'mathe', 'vokabeln', 'karteikarten', 'referat', 'geologie',
    ], [
        'Just clear your desk down to only what this subject needs',
        'Just open the book/PDF to the right page',
        'Just read one paragraph out loud',
        'Just write the topic and today’s date at the top of a page',
        'Just make one flashcard',
        'Just skim the headings for 2 minutes',
    ]),
    ('writing', [
        'write', 'writing', 'essay', 'report', 'article', 'blog', 'thesis',
        'draft', 'story', 'chapter',
        'schreiben', 'aufsatz', 'bericht', 'text', 'hausarbeit', 'geschichte',
    ], [
        'Just write one ugly sentence — it can be terrible',
        'Just write the title and three bullet points',
        'Just open the doc and type the first heading',
        'Just brain-dump for 2 minutes, no editing allowed',
        'Just write what you want to say in one messy line',
    ]),
    ('coding', [
        'code', 'coding', 'program', 'programming', 'bug', 'debug', 'refactor',
        'function', 'script', 'app', 'website', 'api', 'feature',
        'programmieren', 'fehler', 'funktion', 'skript',
    ], [
        'Just open the file and read the last thing you wrote',
        'Just run it once and read the error',
        'Just write one TODO comment for the next step',
        'Just write the function name and a stub',
        'Just reproduce the bug one time',
    ]),
    ('chores', [
        'clean', 'cleaning', 'tidy', 'laundry', 'dishes', 'room', 'kitchen',
        'chores', 'declutter', 'vacuum', 'wash',
        'putzen', 'aufräumen', 'wäsche', 'geschirr', 'zimmer', 'küche', 'saubermachen',
    ], [
        'Just grab the 5 nearest things and put them away',
        'Just clear one single surface',
        'Just start one load / fill the sink',
        'Just pick up 5 things off the floor',
        'Just set a 2-minute timer and go',
    ]),
    ('admin', [
        'email', 'mail', 'inbox', 'bills', 'bill', 'tax', 'taxes', 'form',
        'application', 'paperwork', 'call', 'phone', 'appointment', 'admin',
        'rechnung', 'steuer', 'formular', 'bewerbung', 'papierkram', 'anruf', 'termin',
    ], [
        'Just open the inbox and read the top item',
        'Just write the subject line',
        'Just find the one document you need',
        'Just open the form and fill a single field',
        'Just write down the phone number you need to call',
    ]),
    ('creative', [
        'draw', 'drawing', 'design', 'paint', 'music', 'compose', 'video',
        'edit', 'art', 'sketch', 'illustration',
        'zeichnen', 'malen', 'musik', 'kunst', 'entwerfen',
    ], [
        'Just open the canvas and make one mark',
        'Just set up your tools / workspace',
        'Just make one deliberately bad rough sketch',
        'Just collect two references and look at them',
    ]),
    ('exercise', [
        'workout', 'exercise', 'gym', 'run', 'running', 'training', 'yoga',
        'stretch', 'walk',
        'sport', 'laufen', 'joggen', 'dehnen', 'fitness', 'training',
    ], [
        'Just put on your workout clothes',
        'Just do 5 of anything',
        'Just fill your water bottle and lace up',
        'Just stretch for 2 minutes',
    ]),
]

# ── Thought parking lot (Feature 2): its own JSON file ───────────────────────
THOUGHTS_PATH = os.path.expanduser('~/.desktop_katze_gedanken.json')

# ── Prep phase (Feature 3): gentle block start ───────────────────────────────
PREP_SECONDS = 10          # length of the breathing countdown before focus
MICRO_SECONDS = 120        # length of an anti-freeze block (2 min)

# ── Sound (macOS system sounds, quiet & mutable) ─────────────────────────────
SOUND_DIR = '/System/Library/Sounds/'
SOUNDS = {
    'wrapup':    ('Tink.aiff',  0.25),   # gentle heads-up
    'complete':  ('Glass.aiff', 0.40),   # block finished
    'break_end': ('Ping.aiff',  0.30),   # break over
}

SETTINGS_PATH = os.path.expanduser('~/.desktop_katze.json')

# Available focus intervals (min). ADHD: a rigid 25/5 often doesn't fit.
INTERVALS = [10, 15, 25, 35, 45]
BREAKS    = [3, 5, 10]

# Available cat sizes (factor on the native 240×300 drawing area)
SCALES = [0.5, 0.65, 0.8, 1.0]

# Thought cloud (Feature 2b): a clickable reminder that pops up now and then
CLOUD_INTERVAL = 150       # min seconds between appearances
CLOUD_CHECK_MS = 15000     # how often to check whether to show it
CLOUD_TIMEOUT = 30         # auto-hide after this many seconds without a click

# Button styles (bg, fg, hover-bg) — real colored buttons, since macOS tk.Button
# ignores background colors and would otherwise be nearly invisible.
BTN_STYLES = {
    'primary':   ('#5fd6a6', '#10241d', '#7ee3bb'),
    'secondary': ('#3a3a3c', '#e8e8ea', '#4a4a4e'),
    'accent':    ('#2f4a63', '#cfe8ff', '#3c5f80'),
}


def _today():
    return datetime.date.today().isoformat()


# ═════════════════════════════════════════════════════════════════════════════
# SCALABLE CANVAS  — thin proxy so the drawing code can stay in native
# coordinates while the cat still renders at any size.
# Scales coordinates, line widths and font sizes by factor s.
# ═════════════════════════════════════════════════════════════════════════════
class _ScaledCanvas:
    def __init__(self, canvas, s=1.0):
        self._c = canvas
        self._s = s
        self._shear = 0.0      # tilt (shear) for the drag physics
        self._pivot_y = 20.0   # pivot at the top of the head (native) → body swings

    def set_scale(self, s):
        self._s = s

    def set_shear(self, sh):
        self._shear = sh

    def _sc(self, args):
        s, sh, py = self._s, self._shear, self._pivot_y
        single = len(args) == 1 and isinstance(args[0], (list, tuple))
        seq = list(args[0]) if single else list(args)
        out = []
        i, n = 0, len(seq)
        while i < n:
            x = seq[i]
            y = seq[i + 1] if i + 1 < n else None
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                # shear around the pivot (native), then scale
                out.append((x + sh * (py - y)) * s)
                out.append(y * s)
                i += 2
            else:
                out.append(x)
                i += 1
        return (out,) if single else tuple(out)

    def _kw(self, kw):
        s = self._s
        if isinstance(kw.get('width'), (int, float)):
            kw['width'] = max(1, kw['width'] * s)
        if 'font' in kw:
            f = kw['font']
            try:
                size = max(6, int(round(f[1] * s)))
                kw['font'] = (f[0], size) + tuple(f[2:])
            except Exception:
                pass
        return kw

    def create_line(self, *a, **k):      return self._c.create_line(*self._sc(a), **self._kw(k))
    def create_oval(self, *a, **k):      return self._c.create_oval(*self._sc(a), **self._kw(k))
    def create_rectangle(self, *a, **k): return self._c.create_rectangle(*self._sc(a), **self._kw(k))
    def create_polygon(self, *a, **k):   return self._c.create_polygon(*self._sc(a), **self._kw(k))
    def create_arc(self, *a, **k):       return self._c.create_arc(*self._sc(a), **self._kw(k))
    def create_text(self, *a, **k):      return self._c.create_text(*self._sc(a), **self._kw(k))

    def move(self, tag, dx, dy):         return self._c.move(tag, dx * self._s, dy * self._s)
    def delete(self, *a):                return self._c.delete(*a)

    def __getattr__(self, name):
        return getattr(self._c, name)


# ═════════════════════════════════════════════════════════════════════════════
# FOCUS TIMER  — makes time concrete (vs. time blindness), no-shame controls
# ═════════════════════════════════════════════════════════════════════════════
class FocusTimer:
    """
    State machine for focus/break.

    modes: 'idle'  = no session (the cat roams freely)
           'prep'  = 10s breathing countdown before focus (gentle start, Feature 3)
           'focus' = work block running   → body-double posture
           'break' = break running         → relaxed/playful

    The timer runs in real time (time.monotonic), independent of frame rate.
    Every transition reports back to the app via a callback.
    """

    def __init__(self, app):
        self.app = app
        self.mode = 'idle'
        self.paused = False
        self.remaining = 0.0     # seconds
        self.total = 0.0
        self.wrapup_fired = False
        self.micro = False       # True = anti-freeze 2-min block (Feature 1)
        self._last = None

        # user-adjustable
        self.focus_len = 25      # minutes
        self.break_len = 5

        # daily stats (instant, visible progress)
        self.stats_date = _today()
        self.blocks_today = 0
        self.minutes_today = 0.0

    # ── Day change: reset stats gently (no streak guilt) ──
    def _sync_day(self):
        if self.stats_date != _today():
            self.stats_date = _today()
            self.blocks_today = 0
            self.minutes_today = 0.0

    # ── Controls ─────────────────────────────────────────────────────────────
    def start_prep(self):
        # FEATURE 3: gentle transition instead of a cold start — short breathing countdown
        self.mode = 'prep'
        self.total = PREP_SECONDS
        self.remaining = PREP_SECONDS
        self.paused = False
        self._last = time.monotonic()

    def start_focus(self):
        self._sync_day()
        self.mode = 'focus'
        self.micro = False
        self.total = self.focus_len * 60
        self.remaining = self.total
        self.paused = False
        self.wrapup_fired = False
        self._last = time.monotonic()

    def start_micro(self):
        # FEATURE 1: anti-freeze — tiny 2-min block that forces the start
        self._sync_day()
        self.mode = 'focus'
        self.micro = True
        self.total = MICRO_SECONDS
        self.remaining = MICRO_SECONDS
        self.paused = False
        self.wrapup_fired = True     # no wrap-up for just 2 min
        self._last = time.monotonic()

    def start_break(self):
        self.mode = 'break'
        self.total = self.break_len * 60
        self.remaining = self.total
        self.paused = False
        self.wrapup_fired = False
        self._last = time.monotonic()
        self.app._pick_break_tip()

    def toggle_pause(self):
        # No-shame: pausable anytime, no loss
        if self.mode in ('focus', 'break'):
            self.paused = not self.paused
            if not self.paused:
                self._last = time.monotonic()

    def skip(self):
        # skip block/break — no penalty, no forced reward
        if self.mode == 'focus':
            self.start_break()
        elif self.mode == 'break':
            self.stop()
            self.app._on_break_complete(skipped=True)

    def stop(self):
        self.mode = 'idle'
        self.paused = False
        self.remaining = 0.0
        self.total = 0.0
        self.wrapup_fired = False

    # ── Queries for the HUD ──────────────────────────────────────────────────
    def progress(self):
        return max(0.0, min(1.0, self.remaining / self.total)) if self.total else 0.0

    def mmss(self):
        s = max(0, int(self.remaining + 0.5))
        return f'{s // 60:02d}:{s % 60:02d}'

    # ── Time step (called every frame) ───────────────────────────────────────
    def tick(self):
        now = time.monotonic()
        if self.mode == 'idle' or self.paused:
            self._last = now
            return
        if self._last is None:
            self._last = now
            return
        dt = now - self._last
        self._last = now
        self.remaining -= dt

        # Wrap-up buffer: gentle heads-up ~2 min before block end
        if self.mode == 'focus' and not self.wrapup_fired and self.remaining <= 120:
            self.wrapup_fired = True
            self.app._on_wrapup()

        if self.remaining <= 0:
            if self.mode == 'prep':
                # FEATURE 3: after breathing, automatically into focus
                self.start_focus()
                self.app._on_focus_begin()
            elif self.mode == 'focus' and self.micro:
                # FEATURE 1: anti-freeze done → gently ask "keep going?"
                self.minutes_today += MICRO_SECONDS / 60.0
                self.mode = 'idle'
                self.micro = False
                self.app._on_micro_complete()
            elif self.mode == 'focus':
                # stats + instant reward, then straight into the break
                self.blocks_today += 1
                self.minutes_today += self.focus_len
                self.app._on_focus_complete()
                self.start_break()
            else:
                self.app._on_break_complete()
                self.stop()


# ═════════════════════════════════════════════════════════════════════════════
# DESKTOP CAT  — UI, rendering & cat states
# ═════════════════════════════════════════════════════════════════════════════
class DesktopCat:
    # Window / canvas
    W_CANVAS, H_CANVAS = 240, 300
    # Offset of the (natively drawn) cat within the canvas
    OX, OY = 25, 62
    # Cat anchor points in the canvas (after offset)
    CAT_CX, CAT_CY = 120, 150      # body center (for ring & follow)
    CAT_HEAD_CY = 110              # head center (for pupil tracking)
    RING_R = 106

    def __init__(self):
        self.root = tk.Tk()
        self._setup_window()
        self._setup_canvas()
        self._setup_state()
        self._setup_bindings()
        self._loop()
        self.root.mainloop()

    # ── Setup ────────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.root.title("Neko")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        # physical window size (adjusted to the scale in _apply_scale)
        self.win_w, self.win_h = self.W_CANVAS, self.H_CANVAS
        self.wx = sw - self.win_w - 30
        self.wy = sh - self.win_h - 60
        self.root.geometry(f"{self.win_w}x{self.win_h}+{int(self.wx)}+{int(self.wy)}")

    def _setup_canvas(self):
        os_name = platform.system()
        if os_name == 'Darwin':
            try:
                self.root.wm_attributes("-transparent", True)
                # IMPORTANT: the window background must be transparent too,
                # otherwise a visible box remains around the cat.
                self.root.config(bg='systemTransparent')
                bg = 'systemTransparent'
            except Exception:
                bg = '#2c2c2e'
        elif os_name == 'Windows':
            self._tkey = '#fe00fe'
            self.root.wm_attributes("-transparentcolor", self._tkey)
            bg = self._tkey
        else:
            bg = '#1a1a2e'

        self.canvas = tk.Canvas(
            self.root, width=self.win_w, height=self.win_h,
            bg=bg, highlightthickness=0
        )
        self.canvas.pack()
        # all drawing goes through this scaling proxy
        self.d = _ScaledCanvas(self.canvas, 1.0)

    def _setup_state(self):
        self.frame = 0
        self.state = 'idle'            # idle|walk_right|walk_left|follow|sleep|happy|focus
        self.state_timer = 0
        self.walk_dir = 1
        self.is_dragging = False
        self._drag_x = 0
        self._drag_y = 0
        self.hearts = []
        self.zzz = []
        self.confetti = []
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # Mouse
        self.follow_mouse = True
        self.mouse_x = self.wx + self.CAT_CX
        self.mouse_y = self.wy + self.CAT_CY

        # Focus / task state
        self.timer = FocusTimer(self)
        self.current_task = ''         # "What are you working on?"
        self._goal = ''                # real goal behind an anti-freeze block
        self.break_tip = random.choice(BREAK_TIPS)
        self.info_msg = ''             # temporary speech bubble (dopamine/prompt)
        self.info_until = 0
        self.celebrate_until = 0       # shows the "✓ done" celebration
        self.happy_until = 0           # briefly happy despite focus (petting)

        # Sound / ambience
        self.sound_on = True
        self.ambient_on = False
        self._amb = None               # running afplay process (ambience)

        # Cat size (factor on the native drawing area)
        self.scale = 1.0

        # Drag physics: the body swings while dragging and settles afterwards
        self.shear = 0.0          # current tilt
        self.shear_v = 0.0        # angular "velocity" (for the wobble)
        self.prev_wx = self.wx
        self.prev_wy = self.wy
        self.vx = 0.0             # window velocity (px/frame)
        self.vy = 0.0

        # ── ADHD extras (Features 1–3), all toggleable via config ──
        self.gentle_start = True       # F3: 10s breathing countdown before focus
        self.park_enabled = True       # F2: thought parking lot (tap the cat)
        self.antifreeze_enabled = True # F1: anti-freeze start button in the dialog

        # Thought parking lot (Feature 2)
        self.thoughts = self._load_thoughts()   # list of parked thoughts (str)
        self._tap_after = None         # scheduled single tap (vs. double click)
        self._press_moved = False      # was it dragged during the click?
        self._dialog_open = False      # prevents stacked dialogs

        # Thought cloud (Feature 2b): a clickable reminder that pops up now and then
        self.cloud_enabled = True
        self.cloud_win = None          # the cloud Toplevel while shown, else None
        self._cloud_hide_id = None     # scheduled auto-hide
        self.cloud_last = time.monotonic()

        self._load_settings()
        self._apply_scale(save=False)  # apply the loaded size to window/canvas
        self.root.after(CLOUD_CHECK_MS, self._cloud_scheduler)
        self.root.after(400, self._spaces_tick)   # show over full-screen apps

    def _setup_bindings(self):
        c = self.d
        c.bind('<ButtonPress-1>',   self._drag_start)
        c.bind('<B1-Motion>',       self._drag_motion)
        c.bind('<ButtonRelease-1>', self._drag_end)
        c.bind('<Double-Button-1>', self._on_double_click)
        c.bind('<Button-2>',        self._on_right_click)
        c.bind('<Button-3>',        self._on_right_click)
        self.root.bind('<Escape>',  lambda _: self._quit())

    # ── Settings (JSON in home) ──────────────────────────────────────────────
    def _load_settings(self):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            d = {}
        self.timer.focus_len = int(d.get('focus_len', 25))
        self.timer.break_len = int(d.get('break_len', 5))
        self.sound_on   = bool(d.get('sound_on', True))
        self.ambient_on = bool(d.get('ambient_on', False))
        self.follow_mouse = bool(d.get('follow_mouse', True))
        self.gentle_start = bool(d.get('gentle_start', True))
        self.park_enabled = bool(d.get('park_enabled', True))
        self.antifreeze_enabled = bool(d.get('antifreeze_enabled', True))
        self.cloud_enabled = bool(d.get('cloud_enabled', True))
        self.scale = min(1.5, max(0.4, float(d.get('scale', 1.0))))
        # only take over daily stats if they're from today
        if d.get('stats_date') == _today():
            self.timer.stats_date = d['stats_date']
            self.timer.blocks_today = int(d.get('blocks_today', 0))
            self.timer.minutes_today = float(d.get('minutes_today', 0.0))

    def _save_settings(self):
        d = {
            'focus_len': self.timer.focus_len,
            'break_len': self.timer.break_len,
            'sound_on': self.sound_on,
            'ambient_on': self.ambient_on,
            'follow_mouse': self.follow_mouse,
            'gentle_start': self.gentle_start,
            'park_enabled': self.park_enabled,
            'antifreeze_enabled': self.antifreeze_enabled,
            'cloud_enabled': self.cloud_enabled,
            'scale': self.scale,
            'stats_date': self.timer.stats_date,
            'blocks_today': self.timer.blocks_today,
            'minutes_today': self.timer.minutes_today,
        }
        try:
            with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=2)
        except Exception:
            pass

    # ── Thought parking lot: persistence (Feature 2) ─────────────────────────
    def _load_thoughts(self):
        try:
            with open(THOUGHTS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            pass
        return []

    def _save_thoughts(self):
        try:
            with open(THOUGHTS_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.thoughts, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── Sound ────────────────────────────────────────────────────────────────
    def _play(self, key):
        if not self.sound_on or platform.system() != 'Darwin':
            return
        entry = SOUNDS.get(key)
        if not entry:
            return
        name, vol = entry
        path = SOUND_DIR + name
        if not os.path.exists(path):
            return
        try:
            subprocess.Popen(['afplay', '-v', str(vol), path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _ambient_tick(self):
        """Very quiet, optional focus ambience (Purr) — only during focus."""
        want = (self.ambient_on and self.sound_on
                and self.timer.mode == 'focus' and platform.system() == 'Darwin')
        if want:
            if self._amb is None or self._amb.poll() is not None:
                p = SOUND_DIR + 'Purr.aiff'
                if os.path.exists(p):
                    try:
                        self._amb = subprocess.Popen(
                            ['afplay', '-v', '0.12', p],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        self._amb = None
        else:
            if self._amb and self._amb.poll() is None:
                try:
                    self._amb.terminate()
                except Exception:
                    pass
            self._amb = None

    # ── Show over full-screen apps / on every Space (macOS) ──────────────────
    def _enable_all_spaces(self):
        """macOS only: make the cat (and its dialogs) appear on every Space and
        *over* full-screen apps (browser, video, etc.). Done by setting the
        Cocoa window collectionBehavior via the Objective-C runtime through
        ctypes — no external packages. Silently no-ops if unavailable."""
        if platform.system() != 'Darwin':
            return
        try:
            import ctypes
            import ctypes.util
            objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
            objc.objc_getClass.restype = ctypes.c_void_p
            objc.objc_getClass.argtypes = [ctypes.c_char_p]
            objc.sel_registerName.restype = ctypes.c_void_p
            objc.sel_registerName.argtypes = [ctypes.c_char_p]
            msg = objc.objc_msgSend

            def call(restype, receiver, selname, argtypes=(), args=()):
                msg.restype = restype
                msg.argtypes = [ctypes.c_void_p, ctypes.c_void_p] + list(argtypes)
                return msg(receiver, objc.sel_registerName(selname), *args)

            # CanJoinAllSpaces (1<<0) | FullScreenAuxiliary (1<<8)
            behavior = (1 << 0) | (1 << 8)
            NSApplication = objc.objc_getClass(b'NSApplication')
            app = call(ctypes.c_void_p, NSApplication, b'sharedApplication')
            windows = call(ctypes.c_void_p, app, b'windows')
            count = call(ctypes.c_ulong, windows, b'count')
            for i in range(count):
                win = call(ctypes.c_void_p, windows, b'objectAtIndex:',
                           (ctypes.c_ulong,), (i,))
                if win:
                    call(None, win, b'setCollectionBehavior:',
                         (ctypes.c_ulong,), (behavior,))
        except Exception:
            pass

    def _spaces_tick(self):
        # re-apply periodically so new dialogs / the cloud inherit it too
        self._enable_all_spaces()
        self.root.after(1500, self._spaces_tick)

    # ── Timer callbacks ──────────────────────────────────────────────────────
    def _pick_break_tip(self):
        # rotating suggestion (novelty): not the same as last time
        choices = [t for t in BREAK_TIPS if t != self.break_tip] or BREAK_TIPS
        self.break_tip = random.choice(choices)

    def _on_wrapup(self):
        # gentle heads-up ~2 min before end (color turns amber via wrapup_fired)
        self._play('wrapup')

    def begin_focus(self, task):
        """Start focus — with a gentle breathing countdown depending on settings (F3)."""
        self.current_task = (task or '').strip()
        self.info_msg = ''
        if self.gentle_start:
            self.timer.start_prep()
            self.state, self.state_timer = 'prep', 0
        else:
            self.timer.start_focus()
            self._on_focus_begin()

    def _on_focus_begin(self):
        # shared entry into a real focus block (directly or after prep)
        self.state, self.state_timer = 'focus', 0

    def _on_focus_complete(self):
        # (3) INSTANT MICRO-REWARD: proud/happy + hearts + confetti
        self.state = 'happy'
        self.state_timer = 0
        self.happy_until = self.frame + 120
        self.celebrate_until = self.frame + 130
        self.info_msg = random.choice(DOPAMINE_IDEAS)   # dopamine menu
        self.info_until = self.frame + 200
        self._spawn_confetti(30)
        self._add_hearts(9)
        self._play('complete')
        self._save_settings()
        # FEATURE 2: gently show the parked thoughts at block end
        if self.thoughts:
            self.root.after(1400, self._show_thoughts_review)

    def _on_micro_complete(self):
        # FEATURE 1: anti-freeze over — small acknowledgment + "keep going?"
        self.state, self.state_timer = 'happy', 0
        self._add_hearts(5)
        self._play('complete')
        self._save_settings()
        self.root.after(600, self._show_continue_prompt)

    def _on_break_complete(self, skipped=False):
        self._play('break_end')
        # no pressure: friendly hint, start when ready (no-shame)
        self.info_msg = 'Ready for the next block? 🐾'
        self.info_until = self.frame + 260

    # ── Particles ────────────────────────────────────────────────────────────
    def _add_hearts(self, n):
        for _ in range(n):
            self.hearts.append((random.randint(40, 145),
                                random.randint(10, 55), 0, 60))

    def _spawn_confetti(self, n):
        for _ in range(n):
            self.confetti.append({
                'x': random.uniform(20, self.W_CANVAS - 20),
                'y': random.uniform(0, 60),
                'vx': random.uniform(-1.2, 1.2),
                'vy': random.uniform(1.0, 3.0),
                'c': random.choice(CONFETTI_COLORS),
                's': random.uniform(4, 8),
                'life': 0,
            })

    # ── Mouse position ───────────────────────────────────────────────────────
    def _update_mouse(self):
        try:
            self.mouse_x = self.root.winfo_pointerx()
            self.mouse_y = self.root.winfo_pointery()
        except Exception:
            pass

    def _cat_center(self):
        """Body center in screen coordinates (for follow), scaled."""
        return self.wx + self.CAT_CX * self.scale, self.wy + self.CAT_CY * self.scale

    def _mouse_offset(self):
        """Pupil offset toward the mouse (±5 px), head center as reference."""
        cx = self.wx + self.CAT_CX * self.scale
        cy = self.wy + self.CAT_HEAD_CY * self.scale
        dx = self.mouse_x - cx
        dy = self.mouse_y - cy
        dist = math.hypot(dx, dy) or 1
        k = min(5, dist * 0.03) / dist
        # return in native units — the proxy multiplies by scale
        return dx * k / self.scale, dy * k / self.scale

    # ═════════════════════════════════════════════════════════════════════════
    # DRAWING
    # ═════════════════════════════════════════════════════════════════════════
    def _draw(self):
        self.canvas.delete('all')

        # (1) BODY DOUBLING: during focus the cat breathes calmly (no romping)
        oy = self.OY
        if self.state == 'focus':
            oy += math.sin(self.frame * 0.06) * 1.6
        elif self.state == 'prep':
            # FEATURE 3: deeper, calmer breathing as a visible guide
            oy += math.sin(self.frame * 0.045) * 4.0

        # Draw the cat in native coordinates, then move it as a whole
        # (proxy scales coords/widths/fonts; move scales the offset)
        self.d.set_shear(self.shear)     # drag physics only on the cat
        self._draw_cat()
        self.d.move('all', self.OX, oy)

        # HUD (ring/timer/task) and confetti without tilt, in final coords
        self.d.set_shear(0.0)
        self._draw_hud()
        self._draw_confetti()

    def _draw_cat(self):
        c = self.d
        f = self.frame
        st = self.state

        # ── Tail ──
        if st == 'sleep':
            swing = 0
        elif st == 'happy':
            swing = math.sin(f * 0.55) * 24
        elif st in ('focus', 'prep'):
            swing = math.sin(f * 0.05) * 6      # calm, focused
        elif st in ('walk_right', 'walk_left', 'follow'):
            swing = math.sin(f * 0.30) * 14
        else:
            swing = math.sin(f * 0.07) * 10

        c.create_line(
            94, 118, 94 + swing, 152, 92 + swing * 1.5, 168,
            fill=C_BODY, width=9, smooth=True, capstyle='round'
        )

        # ── Body ──
        c.create_oval(50, 80, 140, 135, fill=C_BODY, outline=C_SHADE, width=2)
        c.create_oval(66, 96, 124, 132, fill=C_BELLY, outline='')

        # ── Head ──
        c.create_oval(44, 18, 146, 96, fill=C_BODY, outline=C_SHADE, width=2)

        # ── Ears ──
        c.create_polygon(54, 46, 45,  8, 74, 32, fill=C_BODY,  outline=C_SHADE, width=1)
        c.create_polygon(136, 46, 145, 8, 116, 32, fill=C_BODY, outline=C_SHADE, width=1)
        c.create_polygon(57, 43, 50, 15, 71, 31, fill=C_PINK,  outline='')
        c.create_polygon(133, 43, 140, 15, 119, 31, fill=C_PINK, outline='')

        # ── Eyes ──
        is_blink = (f % 90) < 3
        px, py = self._mouse_offset()
        if st in ('focus', 'prep'):
            px = py = 0.0            # focused gaze forward

        if st == 'sleep':
            c.create_line(62, 54, 80, 54, fill=C_WHITE, width=3, capstyle='round')
            c.create_line(110, 54, 128, 54, fill=C_WHITE, width=3, capstyle='round')
        elif is_blink:
            c.create_line(62, 55, 80, 55, fill=C_WHITE, width=3, capstyle='round')
            c.create_line(110, 55, 128, 55, fill=C_WHITE, width=3, capstyle='round')
        elif st == 'happy':
            c.create_arc(59, 42, 83, 64, start=10, extent=160,
                         style='arc', outline=C_WHITE, width=3)
            c.create_arc(107, 42, 131, 64, start=10, extent=160,
                         style='arc', outline=C_WHITE, width=3)
        else:
            c.create_oval(60, 42, 83, 66, fill=C_EYE, outline='black', width=1)
            c.create_oval(107, 42, 130, 66, fill=C_EYE, outline='black', width=1)
            c.create_oval(68 + px, 48 + py, 75 + px, 60 + py, fill='black')
            c.create_oval(115 + px, 48 + py, 122 + px, 60 + py, fill='black')
            c.create_oval(65, 44, 69, 48, fill=C_WHITE, outline='')
            c.create_oval(112, 44, 116, 48, fill=C_WHITE, outline='')

        # ── Nose ──
        c.create_polygon(91, 70, 99, 70, 95, 75, fill=C_PINK, outline='')

        # ── Mouth (subtly content during focus, depending on daily progress) ──
        if st == 'happy':
            c.create_arc(82, 72, 108, 88, start=200, extent=-160,
                         style='arc', outline=C_WHITE, width=2)
        elif st == 'focus' and self.timer.blocks_today > 0:
            # (SHOULD) visibly more content over the day: a slight smile
            c.create_arc(84, 73, 106, 85, start=200, extent=-160,
                         style='arc', outline=C_WHITE, width=1)
        else:
            c.create_line(91, 75, 87, 80, fill=C_WHITE, width=1, capstyle='round')
            c.create_line(99, 75, 103, 80, fill=C_WHITE, width=1, capstyle='round')

        # ── Whiskers ──
        c.create_line(38, 68, 80, 72, fill=C_WHITE, width=1)
        c.create_line(38, 76, 80, 76, fill=C_WHITE, width=1)
        c.create_line(110, 72, 152, 68, fill=C_WHITE, width=1)
        c.create_line(110, 76, 152, 76, fill=C_WHITE, width=1)

        # ── Paws ──
        bob = math.sin(f * 0.38) * 6 if st in ('walk_right', 'walk_left', 'follow') else 0
        c.create_oval(56, 122 + int(bob),  82, 140 + int(bob),
                      fill=C_BODY, outline=C_SHADE, width=1)
        c.create_oval(108, 122 - int(bob), 134, 140 - int(bob),
                      fill=C_BODY, outline=C_SHADE, width=1)
        for base_x, sign in ((56, 1), (108, -1)):
            base_y = 122 + int(bob) * sign
            for i in range(3):
                tx = base_x + 7 + i * 8
                c.create_oval(tx, base_y + 13, tx + 6, base_y + 18,
                              fill=C_SHADE, outline='')

        # ── Hearts (move along with the cat) ──
        nxt = []
        for (hx, hy, age, mx_) in self.hearts:
            if age < mx_:
                a = 1.0 - age / mx_
                sz = int(11 + age * 0.25)
                col = f'#{int(255*a):02x}{int(60*a):02x}{int(120*a):02x}'
                c.create_text(hx, hy - age * 0.9,
                              text='♥', font=('Arial', sz, 'bold'), fill=col)
                nxt.append((hx, hy, age + 1, mx_))
        self.hearts = nxt

        # ── Zzz ──
        if st == 'sleep':
            nzzz = []
            for (zx, zy, age, mx_) in self.zzz:
                if age < mx_:
                    a = max(0.0, 1.0 - age / mx_)
                    sz = int(9 + age // 7)
                    col = f'#{int(160*a):02x}{int(160*a):02x}ff'
                    c.create_text(zx, zy, text='z',
                                  font=('Arial', sz, 'bold'), fill=col)
                    nzzz.append((zx, zy - 0.65, age + 1, mx_))
            self.zzz = nzzz
            if f % 50 == 0:
                self.zzz.append((140 + random.randint(-5, 12), 22, 0, 95))

    # ── HUD: ring (timer), task, reward, daily counter ───────────────────────
    def _draw_hud(self):
        c = self.d
        t = self.timer
        cx, cy, r = self.CAT_CX, self.CAT_CY, self.RING_R
        celebrating = self.frame < self.celebrate_until

        # FEATURE 3: gentle start — breathing countdown instead of the timer ring
        if t.mode == 'prep':
            self._draw_prep_hud()
            return

        # (2) EXTERNAL TIMER as a ring around the cat — time becomes visible/tangible
        if t.mode in ('focus', 'break'):
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C_TRACK, width=6)
            if t.mode == 'focus':
                col = C_WRAP if t.wrapup_fired else C_FOCUS
            else:
                col = C_BREAK
            extent = -359.999 * t.progress()   # clockwise from top
            c.create_arc(cx - r, cy - r, cx + r, cy + r,
                         start=90, extent=extent, style='arc', outline=col, width=6)

            # Countdown text (in addition to the ring)
            c.create_text(cx, 22, text=t.mmss(),
                          font=('Helvetica', 21, 'bold'), fill=C_WHITE)

            # Mode label
            if celebrating:
                label, lcol = '✓ Block done!', C_GOLD
            elif t.paused:
                label, lcol = 'paused', C_MUTE
            elif t.mode == 'focus' and t.micro:
                label, lcol = 'Anti-freeze · just begin 🧊', C_FOCUS
            elif t.mode == 'focus' and t.wrapup_fired:
                label, lcol = 'almost done · ease out', C_WRAP
            elif t.mode == 'focus':
                label, lcol = 'Focus', C_FOCUS
            else:
                label, lcol = 'Break', C_BREAK
            c.create_text(cx, 44, text=label, font=('Helvetica', 11), fill=lcol)

        # ── bottom speech bubble: task / break tip / reward / prompt ──
        pill = None
        if self.info_msg and self.frame < self.info_until:
            pill = (self.info_msg, C_GOLD)                       # dopamine/prompt
        elif t.mode == 'focus' and self.current_task:
            # (4) ONE-TASK FOCUS: the current task stays visible
            pill = ('📌 ' + self._short(self.current_task, 30), C_FOCUS)
        elif t.mode == 'break':
            # (5) concrete, active break suggestion
            pill = ('🐾 ' + self._short(self.break_tip, 34), C_BREAK)
        if pill:
            self._draw_pill(cx, 270, pill[0], accent=pill[1])

        # ── Daily counter (instant, visible progress) ──
        n = t.blocks_today
        if n > 0:
            fish = '🐟' * min(n, 5) + ('…' if n > 5 else '')
            c.create_text(cx, 293,
                          text=f'{fish}  {n} blocks · {int(t.minutes_today)} min today',
                          font=('Helvetica', 10), fill=C_MUTE)

    def _draw_prep_hud(self):
        """FEATURE 3: breathing ring + countdown as a gentle lead-in."""
        c = self.d
        t = self.timer
        cx, cy = self.CAT_CX, self.CAT_CY
        phase = math.sin(self.frame * 0.045)              # -1..1 (breathing cycle)
        rr = 60 + (phase + 1) * 24                        # 60..108 px, grows on inhale
        c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=C_BREAK, width=4)
        secs = max(1, int(math.ceil(t.remaining)))
        c.create_text(cx, 22, text=str(secs), font=('Helvetica', 22, 'bold'), fill=C_WHITE)
        breathe = 'Breathe in …' if math.cos(self.frame * 0.045) > 0 else 'Breathe out …'
        c.create_text(cx, 44, text=breathe, font=('Helvetica', 12), fill=C_BREAK)
        self._draw_pill(cx, 270, 'Take a breath … starting soon', accent=C_BREAK)

    def _draw_confetti(self):
        c = self.d
        nxt = []
        for p in self.confetti:
            p['vy'] += 0.06
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] += 1
            if p['y'] < self.H_CANVAS + 10 and p['life'] < 130:
                c.create_rectangle(p['x'], p['y'], p['x'] + p['s'], p['y'] + p['s'],
                                   fill=p['c'], outline='')
                nxt.append(p)
        self.confetti = nxt

    # ── Drawing helpers ──────────────────────────────────────────────────────
    def _draw_pill(self, cx, cy, text, accent=C_FOCUS):
        c = self.d
        w = max(70, int(6.4 * len(text)) + 26)
        w = min(w, self.W_CANVAS - 8)
        h = 26
        self._round_rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 12,
                         fill='#2b2b2e', outline=accent)
        c.create_text(cx, cy, text=text, font=('Helvetica', 11), fill='#e8e8ea')

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.d.create_polygon(pts, smooth=True, **kw)

    @staticmethod
    def _short(s, n):
        s = s.strip()
        return s if len(s) <= n else s[:n - 1] + '…'

    # ═════════════════════════════════════════════════════════════════════════
    # STATE MACHINE
    # ═════════════════════════════════════════════════════════════════════════
    def _update(self):
        self.state_timer += 1
        self._update_mouse()
        self.timer.tick()

        if self.is_dragging:
            self.state = 'happy'
            return

        mode = self.timer.mode

        if mode == 'prep':
            # FEATURE 3: breathe calmly, no distraction, no roaming
            self.state = 'prep'
            return

        if mode == 'focus':
            # BODY DOUBLE: sit calmly, don't roam, don't sleep, don't chase the
            # mouse (otherwise the cat becomes a distraction).
            self.state = 'happy' if self.frame < self.happy_until else 'focus'
            return

        # mode == 'break' or 'idle' → playful/free behavior
        if self.state in ('focus', 'prep'):
            self.state = 'idle'
            self.state_timer = 0
        self._idle_behavior()

    def _idle_behavior(self):
        """Free roaming, mouse follow, occasional nap (base)."""
        sw = self.screen_w

        # ── Mouse follow ──
        if self.follow_mouse and self.state not in ('happy', 'sleep'):
            cat_cx, _ = self._cat_center()
            dist_x = self.mouse_x - cat_cx
            if abs(dist_x) > 80:
                self.state = 'follow'
                self.walk_dir = 1 if dist_x > 0 else -1
                self.state_timer = 0

        if self.state == 'idle':
            if self.state_timer > random.randint(100, 180):
                self.state_timer = 0
                r = random.random()
                if r < 0.20:
                    self.state, self.walk_dir = 'walk_right', 1
                elif r < 0.40:
                    self.state, self.walk_dir = 'walk_left', -1
                elif r < 0.55:
                    self.state = 'sleep'

        elif self.state == 'follow':
            cat_cx, _ = self._cat_center()
            dist_x = self.mouse_x - cat_cx
            speed = int(min(4, max(1, abs(dist_x) // 40)))
            self.wx = int(self.wx + speed * self.walk_dir)
            self.wx = max(0, min(sw - self.win_w, self.wx))
            self.root.geometry(f"{self.win_w}x{self.win_h}+{int(self.wx)}+{int(self.wy)}")
            if abs(dist_x) < 60:
                self.state = 'happy'
                self.state_timer = 0

        elif self.state in ('walk_right', 'walk_left'):
            self.wx += 2 * self.walk_dir
            if self.wx < 0:
                self.wx, self.walk_dir = 0, 1
                self.state = 'walk_right'
            elif self.wx > sw - self.win_w:
                self.wx, self.walk_dir = sw - self.win_w, -1
                self.state = 'walk_left'
            self.root.geometry(f"{self.win_w}x{self.win_h}+{int(self.wx)}+{int(self.wy)}")
            if self.state_timer > random.randint(80, 150):
                self.state_timer = 0
                self.state = 'idle'

        elif self.state == 'sleep':
            if self.state_timer > 380:
                self.state_timer = 0
                self.state = 'idle'
                self.zzz.clear()

        elif self.state == 'happy':
            if self.state_timer > 75:
                self.state_timer = 0
                self.state = 'idle'

    # ── Drag physics ─────────────────────────────────────────────────────────
    def _physics(self):
        """The body leans against the motion while dragging and settles back
        upright with a damped wobble on release."""
        # window velocity this frame
        self.vx = self.wx - self.prev_wx
        self.vy = self.wy - self.prev_wy
        self.prev_wx, self.prev_wy = self.wx, self.wy

        # Target tilt: only while dragging, clamped (otherwise it would stick out
        # of the window and get clipped). On release it pulls back to 0.
        if self.is_dragging:
            target = max(-0.30, min(0.30, self.vx * 0.010))
        else:
            target = 0.0

        # damped spring (underdamped → wobbles briefly)
        self.shear_v = self.shear_v * 0.80 + (target - self.shear) * 0.14
        self.shear += self.shear_v
        self.shear = max(-0.32, min(0.32, self.shear))

    # ── Loop ─────────────────────────────────────────────────────────────────
    def _loop(self):
        self.frame += 1
        self._update()
        self._physics()
        self._ambient_tick()
        self._draw()
        self.root.after(50, self._loop)

    # ═════════════════════════════════════════════════════════════════════════
    # EVENTS
    # ═════════════════════════════════════════════════════════════════════════
    def _drag_start(self, event):
        self._drag_x, self._drag_y = event.x, event.y
        self._press_x, self._press_y = event.x, event.y
        self._press_moved = False
        self.is_dragging = True
        self.state = 'happy'
        self.state_timer = 0
        # a scheduled single tap is voided by a new click
        self._cancel_pending_tap()

    def _drag_motion(self, event):
        # past ~4px of motion it counts as a real drag (not a tap)
        if abs(event.x - self._press_x) + abs(event.y - self._press_y) > 4:
            self._press_moved = True
        self.wx += event.x - self._drag_x
        self.wy += event.y - self._drag_y
        self.wx = max(0, min(self.screen_w - self.win_w, self.wx))
        self.wy = max(0, min(self.screen_h - self.win_h, self.wy))
        self.root.geometry(f"{self.win_w}x{self.win_h}+{int(self.wx)}+{int(self.wy)}")

    def _drag_end(self, event):
        self.is_dragging = False
        # briefly happy, but calm again during focus (happy_until not set)
        if self.timer.mode != 'focus':
            self.state = 'happy'
            self.state_timer = 0
        # FEATURE 2: a tap (click without dragging) opens the thought parking
        # lot. Slightly delayed so a double-click (petting) can intercept it.
        if self.park_enabled and not self._press_moved:
            self._cancel_pending_tap()
            self._tap_after = self.root.after(260, self._fire_tap)

    def _fire_tap(self):
        self._tap_after = None
        self._open_park()

    def _cancel_pending_tap(self):
        if self._tap_after is not None:
            try:
                self.root.after_cancel(self._tap_after)
            except Exception:
                pass
            self._tap_after = None

    def _on_double_click(self, event):
        # double-click = pet → discard the scheduled single tap
        self._cancel_pending_tap()
        self._pet()

    def _pet(self):
        self._add_hearts(7)
        self.state, self.state_timer = 'happy', 0
        if self.timer.mode == 'focus':
            self.happy_until = self.frame + 55   # briefly enjoy, then back to focusing

    # ── Right-click menu ─────────────────────────────────────────────────────
    def _on_right_click(self, event):
        m = tk.Menu(self.root, tearoff=0)
        mode = self.timer.mode

        # Focus controls
        if mode == 'idle':
            m.add_command(label='▶️  Start focus', command=self._open_task_dialog)
        else:
            lbl = '⏸️  Pause' if not self.timer.paused else '▶️  Resume'
            m.add_command(label=lbl, command=self.timer.toggle_pause)
            skip = '⏭️  Skip block' if mode == 'focus' else '⏭️  Skip break'
            m.add_command(label=skip, command=self.timer.skip)
            m.add_command(label='⏹️  End session', command=self.timer.stop)

        # FEATURE 2: park a thought (also by tapping the cat)
        if self.park_enabled:
            m.add_command(label='💭  Park a thought', command=self._open_park)
            if self.thoughts:
                m.add_command(label=f'📋  Show thoughts ({len(self.thoughts)})',
                              command=self._show_thoughts_review)

        # Choose interval
        iv = tk.Menu(m, tearoff=0)
        for v in INTERVALS:
            mark = '  ✓' if v == self.timer.focus_len else ''
            iv.add_command(label=f'{v} min{mark}',
                           command=lambda x=v: self._set_focus_len(x))
        m.add_cascade(label='⏱️  Focus length', menu=iv)

        bp = tk.Menu(m, tearoff=0)
        for v in BREAKS:
            mark = '  ✓' if v == self.timer.break_len else ''
            bp.add_command(label=f'{v} min{mark}',
                           command=lambda x=v: self._set_break_len(x))
        m.add_cascade(label='☕  Break length', menu=bp)

        # Cat size
        sz = tk.Menu(m, tearoff=0)
        for v in SCALES:
            mark = '  ✓' if abs(v - self.scale) < 0.01 else ''
            label = f'{int(round(v * 100))}%'
            if v == 1.0:
                label += ' (default)'
            sz.add_command(label=label + mark, command=lambda x=v: self._set_scale(x))
        m.add_cascade(label='🔍  Size', menu=sz)

        m.add_separator()

        # Toggles
        m.add_command(label='🔊  Sound  ' + ('✓' if self.sound_on else '–'),
                      command=self._toggle_sound)
        m.add_command(label='🎵  Ambience (focus)  ' + ('✓' if self.ambient_on else '–'),
                      command=self._toggle_ambient)
        m.add_command(label='👁  Follow mouse  ' + ('✓' if self.follow_mouse else '–'),
                      command=self._toggle_follow)
        m.add_command(label='😸  Pet', command=self._pet)

        # ADHD extras (Features 1–3) toggleable
        ex = tk.Menu(m, tearoff=0)
        ex.add_command(label='🌬️  Gentle start (breathing countdown)  ' + ('✓' if self.gentle_start else '–'),
                       command=self._toggle_gentle)
        ex.add_command(label='💭  Thought parking lot  ' + ('✓' if self.park_enabled else '–'),
                       command=self._toggle_park)
        ex.add_command(label='🧊  Anti-freeze button  ' + ('✓' if self.antifreeze_enabled else '–'),
                       command=self._toggle_antifreeze)
        ex.add_command(label='☁️  Thought cloud reminder  ' + ('✓' if self.cloud_enabled else '–'),
                       command=self._toggle_cloud)
        m.add_cascade(label='🧠  ADHD extras', menu=ex)

        m.add_separator()

        # Daily info (display only)
        t = self.timer
        m.add_command(
            label=f'📊  Today: {t.blocks_today} blocks · {int(t.minutes_today)} min',
            state='disabled')
        m.add_command(label='❌  Quit', command=self._quit)

        # macOS: the popup menu only appears when the window has focus. For a
        # borderless always-on-top window you have to force it.
        try:
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass
        try:
            m.tk_popup(int(event.x_root), int(event.y_root))
        finally:
            m.grab_release()

    # ── Dialog helper (uniform dark style, stack guard) ──────────────────────
    def _new_dialog(self, title):
        d = tk.Toplevel(self.root)
        d.title(title)
        d.configure(bg='#1e1e1e')
        d.attributes('-topmost', True)
        d.resizable(False, False)
        d.geometry('+%d+%d' % (max(20, self.wx - 110), max(40, self.wy - 30)))
        self._dialog_open = True

        def close():
            self._dialog_open = False
            try:
                d.destroy()
            except Exception:
                pass
            # give focus back to the cat window so the right-click menu works
            # again immediately (otherwise the borderless window stays inactive
            # and you'd have to click/drag the cat first).
            try:
                self.root.lift()
                self.root.focus_force()
                self.canvas.focus_set()
            except Exception:
                pass

        d.protocol('WM_DELETE_WINDOW', close)
        d.bind('<Escape>', lambda _: close())
        return d, close

    def _button(self, parent, text, command, kind='secondary', small=False):
        """A clearly visible colored button (Frame+Label), because macOS
        tk.Button ignores background colors and renders nearly invisibly."""
        bg, fg, hover = BTN_STYLES.get(kind, BTN_STYLES['secondary'])
        size = 11 if small else 12
        weight = 'bold' if kind == 'primary' else 'normal'
        padx, pady = (10, 3) if small else (16, 7)
        f = tk.Frame(parent, bg=bg, highlightthickness=0)
        lbl = tk.Label(f, text=text, bg=bg, fg=fg, font=('Helvetica', size, weight),
                       padx=padx, pady=pady, cursor='pointinghand')
        lbl.pack()

        def on_click(_):
            command()

        def on_enter(_):
            f.configure(bg=hover); lbl.configure(bg=hover)

        def on_leave(_):
            f.configure(bg=bg); lbl.configure(bg=bg)

        for w in (f, lbl):
            w.bind('<Button-1>', on_click)
            w.bind('<Enter>', on_enter)
            w.bind('<Leave>', on_leave)
        return f

    # ── Task dialog ("What are you working on?") ─────────────────────────────
    def _open_task_dialog(self):
        if self._dialog_open:
            return
        d, close = self._new_dialog('Start a focus block')

        tk.Label(d, text='What are you working on?', bg='#1e1e1e', fg='#eaeaea',
                 font=('Helvetica', 14, 'bold')).pack(padx=20, pady=(18, 2))
        tk.Label(d, text='One concrete thing — e.g. "solve 5 exercises"',
                 bg='#1e1e1e', fg=C_MUTE, font=('Helvetica', 11)).pack(padx=20)

        var = tk.StringVar(value=self.current_task)
        e = tk.Entry(d, textvariable=var, width=36, font=('Helvetica', 12),
                     bg='#2b2b2e', fg='#ffffff', insertbackground='#ffffff', relief='flat')
        e.pack(padx=20, pady=12, ipady=4)
        e.focus_force()
        e.icursor('end')

        hint = f'Focus {self.timer.focus_len} min · Break {self.timer.break_len} min'
        if self.gentle_start:
            hint += ' · gentle start'
        tk.Label(d, text=hint, bg='#1e1e1e', fg='#7a7a80',
                 font=('Helvetica', 10)).pack(pady=(0, 6))

        btns = tk.Frame(d, bg='#1e1e1e')
        btns.pack(pady=(2, 8))

        def start():
            task = var.get().strip()
            close()
            self.begin_focus(task)

        self._button(btns, "Let's go 🐾", start, 'primary').pack(side='left', padx=6)
        self._button(btns, 'Cancel', close, 'secondary').pack(side='left', padx=6)

        # FEATURE 1: anti-freeze — for the moments when starting is blocked
        if self.antifreeze_enabled:
            def antifreeze():
                goal = var.get().strip()
                close()
                self._start_antifreeze(goal)
            self._button(d, "🧊  I don't know how to start", antifreeze,
                         'accent').pack(pady=(4, 16))
        else:
            tk.Frame(d, bg='#1e1e1e', height=8).pack()

        d.bind('<Return>', lambda _: start())

    # ── FEATURE 1: start anti-freeze + "keep going?" prompt ──────────────────
    def _antifreeze_task(self, goal):
        """Pick a 2-min starter that fits what you're working on."""
        g = (goal or '').lower()
        for _name, keys, tasks in ANTIFREEZE_CATEGORIES:
            if any(k in g for k in keys):
                return random.choice(tasks)
        return random.choice(ANTIFREEZE_TASKS)

    def _start_antifreeze(self, goal=''):
        # remember the real goal so we can restore it if the user keeps going
        self._goal = (goal or '').strip()
        self.current_task = self._antifreeze_task(self._goal)
        self.info_msg = 'Just this — 2 minutes is enough 🧊'
        self.info_until = self.frame + 160
        self.timer.start_micro()
        self.state, self.state_timer = 'focus', 0

    def _show_continue_prompt(self):
        if self._dialog_open:
            return
        d, close = self._new_dialog('Keep going?')
        tk.Label(d, text='Two minutes done 🎉', bg='#1e1e1e', fg='#eaeaea',
                 font=('Helvetica', 14, 'bold')).pack(padx=24, pady=(18, 2))
        tk.Label(d, text='The hardest part — starting — is behind you.',
                 bg='#1e1e1e', fg=C_MUTE, font=('Helvetica', 11)).pack(padx=24, pady=(0, 14))

        btns = tk.Frame(d, bg='#1e1e1e')
        btns.pack(pady=(0, 18), padx=24)

        def keep_going():
            close()
            # warmed up → straight into focus, without another breathing countdown.
            # Restore the real goal (we showed a tiny starter during the 2 min).
            self.info_msg = ''
            if getattr(self, '_goal', ''):
                self.current_task = self._goal
            self.timer.start_focus()
            self.state, self.state_timer = 'focus', 0

        def take_break():
            close()
            self.timer.start_break()

        def done():
            close()
            self.timer.stop()

        self._button(btns, 'Yes, keep going 🐾', keep_going, 'primary').pack(side='left', padx=5)
        self._button(btns, 'Short break', take_break, 'secondary').pack(side='left', padx=5)
        self._button(btns, "That's enough for now", done, 'secondary').pack(side='left', padx=5)

    # ── FEATURE 2: thought parking lot — park quickly ────────────────────────
    def _open_park(self):
        if self._dialog_open or not self.park_enabled:
            return
        d, close = self._new_dialog('Park a thought')
        tk.Label(d, text='💭 Park it quickly, then back to focus', bg='#1e1e1e',
                 fg='#eaeaea', font=('Helvetica', 13, 'bold')).pack(padx=20, pady=(16, 2))
        tk.Label(d, text='The thought is saved, not chased.',
                 bg='#1e1e1e', fg=C_MUTE, font=('Helvetica', 10)).pack(padx=20)

        var = tk.StringVar()
        e = tk.Entry(d, textvariable=var, width=34, font=('Helvetica', 12),
                     bg='#2b2b2e', fg='#ffffff', insertbackground='#ffffff', relief='flat')
        e.pack(padx=20, pady=12, ipady=4)
        e.focus_force()

        btns = tk.Frame(d, bg='#1e1e1e')
        btns.pack(pady=(0, 16))

        def park():
            txt = var.get().strip()
            if txt:
                self.thoughts.append(txt)
                self._save_thoughts()
                self.info_msg = '💭 parked — carry on'
                self.info_until = self.frame + 40
            close()

        self._button(btns, 'Park 💭', park, 'primary').pack(side='left', padx=6)
        self._button(btns, 'Cancel', close, 'secondary').pack(side='left', padx=6)
        d.bind('<Return>', lambda _: park())

    # ── FEATURE 2: show thoughts at block end (handle/discard) ───────────────
    def _show_thoughts_review(self):
        if self._dialog_open or not self.thoughts:
            return
        d, close = self._new_dialog('Your parked thoughts')
        tk.Label(d, text='You wanted to remember these:', bg='#1e1e1e', fg='#eaeaea',
                 font=('Helvetica', 14, 'bold')).pack(padx=20, pady=(16, 10))

        rows = tk.Frame(d, bg='#1e1e1e')
        rows.pack(padx=18, fill='x')

        def rebuild():
            for w in rows.winfo_children():
                w.destroy()
            if not self.thoughts:
                tk.Label(rows, text='All cleared 🎉', bg='#1e1e1e',
                         fg=C_FOCUS, font=('Helvetica', 12)).pack(pady=10)
                return
            for i, text in enumerate(list(self.thoughts)):
                row = tk.Frame(rows, bg='#1e1e1e')
                row.pack(fill='x', pady=3)
                tk.Label(row, text='• ' + text, bg='#1e1e1e', fg='#e8e8ea',
                         font=('Helvetica', 11), wraplength=250, justify='left',
                         anchor='w').pack(side='left', fill='x', expand=True)

                def discard(idx=i):
                    try:
                        self.thoughts.pop(idx)
                    except IndexError:
                        pass
                    self._save_thoughts()
                    rebuild()

                self._button(row, '✓ done', discard, 'secondary', small=True).pack(side='right')

        rebuild()

        foot = tk.Frame(d, bg='#1e1e1e')
        foot.pack(pady=(12, 16))
        self._button(foot, 'Keep the rest & close', close, 'secondary').pack(side='left', padx=6)

    # ── FEATURE 2b: the thought cloud (periodic clickable reminder) ──────────
    def _cloud_scheduler(self):
        """Every so often, if there are parked thoughts and we're not focusing,
        pop up a clickable cloud. It hides itself after CLOUD_TIMEOUT seconds."""
        try:
            if (self.cloud_enabled and self.thoughts and self.cloud_win is None
                    and not self._dialog_open
                    and self.timer.mode in ('idle', 'break')
                    and time.monotonic() - self.cloud_last >= CLOUD_INTERVAL):
                self._show_cloud()
        except Exception:
            pass
        self.root.after(CLOUD_CHECK_MS, self._cloud_scheduler)

    def _show_cloud(self):
        if self.cloud_win is not None or not self.thoughts:
            return
        n = len(self.thoughts)
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.wm_attributes('-topmost', True)
        x = int(self.wx)
        y = max(30, int(self.wy) - 46)
        w.geometry(f'+{x}+{y}')
        frame = tk.Frame(w, bg='#2b2b2e', highlightbackground=C_BREAK, highlightthickness=2)
        frame.pack()
        text = f'☁️  {n} thought' + ('s' if n != 1 else '') + '  ·  tap to see'
        lbl = tk.Label(frame, text=text, bg='#2b2b2e', fg='#e8e8ea',
                       font=('Helvetica', 12, 'bold'), padx=12, pady=6, cursor='pointinghand')
        lbl.pack()

        def click(_):
            self._hide_cloud()
            self._show_thoughts_review()

        for wid in (frame, lbl):
            wid.bind('<Button-1>', click)
        self.cloud_win = w
        self.cloud_last = time.monotonic()
        # auto-hide after CLOUD_TIMEOUT seconds without a click
        self._cloud_hide_id = self.root.after(CLOUD_TIMEOUT * 1000, self._hide_cloud)

    def _hide_cloud(self):
        if self._cloud_hide_id is not None:
            try:
                self.root.after_cancel(self._cloud_hide_id)
            except Exception:
                pass
            self._cloud_hide_id = None
        if self.cloud_win is not None:
            try:
                self.cloud_win.destroy()
            except Exception:
                pass
            self.cloud_win = None
        self.cloud_last = time.monotonic()   # reset the interval after hiding

    # ── Settings toggles ─────────────────────────────────────────────────────
    def _set_focus_len(self, v):
        self.timer.focus_len = v
        self._save_settings()

    def _set_break_len(self, v):
        self.timer.break_len = v
        self._save_settings()

    def _toggle_sound(self):
        self.sound_on = not self.sound_on
        self._save_settings()

    def _toggle_ambient(self):
        self.ambient_on = not self.ambient_on
        self._save_settings()

    def _toggle_follow(self):
        self.follow_mouse = not self.follow_mouse
        if not self.follow_mouse and self.state == 'follow':
            self.state = 'idle'
        self._save_settings()

    def _toggle_gentle(self):
        self.gentle_start = not self.gentle_start
        self._save_settings()

    def _toggle_park(self):
        self.park_enabled = not self.park_enabled
        self._save_settings()

    def _toggle_antifreeze(self):
        self.antifreeze_enabled = not self.antifreeze_enabled
        self._save_settings()

    def _toggle_cloud(self):
        self.cloud_enabled = not self.cloud_enabled
        if not self.cloud_enabled:
            self._hide_cloud()
        self._save_settings()

    # ── Cat size ─────────────────────────────────────────────────────────────
    def _apply_scale(self, s=None, save=True):
        if s is not None:
            self.scale = s
        self.win_w = max(1, int(round(self.W_CANVAS * self.scale)))
        self.win_h = max(1, int(round(self.H_CANVAS * self.scale)))
        self.d.set_scale(self.scale)
        self.canvas.config(width=self.win_w, height=self.win_h)
        # keep the position on screen
        self.wx = max(0, min(self.screen_w - self.win_w, self.wx))
        self.wy = max(0, min(self.screen_h - self.win_h, self.wy))
        self.root.geometry(f"{self.win_w}x{self.win_h}+{int(self.wx)}+{int(self.wy)}")
        if save:
            self._save_settings()

    def _set_scale(self, s):
        self._apply_scale(s)

    def _quit(self):
        self._save_settings()
        self._hide_cloud()
        if self._amb and self._amb.poll() is None:
            try:
                self._amb.terminate()
            except Exception:
                pass
        self.root.destroy()


if __name__ == '__main__':
    DesktopCat()
