# Cyber Sleuth (DSCS) vs Time Stranger (DSTS) — engine comparison

Living document. Evidence levels: **confirmed** (checked in a binary/source), **inferred** (strong
circumstantial), **idea** (untested improvement proposal).

## Binaries

| | DSCS Complete Edition | DSTS |
|---|---|---|
| Exe | `app_digister\Digimon Story CS.exe` | `Digimon Story Time Stranger.exe` |
| Build timestamp | 2019-10-09 | 2026-06 |
| Protection | **SteamStub 3.1 x64** (`.bind`, `.text` entropy 8.0) — must be unpacked with Steamless before analysis (confirmed) | none |
| Analyzed copy | `bin/DigimonStoryCS.unpacked.exe` (sha256 `015b9e0d…5b55`) | game folder `.i64` |
| Functions (IDA) | 38,374 (12,043 FLIRT library) | 105,109 |
| RTTI types | 1,269 | 2,532 |
| Project codename | `digister` (`app_digister`, `ADigisterModel`) | `digister02_dx11` (source paths) |

Both are Media.Vision's in-house **MVGL** engine (`MVGL::Draw`, `MVGL::Physics`, `MVGL::Utilities`
namespaces; Bullet physics; CRIWARE audio/movie). **124 RTTI types are shared verbatim**, including
`CGameData`, `CMBEManager`, `CGameSave`, `CSavedataManager`, `CDigimonData`, `CPlayerData`,
`CFieldMap`, `CGameResourceManager`, `CGameLoadManager`, `CModelLoadObject`, `ADigisterModel`,
`AGameBaseModel`, `CEventManager`, `CUIManager`, `CTrophyManager`, `CGameDLC`. Those are the best
anchors for matching code between the two exes (find the class vtable in each, compare slots).

## Subsystem differences

| Area | DSCS | DSTS | Notes |
|---|---|---|---|
| Graphics API | OpenGL + NVIDIA Cg (`cg.dll`, `cgGL.dll`) | D3D11 + d3dcompiler_47 | Shader files both named `%s/shaders/%s_{vp,fp}.shad` — same asset convention, different backend (confirmed strings). |
| Scripting | **Squirrel 2.2.4** + Sqrat bindings (`.nut` bytecode; NutCracker decompiles) | **Lua 5.2** (bytecode, unluac decompiles) | Biggest architectural change. Script API names may still carry over — compare DSCS Sqrat-registered names to DSTS `RegisterLua_*` tables. |
| Archives | `.steam.mvgl`, **encrypted on PC** (MVGLTools decrypts transparently) | `.dx11.mvgl`, unencrypted; MBE carries its own schema | DSCS MBE needs external `structure.json`; DSTS MBE is self-describing (MVGLTools README). |
| Archive mounting | Global list `g_ArchiveList/Table/Count` @ `0xF219C0/0xF229C0/0xF20770`; `ResourceManager_AddArchiveOverride` `0x1404FD150` | `PackFileResource_ReadFile`/`GetFileSize` hooked by MVGL.FileLoader | Same concept; DSTS exposes a cleaner hookable read path. |
| UI | MFC statically linked (debug tooling: `CDockingManager`, `CMFC*`, `CDHtml*`) + game `ui::` (≈132 types) | game `ui::` (430 types) | DSCS shipped MFC debug-window classes; worth checking for reachable debug menus/tools (idea). |
| Save | custom XOR-style `Save_EncryptSaveFile/DecryptSaveFile(buf,size,key)` `0x1402CFCF0/0x1402CFF70` | AES-128-ECB (see `TimeStranger/RE/save_encryption_and_offline_inspection.md`) | |
| Digimon id limits | Scan/seen save data capped at **400 Digimon** — DSCSModLoader adds a co-save | Scan record limited to a **signed 16-bit custom id** (`TimeStranger/RE/digimon_scan_and_conversion_system.md`) | The same problem in both. DSCS already has a working fix design. |
| Framerate | Movement tied to FPS (fixed by DSCSModLoader by patching frame-delta reads) | unknown — check | |
| Model/anim formats | `.geom`/`.skel`/`.anim` (Blender-Tools-for-DSCS) | same family (DSTS_Unified; Romsstar fork of the DSCS tools covers DSTS/THL) | Shared lineage confirmed by toolchain history. |
| Mod loader | DSCSModLoader (freetype.dll proxy, **hard-coded RVAs**, raw byte patches, Squirrel API extension, co-save, plugins) | Reloaded-II (sigscan + Reloaded.Hooks, MVGL.FileLoader CSV merges) | |

## Ways to improve each, using the other

### Into DSTS (from DSCS)
1. **Co-save for scan/seen data (idea, high value).** DSCSModLoader's `CoSave` writes a sidecar file
   next to the save via the engine's VFS and hooks create/load/read/write. That's exactly the
   architecture proposed in `TimeStranger/RE/digimon_scan_int32_mod_feasibility.md`. Port the design
   (not the GPL code unless the mod is GPL) to a Reloaded-II mod.
2. **Script-API extension pattern (idea).** DSCSModLoader adds native functions to Squirrel
   (`Digimon.GetScan`, `ModLoader.GetFlag/SetFlag`, `StorageGet/SetInt`). The DSTS equivalent would be
   registering extra C functions into Lua's `_G.Common` (mechanism documented in
   `TimeStranger/RE/lua_registration_mechanics.md`). That gives Lua-only mods persistent custom
   flags/variables — a missing building block for DSTS story/event mods.
3. **FPS/speed controls (idea).** Check whether DSTS movement/timers are frame-locked like DSCS was;
   DSCSModLoader's speedup/FPS-cap approach is a template.

### Into DSCS (from DSTS)
1. **Player model swap (idea, high value).** DSCS already has a costume system with a
   `modelName.startsWith("pc")` check (DSCSModLoader README patch at RVA `0x366413`). The DSTS swap
   design (transient change during model resolution, data rows for each Digimon) should map onto it:
   find DSCS's player model resolver via the shared `CPlayerData`/`ADigisterModel` classes.
2. **Signature-based hooks.** DSCSModLoader uses fixed RVAs. DSCS is no longer patched so that's
   workable, but AOB signatures (as in the DSTS mods) would make plugins robust to the
   Steam-vs-other-store build differences.
3. **Animation retargeting pipeline.** `dsts_retarget.py` plus the Blender toolchain should work for DSCS
   rigs with an exporter swap (same format family) — e.g. human field animations for Digimon in DSCS.

### Into both
- **Cross-game asset porting (idea).** Same engine and same format family, so DSCS models/animations
  (e.g. the 300+ DSCS Digimon, the DSCS protagonists) may convert to DSTS with modest format work, and
  the reverse. Needs a format-diff pass on `.geom`/`.skel`/`.anim` headers between the two games first.

## Next RE steps
1. Map DSCS Squirrel native registrations (Sqrat `Func`/`StaticFunc` call sites near `sq_newclosure`
   `0x140606D20` + `sq_setnativeclosurename` `0x140607FE0`) → DSCS script-API catalog; diff against
   the DSTS Lua API catalog.
2. Locate DSCS player-model resolution (start from the costume `"pc"` check at RVA `0x366413`).
3. Pair shared-RTTI vtables (`CGameData`, `CMBEManager`, `CGameSave`, `CDigimonData`) across both IDBs
   and port names DSTS→DSCS where slot behaviour matches.
4. Diff `.geom`/`.anim` headers between the games using DSTS_Unified and Blender-Tools-for-DSCS readers.
