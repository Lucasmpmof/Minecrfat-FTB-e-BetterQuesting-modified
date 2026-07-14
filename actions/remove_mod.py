from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.analysis import QuestbookAnalyzer
from core.editor import QuestbookEditor
from core.writer import QuestbookWriter
from core.edit_context import EditContext
from core.backup import BackupManager
from core.profile_utils import (
    resolve_profiles,
    output_path_for,
    copy_loose_root_entries,
)



def remove_mod(
    folder,
    mod: str,
    output,
    dry_run=False
):


    folder = Path(folder)

    output = Path(output)



    print("Carregando questbook...\n")



    # Detecta todos os perfis (challenge/classic/etc., se houver)

    parser = QuestbookParser()

    profiles, loose_entries = resolve_profiles(parser, folder)

    multi = len(profiles) > 1

    for profile in profiles:

        if profile.type != "ftbquests":

            raise Exception(
                "Apenas FTB Quests suportado atualmente."
            )

    if not dry_run:

        print()

        print("Criando backup...")

        backup = BackupManager()

        backup_path = backup.create_backup(folder)

        print(f"Backup criado em: {backup_path}")

        if loose_entries:

            copy_loose_root_entries(loose_entries, output)

            print(
                "Arquivos/pastas soltos na raiz preservados: "
                f"{[e.name for e in loose_entries]}"
            )

    for profile in profiles:

        if multi:

            print()
            print("#" * 70)
            print(f"# Perfil: {profile.name}")
            print("#" * 70)

        _remove_mod_from_profile(
            profile,
            mod,
            output_path_for(output, profile, multi),
            dry_run,
        )


def _remove_mod_from_profile(
    profile,
    mod: str,
    output: Path,
    dry_run: bool,
):

    path = profile.path

    # Carrega

    loader = FTBQuestsParser()

    questbook = loader.parse(
        path
    )

    if questbook.malformed_files:

        print()

        print(
            f"AVISO: {questbook.malformed_files} arquivo(s) de quest "
            "não puderam ser interpretados e serão preservados como "
            "estão (sem edição):"
        )

        for warning in questbook.warnings:

            print(f" - {warning}")

    analyzer = QuestbookAnalyzer()

    analyzer.analyze(
        questbook
    )



    print(
        f"Questbook carregado:"
    )

    print(
        f"Nome: {questbook.name}"
    )



    print(
        f"Quests antes: {questbook.total_quests()}"
    )



    print(
        f"\nMod alvo:"
    )

    print(
        mod
    )



    # --------------------------------------------------
    # Localizar quests
    # --------------------------------------------------

    affected = [

        quest

        for quest in questbook.all_quests()

        if quest.mod.lower() == mod.lower()

    ]



    if not affected:

        print(
            "\nNenhuma quest encontrada."
        )

        return



    affected_ids = {

        quest.id

        for quest in affected

    }



    affected_chapters = {

        quest.chapter_id

        for quest in affected

        if quest.chapter_id

    }



    print()

    print(
        "Encontrado:"
    )

    print(
        f"Quests: {len(affected)}"
    )

    print(
        f"Capítulos afetados: {len(affected_chapters)}"
    )
    if dry_run:

        print()

        print(
            "Modo simulação ativado."
        )

        print(
            "Nenhuma alteração será feita."
        )

        return



    # --------------------------------------------------
    # Editor
    # --------------------------------------------------

    context = EditContext()


    context.add_removed_mod(
        mod
    )


    for quest in affected:

        context.add_removed_quest(
            quest.id
        )



    editor = QuestbookEditor(
        questbook
    )



    removed_dependencies = (

        editor.remove_quests(

            affected_ids

        )

    )



    context.removed_dependencies = (

        removed_dependencies

    )



    analyzer.analyze(
        questbook
    )



    print()

    print(
        "Resultado:"
    )

    print(
        f"Depois: {questbook.total_quests()} quests"
    )



    # --------------------------------------------------
    # Writer
    # --------------------------------------------------

    print()

    print(
        "Gerando questbook..."
    )



    writer = QuestbookWriter()



    writer.write(

        questbook,

        output,

        context

    )



    print()

    print(
        f"Questbook salvo em: {output}"
    )