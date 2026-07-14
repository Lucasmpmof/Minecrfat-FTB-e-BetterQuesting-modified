from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.progression_analyzer import ProgressionAnalyzer
from core.cluster_export import export_clusters
from core.profile_utils import resolve_profiles


def progression(folder, export_clusters_file=None):

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

        if export_clusters_file:

            profile_export_file = (
                _per_profile_path(export_clusters_file, profile.name)
                if multi else export_clusters_file
            )

            export_clusters(questbook, profile_export_file)

            print(f"Clusters exportados em: {profile_export_file}")


def _per_profile_path(path_str, profile_name):

    path = Path(path_str)

    return str(path.with_name(f"{path.stem}_{profile_name}{path.suffix}"))