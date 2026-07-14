from dataclasses import dataclass, field

from core.models import QuestBook
from core.progression_graph import ProgressionGraph


@dataclass
class ComponentInfo:
    """
    Informação enriquecida sobre um componente conectado do grafo de
    progressão (v0.8.1).

    Antes, um componente desconectado era reportado apenas como uma
    lista de IDs dentro de `disconnected_components`, sem contexto
    suficiente para decidir se ele representa uma progressão real ou
    apenas uma quest solta.
    """

    quest_ids: list[str] = field(default_factory=list)

    size: int = 0

    chapters: list[str] = field(default_factory=list)

    is_isolated: bool = False

    is_independent_progression: bool = False

    def to_dict(self) -> dict:

        return {

            "quest_ids": self.quest_ids,

            "size": self.size,

            "chapters": self.chapters,

            "is_isolated": self.is_isolated,

            "is_independent_progression": self.is_independent_progression,

        }


@dataclass
class ProgressionReport:
    """
    Resultado da análise de progressão de um QuestBook.

    Somente leitura: nunca é usado para modificar o QuestBook.
    """

    total_quests: int = 0

    total_dependencies: int = 0

    root_quests: list[str] = field(default_factory=list)

    terminal_quests: list[str] = field(default_factory=list)

    isolated_quests: list[str] = field(default_factory=list)

    # Mantido por compatibilidade: lista de IDs por componente.
    disconnected_components: list[list[str]] = field(default_factory=list)

    # v0.8.1: versão enriquecida de disconnected_components, com
    # tamanho, capítulos envolvidos e classificação de cada
    # componente. Preferir este campo para relatórios/consumo novo.
    components: list[ComponentInfo] = field(default_factory=list)

    dependency_cycles: list[list[str]] = field(default_factory=list)

    unreachable_quests: list[str] = field(default_factory=list)

    broken_dependencies: list[tuple[str, str]] = field(default_factory=list)

    max_depth: int = 0

    average_depth: float = 0.0

    chains: list[list[str]] = field(default_factory=list)

    longest_chain: list[str] = field(default_factory=list)

    average_chain_size: float = 0.0

    # ------------------------------------------------------
    # Export
    # ------------------------------------------------------

    def to_dict(self) -> dict:

        return {

            "total_quests": self.total_quests,

            "total_dependencies": self.total_dependencies,

            "root_quests": self.root_quests,

            "terminal_quests": self.terminal_quests,

            "isolated_quests": self.isolated_quests,

            "disconnected_components": self.disconnected_components,

            "components": [
                component.to_dict()
                for component in self.components
            ],

            "dependency_cycles": self.dependency_cycles,

            "unreachable_quests": self.unreachable_quests,

            "broken_dependencies": [
                {"quest": quest, "dependency": dependency}
                for quest, dependency in self.broken_dependencies
            ],

            "max_depth": self.max_depth,

            "average_depth": self.average_depth,

            "chains": self.chains,

            "longest_chain": self.longest_chain,

            "average_chain_size": self.average_chain_size,

        }

    # ------------------------------------------------------
    # Resumo terminal
    # ------------------------------------------------------

    def summary(self):

        independent_progressions = [
            component
            for component in self.components
            if component.is_independent_progression
        ]

        isolated_components = [
            component
            for component in self.components
            if component.is_isolated
        ]

        print("\n================================")

        print(" Progression Analysis Report")

        print("================================")

        print("\nSTRUCTURE")

        print(f" Total quests: {self.total_quests}")

        print(f" Total dependencies: {self.total_dependencies}")

        print(f" Root quests: {len(self.root_quests)}")

        print(f" Terminal quests: {len(self.terminal_quests)}")

        print(f" Isolated quests: {len(self.isolated_quests)}")

        print("\nCOMPONENTS")

        print(f" Total components: {len(self.components)}")

        print(f" Independent progressions (size > 1): {len(independent_progressions)}")

        print(f" Isolated components (single quest): {len(isolated_components)}")

        if independent_progressions:

            largest = max(independent_progressions, key=lambda c: c.size)

            print(
                f" Largest independent progression: {largest.size} quests"
                f" ({', '.join(largest.chapters) if largest.chapters else 'no chapter info'})"
            )

        print("\nINTEGRITY")

        print(f" Dependency cycles: {len(self.dependency_cycles)}")

        print(f" Unreachable quests: {len(self.unreachable_quests)}")

        print(f" Broken dependencies: {len(self.broken_dependencies)}")

        print("\nDEPTH")

        print(f" Max depth: {self.max_depth}")

        print(f" Average depth: {self.average_depth:.2f}")

        print("\nCHAINS")

        print(f" Detected chains (one per progression root): {len(self.chains)}")

        print(f" Longest chain size: {len(self.longest_chain)}")

        print(f" Average chain size: {self.average_chain_size:.2f}")

        print("================================\n")


class ProgressionAnalyzer:
    """
    Analisa a progressão de gameplay de um QuestBook.

    Constrói um ProgressionGraph e produz um ProgressionReport.

    Nunca edita o QuestBook.
    """

    def analyze(self, questbook: QuestBook) -> ProgressionReport:

        graph = ProgressionGraph.build(questbook)

        chains = graph.find_chains()

        chain_sizes = [len(chain) for chain in chains]

        average_chain_size = (
            sum(chain_sizes) / len(chain_sizes)
            if chain_sizes else 0.0
        )

        total_dependencies = sum(
            len(quest.dependencies)
            for quest in questbook.all_quests()
        )

        raw_components = graph.find_disconnected_components()

        components = [
            self._build_component_info(graph, component)
            for component in raw_components
        ]

        report = ProgressionReport(

            total_quests=questbook.total_quests(),

            total_dependencies=total_dependencies,

            root_quests=graph.find_root_quests(),

            terminal_quests=graph.find_terminal_quests(),

            isolated_quests=graph.find_isolated_quests(),

            disconnected_components=raw_components,

            components=components,

            dependency_cycles=graph.detect_cycles(),

            unreachable_quests=graph.find_unreachable_quests(),

            broken_dependencies=list(graph.broken_dependencies),

            max_depth=graph.max_depth(),

            average_depth=graph.average_depth(),

            chains=chains,

            longest_chain=graph.longest_chain(),

            average_chain_size=average_chain_size,

        )

        return report

    # ------------------------------------------------------
    # Construção de ComponentInfo
    # ------------------------------------------------------

    def _build_component_info(
        self,
        graph: ProgressionGraph,
        quest_ids: list[str]
    ) -> ComponentInfo:

        chapters = sorted(
            {
                graph.get_chapter_of(quest_id)
                for quest_id in quest_ids
                if graph.get_chapter_of(quest_id)
            }
        )

        size = len(quest_ids)

        return ComponentInfo(

            quest_ids=quest_ids,

            size=size,

            chapters=chapters,

            is_isolated=(size == 1),

            # Um componente com mais de um nó, por definição de
            # componente fracamente conectado, sempre possui ao
            # menos uma aresta - ou seja, representa uma progressão
            # (uma cadeia de dependências) desconectada do restante
            # do questbook.
            is_independent_progression=(size > 1),

        )

    # ------------------------------------------------------
    # Sensores diretos (sem precisar montar o relatório inteiro)
    # ------------------------------------------------------

    def find_root_quests(self, questbook: QuestBook) -> list[str]:

        return ProgressionGraph.build(questbook).find_root_quests()

    def find_terminal_quests(self, questbook: QuestBook) -> list[str]:

        return ProgressionGraph.build(questbook).find_terminal_quests()

    def find_isolated_quests(self, questbook: QuestBook) -> list[str]:

        return ProgressionGraph.build(questbook).find_isolated_quests()

    def detect_cycles(self, questbook: QuestBook) -> list[list[str]]:

        return ProgressionGraph.build(questbook).detect_cycles()