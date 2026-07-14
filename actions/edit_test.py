from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.analysis import QuestbookAnalyzer
from core.editor import QuestbookEditor
from core.profile_utils import resolve_profiles



def edit_test(
    folder: str
):

    print("Carregando questbook...\n")


    parser = QuestbookParser()

    profiles, loose_entries = resolve_profiles(parser, Path(folder))

    if loose_entries:

        print(
            "Arquivos/pastas soltos na raiz (ignorados por este "
            f"comando de desenvolvimento): {[e.name for e in loose_entries]}"
        )

    if len(profiles) > 1:

        print(
            f"Múltiplos perfis detectados ({[p.name for p in profiles]}); "
            "edit-test é um comando de desenvolvimento e roda só sobre "
            f"o primeiro: {profiles[0].name}"
        )

    profile = profiles[0]

    if profile.type != "ftbquests":

        raise Exception(
            "Edit test suporta apenas FTB Quests atualmente."
        )


    questbook = FTBQuestsParser().parse(
        profile.path
    )


    QuestbookAnalyzer().analyze(
        questbook
    )


    print("Questbook carregado:")
    print(
        f"Nome: {questbook.name}"
    )

    print()

    print("Antes:")
    print(
        f"Capítulos: {len(questbook.chapters)}"
    )

    print(
        f"Quests: {questbook.total_quests()}"
    )

    print(
        f"Quest Index: {len(questbook.quest_index)}"
    )


    print(
        "\nExecutando teste do Editor...\n"
    )


    editor = QuestbookEditor(
        questbook
    )


    removed = editor.remove_empty_chapters()


    print(
        f"Capítulos vazios removidos: {removed}"
    )


    print()


    print("Depois:")

    print(
        f"Capítulos: {len(questbook.chapters)}"
    )

    print(
        f"Quests: {questbook.total_quests()}"
    )

    print(
        f"Quest Index: {len(questbook.quest_index)}"
    )


    print(
        "\nEditor funcionando corretamente."
    )