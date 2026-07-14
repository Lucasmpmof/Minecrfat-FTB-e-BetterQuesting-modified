from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.validator import QuestbookValidator
from core.profile_utils import resolve_profiles




def validate(folder, json_output=None):

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

            raise Exception(
                "Formato não suportado"
            )

        ftb = FTBQuestsParser()

        questbook = ftb.parse(
            profile.path
        )

        validator = QuestbookValidator(
            questbook,
            profile.path
        )

        report = validator.validate()

        report.summary()

        if json_output:

            profile_json_output = (
                _per_profile_path(json_output, profile.name)
                if multi else json_output
            )

            report.save_json(
                profile_json_output
            )

            print(
                f"JSON salvo em: {profile_json_output}"
            )


def _per_profile_path(path_str, profile_name):

    path = Path(path_str)

    return str(path.with_name(f"{path.stem}_{profile_name}{path.suffix}"))