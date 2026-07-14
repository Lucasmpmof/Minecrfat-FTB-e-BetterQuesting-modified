# Questbook Toolkit - AI Context

Version: 0.7.0
Language: Python 3.12+

---

# Project Overview

Questbook Toolkit is an offline toolkit for reading, analyzing, editing and writing Minecraft questbooks.

Current supported format:

- FTB Quests

Planned after V1:

- Better Questing
- Hardcore Questing Mode

The architecture is intentionally modular and every operation should work over the same in-memory QuestBook model.

---

# Current Development Goal

Current priority is finishing V0.7 (Playable Beta): the Toolkit must be
reliable enough to adapt a large questbook and support a full Minecraft
playthrough with zero data loss caused by the Toolkit itself.

Primary objective:

Generate questbooks adapted to personal Minecraft modpacks.

Development priority:

1. Correctness
2. Stability / no silent data loss
3. Gameplay features
4. Maintainability
5. Documentation

Avoid large architectural refactors before V1 unless they remove duplicated code or fix real bugs.

---

# Architecture

```
main.py
    │
    ▼
Actions
    │
    ▼
Parser
    │
    ▼
QuestBook
    │
    ├── Analyzer
    ├── Validator
    ├── Editor
    ├── Optimizer
    └── Writer
```

Everything operates over the QuestBook model.

Only QuestbookWriter writes files.

Parser never edits data.

Actions only orchestrate.

Business logic belongs inside core/.

---

# Core Models

## QuestBook

Contains:

- chapters
- warnings
- malformed files
- indexes
- source_folder (original folder read; used only by Writer)
- extra_root_entries (paths not modeled by Parser - file.snbt,
  reward_tables/, chapters/index.snbt - preserved as-is by Writer)

---

## Chapter

Contains:

- quests
- analysis
- malformed_quest_ids (quest files that failed to parse; preserved
  as-is by Writer instead of being dropped)
- chapter_malformed (true when chapter.snbt itself failed to parse;
  chapter is kept, not discarded, so its folder isn't lost)

---

## Quest

Contains:

- id
- title
- chapter_id
- mod
- mods
- dependencies
- task_types
- reward_types
- source_file
- references_vanilla

Parser output should never be modified directly.

Editors modify Quest objects.

---

# Main Components

## FTBQuestsParser

Reads SNBT.

Produces QuestBook.

Never edits files.

Never drops malformed content: a quest or chapter that fails to
parse is kept (marked malformed) instead of discarded, so the
Writer can preserve its file(s) unchanged.

Records any file/folder it doesn't model (file.snbt, reward_tables/,
chapters/index.snbt) in QuestBook.extra_root_entries.

---

## QuestbookAnalyzer

Generates statistics.

Rebuilds indexes after structural changes.

Never edits quests.

---

## QuestbookValidator

Validates:

- missing quests
- malformed files
- broken dependencies
- empty chapters
- unknown quests

Produces ValidationReport.

---

## UnknownAnalyzer

Classifies every quest into:

- detected_mod
- vanilla
- ftb_internal
- manual
- unknown

The sum of every category must equal the total number of quests.

---

## DependencyCleaner

Removes broken dependencies.

Never deletes quests.

---

## ChapterCleaner

Removes empty chapters.

A chapter with malformed_quest_ids or chapter_malformed=True is
never considered empty, even with zero parsed quests.

Never deletes quests directly.

---

## QuestOptimizer

Combines:

- DependencyCleaner
- ChapterCleaner

Rebuilds indexes after optimization.

Used by:

- clean
- modpack-profile

---

## InstalledModsScanner

Reads installed mods directly from .jar metadata.

Supported metadata:

- META-INF/mods.toml
- fabric.mod.json
- quilt.mod.json

Does not rely on jar filenames.

Uses only Python standard library.

---

## ModpackProfile

Compares:

QuestBook mods

vs

Installed mods.

Removes quests belonging to missing mods.

Delegates cleanup to QuestOptimizer.

Produces:

- missing mods
- removed quests
- affected chapters
- removed dependencies
- removed chapters

Supports dry-run.

---

## QuestbookEditor

Edits QuestBook in memory.

Examples:

- remove quests
- remove dependencies

---

## QuestbookWriter

Writes QuestBook back to disk.

Must preserve folder structure.

Preserves malformed quest/chapter files unchanged (never silently
deletes them).

Copies QuestBook.extra_root_entries unchanged (file.snbt,
reward_tables/, chapters/index.snbt).

---

# Data Flow

Questbook Folder

↓

QuestbookParser

↓

FTBQuestsParser

↓

QuestBook

↓

Analyzer / Validator / Editor / Optimizer / Writer

QuestBook is the single shared data model.

---

# Main CLI Commands

scan

Read questbook.

---

analyze

Generate statistics.

---

validate

Validate integrity.

---

clean

Optimize questbook structure.

---

modpack-profile

Adapt a questbook to a specific installed modpack.

---

remove-mod

Remove quests belonging to one mod.

---

edit-test

Development command.

---

# Sensor Functions

Every major component should expose read-only sensor methods.

Examples:

validator.validate()

analyzer.summary()

optimizer.is_valid()

editor.preview()

find_empty_chapters()

detect_missing_mods()

estimate_removed_quests()

estimate_removed_chapters()

estimate_dependency_cleanup()

Sensors must never modify QuestBook.

---

# Coding Rules

Business logic belongs inside core/.

Actions are thin wrappers.

Prefer composition.

Avoid circular imports.

Keep functions small.

Reuse QuestBook whenever possible.

Never duplicate parser logic.

Never parse SNBT outside Parser.

Only Writer writes files.

Use dataclasses whenever possible.

---

# Single Source of Truth

Quest.mods

contains every detected namespace.

Quest.mod

must always be derived from Quest.mods.

Never maintain two independent detection systems.

---

# Known Issues

## Unknown Quest Investigation

Status: OPEN (low remaining count, not a priority for V0.7)

ModDetector already handles: minecraft:, ForgeCaps-hidden namespaces
(e.g. astralsorcery via ForgeCaps), and GregTech-style
"namespace:path meta count" item strings.

Rejected on purpose (never treated as a mod): URLs (http://, mailto:),
timestamps (12:30), free text ("label: some sentence").

Strategy for any new Unknown case found:

1. Inspect one Unknown SNBT.
2. Identify its serialization format.
3. Extend ModDetector only for that format.
4. Repeat until Unknown count becomes minimal.

Never rewrite the detector from scratch. Extend it incrementally.

---

# Validation Invariant

The validator should always satisfy:

Detected Mods

-

Vanilla

-

Manual

-

FTB Internal

-

Real Unknown

=

Total Quests

If this equation fails, classification is incorrect.

---

# Data Preservation Guarantee

The Writer must never silently delete content it doesn't understand.

Applies to:

- A quest file that fails to parse (kept via Chapter.malformed_quest_ids).
- A chapter.snbt that fails to parse (kept via Chapter.chapter_malformed).
- Anything the Parser doesn't model: file.snbt, reward_tables/,
  chapters/index.snbt (kept via QuestBook.extra_root_entries).

ChapterCleaner/Optimizer must never treat preserved-but-unparsed
content as "empty" and remove it.

Any new top-level file/folder FTB Quests may introduce in the future
should default to this same opaque preservation, not be ignored.

---

# Multi-Profile Questbooks (fixed)

Status: FIXED

Some modpacks (e.g. the "seven-coats-tie" instance used for real-world
validation) store more than one questbook side by side under the same
`ftbquests/` folder - e.g. `challenge/` and `classic/`, each with its
own `chapters/` and `reward_tables/`.

QuestbookParser.detect() used to `return` on the first matching
profile it found, silently discarding every sibling profile and any
loose root-level file (e.g. a `.md`). This was a real data-loss bug,
not just a UX issue: `modpack-profile` on a two-profile modpack only
ever processed one of the two questbooks and dropped the other
entirely from the output.

Fix:

- `QuestbookParser.detect_all(folder)` returns every profile found
  (`QuestbookProfile(name, type, path)`), instead of just the first.
  `detect()` is kept only for backward compatibility and still
  returns just the first profile - new code should use
  `detect_all()`.
- `QuestbookParser.loose_root_entries(folder, profiles)` returns
  files/folders at the true root that don't belong to any detected
  profile (e.g. a `.md`), so they can be preserved instead of
  silently dropped.
- `core/profile_utils.py` (`resolve_profiles`, `output_path_for`,
  `copy_loose_root_entries`) is the shared helper every action uses
  to loop over all detected profiles and route each one to its own
  `output/<profile_name>/` subfolder when there's more than one
  profile, or straight to `output/` when there's only one (keeps
  backward compatibility with existing single-profile modpacks).
- All actions (`scan`, `analyze`, `validate`, `clean`, `remove-mod`,
  `modpack-profile`, `edit-test`) were updated to loop over every
  detected profile instead of assuming exactly one. Backup is done
  once per invocation (covers the whole root folder, all profiles
  included), not once per profile.
- Regression test: `test_multi_profile.py`.

---

# Current Real-World Validation

Reference questbook:

MC Eternal

957 quests

Current results:

- Parser stable (malformed quests/chapters preserved, not dropped)
- Writer stable (file.snbt, reward_tables/, chapters/index.snbt preserved)
- Optimizer stable
- Modpack adaptation working
- Dependency cleanup working
- Chapter cleanup working

---

# Future Roadmap

V0.7 (closing out)

- Manual validation of a full real-world adaptation + playthrough
- Improve ModDetector coverage only if new Unknown cases appear

V1.0

Stable playable release.

After V1:

- BetterQuesting support
- HQM support
- Large refactors
- Performance improvements
- Documentation polish

---

End of AI Context.
