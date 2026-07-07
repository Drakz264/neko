#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐱 Desktop-Katze — Konzentrations-Tool für ADHS
════════════════════════════════════════════════
Eine ruhige Katze, die auf dem Desktop lebt und als "Body Double" beim
Fokussieren hilft: sie arbeitet sichtbar mit, macht Zeit über einen Ring
sichtbar, belohnt jeden geschafften Block sofort und schlägt bewegte
Pausen vor — kooperativ, nie bestrafend.

Steuerung
─────────
• Linksklick (kurz)     → Gedanke parken (Feature 2)
• Linksklick + Ziehen   → Katze mitnehmen
• Doppelklick           → Streicheln (Herzen!)
• Rechtsklick           → Menü (Fokus starten, Intervall, ADHS-Extras, …)
• ESC                   → Beenden

Wissenschaftliche Grundlage (siehe Kommentare unten):
  1) Body Doubling  2) externer Timer gegen Zeitblindheit
  3) sofortige Mikro-Belohnung  4) Aufgaben-Chunking  5) bewegte Pausen
  + Anti-Freeze-Start (Aktivierung), Gedanken-Parkplatz (Impulskontrolle),
    sanfter Atem-Start (Übergänge)

Nur Python-Standardbibliothek. Sound optional via `afplay` (macOS).
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


# ── Farben ───────────────────────────────────────────────────────────────────
C_BODY   = '#1e1e1e'
C_SHADE  = '#0d0d0d'
C_BELLY  = '#c8a070'
C_PINK   = '#ffaacc'
C_EYE    = '#77ee77'
C_WHITE  = '#ffffff'

# HUD-Farben
C_FOCUS  = '#5fd6a6'   # ruhiges Grün  = Fokus
C_WRAP   = '#ffc368'   # Amber         = Wrap-up (letzte 2 Min)
C_BREAK  = '#8fb8ff'   # sanftes Blau  = Pause
C_TRACK  = '#3a3a3c'   # Ring-Hintergrund
C_MUTE   = '#9a9aa0'   # dezenter Text
C_GOLD   = '#ffcf6b'

CONFETTI_COLORS = ['#ff6b6b', '#ffd166', '#6bcb77', '#4d96ff', '#c77dff', '#ff9e6b']

# ── Texte: bewegte Pausen (Bewegung + Novelty durch Rotation) ────────────────
BREAK_TIPS = [
    'Aufstehen & einmal richtig strecken 🙆',
    'Ein Glas Wasser holen 💧',
    'Ans Fenster, kurz in die Ferne schauen 👀',
    'Ein paar Schritte umhergehen 🚶',
    'Schultern langsam kreisen lassen 🔄',
    'Dreimal tief durchatmen 🌬️',
    'Kurz die Augen schließen & lockern 😌',
    'Katze streicheln & durchatmen 😸',
]

# ── Texte: Dopamin-Menü (sofortige Mini-Belohnung nach dem Block) ────────────
DOPAMINE_IDEAS = [
    'Belohnung: Streck dich genüsslich 🙆',
    'Belohnung: ein Schluck Wasser 💧',
    'Belohnung: 2 Min Lieblingssong 🎵',
    'Belohnung: kurz ans Fenster 🪟',
    'Belohnung: ein Stück Schokolade 🍫',
    'Belohnung: Katze streicheln 😸',
    'Belohnung: 3 tiefe Atemzüge 🌬️',
    'Belohnung: kurz schütteln & lockern 🕺',
]

# ── FEATURE 1: Anti-Freeze — winzige 2-Min-Einstiegsaufgaben (Aktivierung) ───
# Senken die Aktivierungsenergie: der erste Schritt wird lächerlich klein
# gemacht, damit die ADHS-Paralyse am Start überwunden wird. Rotierend (Novelty).
ANTIFREEZE_TASKS = [
    'Nur die Datei öffnen und die Überschrift tippen',
    'Nur 3 Sätze schreiben — egal wie schlecht',
    'Nur das Buch aufschlagen und eine Seite lesen',
    'Nur den ersten Schritt auf einen Zettel schreiben',
    'Nur den Arbeitsplatz kurz frei räumen',
    'Nur die Aufgabe laut vorlesen',
    'Nur 5 Minuten das Allerkleinste anfangen',
    'Nur Stift & Papier hinlegen und loslegen',
]

# ── Gedanken-Parkplatz (Feature 2): eigene JSON-Datei ────────────────────────
THOUGHTS_PATH = os.path.expanduser('~/.desktop_katze_gedanken.json')

# ── Prep-Phase (Feature 3): sanfter Blockstart ───────────────────────────────
PREP_SECONDS = 10          # Länge des Atem-Countdowns vor dem Fokus
MICRO_SECONDS = 120        # Länge eines Anti-Freeze-Blocks (2 Min)

# ── Sound (macOS-Systemklänge, leise & abschaltbar) ──────────────────────────
SOUND_DIR = '/System/Library/Sounds/'
SOUNDS = {
    'wrapup':    ('Tink.aiff',  0.25),   # sanfte Vorwarnung
    'complete':  ('Glass.aiff', 0.40),   # Block geschafft
    'break_end': ('Ping.aiff',  0.30),   # Pause vorbei
}

SETTINGS_PATH = os.path.expanduser('~/.desktop_katze.json')

# Verfügbare Fokus-Intervalle (Min). ADHS: starres 25/5 passt oft nicht.
INTERVALS = [10, 15, 25, 35, 45]
BREAKS    = [3, 5, 10]

# Verfügbare Katzen-Größen (Faktor auf die native 240×300-Zeichenfläche)
SCALES = [0.5, 0.65, 0.8, 1.0]


def _today():
    return datetime.date.today().isoformat()


# ═════════════════════════════════════════════════════════════════════════════
# SKALIERBARER CANVAS  — dünner Proxy, damit der Zeichencode in nativen
# Koordinaten bleiben kann und die Katze trotzdem in jeder Größe rendert.
# Skaliert Koordinaten, Linienbreiten und Schriftgrößen um den Faktor s.
# ═════════════════════════════════════════════════════════════════════════════
class _ScaledCanvas:
    def __init__(self, canvas, s=1.0):
        self._c = canvas
        self._s = s

    def set_scale(self, s):
        self._s = s

    def _sc(self, args):
        s = self._s
        # create_polygon(_round_rect) übergibt eine einzelne Liste von Zahlen
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            return ([a * s if isinstance(a, (int, float)) else a for a in args[0]],)
        return tuple(a * s if isinstance(a, (int, float)) else a for a in args)

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
# FOKUS-TIMER  — macht Zeit konkret (gegen Zeitblindheit), No-Shame-Steuerung
# ═════════════════════════════════════════════════════════════════════════════
class FocusTimer:
    """
    Zustandsautomat für Fokus/Pause.

    modi: 'idle'  = keine Session (Katze streift frei umher)
          'prep'  = 10s Atem-Countdown vor dem Fokus (sanfter Start, Feature 3)
          'focus' = Arbeitsblock läuft   → Body-Double-Haltung
          'break' = Pause läuft           → entspannt/verspielt

    Der Timer läuft in Echtzeit (time.monotonic), unabhängig von der
    Framerate. Alle Übergänge melden sich per Callback an die App.
    """

    def __init__(self, app):
        self.app = app
        self.mode = 'idle'
        self.paused = False
        self.remaining = 0.0     # Sekunden
        self.total = 0.0
        self.wrapup_fired = False
        self.micro = False       # True = Anti-Freeze-2-Min-Block (Feature 1)
        self._last = None

        # per Nutzer einstellbar
        self.focus_len = 25      # Minuten
        self.break_len = 5

        # Tagesstatistik (sofortiger, sichtbarer Fortschritt)
        self.stats_date = _today()
        self.blocks_today = 0
        self.minutes_today = 0.0

    # ── Tageswechsel: Statistik sanft zurücksetzen (kein Streak-Guilt) ──
    def _sync_day(self):
        if self.stats_date != _today():
            self.stats_date = _today()
            self.blocks_today = 0
            self.minutes_today = 0.0

    # ── Steuerung ────────────────────────────────────────────────────────────
    def start_prep(self):
        # FEATURE 3: sanfter Übergang statt Kaltstart — kurzer Atem-Countdown
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
        # FEATURE 1: Anti-Freeze — winziger 2-Min-Block, der den Einstieg erzwingt
        self._sync_day()
        self.mode = 'focus'
        self.micro = True
        self.total = MICRO_SECONDS
        self.remaining = MICRO_SECONDS
        self.paused = False
        self.wrapup_fired = True     # kein Wrap-up bei nur 2 Min
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
        # No-Shame: jederzeit pausierbar, ohne Verlust
        if self.mode in ('focus', 'break'):
            self.paused = not self.paused
            if not self.paused:
                self._last = time.monotonic()

    def skip(self):
        # Block/Pause überspringen — ohne Strafe, ohne erzwungene Belohnung
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

    # ── Abfragen fürs HUD ────────────────────────────────────────────────────
    def progress(self):
        return max(0.0, min(1.0, self.remaining / self.total)) if self.total else 0.0

    def mmss(self):
        s = max(0, int(self.remaining + 0.5))
        return f'{s // 60:02d}:{s % 60:02d}'

    # ── Zeitschritt (jede Frame aufgerufen) ──────────────────────────────────
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

        # Wrap-up-Buffer: sanfte Vorwarnung ~2 Min vor Blockende
        if self.mode == 'focus' and not self.wrapup_fired and self.remaining <= 120:
            self.wrapup_fired = True
            self.app._on_wrapup()

        if self.remaining <= 0:
            if self.mode == 'prep':
                # FEATURE 3: nach dem Durchatmen automatisch in den Fokus
                self.start_focus()
                self.app._on_focus_begin()
            elif self.mode == 'focus' and self.micro:
                # FEATURE 1: Anti-Freeze fertig → sanft "Weitermachen?" fragen
                self.minutes_today += MICRO_SECONDS / 60.0
                self.mode = 'idle'
                self.micro = False
                self.app._on_micro_complete()
            elif self.mode == 'focus':
                # Statistik + sofortige Belohnung, dann direkt in die Pause
                self.blocks_today += 1
                self.minutes_today += self.focus_len
                self.app._on_focus_complete()
                self.start_break()
            else:
                self.app._on_break_complete()
                self.stop()


# ═════════════════════════════════════════════════════════════════════════════
# DESKTOP-KATZE  — UI, Rendering & Katzen-States
# ═════════════════════════════════════════════════════════════════════════════
class DesktopCat:
    # Fenster / Canvas
    W_CANVAS, H_CANVAS = 240, 300
    # Verschiebung der (in Originalkoordinaten gezeichneten) Katze im Canvas
    OX, OY = 25, 62
    # Katzen-Ankerpunkte im Canvas (nach Verschiebung)
    CAT_CX, CAT_CY = 120, 150      # Körpermittelpunkt (für Ring & Follow)
    CAT_HEAD_CY = 110              # Kopfmitte (für Pupillen-Tracking)
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
        # physische Fenstergröße (wird in _apply_scale an die Skalierung angepasst)
        self.win_w, self.win_h = self.W_CANVAS, self.H_CANVAS
        self.wx = sw - self.win_w - 30
        self.wy = sh - self.win_h - 60
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.wx}+{self.wy}")

    def _setup_canvas(self):
        os_name = platform.system()
        if os_name == 'Darwin':
            try:
                self.root.wm_attributes("-transparent", True)
                # WICHTIG: auch der Fenster-Hintergrund muss transparent sein,
                # sonst bleibt ein sichtbarer Kasten um die Katze.
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
        # gesamter Zeichencode läuft über diesen skalierenden Proxy
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

        # Maus
        self.follow_mouse = True
        self.mouse_x = self.wx + self.CAT_CX
        self.mouse_y = self.wy + self.CAT_CY

        # Fokus-/Aufgaben-Zustand
        self.timer = FocusTimer(self)
        self.current_task = ''         # "Woran arbeitest du gerade?"
        self.break_tip = random.choice(BREAK_TIPS)
        self.info_msg = ''             # temporäre Sprechblase (Dopamin/Prompt)
        self.info_until = 0
        self.celebrate_until = 0       # zeigt "✓ geschafft"-Feier
        self.happy_until = 0           # kurzzeitig happy trotz Fokus (Streicheln)

        # Sound / Ambience
        self.sound_on = True
        self.ambient_on = False
        self._amb = None               # laufender afplay-Prozess (Ambience)

        # Größe der Katze (Faktor auf die native Zeichenfläche)
        self.scale = 1.0

        # ── ADHS-Extras (Feature 1–3), alle per Config an/abschaltbar ──
        self.gentle_start = True       # F3: 10s Atem-Countdown vor dem Fokus
        self.park_enabled = True       # F2: Gedanken-Parkplatz (Tap auf Katze)
        self.antifreeze_enabled = True # F1: Anti-Freeze-Startknopf im Dialog

        # Gedanken-Parkplatz (Feature 2)
        self.thoughts = self._load_thoughts()   # Liste geparkter Gedanken (str)
        self._tap_after = None         # geplanter Einzel-Tap (vs. Doppelklick)
        self._press_moved = False      # wurde beim Klick gezogen?
        self._dialog_open = False      # verhindert Dialog-Stapel

        self._load_settings()
        self._apply_scale(save=False)  # geladene Größe auf Fenster/Canvas anwenden

    def _setup_bindings(self):
        c = self.d
        c.bind('<ButtonPress-1>',   self._drag_start)
        c.bind('<B1-Motion>',       self._drag_motion)
        c.bind('<ButtonRelease-1>', self._drag_end)
        c.bind('<Double-Button-1>', self._on_double_click)
        c.bind('<Button-2>',        self._on_right_click)
        c.bind('<Button-3>',        self._on_right_click)
        self.root.bind('<Escape>',  lambda _: self._quit())

    # ── Einstellungen (JSON im Home) ─────────────────────────────────────────
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
        self.scale = min(1.5, max(0.4, float(d.get('scale', 1.0))))
        # Tagesstatistik nur übernehmen, wenn sie von heute ist
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

    # ── Gedanken-Parkplatz: Persistenz (Feature 2) ───────────────────────────
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
        """Sehr leise, optionale Fokus-Ambience (Purr) — nur im Fokus."""
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

    # ── Timer-Callbacks ──────────────────────────────────────────────────────
    def _pick_break_tip(self):
        # rotierender Vorschlag (Novelty): nicht denselben wie zuletzt
        choices = [t for t in BREAK_TIPS if t != self.break_tip] or BREAK_TIPS
        self.break_tip = random.choice(choices)

    def _on_wrapup(self):
        # sanfte Vorwarnung ~2 Min vor Ende (Farbe wird amber via wrapup_fired)
        self._play('wrapup')

    def begin_focus(self, task):
        """Fokus starten — je nach Einstellung mit sanftem Atem-Countdown (F3)."""
        self.current_task = (task or '').strip()
        self.info_msg = ''
        if self.gentle_start:
            self.timer.start_prep()
            self.state, self.state_timer = 'prep', 0
        else:
            self.timer.start_focus()
            self._on_focus_begin()

    def _on_focus_begin(self):
        # gemeinsamer Einstieg in einen echten Fokusblock (direkt oder nach prep)
        self.state, self.state_timer = 'focus', 0

    def _on_focus_complete(self):
        # (3) SOFORTIGE MIKRO-BELOHNUNG: stolz/glücklich + Herzen + Konfetti
        self.state = 'happy'
        self.state_timer = 0
        self.happy_until = self.frame + 120
        self.celebrate_until = self.frame + 130
        self.info_msg = random.choice(DOPAMINE_IDEAS)   # Dopamin-Menü
        self.info_until = self.frame + 200
        self._spawn_confetti(30)
        self._add_hearts(9)
        self._play('complete')
        self._save_settings()
        # FEATURE 2: am Blockende die geparkten Gedanken sanft zeigen
        if self.thoughts:
            self.root.after(1400, self._show_thoughts_review)

    def _on_micro_complete(self):
        # FEATURE 1: Anti-Freeze vorbei — kleine Anerkennung + "Weitermachen?"
        self.state, self.state_timer = 'happy', 0
        self._add_hearts(5)
        self._play('complete')
        self._save_settings()
        self.root.after(600, self._show_continue_prompt)

    def _on_break_complete(self, skipped=False):
        self._play('break_end')
        # kein Zwang: freundlicher Hinweis, Start wenn bereit (No-Shame)
        self.info_msg = 'Bereit für den nächsten Block? 🐾'
        self.info_until = self.frame + 260

    # ── Partikel ─────────────────────────────────────────────────────────────
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

    # ── Mausposition ─────────────────────────────────────────────────────────
    def _update_mouse(self):
        try:
            self.mouse_x = self.root.winfo_pointerx()
            self.mouse_y = self.root.winfo_pointery()
        except Exception:
            pass

    def _cat_center(self):
        """Körpermittelpunkt in Bildschirm-Koordinaten (für Follow), skaliert."""
        return self.wx + self.CAT_CX * self.scale, self.wy + self.CAT_CY * self.scale

    def _mouse_offset(self):
        """Pupillenversatz Richtung Maus (±5 px), Kopfmitte als Bezug."""
        cx = self.wx + self.CAT_CX * self.scale
        cy = self.wy + self.CAT_HEAD_CY * self.scale
        dx = self.mouse_x - cx
        dy = self.mouse_y - cy
        dist = math.hypot(dx, dy) or 1
        k = min(5, dist * 0.03) / dist
        # in nativen Einheiten zurückgeben — der Proxy multipliziert mit scale
        return dx * k / self.scale, dy * k / self.scale

    # ═════════════════════════════════════════════════════════════════════════
    # ZEICHNEN
    # ═════════════════════════════════════════════════════════════════════════
    def _draw(self):
        self.canvas.delete('all')

        # (1) BODY DOUBLING: im Fokus atmet die Katze ruhig (kein Herumtollen)
        oy = self.OY
        if self.state == 'focus':
            oy += math.sin(self.frame * 0.06) * 1.6
        elif self.state == 'prep':
            # FEATURE 3: tieferer, ruhiger Atem als sichtbare Anleitung
            oy += math.sin(self.frame * 0.045) * 4.0

        # Katze in Originalkoordinaten zeichnen, dann als Ganzes verschieben
        # (Proxy skaliert Koordinaten/Breiten/Fonts; move skaliert den Versatz)
        self._draw_cat()
        self.d.move('all', self.OX, oy)

        # HUD (Ring/Timer/Aufgabe) und Konfetti in finalen Koordinaten
        self._draw_hud()
        self._draw_confetti()

    def _draw_cat(self):
        c = self.d
        f = self.frame
        st = self.state

        # ── Schwanz ──
        if st == 'sleep':
            swing = 0
        elif st == 'happy':
            swing = math.sin(f * 0.55) * 24
        elif st in ('focus', 'prep'):
            swing = math.sin(f * 0.05) * 6      # ruhig, konzentriert
        elif st in ('walk_right', 'walk_left', 'follow'):
            swing = math.sin(f * 0.30) * 14
        else:
            swing = math.sin(f * 0.07) * 10

        c.create_line(
            94, 118, 94 + swing, 152, 92 + swing * 1.5, 168,
            fill=C_BODY, width=9, smooth=True, capstyle='round'
        )

        # ── Körper ──
        c.create_oval(50, 80, 140, 135, fill=C_BODY, outline=C_SHADE, width=2)
        c.create_oval(66, 96, 124, 132, fill=C_BELLY, outline='')

        # ── Kopf ──
        c.create_oval(44, 18, 146, 96, fill=C_BODY, outline=C_SHADE, width=2)

        # ── Ohren ──
        c.create_polygon(54, 46, 45,  8, 74, 32, fill=C_BODY,  outline=C_SHADE, width=1)
        c.create_polygon(136, 46, 145, 8, 116, 32, fill=C_BODY, outline=C_SHADE, width=1)
        c.create_polygon(57, 43, 50, 15, 71, 31, fill=C_PINK,  outline='')
        c.create_polygon(133, 43, 140, 15, 119, 31, fill=C_PINK, outline='')

        # ── Augen ──
        is_blink = (f % 90) < 3
        px, py = self._mouse_offset()
        if st in ('focus', 'prep'):
            px = py = 0.0            # konzentrierter Blick nach vorn

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

        # ── Nase ──
        c.create_polygon(91, 70, 99, 70, 95, 75, fill=C_PINK, outline='')

        # ── Mund (im Fokus dezent zufrieden, je nach Tagesfortschritt) ──
        if st == 'happy':
            c.create_arc(82, 72, 108, 88, start=200, extent=-160,
                         style='arc', outline=C_WHITE, width=2)
        elif st == 'focus' and self.timer.blocks_today > 0:
            # (SOLLTE) über den Tag sichtbar zufriedener: leichtes Lächeln
            c.create_arc(84, 73, 106, 85, start=200, extent=-160,
                         style='arc', outline=C_WHITE, width=1)
        else:
            c.create_line(91, 75, 87, 80, fill=C_WHITE, width=1, capstyle='round')
            c.create_line(99, 75, 103, 80, fill=C_WHITE, width=1, capstyle='round')

        # ── Schnurrbarthaare ──
        c.create_line(38, 68, 80, 72, fill=C_WHITE, width=1)
        c.create_line(38, 76, 80, 76, fill=C_WHITE, width=1)
        c.create_line(110, 72, 152, 68, fill=C_WHITE, width=1)
        c.create_line(110, 76, 152, 76, fill=C_WHITE, width=1)

        # ── Pfoten ──
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

        # ── Herzen (bewegen mit der Katze mit) ──
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

    # ── HUD: Ring (Timer), Aufgabe, Belohnung, Tageszähler ───────────────────
    def _draw_hud(self):
        c = self.d
        t = self.timer
        cx, cy, r = self.CAT_CX, self.CAT_CY, self.RING_R
        celebrating = self.frame < self.celebrate_until

        # FEATURE 3: sanfter Start — Atem-Countdown statt Timer-Ring
        if t.mode == 'prep':
            self._draw_prep_hud()
            return

        # (2) EXTERNER TIMER als Ring um die Katze — Zeit wird sichtbar/greifbar
        if t.mode in ('focus', 'break'):
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C_TRACK, width=6)
            if t.mode == 'focus':
                col = C_WRAP if t.wrapup_fired else C_FOCUS
            else:
                col = C_BREAK
            extent = -359.999 * t.progress()   # im Uhrzeigersinn ab oben
            c.create_arc(cx - r, cy - r, cx + r, cy + r,
                         start=90, extent=extent, style='arc', outline=col, width=6)

            # Countdown-Text (Ergänzung zum Ring)
            c.create_text(cx, 22, text=t.mmss(),
                          font=('Helvetica', 21, 'bold'), fill=C_WHITE)

            # Modus-Label
            if celebrating:
                label, lcol = '✓ Block geschafft!', C_GOLD
            elif t.paused:
                label, lcol = 'pausiert', C_MUTE
            elif t.mode == 'focus' and t.micro:
                label, lcol = 'Anti-Freeze · nur anfangen 🧊', C_FOCUS
            elif t.mode == 'focus' and t.wrapup_fired:
                label, lcol = 'gleich fertig · sanft ausklingen', C_WRAP
            elif t.mode == 'focus':
                label, lcol = 'Fokus', C_FOCUS
            else:
                label, lcol = 'Pause', C_BREAK
            c.create_text(cx, 44, text=label, font=('Helvetica', 11), fill=lcol)

        # ── untere Sprechblase: Aufgabe / Pausen-Tipp / Belohnung / Prompt ──
        pill = None
        if self.info_msg and self.frame < self.info_until:
            pill = (self.info_msg, C_GOLD)                       # Dopamin/Prompt
        elif t.mode == 'focus' and self.current_task:
            # (4) EINE-AUFGABE-FOKUS: aktuelle Aufgabe bleibt sichtbar
            pill = ('📌 ' + self._short(self.current_task, 30), C_FOCUS)
        elif t.mode == 'break':
            # (5) konkreter, bewegter Pausen-Vorschlag
            pill = ('🐾 ' + self._short(self.break_tip, 34), C_BREAK)
        if pill:
            self._draw_pill(cx, 270, pill[0], accent=pill[1])

        # ── Tageszähler (sofortiger, sichtbarer Fortschritt) ──
        n = t.blocks_today
        if n > 0:
            fish = '🐟' * min(n, 5) + ('…' if n > 5 else '')
            c.create_text(cx, 293,
                          text=f'{fish}  {n} Blöcke · {int(t.minutes_today)} Min heute',
                          font=('Helvetica', 10), fill=C_MUTE)
        elif t.mode == 'idle':
            c.create_text(cx, 293, text='Rechtsklick → Fokus starten',
                          font=('Helvetica', 10), fill=C_MUTE)

    def _draw_prep_hud(self):
        """FEATURE 3: atmender Ring + Countdown als sanfter Einstieg."""
        c = self.d
        t = self.timer
        cx, cy = self.CAT_CX, self.CAT_CY
        phase = math.sin(self.frame * 0.045)              # -1..1 (Atemzyklus)
        rr = 60 + (phase + 1) * 24                        # 60..108 px, wächst beim Einatmen
        c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=C_BREAK, width=4)
        secs = max(1, int(math.ceil(t.remaining)))
        c.create_text(cx, 22, text=str(secs), font=('Helvetica', 22, 'bold'), fill=C_WHITE)
        breathe = 'Einatmen …' if math.cos(self.frame * 0.045) > 0 else 'Ausatmen …'
        c.create_text(cx, 44, text=breathe, font=('Helvetica', 12), fill=C_BREAK)
        self._draw_pill(cx, 270, 'Kurz durchatmen … gleich geht’s los', accent=C_BREAK)

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

    # ── Zeichen-Helfer ───────────────────────────────────────────────────────
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
    # ZUSTANDSAUTOMAT
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
            # FEATURE 3: ruhig durchatmen, keine Ablenkung, kein Wandern
            self.state = 'prep'
            return

        if mode == 'focus':
            # BODY DOUBLE: ruhig sitzen, nicht wandern, nicht schlafen, nicht
            # der Maus hinterherlaufen (sonst wird die Katze zur Ablenkung).
            self.state = 'happy' if self.frame < self.happy_until else 'focus'
            return

        # mode == 'break' oder 'idle' → verspieltes/freies Verhalten
        if self.state in ('focus', 'prep'):
            self.state = 'idle'
            self.state_timer = 0
        self._idle_behavior()

    def _idle_behavior(self):
        """Freies Streifen, Maus-Follow, gelegentliches Nickerchen (Basis)."""
        sw = self.screen_w

        # ── Maus-Follow ──
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
            speed = min(4, max(1, abs(dist_x) // 40))
            self.wx += speed * self.walk_dir
            self.wx = max(0, min(sw - self.win_w, self.wx))
            self.root.geometry(f"{self.win_w}x{self.win_h}+{self.wx}+{self.wy}")
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
            self.root.geometry(f"{self.win_w}x{self.win_h}+{self.wx}+{self.wy}")
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

    # ── Loop ─────────────────────────────────────────────────────────────────
    def _loop(self):
        self.frame += 1
        self._update()
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
        # ein evtl. geplanter Einzel-Tap wird durch neuen Klick hinfällig
        self._cancel_pending_tap()

    def _drag_motion(self, event):
        # ab ~4px Bewegung gilt es als echtes Ziehen (nicht als Tap)
        if abs(event.x - self._press_x) + abs(event.y - self._press_y) > 4:
            self._press_moved = True
        self.wx += event.x - self._drag_x
        self.wy += event.y - self._drag_y
        self.wx = max(0, min(self.screen_w - self.win_w, self.wx))
        self.wy = max(0, min(self.screen_h - self.win_h, self.wy))
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.wx}+{self.wy}")

    def _drag_end(self, event):
        self.is_dragging = False
        # kurz happy, aber im Fokus danach wieder ruhig (via happy_until nicht gesetzt)
        if self.timer.mode != 'focus':
            self.state = 'happy'
            self.state_timer = 0
        # FEATURE 2: Tap (Klick ohne Ziehen) öffnet den Gedanken-Parkplatz.
        # Kurz verzögert, damit ein Doppelklick (Streicheln) ihn abfangen kann.
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
        # Doppelklick = Streicheln → geplanten Einzel-Tap verwerfen
        self._cancel_pending_tap()
        self._pet()

    def _pet(self):
        self._add_hearts(7)
        self.state, self.state_timer = 'happy', 0
        if self.timer.mode == 'focus':
            self.happy_until = self.frame + 55   # kurz freuen, dann weiter fokussieren

    # ── Rechtsklick-Menü ─────────────────────────────────────────────────────
    def _on_right_click(self, event):
        m = tk.Menu(self.root, tearoff=0)
        mode = self.timer.mode

        # Fokus-Steuerung
        if mode == 'idle':
            m.add_command(label='▶️  Fokus starten', command=self._open_task_dialog)
        else:
            lbl = '⏸️  Pause' if not self.timer.paused else '▶️  Fortsetzen'
            m.add_command(label=lbl, command=self.timer.toggle_pause)
            skip = '⏭️  Block überspringen' if mode == 'focus' else '⏭️  Pause überspringen'
            m.add_command(label=skip, command=self.timer.skip)
            m.add_command(label='⏹️  Session beenden', command=self.timer.stop)

        # FEATURE 2: Gedanke parken (auch per Klick auf die Katze)
        if self.park_enabled:
            m.add_command(label='💭  Gedanke parken', command=self._open_park)
            if self.thoughts:
                m.add_command(label=f'📋  Gedanken zeigen ({len(self.thoughts)})',
                              command=self._show_thoughts_review)

        # Intervall wählen
        iv = tk.Menu(m, tearoff=0)
        for v in INTERVALS:
            mark = '  ✓' if v == self.timer.focus_len else ''
            iv.add_command(label=f'{v} Min{mark}',
                           command=lambda x=v: self._set_focus_len(x))
        m.add_cascade(label='⏱️  Fokus-Länge', menu=iv)

        bp = tk.Menu(m, tearoff=0)
        for v in BREAKS:
            mark = '  ✓' if v == self.timer.break_len else ''
            bp.add_command(label=f'{v} Min{mark}',
                           command=lambda x=v: self._set_break_len(x))
        m.add_cascade(label='☕  Pausen-Länge', menu=bp)

        # Größe der Katze
        sz = tk.Menu(m, tearoff=0)
        for v in SCALES:
            mark = '  ✓' if abs(v - self.scale) < 0.01 else ''
            label = f'{int(round(v * 100))}%'
            if v == 1.0:
                label += ' (Original)'
            sz.add_command(label=label + mark, command=lambda x=v: self._set_scale(x))
        m.add_cascade(label='🔍  Größe', menu=sz)

        m.add_separator()

        # Toggles
        m.add_command(label='🔊  Sound  ' + ('✓' if self.sound_on else '–'),
                      command=self._toggle_sound)
        m.add_command(label='🎵  Ambience (Fokus)  ' + ('✓' if self.ambient_on else '–'),
                      command=self._toggle_ambient)
        m.add_command(label='👁  Maus verfolgen  ' + ('✓' if self.follow_mouse else '–'),
                      command=self._toggle_follow)
        m.add_command(label='😸  Streicheln', command=self._pet)

        # ADHS-Extras (Feature 1–3) an/abschaltbar
        ex = tk.Menu(m, tearoff=0)
        ex.add_command(label='🌬️  Sanfter Start (Atem-Countdown)  ' + ('✓' if self.gentle_start else '–'),
                       command=self._toggle_gentle)
        ex.add_command(label='💭  Gedanken-Parkplatz  ' + ('✓' if self.park_enabled else '–'),
                       command=self._toggle_park)
        ex.add_command(label='🧊  Anti-Freeze-Startknopf  ' + ('✓' if self.antifreeze_enabled else '–'),
                       command=self._toggle_antifreeze)
        m.add_cascade(label='🧠  ADHS-Extras', menu=ex)

        m.add_separator()

        # Tages-Info (nur Anzeige)
        t = self.timer
        m.add_command(
            label=f'📊  Heute: {t.blocks_today} Blöcke · {int(t.minutes_today)} Min',
            state='disabled')
        m.add_command(label='❌  Beenden', command=self._quit)

        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    # ── Dialog-Helfer (einheitlicher, dunkler Stil, Stapel-Schutz) ───────────
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

        d.protocol('WM_DELETE_WINDOW', close)
        d.bind('<Escape>', lambda _: close())
        return d, close

    def _dialog_button(self, parent, text, command, primary=False):
        f = ('Helvetica', 12, 'bold') if primary else ('Helvetica', 12)
        return tk.Button(parent, text=text, command=command, font=f, relief='flat',
                         highlightbackground='#1e1e1e', padx=14, pady=4)

    # ── Aufgaben-Dialog ("Woran arbeitest du gerade?") ───────────────────────
    def _open_task_dialog(self):
        if self._dialog_open:
            return
        d, close = self._new_dialog('Fokusblock starten')

        tk.Label(d, text='Woran arbeitest du gerade?', bg='#1e1e1e', fg='#eaeaea',
                 font=('Helvetica', 14, 'bold')).pack(padx=20, pady=(18, 2))
        tk.Label(d, text='Eine konkrete Sache — z.B. „5 Aufgaben rechnen“',
                 bg='#1e1e1e', fg=C_MUTE, font=('Helvetica', 11)).pack(padx=20)

        var = tk.StringVar(value=self.current_task)
        e = tk.Entry(d, textvariable=var, width=36, font=('Helvetica', 12),
                     bg='#2b2b2e', fg='#ffffff', insertbackground='#ffffff', relief='flat')
        e.pack(padx=20, pady=12, ipady=4)
        e.focus_force()
        e.icursor('end')

        hint = f'Fokus {self.timer.focus_len} Min · Pause {self.timer.break_len} Min'
        if self.gentle_start:
            hint += ' · sanfter Start'
        tk.Label(d, text=hint, bg='#1e1e1e', fg='#7a7a80',
                 font=('Helvetica', 10)).pack(pady=(0, 6))

        btns = tk.Frame(d, bg='#1e1e1e')
        btns.pack(pady=(2, 8))

        def start():
            task = var.get().strip()
            close()
            self.begin_focus(task)

        self._dialog_button(btns, 'Los geht’s 🐾', start, primary=True).pack(side='left', padx=6)
        self._dialog_button(btns, 'Abbrechen', close).pack(side='left', padx=6)

        # FEATURE 1: Anti-Freeze — für die Momente, in denen der Start blockiert
        if self.antifreeze_enabled:
            def antifreeze():
                close()
                self._start_antifreeze()
            tk.Button(d, text='🧊  Ich weiß nicht wie ich anfangen soll',
                      command=antifreeze, font=('Helvetica', 11), relief='flat',
                      highlightbackground='#1e1e1e', fg='#cfe8ff',
                      padx=10, pady=4).pack(pady=(0, 16))
        else:
            tk.Frame(d, bg='#1e1e1e', height=8).pack()

        d.bind('<Return>', lambda _: start())

    # ── FEATURE 1: Anti-Freeze starten + "Weitermachen?"-Prompt ──────────────
    def _start_antifreeze(self):
        self.current_task = random.choice(ANTIFREEZE_TASKS)
        self.info_msg = 'Nur das hier — 2 Minuten reichen 🧊'
        self.info_until = self.frame + 160
        self.timer.start_micro()
        self.state, self.state_timer = 'focus', 0

    def _show_continue_prompt(self):
        if self._dialog_open:
            return
        d, close = self._new_dialog('Weitermachen?')
        tk.Label(d, text='Zwei Minuten geschafft 🎉', bg='#1e1e1e', fg='#eaeaea',
                 font=('Helvetica', 14, 'bold')).pack(padx=24, pady=(18, 2))
        tk.Label(d, text='Der schwerste Teil — der Anfang — ist erledigt.',
                 bg='#1e1e1e', fg=C_MUTE, font=('Helvetica', 11)).pack(padx=24, pady=(0, 14))

        btns = tk.Frame(d, bg='#1e1e1e')
        btns.pack(pady=(0, 18), padx=24)

        def keep_going():
            close()
            # warm gelaufen → direkt in den Fokus, ohne erneuten Atem-Countdown
            self.info_msg = ''
            self.timer.start_focus()
            self.state, self.state_timer = 'focus', 0

        def take_break():
            close()
            self.timer.start_break()

        def done():
            close()
            self.timer.stop()

        self._dialog_button(btns, 'Ja, weiter 🐾', keep_going, primary=True).pack(side='left', padx=5)
        self._dialog_button(btns, 'Kurze Pause', take_break).pack(side='left', padx=5)
        self._dialog_button(btns, 'Reicht für jetzt', done).pack(side='left', padx=5)

    # ── FEATURE 2: Gedanken-Parkplatz — schnell parken ───────────────────────
    def _open_park(self):
        if self._dialog_open or not self.park_enabled:
            return
        d, close = self._new_dialog('Gedanke parken')
        tk.Label(d, text='💭 Kurz parken, dann weiter im Fokus', bg='#1e1e1e',
                 fg='#eaeaea', font=('Helvetica', 13, 'bold')).pack(padx=20, pady=(16, 2))
        tk.Label(d, text='Der Gedanke wird gemerkt, nicht verfolgt.',
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
                self.info_msg = '💭 geparkt — weiter geht’s'
                self.info_until = self.frame + 40
            close()

        self._dialog_button(btns, 'Parken 💭', park, primary=True).pack(side='left', padx=6)
        self._dialog_button(btns, 'Abbrechen', close).pack(side='left', padx=6)
        d.bind('<Return>', lambda _: park())

    # ── FEATURE 2: Gedanken am Blockende zeigen (abarbeiten/verwerfen) ────────
    def _show_thoughts_review(self):
        if self._dialog_open or not self.thoughts:
            return
        d, close = self._new_dialog('Deine geparkten Gedanken')
        tk.Label(d, text='Das wolltest du dir merken:', bg='#1e1e1e', fg='#eaeaea',
                 font=('Helvetica', 14, 'bold')).pack(padx=20, pady=(16, 10))

        rows = tk.Frame(d, bg='#1e1e1e')
        rows.pack(padx=18, fill='x')

        def rebuild():
            for w in rows.winfo_children():
                w.destroy()
            if not self.thoughts:
                tk.Label(rows, text='Alles abgearbeitet 🎉', bg='#1e1e1e',
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

                tk.Button(row, text='✓ erledigt', command=discard,
                          font=('Helvetica', 10), relief='flat',
                          highlightbackground='#1e1e1e', fg='#9fe0b4').pack(side='right')

        rebuild()

        foot = tk.Frame(d, bg='#1e1e1e')
        foot.pack(pady=(12, 16))
        self._dialog_button(foot, 'Rest behalten & schließen', close).pack(side='left', padx=6)

    # ── Einstellungs-Toggles ─────────────────────────────────────────────────
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

    # ── Größe der Katze ──────────────────────────────────────────────────────
    def _apply_scale(self, s=None, save=True):
        if s is not None:
            self.scale = s
        self.win_w = max(1, int(round(self.W_CANVAS * self.scale)))
        self.win_h = max(1, int(round(self.H_CANVAS * self.scale)))
        self.d.set_scale(self.scale)
        self.canvas.config(width=self.win_w, height=self.win_h)
        # Position im Bildschirm halten
        self.wx = max(0, min(self.screen_w - self.win_w, self.wx))
        self.wy = max(0, min(self.screen_h - self.win_h, self.wy))
        self.root.geometry(f"{self.win_w}x{self.win_h}+{self.wx}+{self.wy}")
        if save:
            self._save_settings()

    def _set_scale(self, s):
        self._apply_scale(s)

    def _quit(self):
        self._save_settings()
        if self._amb and self._amb.poll() is None:
            try:
                self._amb.terminate()
            except Exception:
                pass
        self.root.destroy()


if __name__ == '__main__':
    DesktopCat()
