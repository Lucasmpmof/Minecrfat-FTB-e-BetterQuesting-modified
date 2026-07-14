from __future__ import annotations

import networkx as nx

from core.progression_graph import ProgressionGraph
from core.progression_cluster import ProgressionCluster


# ==========================================================
# ClusterGraph
# ==========================================================

class ClusterGraph:
    """
    Cluster -> Cluster dependency graph.

    Built by folding the existing quest-level ProgressionGraph edges
    down to cluster level: every quest-level edge that crosses a
    cluster boundary becomes (or strengthens) a Cluster -> Cluster
    edge, weighted by how many underlying quest dependencies cross
    that boundary. Edges fully contained inside a single cluster are
    not represented here (that's what ProgressionCluster.density
    already covers).

    This graph is the main input for the future Compatibility
    Analyzer and Progression Builder: it lets those components
    reason about "does this cluster depend on that one" without
    re-walking the full quest-level graph.

    Never edits QuestBook, ProgressionGraph or the clusters it is
    built from. Read-only, like every other analysis component in
    this project. Built in a single O(V+E) pass over the existing
    ProgressionGraph edges - no duplicated graph traversal.
    """

    def __init__(self):

        self.graph: nx.DiGraph = nx.DiGraph()

    @classmethod
    def build(
        cls,
        graph: ProgressionGraph,
        clusters: list[ProgressionCluster],
    ) -> "ClusterGraph":

        instance = cls()

        quest_to_cluster = {
            quest_id: cluster.id
            for cluster in clusters
            for quest_id in cluster.node_ids
        }

        for cluster in clusters:

            instance.graph.add_node(
                cluster.id,
                size=cluster.size(),
            )

        for prerequisite, dependent in graph.graph.edges():

            source_cluster = quest_to_cluster.get(prerequisite)

            target_cluster = quest_to_cluster.get(dependent)

            if source_cluster is None or target_cluster is None:

                continue

            if source_cluster == target_cluster:

                continue

            if instance.graph.has_edge(source_cluster, target_cluster):

                instance.graph[source_cluster][target_cluster]["weight"] += 1

            else:

                instance.graph.add_edge(
                    source_cluster,
                    target_cluster,
                    weight=1,
                )

        return instance

    # ------------------------------------------------------
    # Sensores
    # ------------------------------------------------------

    def node_count(self) -> int:

        return self.graph.number_of_nodes()

    def edge_count(self) -> int:

        return self.graph.number_of_edges()

    def get_dependencies(self, cluster_id: str) -> list[str]:

        if cluster_id not in self.graph:

            return []

        return sorted(self.graph.predecessors(cluster_id))

    def get_dependents(self, cluster_id: str) -> list[str]:

        if cluster_id not in self.graph:

            return []

        return sorted(self.graph.successors(cluster_id))

    def is_acyclic(self) -> bool:

        return nx.is_directed_acyclic_graph(self.graph)

    def detect_cycles(self) -> list[list[str]]:

        return [
            sorted(cycle)
            for cycle in nx.simple_cycles(self.graph)
        ]

    # ------------------------------------------------------
    # Export
    # ------------------------------------------------------

    def to_dict(self) -> dict:

        edges = [
            {
                "from": source,
                "to": target,
                "weight": data["weight"],
            }
            for source, target, data in sorted(
                self.graph.edges(data=True),
                key=lambda edge: (edge[0], edge[1]),
            )
        ]

        return {
            "clusters": sorted(self.graph.nodes),
            "edges": edges,
        }