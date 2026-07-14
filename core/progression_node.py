from __future__ import annotations

from dataclasses import dataclass, field


# ==========================================================
# ProgressionNode
# ==========================================================

@dataclass
class ProgressionNode:
    """
    Lightweight wrapper around a Quest that exposes progression-graph
    metadata (parents, children, depth, in/out-degree, cluster
    membership) without duplicating any Quest data.

    Never mutates the Quest it refers to (only stores its id).
    Always built from a ProgressionGraph - never recomputes graph
    traversals on its own, so it stays consistent with
    ProgressionAnalyzer/ProgressionGraph sensors.

    cluster_id is optional and left as None until a
    ProgressionClusterBuilder assigns the node to a cluster.
    """

    quest_id: str

    chapter_id: str | None = None

    parents: list[str] = field(default_factory=list)

    children: list[str] = field(default_factory=list)

    depth: int = -1

    in_degree: int = 0

    out_degree: int = 0

    cluster_id: str | None = None

    # ------------------------------------------------------
    # Sensores
    # ------------------------------------------------------

    def is_root(self) -> bool:

        return self.in_degree == 0 and self.out_degree > 0

    def is_terminal(self) -> bool:

        return self.out_degree == 0 and self.in_degree > 0

    def is_isolated(self) -> bool:

        return self.in_degree == 0 and self.out_degree == 0

    # ------------------------------------------------------
    # Export
    # ------------------------------------------------------

    def to_dict(self) -> dict:

        return {
            "quest_id": self.quest_id,
            "chapter_id": self.chapter_id,
            "parents": self.parents,
            "children": self.children,
            "depth": self.depth,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "cluster_id": self.cluster_id,
        }


# ==========================================================
# ProgressionNodeBuilder
# ==========================================================

class ProgressionNodeBuilder:
    """
    Builds ProgressionNode instances from a ProgressionGraph.

    Depths are computed once via the graph's existing cached
    traversal (`_compute_depths`, the same routine backing
    `depth_of()`/`max_depth()`) instead of once per node - O(V+E)
    total for the whole questbook, matching the graph's own
    performance characteristics instead of adding a new one.

    Never edits the ProgressionGraph or QuestBook. Read-only, like
    every other analysis component in this project.
    """

    @classmethod
    def build_all(cls, graph) -> dict[str, ProgressionNode]:

        depths = graph._compute_depths()

        nodes: dict[str, ProgressionNode] = {}

        for quest_id in graph.graph.nodes:

            nodes[quest_id] = ProgressionNode(
                quest_id=quest_id,
                chapter_id=graph.get_chapter_of(quest_id),
                parents=graph.get_parents(quest_id),
                children=graph.get_children(quest_id),
                depth=depths.get(quest_id, -1),
                in_degree=graph.graph.in_degree(quest_id),
                out_degree=graph.graph.out_degree(quest_id),
            )

        return nodes