from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# ==========================================================
# Quest
# ==========================================================

@dataclass
class Quest:

    id: str

    title: str


    # Capítulo ao qual pertence
    #
    # v0.4
    #
    chapter_id: str | None = None


    # Mod principal detectado
    #
    mod: str = "Unknown"


    # Todos os mods encontrados
    #
    # v0.4.5
    #
    mods: set[str] = field(default_factory=set)
    references_vanilla: bool = False


    dependencies: list[str] = field(default_factory=list)


    task_types: list[str] = field(default_factory=list)


    reward_types: list[str] = field(default_factory=list)


    source_file: Path | None = None


# ==========================================================
# Chapter Analysis
# ==========================================================

@dataclass
class ChapterAnalysis:

    total_quests: int = 0

    mods: set[str] = field(default_factory=set)

    task_types: set[str] = field(default_factory=set)

    reward_types: set[str] = field(default_factory=set)

    dependencies: int = 0


# ==========================================================
# Chapter
# ==========================================================

@dataclass
class Chapter:

    id: str

    title: str

    quests: list[Quest] = field(default_factory=list)

    source_folder: Path | None = None

    analysis: ChapterAnalysis = field(default_factory=ChapterAnalysis)

    # IDs (stem do arquivo) de quests que existem no disco mas não
    # puderam ser interpretadas pelo Parser (SNBT malformado/formato
    # não suportado). Mantido só para o Writer saber que precisa
    # preservar esses arquivos "as-is" em vez de descartá-los -
    # nunca é usado para lógica de negócio.
    #
    # v0.6.2
    #
    malformed_quest_ids: list[str] = field(default_factory=list)

    # True quando o próprio chapter.snbt não pôde ser interpretado
    # (SNBT malformado ou arquivo ausente). O capítulo ainda é
    # mantido - com id/title vindos do nome da pasta - para que o
    # Writer preserve a pasta inteira em vez de descartá-la. Nunca
    # usado para lógica de negócio além disso.
    #
    # v0.6.3
    #
    chapter_malformed: bool = False


# ==========================================================
# Mod Analysis
# ==========================================================

@dataclass
class ModAnalysis:

    name: str

    quests: int = 0

    chapters: set[str] = field(default_factory=set)


# ==========================================================
# QuestBook
# ==========================================================

@dataclass
class QuestBook:

    name: str

    chapters: list[Chapter] = field(default_factory=list)

    loaded_files: int = 0

    malformed_files: int = 0

    warnings: list[str] = field(default_factory=list)

    # Pasta original de onde este QuestBook foi lido. Usado só pelo
    # Writer para localizar as entradas de extra_root_entries -
    # nunca para lógica de negócio.
    #
    # v0.6.4
    #
    source_folder: Path | None = None

    # Caminhos (absolutos) de arquivos/pastas que existem no
    # questbook original mas que o Parser não modela (ex.: file.snbt,
    # reward_tables/, chapters/index.snbt). Preservados como estão
    # pelo Writer, sem serem interpretados - ver AI_CONTEXT: "Never
    # parse SNBT outside Parser" continua valendo, porque esses dados
    # nunca são parseados, só copiados.
    #
    # v0.6.4
    #
    extra_root_entries: list[Path] = field(default_factory=list)

    #
    # Índices criados na v0.3
    #

    quest_index: dict[str, Quest] = field(default_factory=dict)

    mod_index: dict[str, ModAnalysis] = field(default_factory=dict)
    reference_mod_index: dict[str, ModAnalysis] = field(default_factory=dict)

    dependency_graph: dict[str, list[str]] = field(default_factory=dict)


    # ------------------------------------------------------

    def total_quests(self) -> int:

        return sum(
            len(chapter.quests)
            for chapter in self.chapters
        )


    # ------------------------------------------------------

    def all_quests(self):

        for chapter in self.chapters:

            for quest in chapter.quests:

                yield quest


    # ------------------------------------------------------

    def all_chapters(self):

        yield from self.chapters


    # ------------------------------------------------------
    # v0.4
    #
    # Busca rápida de capítulo.
    #
    # ------------------------------------------------------

    def get_chapter(
        self,
        chapter_id: str
    ) -> Chapter | None:

        for chapter in self.chapters:

            if chapter.id == chapter_id:

                return chapter

        return None