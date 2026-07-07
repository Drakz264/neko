# 🐱 Neko — a focus cat for ADHD brains

![demo](demo.gif)

**Neko is a small, calm cat that lives on your desktop and quietly works *alongside* you.**
It's built on **body doubling** — the ADHD-friendly effect where the silent presence of
another "being" gives your brain a steady *"it's work time now"* signal, making it easier
to start a task and to find your way back when you drift.

No coaching, no pressure, no streaks to lose. Just a companion at your desk.

> Made for my own ADHD brain, shared in case it helps yours. Everything is gentle,
> everything is skippable, and there is never any shame for a missed block.

---

## Why a cat?

People with ADHD often struggle less with *doing* the work and more with **starting**,
**resisting distractions**, and **switching tasks**. Neko targets exactly those weak points
— with a soothing pet instead of a nagging timer, because pressure and leaderboards burn
you out, while a calm presence keeps you coming back.

---

## Features

- **🐾 Body-doubling presence** — during a focus block the cat sits upright in a calm
  "working posture" and breathes quietly. It's *with* you, never demanding.
- **⏱️ Flexible focus timer** — a ring fills *around the cat* so time becomes visible
  (fights ADHD "time blindness"). Intervals 10/15/25/35/45 min — because rigid 25/5
  often doesn't fit ADHD.
- **📌 One-task focus** — a quick *"What are you working on?"* prompt; the single task
  stays visible so you remember what you're actually doing.
- **🎉 Instant micro-rewards** — every finished block triggers confetti, hearts, a proud
  cat and a tiny reward idea. Dopamine *now*, not "on the weekend".
- **🌬️ Gentle breathing start** — a 10-second breathe-in/breathe-out countdown eases you
  into a block instead of a cold start.
- **🧊 Anti-freeze starter** — stuck at the start? One button gives you a ridiculously
  small 2-minute task ("just open the file and type the title") to break the paralysis.
- **💭 Thought parking lot** — a random thought pops up ("order that Vespa part!")?
  Click the cat, type it, it's parked — *not* chased. Your focus stays intact; the cat
  shows you the list at the end of the block.
- **🚶 Movement breaks** — short breaks with rotating suggestions (stand up, water,
  look out the window) so a 5-minute break doesn't become 40.
- **🪟 Lives on your desktop** — draggable, transparent, always on top. Drag it anywhere.

Everything above can be toggled in the right-click menu, and every setting is optional —
Neko works great with zero configuration.

### Controls

| Action | What it does |
|---|---|
| **Left-click (tap)** | Park a thought 💭 |
| **Left-click + drag** | Move the cat |
| **Double-click** | Pet the cat (hearts) |
| **Right-click** | Menu: start focus, intervals, ADHD extras, sound, quit |
| **Esc** | Quit |

---

## Install (no coding needed)

1. Go to the [**Releases**](../../releases) page and download `Neko.app.zip`.
2. Double-click the `.zip` to unzip it. Move **Neko.app** to your **Applications** folder (optional).
3. **First launch** — because the app isn't signed with a paid Apple certificate, macOS
   will refuse to open it on a normal double-click. This is expected. Do this instead:

   > **Right-click** (or Control-click) **Neko.app → Open → Open** in the dialog.

   You only need to do this **once**. After that it opens normally.

<details>
<summary>If macOS still says "Neko can't be opened" or "is damaged"</summary>

Newer macOS versions sometimes hide the right-click option. Two fixes:

- **System Settings → Privacy & Security**, scroll down, and click **"Open Anyway"**
  next to the Neko message, then launch again.
- Or, in Terminal, remove the quarantine flag once:
  ```bash
  xattr -dr com.apple.quarantine /Applications/Neko.app
  ```
  (It says "damaged" only because it's unsigned + quarantined, not because anything is wrong.)
</details>

---

## Is it safe? What it does to your Mac

Neko asks to stay **always on top**, so it's fair to want to know what it does. Short answer:
**almost nothing, and all of it is local.**

- 🪟 It draws **one transparent window** (the cat). That's it.
- 💾 It saves two small text files in your home folder:
  - `~/.desktop_katze.json` — your settings + today's block count
  - `~/.desktop_katze_gedanken.json` — your parked thoughts
- 🌐 It makes **no network connections at all** — nothing is uploaded, there are no
  accounts, no analytics, **no tracking** of any kind.
- 🔊 Optional sounds just play macOS's built-in system sounds via `afplay`.
- 🔓 It's **100% open source** — the entire app is one readable Python file in
  [`src/desktop_katze.py`](src/desktop_katze.py). Read every line yourself.

---

## Run from source (for developers)

```bash
git clone https://github.com/<your-username>/neko.git
cd neko
python3 src/desktop_katze.py
```

Pure Python standard library — no `pip install` needed.

> **⚠️ Transparency needs Tcl/Tk 8.6.** On macOS, the transparent background only works
> with **Tk 8.6**. Many current Python installs (python.org 3.14+, recent builds) ship
> **Tk 9.0**, which renders the window as a solid **black box**. Check yours with:
> ```bash
> python3 -c "import tkinter; print(tkinter.TkVersion)"
> ```
> If it prints `9.0`, get a Tk-8.6 Python without touching your system (via [uv](https://docs.astral.sh/uv/)):
> ```bash
> curl -LsSf https://astral.sh/uv/install.sh | sh
> uv python install 3.9
> uv run --python 3.9 src/desktop_katze.py
> ```
> The prebuilt **Neko.app from Releases bundles Tk 8.6**, so downloaders never have to
> worry about this.

### Building the app yourself

```bash
./build.sh
```

This picks a Tk-8.6 Python automatically, installs PyInstaller in an isolated
environment, and produces `dist/Neko.app`. To share it:

```bash
cd dist && zip -r -y Neko.app.zip Neko.app
```

---

## Recording the demo GIF

1. Press **⌘⇧5**, choose **"Record Selected Portion"**, draw a box around the cat, hit
   **Record**. Do a short run: start a focus block, let it celebrate, park a thought.
   Stop from the menu bar. A `.mov` lands on your Desktop.
2. Convert it to a small, crisp GIF with **ffmpeg** (`brew install ffmpeg`):
   ```bash
   ffmpeg -i ~/Desktop/recording.mov \
     -vf "fps=12,scale=480:-1:flags=lanczos,palettegen" palette.png
   ffmpeg -i ~/Desktop/recording.mov -i palette.png \
     -filter_complex "fps=12,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse" demo.gif
   ```
   (The two-step palette method keeps the file small and the colors clean. For even nicer
   output, [`gifski`](https://gif.ski) is a great alternative.)
3. Drop `demo.gif` in the repo root — the image at the top of this README will pick it up.

---

## License

[MIT](LICENSE) © 2026 ShaquilleOMeal — do whatever you like, no warranty.
