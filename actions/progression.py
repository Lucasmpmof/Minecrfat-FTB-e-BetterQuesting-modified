from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.progression_analyzer import ProgressionAnalyzer
from core.profile_utils import resolve_profiles


def progression(folder):

    folder = Path(folder)

    parser = QuestbookParser()

    profiles, loose_entries = resolve_profiles(parser, folder)

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

        analyzer = ProgressionAnalyzer()

        report = analyzer.analyze(questbook)

        report.summary()