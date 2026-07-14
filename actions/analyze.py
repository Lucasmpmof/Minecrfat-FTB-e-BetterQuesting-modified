import json
from pathlib import Path
from datetime import datetime

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.analysis import QuestbookAnalyzer
from core.profile_utils import resolve_profiles


TOOLKIT_VERSION = "0.3.0"


def build_analysis(questbook, questbook_type):

    chapters = []

    total_mods = {}

    for chapter in questbook.chapters:

        mods = {}

        for quest in chapter.quests:

            mods[quest.mod] = mods.get(quest.mod, 0) + 1

            total_mods[quest.mod] = (
                total_mods.get(quest.mod, 0) + 1
            )

        chapters.append({

            "id": chapter.id,

            "title": chapter.title,

            "quests": chapter.analysis.total_quests,

            "mods": dict(

                sorted(

                    mods.items(),

                    key=lambda x: x[1],

                    reverse=True

                )

            )

        })

    return {

        "metadata": {

            "toolkit_version": TOOLKIT_VERSION,

            "generated_at": datetime.now().isoformat(),

            "questbook_name": questbook.name,

            "questbook_type": questbook_type

        },

        "summary": {

            "chapters": len(questbook.chapters),

            "quests": questbook.total_quests(),

            "mods": len(total_mods)

        },

        "global_mods": dict(

            sorted(

                total_mods.items(),

                key=lambda x: x[1],

                reverse=True

            )

        ),

        "chapter_analysis": chapters

    }


def analyze(folder, output=None):

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

            print("Formato ainda não suportado.")

            continue

        ftb = FTBQuestsParser()

        questbook = ftb.parse(profile.path)

        analyzer = QuestbookAnalyzer()

        analyzer.analyze(questbook)

        report = build_analysis(
            questbook,
            profile.type
        )

        print()

        print("=" * 70)
        print("Questbook Analysis")
        print("=" * 70)

        print()

        print("Toolkit :", TOOLKIT_VERSION)
        print("Questbook :", questbook.name)
        print("Generated :", report["metadata"]["generated_at"])

        print()

        for chapter in report["chapter_analysis"]:

            print("=" * 50)

            print(chapter["title"])

            print(f"Quests : {chapter['quests']}")

            print()

            for mod, amount in chapter["mods"].items():

                print(f"{mod:<30}{amount}")

            print()

        if output:

            profile_output = (
                _per_profile_path(output, profile.name)
                if multi else output
            )

            with open(
                profile_output,
                "w",
                encoding="utf8"
            ) as file:

                json.dump(
                    report,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            print(f"\nRelatório salvo em: {profile_output}")


def _per_profile_path(path_str, profile_name):

    path = Path(path_str)

    return str(path.with_name(f"{path.stem}_{profile_name}{path.suffix}"))