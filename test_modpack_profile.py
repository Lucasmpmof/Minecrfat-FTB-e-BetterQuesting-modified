"""
Teste funcional do ModpackProfile v0.6 final.

Cobre:
  - sensores (detect_missing_mods, estimate_removed_quests,
    estimate_removed_chapters, estimate_dependency_cleanup)
  - dry-run vs execução real (mesmo resultado, exceto escrita)
  - relatório detalhado por mod ausente
  - geração de JSON com todos os campos exigidos
"""

import copy

from core.models import QuestBook, Chapter, Quest
from core.modpack_profile import ModpackProfile


REQUIRED_JSON_FIELDS = {
    "mods_installed",
    "mods_used",
    "missing_mods",
    "removed_quests",
    "removed_dependencies",
    "removed_chapters",
    "affected_chapters",
    "dry_run",
    "timestamp",
}


class FakeScanner:
    """Substitui o InstalledModsScanner para não depender de jars reais."""

    def __init__(self, installed: set[str]):
        self.installed = installed

    def scan(self, mods_folder):
        return set(self.installed)


def build_questbook() -> QuestBook:
    qb = QuestBook(name="test")

    chapter_a = Chapter(id="chapter_a", title="A")
    chapter_a.quests.append(
        Quest(id="quest_1", title="q1", chapter_id="chapter_a", mods={"thermal"})
    )
    chapter_a.quests.append(
        Quest(
            id="quest_2",
            title="q2",
            chapter_id="chapter_a",
            mods=set(),
            dependencies=["quest_1"],
        )
    )

    chapter_b = Chapter(id="chapter_b", title="B (so botania)")
    chapter_b.quests.append(
        Quest(id="quest_3", title="q3", chapter_id="chapter_b", mods={"botania"})
    )

    qb.chapters = [chapter_a, chapter_b]
    return qb


def run():
    failures = []

    def check(label, actual, expected):
        status = "OK" if actual == expected else "FAIL"
        if status == "FAIL":
            failures.append(label)
        print(f"[{status}] {label}: got={actual!r} expected={expected!r}")

    # ------------------------------------------------------
    # Setup: thermal instalado, botania ausente
    # ------------------------------------------------------
    qb = build_questbook()
    profile = ModpackProfile(qb, mods_folder="/fake/mods")
    profile.scanner = FakeScanner({"thermal"})

    # ------------------------------------------------------
    # Sensores (somente leitura)
    # ------------------------------------------------------
    missing = profile.detect_missing_mods()
    check("detect_missing_mods", missing, {"botania"})

    check("used_mods", profile.used_mods(), {"thermal", "botania"})

    removed_quests = profile.estimate_removed_quests(missing)
    check("estimate_removed_quests", removed_quests, {"quest_3"})

    removed_chapters = profile.estimate_removed_chapters(missing)
    check("estimate_removed_chapters", removed_chapters, {"chapter_b"})

    dep_cleanup = profile.estimate_dependency_cleanup(missing)
    check("estimate_dependency_cleanup", dep_cleanup, 0)

    # Sensores não devem ter alterado o QuestBook original
    check("questbook intacto apos sensores (chapters)", len(qb.chapters), 2)
    check(
        "questbook intacto apos sensores (quest_3 presente)",
        any(q.id == "quest_3" for q in qb.all_quests()),
        True,
    )

    detail = profile.missing_mods_detail(missing)
    check("missing_mods_detail: 1 mod ausente", len(detail), 1)
    check("missing_mods_detail: mod correto", detail[0].mod, "botania")
    check("missing_mods_detail: quests afetadas", detail[0].affected_quests, 1)
    check("missing_mods_detail: capitulos afetados", detail[0].affected_chapters, 1)
    check("missing_mods_detail: quest_ids", detail[0].quest_ids, ["quest_3"])

    # ------------------------------------------------------
    # Dry-run: mesma logica, QuestBook original intacto
    # ------------------------------------------------------
    qb_snapshot = copy.deepcopy(qb)

    dry_report = profile.apply(dry_run=True)

    check("dry_run flag no relatorio", dry_report.dry_run, True)
    check("dry-run: removed_quests", dry_report.removed_quests, ["quest_3"])
    check("dry-run: removed_chapters", dry_report.removed_chapters, ["chapter_b"])
    check("dry-run: affected_chapters", dry_report.affected_chapters, ["chapter_b"])
    check("dry-run: removed_dependencies", dry_report.removed_dependencies, 0)
    check("dry-run: mods_installed", sorted(dry_report.mods_installed), ["thermal"])
    check("dry-run: mods_used", sorted(dry_report.mods_used), ["botania", "thermal"])

    # QuestBook original não deve ter mudado em nada
    check("questbook nao mutou apos dry-run (n capitulos)", len(qb.chapters), len(qb_snapshot.chapters))
    check(
        "questbook nao mutou apos dry-run (quest_3 ainda existe)",
        any(q.id == "quest_3" for q in qb.all_quests()),
        True,
    )
    check(
        "questbook nao mutou apos dry-run (quest_2 dependencies)",
        qb.get_chapter("chapter_a").quests[1].dependencies,
        ["quest_1"],
    )

    # ------------------------------------------------------
    # Execucao real: deve produzir o MESMO resultado do dry-run,
    # mas mutando de fato o questbook
    # ------------------------------------------------------
    real_report = profile.apply(dry_run=False)

    check("real: dry_run flag", real_report.dry_run, False)
    check("real: removed_quests == dry-run", real_report.removed_quests, dry_report.removed_quests)
    check("real: removed_chapters == dry-run", real_report.removed_chapters, dry_report.removed_chapters)
    check("real: affected_chapters == dry-run", real_report.affected_chapters, dry_report.affected_chapters)
    check(
        "real: removed_dependencies == dry-run",
        real_report.removed_dependencies,
        dry_report.removed_dependencies,
    )

    # Agora sim o questbook deve ter mudado
    check("questbook mutou apos execucao real (n capitulos)", len(qb.chapters), 1)
    check(
        "questbook mutou apos execucao real (quest_3 removida)",
        any(q.id == "quest_3" for q in qb.all_quests()),
        False,
    )

    # ------------------------------------------------------
    # JSON: todos os campos exigidos presentes
    # ------------------------------------------------------
    as_dict = real_report.to_dict()
    missing_fields = REQUIRED_JSON_FIELDS - set(as_dict.keys())
    check("JSON contem todos os campos exigidos", missing_fields, set())

    # ------------------------------------------------------
    # Caso sem mods ausentes: relatorio vazio, nada removido
    # ------------------------------------------------------
    qb2 = build_questbook()
    profile2 = ModpackProfile(qb2, mods_folder="/fake/mods")
    profile2.scanner = FakeScanner({"thermal", "botania"})

    report_ok = profile2.apply(dry_run=True)
    check("sem mods ausentes: missing_mods vazio", report_ok.missing_mods, [])
    check("sem mods ausentes: removed_quests vazio", report_ok.removed_quests, [])
    check("sem mods ausentes: questbook intacto", len(qb2.chapters), 2)

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
