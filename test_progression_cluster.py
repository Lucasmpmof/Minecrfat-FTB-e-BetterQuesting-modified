"""
Teste funcional do milestone "Progression Cluster Refinement".

Cobre:
  - ProgressionNode / ProgressionNodeBuilder
  - ProgressionCluster / ProgressionClusterBuilder (Louvain)
  - ClusterGraph
  - export_clusters (JSON)
"""

import json
import tempfile
from pathlib import Path

from core.models import QuestBook, Chapter, Quest
from core.progression_graph import ProgressionGraph
from core.progression_node import ProgressionNodeBuilder
from core.progression_cluster import ProgressionClusterBuilder
from core.cluster_graph import ClusterGraph
from core.cluster_export import export_clusters, build_cluster_export_data


def build_questbook() -> QuestBook:
    """
    Duas progressões independentes (A1->A2->A3 e B1->B2), mais uma
    quest isolada (C1) - o suficiente para gerar >= 2 clusters
    distintos e testar cruzamento de cluster (se o Louvain os
    mantiver separados, não deve haver nenhuma aresta cross-cluster
    aqui, já que os dois grupos não têm dependências entre si).
    """

    qb = QuestBook(name="test")

    chapter = Chapter(id="ch1", title="Chapter 1")

    chapter.quests = [
        Quest(id="a1", title="a1", chapter_id="ch1"),
        Quest(id="a2", title="a2", chapter_id="ch1", dependencies=["a1"]),
        Quest(id="a3", title="a3", chapter_id="ch1", dependencies=["a2"]),
        Quest(id="b1", title="b1", chapter_id="ch1"),
        Quest(id="b2", title="b2", chapter_id="ch1", dependencies=["b1"]),
        Quest(id="c1", title="c1", chapter_id="ch1"),
    ]

    qb.chapters = [chapter]

    return qb


def run():

    failures = []

    def check(label, actual, expected):
        status = "OK" if actual == expected else "FAIL"
        if status == "FAIL":
            failures.append(label)
        print(f"[{status}] {label}: got={actual!r} expected={expected!r}")

    qb = build_questbook()

    graph = ProgressionGraph.build(qb)

    # ------------------------------------------------------
    # ProgressionNode
    # ------------------------------------------------------

    nodes = ProgressionNodeBuilder.build_all(graph)

    check("node count", len(nodes), 6)

    check("a1 is root", nodes["a1"].is_root(), True)
    check("a3 is terminal", nodes["a3"].is_terminal(), True)
    check("c1 is isolated", nodes["c1"].is_isolated(), True)
    check("a2 depth", nodes["a2"].depth, 1)
    check("a2 parents", nodes["a2"].parents, ["a1"])
    check("a1 children", nodes["a1"].children, ["a2"])
    check("cluster_id starts unset", nodes["a1"].cluster_id, None)

    # ------------------------------------------------------
    # ProgressionCluster
    # ------------------------------------------------------

    clusters = ProgressionClusterBuilder.build(graph)

    check("at least 2 clusters formed", len(clusters) >= 2, True)

    all_clustered_ids = {
        quest_id
        for cluster in clusters
        for quest_id in cluster.node_ids
    }

    check("every quest belongs to exactly one cluster", all_clustered_ids, {"a1", "a2", "a3", "b1", "b2", "c1"})

    # a1/a2/a3 devem terminar no mesmo cluster (progressão conectada)
    a_clusters = {
        cluster.id
        for cluster in clusters
        if {"a1", "a2", "a3"} & set(cluster.node_ids)
    }

    check("a1/a2/a3 share the same cluster region", len(a_clusters) >= 1, True)

    for cluster in clusters:

        check(
            f"{cluster.id} confidence within [0,1]",
            0.0 <= cluster.confidence <= 1.0,
            True,
        )

        check(
            f"{cluster.id} density within [0,1]",
            0.0 <= cluster.density <= 1.0,
            True,
        )

        check(
            f"{cluster.id} nodes tagged with cluster_id",
            all(node.cluster_id == cluster.id for node in cluster.nodes.values()),
            True,
        )

    # ------------------------------------------------------
    # ClusterGraph
    # ------------------------------------------------------

    cluster_graph = ClusterGraph.build(graph, clusters)

    check("cluster graph node count", cluster_graph.node_count(), len(clusters))

    check("cluster graph is acyclic (no cycles in source data)", cluster_graph.is_acyclic(), True)

    # ------------------------------------------------------
    # Export
    # ------------------------------------------------------

    data = build_cluster_export_data(qb)

    check("export total_quests", data["total_quests"], 6)

    check("export total_clusters matches", data["total_clusters"], len(clusters))

    check(
        "export cluster ids match built clusters",
        {c["id"] for c in data["clusters"]},
        {c.id for c in clusters},
    )

    with tempfile.TemporaryDirectory() as tmp:

        output_path = Path(tmp) / "clusters.json"

        export_clusters(qb, output_path)

        check("export file created", output_path.exists(), True)

        with open(output_path, encoding="utf8") as file:
            loaded = json.load(file)

        check("exported JSON matches in-memory data", loaded, data)

    print()
    if failures:
        print(f"FALHAS: {len(failures)}")
        for f in failures:
            print(f" - {f}")
        raise SystemExit(1)
    else:
        print("Todos os testes passaram.")


if __name__ == "__main__":
    run()