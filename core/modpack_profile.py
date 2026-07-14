from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from core.models import QuestBook
from core.installed_mods import InstalledModsScanner
from core.editor import QuestbookEditor
from core.optimizer import QuestOptimizer, OptimizationReport


# Quantidade máxima de quests listadas por mod no relatório detalhado
MAX_QUEST_SAMPLE = 20


# ==========================================================
# Detalhe por mod ausente
# ==========================================================

@dataclass
class MissingModDetail:

    mod: str

    affected_quests: int = 0

    affected_chapters: int = 0

    quest_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:

        return {
            "mod": self.mod,
            "affected_quests": self.affected_quests,
            "affected_chapters": self.affected_chapters,
            "quest_ids": list(self.quest_ids),
        }


# ==========================================================
# Relatório
# ==========================================================

@dataclass
class ModpackProfileReport:

    mods_installed: list[str] = field(default_factory=list)

    mods_used: list[str] = field(default_factory=list)

    missing_mods: list[str] = field(default_factory=list)

    missing_mods_detail: list[MissingModDetail] = field(default_factory=list)

    removed_quests: list[str] = field(default_factory=list)

    removed_dependencies: int = 0

    removed_chapters: list[str] = field(default_factory=list)

    affected_chapters: list[str] = field(default_factory=list)

    dry_run: bool = False

    timestamp: str = ""

    def to_dict(self) -> dict:

        return {
            "mods_installed": sorted(self.mods_installed),
            "mods_used": sorted(self.mods_used),
            "missing_mods": sorted(self.missing_mods),
            "missing_mods_detail": [
                detail.to_dict() for detail in self.missing_mods_detail
            ],
            "removed_quests": sorted(self.removed_quests),
            "removed_dependencies": self.removed_dependencies,
            "removed_chapters": sorted(self.removed_chapters),
            "affected_chapters": sorted(self.affected_chapters),
            "dry_run": self.dry_run,
            "timestamp": self.timestamp,
        }


# ==========================================================
# ModpackProfile
# ==========================================================

class ModpackProfile:
    """
    Adapta um QuestBook ao modpack realmente instalado.

    Compara os mods referenciados pelas quests (`quest.mods`, todos
    os namespaces encontrados, não só o mod principal) com os mods
    presentes na pasta `mods/` de uma instância e remove as quests
    de mods ausentes, junto com dependências e capítulos que ficarem
    órfãos por causa disso.

    Todos os sensores (`detect_missing_mods`, `estimate_removed_quests`,
    `estimate_removed_chapters`, `estimate_dependency_cleanup`) são
    somente leitura: simulam a remoção em uma cópia do QuestBook e
    nunca modificam `self.questbook`. O próprio Dry Run reutiliza essa
    mesma simulação, garantindo que ele execute exatamente a mesma
    lógica da remoção real — a única diferença é operar sobre uma
    cópia em vez do QuestBook original, e nunca persistir em disco.
    """

    #
    # Namespaces que nunca devem ser tratados como "mod ausente",
    # pois não representam um mod real instalável separadamente.
    #
    IGNORE_MODS = {
        "Unknown",
        "minecraft",
        "forge",
        "neoforge",
        "ftbquests",
    }

    def __init__(self, questbook: QuestBook, mods_folder: Path):

        self.questbook = questbook

        self.mods_folder = Path(mods_folder)

        self.scanner = InstalledModsScanner()

    # ------------------------------------------------------
    # Sensores (somente leitura)
    # ------------------------------------------------------

    def detect_installed_mods(self) -> set[str]:

        return self.scanner.scan(self.mods_folder)

    def used_mods(self) -> set[str]:

        mods: set[str] = set()

        for quest in self.questbook.all_quests():

            mods.update(quest.mods)

        return mods

    def detect_missing_mods(self) -> set[str]:

        installed = self.detect_installed_mods()

        return {
            mod
            for mod in self.used_mods()
            if mod not in installed
            and mod not in self.IGNORE_MODS
        }

    # Alias mantido por compatibilidade com chamadas existentes.
    def missing_mods(self) -> set[str]:

        return self.detect_missing_mods()

    def missing_mods_detail(
        self,
        missing: set[str] | None = None,
    ) -> list[MissingModDetail]:
        """
        Para cada mod ausente, calcula quantas quests e capítulos são
        afetados, além de uma lista (limitada) das quests envolvidas.
        Somente leitura: não modifica o QuestBook.
        """

        if missing is None:

            missing = self.detect_missing_mods()

        details: list[MissingModDetail] = []

        for mod in sorted(missing):

            affected = [
                quest
                for quest in self.questbook.all_quests()
                if mod in quest.mods
            ]

            chapters = {
                quest.chapter_id
                for quest in affected
                if quest.chapter_id
            }

            quest_ids = sorted(quest.id for quest in affected)

            details.append(
                MissingModDetail(
                    mod=mod,
                    affected_quests=len(affected),
                    affected_chapters=len(chapters),
                    quest_ids=quest_ids[:MAX_QUEST_SAMPLE],
                )
            )

        return details

    def estimate_removed_quests(
        self,
        missing: set[str] | None = None,
    ) -> set[str]:

        affected_ids, _affected_chapters, _optimization = self._simulate(missing)

        return affected_ids

    def estimate_removed_chapters(
        self,
        missing: set[str] | None = None,
    ) -> set[str]:

        _affected_ids, _affected_chapters, optimization = self._simulate(missing)

        return set(optimization.removed_chapters)

    def estimate_dependency_cleanup(
        self,
        missing: set[str] | None = None,
    ) -> int:

        _affected_ids, _affected_chapters, optimization = self._simulate(missing)

        return optimization.removed_dependencies

    # ------------------------------------------------------
    # Simulação (base compartilhada por sensores e dry-run)
    # ------------------------------------------------------

    def _simulate(
        self,
        missing: set[str] | None = None,
    ) -> tuple[set[str], set[str], OptimizationReport]:
        """
        Executa a remoção completa (Editor + QuestOptimizer) sobre uma
        cópia profunda do QuestBook, sem jamais tocar em
        `self.questbook`. Usada tanto pelos sensores de estimativa
        quanto pelo Dry Run, garantindo que ambos reflitam exatamente
        a mesma lógica usada na execução real.
        """

        if missing is None:

            missing = self.detect_missing_mods()

        if not missing:

            return set(), set(), OptimizationReport()

        target = copy.deepcopy(self.questbook)

        affected = [
            quest
            for quest in target.all_quests()
            if quest.mods & missing
        ]

        if not affected:

            return set(), set(), OptimizationReport()

        affected_ids = {quest.id for quest in affected}

        affected_chapters = {
            quest.chapter_id
            for quest in affected
            if quest.chapter_id
        }

        QuestbookEditor(target).remove_quests(affected_ids)

        optimization = QuestOptimizer(target).optimize()

        return affected_ids, affected_chapters, optimization

    # ------------------------------------------------------
    # Aplica a adaptação ao QuestBook
    # ------------------------------------------------------

    def apply(self, dry_run: bool = False) -> ModpackProfileReport:
        """
        Calcula e aplica (ou simula) a adaptação do QuestBook ao
        modpack instalado.

        dry_run=False (padrão): remove quests, dependências órfãs e
            capítulos vazios diretamente em `self.questbook`.
        dry_run=True: executa exatamente a mesma lógica de remoção,
            mas sobre uma cópia — `self.questbook` permanece intacto e
            nada é escrito em disco.
        """

        installed = self.detect_installed_mods()

        used = self.used_mods()

        missing = self.detect_missing_mods()

        report = ModpackProfileReport(
            mods_installed=list(installed),
            mods_used=list(used),
            missing_mods=list(missing),
            missing_mods_detail=self.missing_mods_detail(missing),
            dry_run=dry_run,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        if not missing:

            return report

        if dry_run:

            affected_ids, affected_chapters, optimization = self._simulate(missing)

            report.removed_quests = sorted(affected_ids)
            report.affected_chapters = sorted(affected_chapters)
            report.removed_dependencies = optimization.removed_dependencies
            report.removed_chapters = sorted(optimization.removed_chapters)

            return report

        # Execução real: opera diretamente sobre self.questbook
        affected = [
            quest
            for quest in self.questbook.all_quests()
            if quest.mods & missing
        ]

        if not affected:

            return report

        affected_ids = {quest.id for quest in affected}

        affected_chapters = {
            quest.chapter_id
            for quest in affected
            if quest.chapter_id
        }

        QuestbookEditor(self.questbook).remove_quests(affected_ids)

        optimization = QuestOptimizer(self.questbook).optimize()

        report.removed_quests = sorted(affected_ids)
        report.affected_chapters = sorted(affected_chapters)
        report.removed_dependencies = optimization.removed_dependencies
        report.removed_chapters = optimization.removed_chapters

        return report
