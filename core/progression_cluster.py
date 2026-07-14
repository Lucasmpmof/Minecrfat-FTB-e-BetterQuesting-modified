from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from core.progression_graph import ProgressionGraph
from core.progression_node import ProgressionNode, ProgressionNodeBuilder


# ==========================================================
# ProgressionCluster
# ==========================================================

@dataclass
class ProgressionCluster:
    """
    A group of quests that form a cohesive sub-progression, as found
    by Louvain community detection over the progression graph.

    Works internally with ProgressionNodes (never raw quest ids
    alone), so every cluster carries its own progression metadata
    (depth, parents/children, degree) instead of forcing consumers
    to look each quest back up in the graph.
    """

    id: str

    node_ids: list[str] = field(default_factory=list)

    nodes: dict[str, ProgressionNode] = field(default_factory=dict)

    # Coesão estrutural do cluster (0..1): proporção de arestas que
    # ficam contidas dentro do próprio cluster, em vez de cruzar
    # para outro. Serve como um score de confiança de que o cluster
    # representa mesmo uma unidade de progressão coesa.
    confidence: float = 0.0

    # Densidade do subgrafo interno do cluster (arestas reais /
    # arestas possíveis).
    density: float = 0.0

    # Grau médio de saída dentro do cluster.
    average_branching_factor: float = 0.0

    # Quests com alto fan-out dentro do cluster (múltiplos caminhos
    # nascem delas).
    hub_nodes: list[str] = field(default_factory=list)

    # Quests com alto fan-in dentro do cluster (múltiplos caminhos
    # convergem nelas - possíveis gates de progressão).
    bottleneck_nodes: list[str] = field(default_factory=list)

    def size(self) -> int:

        return len(self.node_ids)

    def to_dict(self) -> dict:

        return {
            "id": self.id,
            "size": self.size(),
            "quest_ids": self.node_ids,
            "confidence": self.confidence,
            "density": self.density,
            "average_branching_factor": self.average_branching_factor,
            "hub_nodes": self.hub_nodes,
            "bottleneck_nodes": self.bottleneck_nodes,
        }


# ==========================================================
# ProgressionClusterBuilder
# ==========================================================

class ProgressionClusterBuilder:
    """
    Groups quests into ProgressionClusters using Louvain community
    detection (unchanged - `networkx.algorithms.community.
    louvain_communities`) over the progression graph.

    Louvain modularity is only defined over undirected graphs, so
    the directed ProgressionGraph is converted to undirected only
    for the community-detection step itself; every metric computed
    afterwards (density, branching factor, hub/bottleneck detection)
    uses the original directed subgraph of each cluster, so direction
    is never lost from the metrics that matter for gameplay.

    Never edits the ProgressionGraph or QuestBook. Read-only.
    """

    HUB_THRESHOLD = 3

    BOTTLENECK_THRESHOLD = 3

    @classmethod
    def build(cls, graph: ProgressionGraph) -> list[ProgressionCluster]:

        if graph.node_count() == 0:

            return []

        all_nodes = ProgressionNodeBuilder.build_all(graph)

        undirected = graph.graph.to_undirected()

        communities = nx.algorithms.community.louvain_communities(
            undirected,
            seed=0,
        )

        # Ordem determinística: maiores clusters primeiro; empate
        # resolvido pelo menor quest_id do grupo.
        ordered = sorted(
            communities,
            key=lambda community: (-len(community), min(community)),
        )

        clusters: list[ProgressionCluster] = []

        for index, community in enumerate(ordered):

            cluster = cls._build_cluster(
                cluster_id=f"cluster_{index}",
                node_ids=sorted(community),
                all_nodes=all_nodes,
                graph=graph,
            )

            clusters.append(cluster)

        for cluster in clusters:

            for node_id in cluster.node_ids:

                cluster.nodes[node_id].cluster_id = cluster.id

        return clusters

    @classmethod
    def _build_cluster(
        cls,
        cluster_id: str,
        node_ids: list[str],
        all_nodes: dict[str, ProgressionNode],
        graph: ProgressionGraph,
    ) -> ProgressionCluster:

        subgraph = graph.graph.subgraph(node_ids)

        possible_edges = len(node_ids) * (len(node_ids) - 1)

        density = (
            subgraph.number_of_edges() / possible_edges
            if possible_edges > 0 else 0.0
        )

        out_degrees = [
            subgraph.out_degree(node_id)
            for node_id in node_ids
        ]

        average_branching = (
            sum(out_degrees) / len(out_degrees)
            if out_degrees else 0.0
        )

        hub_nodes = sorted(
            node_id
            for node_id in node_ids
            if subgraph.out_degree(node_id) >= cls.HUB_THRESHOLD
        )

        bottleneck_nodes = sorted(
            node_id
            for node_id in node_ids
            if subgraph.in_degree(node_id) >= cls.BOTTLENECK_THRESHOLD
        )

        internal_edges = subgraph.number_of_edges()

        touching_edges = sum(
            graph.graph.in_degree(node_id) + graph.graph.out_degree(node_id)
            for node_id in node_ids
        )

        # Cada aresta interna é contada duas vezes em touching_edges
        # (uma pela origem, uma pelo destino) - por isso o fator 2
        # no numerador, para que confidence == 1.0 quando o cluster
        # é totalmente isolado do resto do grafo.
        confidence = (
            (2 * internal_edges) / touching_edges
            if touching_edges > 0 else 1.0
        )

        nodes = {
            node_id: all_nodes[node_id]
            for node_id in node_ids
        }

        return ProgressionCluster(
            id=cluster_id,
            node_ids=node_ids,
            nodes=nodes,
            confidence=round(confidence, 4),
            density=round(density, 4),
            average_branching_factor=round(average_branching, 4),
            hub_nodes=hub_nodes,
            bottleneck_nodes=bottleneck_nodes,
        )