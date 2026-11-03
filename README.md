# Desktop Pet for Windows

A transparent, always-on-top desktop companion that lives on your screen and in your system tray.
Drag it around, throw a ball, let it follow your cursor, or just watch it wander on its own.

> **Pet sprites and animations are taken from [vscode-pets](https://github.com/tonybaloney/vscode-pets)** by Anthony Shaw — a beloved VS Code extension.  
> This project is a standalone Windows reimagining: the pets are extracted from the extension, wrapped in a native PyQt6 transparent window, and given new behaviors (physics ball, mouse-following AI, multi-pet support, a cyberpunk settings UI, and Windows Registry persistence).

---

## Features

- **21 pet types** — fox, panda, cockatiel, dog, turtle, Totoro, chicken, Clippy, crab, Deno, horse, Mod, monkey, Morph, rat, Rocky, rubber duck, skeleton, snail, snake, Zappy
- **Transparent frameless window** — always on top, no taskbar entry
- **System tray** — close button minimises to tray; double-click to restore
- **Ball physics** — throw a ball with click-drag; the pet chases and carries it
- **Mouse following** — toggle the pet to shadow your cursor
- **Multiple pets** — spawn as many companions as you want from the settings window
- **Cyberpunk settings UI** — animated holographic card picker, live language switch
- **Bilingual** — English and Russian, switched instantly; language and pet choice persisted in the Windows Registry (no loose files)
- **Zero install** — single `.exe`, no Python required

---

## Quick Start

### Pre-built exe
```
dist/DesktopPet.exe  — double-click, no Python needed
```
The existing EXE predates the Qt6 security changes. It has been preserved for rollback;
use the checked release-build workflow below to produce a new candidate.
Pet state is stored in `pet_data.db` next to the exe.  
Language and pet choice are stored in `HKCU\Software\DesktopPet` (Windows Registry).

### From source
Use Windows CPython 3.13 AMD64 in a local virtual environment for the locked release target:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip --isolated install --index-url https://pypi.org/simple --require-hashes --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The source API supports Python 3.10+, but checked release wheel hashes target 3.13 x64.
To run from an already prepared environment:

```bash
python main.py
```

---

## Controls

| Action | Effect |
|---|---|
| Left-click drag | Move the pet |
| Right-click | Context menu |
| Double-click tray icon | Show / hide |

### Context menu (right-click on pet)

| Item | Description |
|---|---|
| 💤 Sleep / ☀️ Wake Up | Toggle resting state |
| 🎾 Throw Ball | Enter throw mode — drag & release to throw |
| 🔍 Follow Mouse / Stop Following | Toggle cursor tracking |
| ⚙️ Settings | Open the settings window |
| 👁 Minimize to Tray | Hide window, keep tray icon |
| ❌ Quit | Exit the app |

### Tray icon (right-click)

Choose **Menu style → Panel / Ring** in the tray menu or the pet's **More…** menu.
The choice is saved for all pets. Both styles offer the same actions; a small screen
uses a scrollable panel when the ring cannot fit. Pet, Ball and Sleep are the main
actions; Settings has a direct gear button, with secondary commands under More.
The tray's **Pets → name** menu also reaches every pet without clicking its sprite.
Nearby mouse movement can interest **one randomly chosen pet** for 2–4 seconds,
after a short delay, followed by a shared 4–6 second break. It may approach or run
away according to its character. Hovering the pet stops free walking and gives
1.8 seconds of click grace after the pointer leaves; pressing freezes movement
immediately. A still cursor does not start a reaction. **Follow continuously** is
an explicit command; sleep, petting, dragging, menus and ball play take priority.
Keyboard activity does not animate or move the pet.

| Item | Description |
|---|---|
| Show Pet / Hide Pet | Toggle primary pet visibility |
| Hide All / Show All | Toggle all pets at once |
| ⚙️ Settings | Open settings |
| Menu style → Panel / Ring | Set the interaction menu for all pets |
| Pets → name | Open actions for a pet without chasing its sprite |
| ➕ Add Pet | Spawn a satellite pet (submenu) |
| ❌ Quit | Exit |

### Throwing the ball

1. Right-click → **🎾 Throw Ball**
2. Hold left-click anywhere and drag to aim
3. Release — the ball flies with gravity and bounces
4. The pet chases the ball, picks it up, and carries it briefly

---

## Pet Types

All pets use the **SimplePet** model: they wander randomly, chase balls, and react to the mouse. No hunger/health stats — just pure animation and physics.

| Type | Default name (EN) | Default name (RU) |
|---|---|---|
| `fox` | Rusty | Рыжик |
| `panda` | Panda | Панда |
| `cockatiel` | Cockatiel | Корелла |
| `dog` | Buddy | Бобик |
| `turtle` | Shelly | Черепаха |
| `totoro` | Totoro | Тоторо |
| `chicken` | Clucky | Курица |
| `clippy` | Clippy | Скрепка |
| `crab` | Crab | Краб |
| `deno` | Deno | Дено |
| `horse` | Horsey | Лошадь |
| `mod` | Mod | Мод |
| `monkey` | Monki | Мартышка |
| `morph` | Morph | Морф |
| `rat` | Ratty | Крыска |
| `rocky` | Rocky | Роки |
| `rubber_duck` | Ducky | Уточка |
| `skeleton` | Bones | Скелет |
| `snail` | Snaily | Улитка |
| `snake` | Snek | Змейка |
| `zappy` | Zappy | Заппи |

### Autonomous behaviour

- Every 3 seconds the pet randomly walks to a point on screen or lies down
- When the cursor is within 150 px the pet may approach
- At random intervals (every 15–60 min) the pet spontaneously runs toward the cursor
- In **Follow Mouse** mode the pet continuously tracks the cursor; it idles or wanders briefly when the cursor stops

---

## Settings Window

Open via tray menu or right-click context menu.

| Section | What you can do |
|---|---|
| **Pet** | Pick any of the 21 pet types via animated card grid |
| **Name** | Rename the pet (applies on click of **Apply**) |
| **Language** | Switch between English and Russian instantly |
| **On Screen** | See and remove active satellite pets |
| **Add** | Spawn the selected pet type as an additional companion |
| **Apply** | Save name and pet type changes |

Language and pet type are written to the Windows Registry immediately — they survive restarts without any config file.

---

## Project Structure

```
pet/
├── main.py                    # Entry point — loads settings, creates QApplication
├── DesktopPet.spec            # PyInstaller one-file build config
├── requirements.txt
│
├── pet/
│   ├── base_pet.py            # BasePet ABC — contract for all pet types (LSP)
│   ├── simple_pet.py          # SimplePet — physics, ball-chasing, mouse-following
│   ├── full_pet.py            # FullPet — hunger/happiness/energy stats + AI (unused by default)
│   ├── factory.py             # PetFactory.create(pet_type) — OCP gateway
│   ├── protocols.py           # HasStats, BallChaser, MouseFollower, PetStorage — runtime Protocols (ISP/DIP)
│   ├── state.py               # PetState enum (for FullPet)
│   └── ball.py                # Ball physics (gravity, bounce, damping)
│
├── ui/
│   ├── pet_window.py          # Transparent window — rendering, events, pet lifecycle
│   ├── tray_manager.py        # System tray icon, menu, tooltip, notifications (SRP)
│   ├── settings.py            # Cyberpunk settings dialog
│   ├── ball_widget.py         # Transparent ball overlay (60 fps physics tick)
│   └── stats_widget.py        # Stat bars for FullPet (unused by default)
│
├── utils/
│   ├── i18n.py                # Translations (EN/RU) + Windows Registry persistence
│   ├── paths.py               # resource_base() / data_dir() — PyInstaller compatibility
│   ├── sprite_loader.py       # PNG frame loader with caching and placeholder fallback
│   └── database.py            # SQLite: pet_state + achievements (used by FullPet)
│
├── assets/
│   ├── icons/                 # .ico files (tray icon, exe icon)
│   └── sprites/               # One folder per pet type → one sub-folder per animation
│       ├── fox/               # idle/ walk/ run/ with_ball/ lie/
│       ├── panda/             # idle/ walk/ run/ with_ball/ lie/
│       ├── cockatiel/         # idle/ walk/ run/ with_ball/
│       └── …                  # dog/ turtle/ totoro/ chicken/ clippy/ …
│
└── tests/
    ├── test_pets.py
    └── test_database.py
```

---

## Architecture

```
main.py
  └─ PetWindow (ui/pet_window.py)   — window rendering, events, pet lifecycle
       ├─ TrayManager (ui/tray_manager.py)   — owns all tray concerns (SRP)
       │    └─ QSystemTrayIcon — icon, tooltip, menu, notifications
       ├─ BasePet  ←  PetFactory.create(pet_type)
       │    └─ SimplePet / FullPet
       │         ├─ SpriteLoader — lazy-loaded, per-animation PNG cache
       │         └─ FullPet only: PetStorage ← PetDatabase (DIP)
       ├─ Ball (pet/ball.py) + BallWidget (ui/ball_widget.py)
       └─ Timers
            ├─ animation_timer   33 ms  — next frame + move
            ├─ state_timer        1 s   — update_stats()
            ├─ behavior_timer     3 s   — decide_next_action()
            └─ mouse_timer      200 ms  — tick_mouse_check()
```

### SOLID design

| Principle | How it's applied |
|---|---|
| SRP | `TrayManager` owns all tray concerns; `PetWindow` owns only window + pet lifecycle; `SpriteLoader`, `PetDatabase` each do one thing |
| OCP | `PetFactory` lets new pet types be added without modifying `PetWindow` or any UI code |
| LSP | `SimplePet` and `FullPet` are interchangeable everywhere `BasePet` is expected |
| ISP | `HasStats`, `BallChaser`, `MouseFollower`, `PetStorage` — four narrow, role-specific protocols |
| DIP | `PetWindow` depends on `BasePet` + protocols; `FullPet` depends on `PetStorage` (abstraction), not `PetDatabase` (concrete) |

---

## Sprites

Sprites are sourced from **[vscode-pets](https://github.com/tonybaloney/vscode-pets)** by Anthony Shaw (MIT licence).

Each pet lives in `assets/sprites/<pet_type>/`. Inside are animation sub-folders containing `frame_1.png`, `frame_2.png`, … — PNG files with a transparent background, originally 100 × 100 px, scaled to fit the window at runtime.

If a sprite folder is missing, `SpriteLoader` falls back to a coloured circle placeholder so the app never crashes on a missing asset.

---

## Persistence

Language and all pets (primary and extras, including names, types and positions) are stored in the Windows Registry under:

```
HKEY_CURRENT_USER\Software\DesktopPet
```

The key is created on the first change and survives exe updates. Legacy `lang` and `pet` values are supported; `pets` stores the validated roster. Extra pets are restored on startup, invalid records fall back to defaults, and removed pets stay removed.

Malformed/deep JSON and inputs exceeding 4,194,304 characters use an in-memory fallback.
The original stored roster is preserved through automatic saves. Explicit Settings Apply,
adding a pet or removing a pet authorizes replacing that damaged roster. There is no hidden
pet-count cap. Names are displayed as plain text.

Pet state (for FullPet) is stored in `pet_data.db` (SQLite) next to the exe.

---

## Building from Source

```powershell
python scripts/build_release.py --install
```

Requires a working Windows CPython 3.13 AMD64 (MSC) interpreter. The helper creates
a project-local build venv, installs only the reviewed hash-locked wheels from PyPI,
runs pip check and tests, and builds into a new `dist-test-security-<timestamp>` folder.
Existing `dist/DesktopPet.exe` and prior candidates are preserved.

It checks actual Qt6 DLL versions and the manifest in the produced file without launching
that EXE. Reports include package versions, a source/asset manifest and candidate hash.
See [secure build and signing](docs/SECURE_BUILD.md) for reproducible setup, rollback,
the current Qt advisory scope and optional signing with a personal certificate.


---

## Running Tests

```bash
pytest tests/ -v
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Pet doesn't appear | Install the locked runtime in the local venv shown above |
| Tray icon missing | Check that `assets/icons/fox_ico.ico` exists |
| Sprites not loading | Normal — coloured circles are the fallback |
| × button doesn't close | Correct — it minimises to tray. Use **❌ Quit** from the tray or context menu |
| App won't start on first launch | Rebuild using the committed spec; assets are bundled inside the executable |

---

## Credits

- **Pet sprites & animations** — [vscode-pets](https://github.com/tonybaloney/vscode-pets) by [Anthony Shaw](https://github.com/tonybaloney) (MIT)
- **UI framework** — [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- **Packaging** — [PyInstaller](https://pyinstaller.org/)

---

## Licence

This project is released for personal use.  
Pet assets are © their respective creators and are redistributed under the terms of the [vscode-pets MIT licence](https://github.com/tonybaloney/vscode-pets/blob/main/LICENSE).


Development and wheel distribution:

```powershell
python -m pip --isolated install --index-url https://pypi.org/simple --require-hashes --only-binary=:all: -r requirements/test-cp313-win_amd64.lock
python -m pip install --no-deps --no-build-isolation -e .
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest
Remove-Item Env:QT_QPA_PLATFORM
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist-wheel .
```

The wheel includes `desktop-pet`, sprites and icons. PyQt6 is the runtime
dependency; test/build tools are in the optional `dev` extra. Hidden pets pause
their timers and end ball activity; showing them resets elapsed time. The
stats timer runs only for pets with stats. Settings animate only while visible.

For a single isolated verification run from the project root:

```powershell
python scripts/verify.py
```

On the supported Windows CPython 3.13 AMD64 target, `python scripts/verify.py --install-deps`
installs the reviewed hash-locked tools into `.verification/deps`, never globally.
The runner records subprocess logs and `summary.json` under `reports/verification/<timestamp>`.
It runs unit tests, pytest, lint, an event-loop smoke, and separate 1/5/10-pet CPU/memory
scenarios (idle, moving, hidden). Default benchmarks use Qt offscreen; their CPU numbers
exclude the desktop compositor and GPU. `--platform windows` explicitly opts into visible
benchmark windows. The existing EXE is never executed or rebuilt; its hash is checked.

In the current source version, a short click on any pet (or **Pet** in its right-click
panel) shows three pixel hearts that rise and fade. Pets put to sleep and repeated
clicks during the effect do not trigger extra effects. Only the fox also reacts with
its head, keeping its idle tail animation. Other pets continue their current behavior.
For a code-rendered preview, open `output/fox-pet-react/heart-effect/petting-hearts-4x.apng`.
It plays once; it is not a GUI screenshot. Reproduce it with
`python scripts/preview_heart_effect.py` in a development Python with Pillow.

Build the current project into a separate candidate folder, from any working directory:

```powershell
python 'C:\Users\User\Desktop\prikol\pet\Desktop-Pets\scripts\build_release.py' --install
```

This direct Python CLI needs no PowerShell execution-policy changes. A thin optional
`scripts/build_test.ps1` wrapper remains available. The parent `pet/main.py` is an older
separate copy. Neither it nor old EXEs are updated by the security fixes.

`output/menu-concepts/menu-preview.html` is now a standalone offline preview with local
icons and a deny-network CSP. Regenerate it with `python scripts/export_menu_preview.py --force`.
