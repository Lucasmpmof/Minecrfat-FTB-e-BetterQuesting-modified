from __future__ import annotations

import json
from pathlib import Path

from core.models import QuestBook
from core.progression_graph import ProgressionGraph
from core.progression_cluster import ProgressionClusterBuilder
from core.cluster_graph import ClusterGraph


def build_cluster_export_data(questbook: QuestBook) -> dict:
    """
    Builds the ProgressionCluster set and the ClusterGraph for a
    QuestBook and returns everything needed to inspect them without
    rebuilding the progression graph - a single dict, ready to be
    serialized.

    Read-only: never modifies the QuestBook.
    """

    graph = ProgressionGraph.build(questbook)

    clusters = ProgressionClusterBuilder.build(graph)

    cluster_graph = ClusterGraph.build(graph, clusters)

    return {
        "total_quests": questbook.total_quests(),
        "total_clusters": len(clusters),
        "clusters": [cluster.to_dict() for cluster in clusters],
        "cluster_graph": cluster_graph.to_dict(),
    }


def export_clusters(questbook: QuestBook, output: str | Path) -> Path:
    """
    Same as `build_cluster_export_data`, but writes the result
    straight to a JSON file. This is what `progression
    --export-clusters` uses.
    """

    data = build_cluster_export_data(questbook)

    output = Path(output)

    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf8") as file:

        json.dump(data, file, indent=2, ensure_ascii=False)

    return output