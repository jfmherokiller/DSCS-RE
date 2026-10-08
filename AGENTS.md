# AGENTS.md — Digimon Story Cyber Sleuth (DSCS) RE

Sister project to `E:\ReverseEngineProjects\TimeStranger` (DSTS). The goal is to reverse
engineer DSCS Complete Edition, compare it against DSTS (same Media.Vision MVGL engine), and use each
game's findings and mods to improve the other. The comparison lives in `docs/COMPARISON.md`; read it first.

## Layout
| Path | Contents |
|---|---|
| `bin/Digimon Story CS.exe` | Copy of the shipped exe (SteamStub-packed, do not analyze) |
| `bin/DigimonStoryCS.unpacked.exe` (+ `.i64`) | Steamless-unpacked copy; **this is the IDB to use** |
| `tools/Steamless/` | Steamless v3.1.0.5 (`Steamless.CLI.exe --quiet <exe>`) |
| `external/DSCSModLoader/` | SydMontague's loader source (GPLv3) — source of the known RVAs |
| `external/MVGLTools/` | SydMontague's MVGL/MBE/save tools for DSCS + DSTS (BSD-3) |
| `dscsmodloader_symbols.json` | RVAs imported from DSCSModLoader into the IDB |
| `docs/` | Findings |

Game install: `E:\SteamLibrary\steamapps\common\Digimon Story Cyber Sleuth Complete Edition`
(`app_digister\` exe + DSCSModLoader, `resources\*.steam.mvgl`, `SimpleDSCSModManager\`, `DCSTOOLS\`).
Never write into the game folder; work on copies here.

## IDA
- Open headless: `idb_open(input_path=...\bin\DigimonStoryCS.unpacked.exe, mode=force_headless, preferred_session_id=dscs_unpacked)`.
  The ida-pro-mcp server needs `IDADIR` set (see Hermes memory). Initial auto-analysis takes over 5 minutes.
- Image base `0x140000000`; DSCSModLoader offsets are RVAs (add the base).
- ~100 functions/globals already named from DSCSModLoader (Squirrel `sq_*` API, save I/O, VFS,
  archive list, frame timing). Note: the loader's `sq_setparamscheck` RVA `0x6080D0` lies inside
  the function starting at `0x1406080B0`; the name was applied to the function start.
- Save the IDB after each naming batch.

## Conventions
- Same evidence rules as `TimeStranger/RE/methodology_and_binary_overview.md`: confirmed vs. inferred
  vs. idea, and no names applied without behavioural evidence.
- Don't commit game binaries, IDBs or extracted assets (see `.gitignore`).
- DSCSModLoader is GPLv3: reuse its *knowledge* (addresses, designs) freely, but copying its code into
  a non-GPL mod is not allowed.
