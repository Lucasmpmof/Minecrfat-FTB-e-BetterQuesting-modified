from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.analysis import QuestbookAnalyzer
from core.report import report_to_json
from core.validator import QuestbookValidator
from core.profile_utils import resolve_profiles
#SCAN.py

def print_summary(questbook):

    print()
    print("=" * 70)
    print("Questbook Toolkit")
    print("=" * 70)
    print()

    print(f"Questbook : {questbook.name}")
    print(f"Chapters  : {len(questbook.chapters)}")
    print(f"Quests    : {questbook.total_quests()}")
    print(f"Mods      : {len(questbook.mod_index)}")
    print()

    print("Top 10 Mods")
    print("-" * 70)

    mods = sorted(
        questbook.mod_index.values(),
        key=lambda m: m.quests,
        reverse=True
    )

    for mod in mods[:10]:

        print(
            f"{mod.name:<30} "
            f"{mod.quests:>5} quests   "
            f"{len(mod.chapters):>3} chapters"
        )

    print()


def scan(
    folder,
    debug=False,
    report_file=None,
    show_validation=True,
):

    parser = QuestbookParser()

    profiles, loose_entries = resolve_profiles(parser, Path(folder))

    multi = len(profiles) > 1

    if loose_entries:

        print(
            "Arquivos/pastas soltos na raiz (não pertencem a nenhum "
            f"perfil, preservados): {[e.name for e in loose_entries]}"
        )

    for profile in profiles:

        if multi:

            print()
            print("#" * 70)
            print(f"# Perfil: {profile.name}")
            print("#" * 70)

        if profile.type != "ftbquests":

            print(
                f"Formato '{profile.type}' ainda não suportado."
            )

            continue

        ftb = FTBQuestsParser()

        questbook = ftb.parse(profile.path)

        analyzer = QuestbookAnalyzer()

        analyzer.analyze(questbook)

        validator = QuestbookValidator(
            questbook,
            profile.path
        )

        validation = validator.validate()

        print_summary(questbook)

        print(
            "Validation :",
            "PASS" if validation.to_dict()["status"] else "FAIL"
        )

        print()

        json_report = report_to_json(questbook)

        print(json_report)

        if report_file:

            profile_report_file = (
                _per_profile_path(report_file, profile.name)
                if multi else report_file
            )

            with open(
                profile_report_file,
                "w",
                encoding="utf8"
            ) as f:

                f.write(json_report)

            print()
            print(f"Relatório salvo em: {profile_report_file}")


def _per_profile_path(path_str, profile_name):

    path = Path(path_str)

    return str(path.with_name(f"{path.stem}_{profile_name}{path.suffix}"))