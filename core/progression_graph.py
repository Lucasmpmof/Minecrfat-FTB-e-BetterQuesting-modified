from __future__ import annotations

import networkx as nx

from core.models import QuestBook


class ProgressionGraph:
    """
    Representa a progressão de um QuestBook como um grafo direcionado.

    Nós: IDs de quests.
    Arestas: prerequisito -> dependente
        (A -> B significa "B depende de A").

    Nunca edita o QuestBook. Nunca escreve arquivos. Apenas leitura
    e análise, seguindo a mesma filosofia de Parser/Analyzer/Validator
    já usada no restante do projeto.

    Dependências quebradas (apontando para um quest_id inexistente)
    nunca viram uma aresta fictícia - são registradas em
    `broken_dependencies` para que o ProgressionAnalyzer possa
    reportá-las, em vez de serem silenciosamente ignoradas.

    v0.8.1 - Root/terminal refinement + scalable chains
    ------------------------------------------------------
    "Root" e "terminal" agora exigem participação real na progressão:

    - Uma quest isolada (sem pais e sem filhos) NÃO é mais
      considerada raiz nem terminal. Ela é apenas isolada. Antes,
      toda quest informativa/standalone (comum em questbooks reais,
      ex.: quests de aviso, lore, ou hub sem dependências) contava
      como "raiz de progressão", inflando a métrica sem significado
      de gameplay.

    - Root: in_degree == 0 AND out_degree > 0 (de fato inicia uma
      cadeia).
    - Terminal: out_degree == 0 AND in_degree > 0 (de fato conclui
      uma cadeia).
    - Isolated: in_degree == 0 AND out_degree == 0 (não participa de
      progressão alguma - continua reportado separadamente).

    `find_chains()` deixou de enumerar todos os caminhos simples
    (exponencial em grafos com muita ramificação). Em vez disso,
    calcula, para cada raiz real, o caminho descendente mais longo a
    partir dela via programação dinâmica sobre a ordenação
    topológica (O(V+E) por componente). Isso produz no máximo uma
    cadeia por raiz - uma representação da "linha principal" de
    progressão que nasce ali - em vez de todo caminho possível.
    """

    def __init__(self):

        self.graph: nx.DiGraph = nx.DiGraph()

        self.broken_dependencies: list[tuple[str, str]] = []

        # quest_id -> chapter_id (ou None). Usado só para enriquecer
        # relatórios (ex.: quais capítulos um componente atravessa).
        self._chapter_of: dict[str, str | None] = {}

    # ------------------------------------------------------
    # Construção
    # ------------------------------------------------------

    @classmethod
    def build(cls, questbook: QuestBook) -> "ProgressionGraph":

        instance = cls()

        valid_ids = {
            quest.id
            for quest in questbook.all_quests()
        }

        for quest in questbook.all_quests():

            instance.graph.add_node(quest.id)

            instance._chapter_of[quest.id] = quest.chapter_id

        for quest in questbook.all_quests():

            for dependency in quest.dependencies:

                if dependency not in valid_ids:

                    instance.broken_dependencies.append(
                        (quest.id, dependency)
                    )

                    continue

                # prerequisito -> dependente
                instance.graph.add_edge(dependency, quest.id)

        return instance

    # ------------------------------------------------------
    # Sensores básicos
    # ------------------------------------------------------

    def node_count(self) -> int:

        return self.graph.number_of_nodes()

    def edge_count(self) -> int:

        return self.graph.number_of_edges()

    def get_chapter_of(self, quest_id: str) -> str | None:

        return self._chapter_of.get(quest_id)

    # ------------------------------------------------------
    # Raízes / terminais / isoladas
    # ------------------------------------------------------

    def find_root_quests(self) -> list[str]:
        """
        Quests que iniciam uma cadeia real de progressão: sem
        pré-requisitos, mas com pelo menos uma quest dependendo
        delas. Quests isoladas NÃO contam como raiz - ver
        `find_isolated_quests()`.
        """

        return sorted(
            node
            for node in self.graph.nodes
            if self.graph.in_degree(node) == 0
            and self.graph.out_degree(node) > 0
        )

    def find_terminal_quests(self) -> list[str]:
        """
        Quests que concluem uma cadeia real de progressão: nada
        depende delas, mas elas dependem de algo. Quests isoladas
        NÃO contam como terminal - ver `find_isolated_quests()`.
        """

        return sorted(
            node
            for node in self.graph.nodes
            if self.graph.out_degree(node) == 0
            and self.graph.in_degree(node) > 0
        )

    def find_isolated_quests(self) -> list[str]:
        """
        Quests sem pais e sem filhos - não participam de nenhuma
        cadeia de progressão (ex.: quests informativas/standalone).
        """

        return sorted(
            node
            for node in self.graph.nodes
            if self.graph.in_degree(node) == 0
            and self.graph.out_degree(node) == 0
        )

    # ------------------------------------------------------
    # Relações diretas
    # ------------------------------------------------------

    def get_children(self, quest_id: str) -> list[str]:

        if quest_id not in self.graph:

            return []

        return sorted(self.graph.successors(quest_id))

    def get_parents(self, quest_id: str) -> list[str]:

        if quest_id not in self.graph:

            return []

        return sorted(self.graph.predecessors(quest_id))

    # ------------------------------------------------------
    # Fechos transitivos
    # ------------------------------------------------------

    def get_ancestors(self, quest_id: str) -> set[str]:

        if quest_id not in self.graph:

            return set()

        return nx.ancestors(self.graph, quest_id)

    def get_descendants(self, quest_id: str) -> set[str]:

        if quest_id not in self.graph:

            return set()

        return nx.descendants(self.graph, quest_id)

    # ------------------------------------------------------
    # Componentes desconectados
    # ------------------------------------------------------

    def find_disconnected_components(self) -> list[list[str]]:
        """
        Mantido por compatibilidade: retorna apenas listas de IDs de
        quest por componente. Para informação enriquecida (tamanho,
        capítulos, se é isolado, se é uma progressão independente),
        veja `ProgressionAnalyzer` / `ComponentInfo`.
        """

        components = [
            sorted(component)
            for component in nx.weakly_connected_components(self.graph)
        ]

        components.sort(key=lambda c: (len(c), c))

        return components

    # ------------------------------------------------------
    # Ciclos
    # ------------------------------------------------------

    def detect_cycles(self) -> list[list[str]]:

        return [
            sorted(cycle)
            for cycle in nx.simple_cycles(self.graph)
        ]

    def is_acyclic(self) -> bool:

        return nx.is_directed_acyclic_graph(self.graph)

    # ------------------------------------------------------
    # Alcançabilidade
    # ------------------------------------------------------

    def find_unreachable_quests(self) -> list[str]:
        """
        Quests que não podem ser alcançadas a partir de nenhuma
        raiz real. Quests isoladas são excluídas deste cálculo -
        elas já são reportadas como categoria própria e não
        representam uma falha de alcançabilidade dentro de uma
        cadeia.
        """

        if not self.is_acyclic():

            # "Alcançável a partir de uma raiz" é ambíguo na presença
            # de ciclos (um ciclo sem nenhuma raiz apontando para ele
            # já é reportado como componente desconectado / ciclo).
            # Em vez de produzir uma resposta parcial e enganosa,
            # este sensor retorna vazio nesse cenário.

            return []

        roots = self.find_root_quests()

        isolated = set(self.find_isolated_quests())

        reachable: set[str] = set(roots) | isolated

        for root in roots:

            reachable.update(
                nx.descendants(self.graph, root)
            )

        return sorted(
            node
            for node in self.graph.nodes
            if node not in reachable
        )

    # ------------------------------------------------------
    # Profundidade
    # ------------------------------------------------------

    def depth_of(self, quest_id: str) -> int:

        depths = self._compute_depths()

        return depths.get(quest_id, -1)

    def _compute_depths(self) -> dict[str, int]:

        if not self.is_acyclic():

            # Nós em ciclos não têm profundidade bem definida em uma
            # ordenação topológica - são excluídos do cálculo.

            acyclic_nodes = set(self.graph.nodes) - {
                node
                for cycle in nx.simple_cycles(self.graph)
                for node in cycle
            }

            subgraph = self.graph.subgraph(acyclic_nodes)

        else:

            subgraph = self.graph

        depths: dict[str, int] = {}

        for node in nx.topological_sort(subgraph):

            parents = list(subgraph.predecessors(node))

            if not parents:

                depths[node] = 0

            else:

                depths[node] = 1 + max(
                    depths[parent]
                    for parent in parents
                )

        return depths

    def max_depth(self) -> int:

        depths = self._compute_depths()

        if not depths:

            return 0

        return max(depths.values())

    def average_depth(self) -> float:

        depths = self._compute_depths()

        if not depths:

            return 0.0

        return sum(depths.values()) / len(depths)

    # ------------------------------------------------------
    # Cadeias de progressão
    #
    # v0.8.1: substituído o antigo `all_simple_paths` (enumeração
    # exaustiva de todo caminho raiz->terminal, exponencial em
    # grafos ramificados) por uma abordagem baseada em programação
    # dinâmica sobre a ordenação topológica: para cada raiz real,
    # computa-se O(1) (após pré-cálculo O(V+E) por componente) o
    # caminho descendente mais longo que nasce ali. Isso modela "a
    # linha principal de progressão de cada início de cadeia", sem
    # enumerar todo desvio/ramificação possível.
    # ------------------------------------------------------

    def _longest_downstream_paths(
        self,
        subgraph: nx.DiGraph
    ) -> dict[str, list[str]]:
        """
        Para cada nó do subgrafo (acíclico), retorna o caminho mais
        longo que começa nele e desce até um nó terminal do
        subgrafo. Calculado em uma única passada em ordem topológica
        reversa (programação dinâmica), O(V+E).
        """

        order = list(nx.topological_sort(subgraph))

        best: dict[str, list[str]] = {}

        for node in reversed(order):

            successors = list(subgraph.successors(node))

            if not successors:

                best[node] = [node]

                continue

            best_successor = max(
                successors,
                key=lambda successor: len(best[successor])
            )

            best[node] = [node] + best[best_successor]

        return best

    def find_chains(self) -> list[list[str]]:
        """
        Retorna, para cada raiz real de cada componente acíclico, o
        caminho descendente mais longo que nasce ali - uma cadeia
        representativa da progressão principal daquele ponto de
        partida. Não enumera todos os caminhos possíveis.

        Componentes cíclicos são ignorados aqui (o ciclo já é
        reportado por `detect_cycles()`), em vez de abortar o
        cálculo de cadeias do questbook inteiro.
        """

        if self.node_count() == 0:

            return []

        chains: list[list[str]] = []

        for component_nodes in nx.weakly_connected_components(self.graph):

            if len(component_nodes) < 2:

                # Quest isolada - não forma cadeia.
                continue

            subgraph = self.graph.subgraph(component_nodes)

            if not nx.is_directed_acyclic_graph(subgraph):

                continue

            longest_paths = self._longest_downstream_paths(subgraph)

            roots_in_component = [
                node
                for node in component_nodes
                if subgraph.in_degree(node) == 0
                and subgraph.out_degree(node) > 0
            ]

            for root in roots_in_component:

                chains.append(longest_paths[root])

        # Remove duplicatas exatas (pode acontecer se dois "roots"
        # calculados coincidirem em cenários degenerados) mantendo
        # ordem determinística.
        seen: set[tuple[str, ...]] = set()

        unique_chains: list[list[str]] = []

        for chain in sorted(chains, key=lambda c: (-len(c), c)):

            key = tuple(chain)

            if key in seen:

                continue

            seen.add(key)

            unique_chains.append(chain)

        return unique_chains

    def longest_chain(self) -> list[str]:

        chains = self.find_chains()

        if not chains:

            return []

        return chains[0]