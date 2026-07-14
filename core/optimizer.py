from dataclasses import dataclass, field

from core.models import QuestBook
from core.analysis import QuestbookAnalyzer
from core.dependency_cleaner import DependencyCleaner
from core.chapter_cleaner import ChapterCleaner


# ==========================================================
# Relatório de otimização
# ==========================================================

@dataclass
class OptimizationReport:

    removed_dependencies: int = 0

    removed_chapters: list[str] = field(default_factory=list)

    valid: bool = True

    def to_dict(self) -> dict:

        return {
            "removed_dependencies": self.removed_dependencies,
            "removed_chapters": list(self.removed_chapters),
            "valid": self.valid,
        }


# ==========================================================
# QuestOptimizer
# ==========================================================

class QuestOptimizer:
    """
    Etapa de otimização do QuestBook.

    Reúne, em uma única chamada, as limpezas estruturais que devem
    acontecer depois de qualquer edição:

    - Remove dependências órfãs (referências a quests que não
      existem mais).
    - Remove capítulos que ficaram vazios em consequência disso.
    - Reconstrói os índices via QuestbookAnalyzer.
    - Valida o resultado (sensor `is_valid`).

    Nunca remove quests. Apenas repara referências e estrutura
    deixadas por outras edições (Editor, ModpackProfile etc.).
    """

    def __init__(self, questbook: QuestBook):

        self.questbook = questbook

        self.dependency_cleaner = DependencyCleaner()

        self.chapter_cleaner = ChapterCleaner()

    # ------------------------------------------------------
    # Sensores
    # ------------------------------------------------------

    def find_broken_dependencies(self):

        return self.dependency_cleaner.find_broken_dependencies(
            self.questbook
        )

    def find_empty_chapters(self):

        return self.chapter_cleaner.find_empty_chapters(self.questbook)

    def is_valid(self) -> bool:

        return len(self.find_broken_dependencies()) == 0

    # ------------------------------------------------------
    # Otimização completa
    # ------------------------------------------------------

    def optimize(self, validate: bool = True) -> OptimizationReport:

        report = OptimizationReport()

        # dependências órfãs / referências inválidas
        report.removed_dependencies = self.dependency_cleaner.clean(
            self.questbook
        )

        # capítulos que ficaram vazios (dados mortos deixados por remoções)
        self.chapter_cleaner.clean(self.questbook)

        report.removed_chapters = list(
            self.chapter_cleaner.removed_chapters
        )

        # reindexação final
        QuestbookAnalyzer().analyze(self.questbook)

        if validate:

            report.valid = self.is_valid()

        return report
