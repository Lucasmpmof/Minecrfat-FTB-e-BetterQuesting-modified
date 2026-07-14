from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.validator import QuestbookValidator
from core.backup import BackupManager
from core.optimizer import QuestOptimizer
from core.writer import QuestbookWriter
from core.edit_context import EditContext
from core.profile_utils import (
    resolve_profiles,
    output_path_for,
    copy_loose_root_entries,
)


def clean(folder, output):

    folder = Path(folder)

    output = Path(output)

    print("Iniciando limpeza do questbook...\n")

    # ----------------------------
    # Detectar
    # ----------------------------

    parser = QuestbookParser()

    profiles, loose_entries = resolve_profiles(parser, folder)

    multi = len(profiles) > 1

    for profile in profiles:

        if profile.type != "ftbquests":

            raise Exception("Formato não suportado")

    # ----------------------------
    # Backup (uma vez só, da pasta inteira fornecida)
    # ----------------------------

    print("Criando backup...")

    backup = BackupManager()

    backup.create_backup(folder)

    print("Backup concluído.")

    for profile in profiles:

        if multi:

            print()
            print("#" * 70)
            print(f"# Perfil: {profile.name}")
            print("#" * 70)

        _clean_profile(profile, output_path_for(output, profile, multi))

    if loose_entries:

        copy_loose_root_entries(loose_entries, output)

        print(
            "\nArquivos/pastas soltos na raiz preservados: "
            f"{[e.name for e in loose_entries]}"
        )


def _clean_profile(profile, output):

    # ----------------------------
    # Carregar
    # ----------------------------

    loader = FTBQuestsParser()

    questbook = loader.parse(profile.path)

    if questbook.malformed_files:

        print(
            f"\nAVISO: {questbook.malformed_files} arquivo(s) de quest "
            "não puderam ser interpretados e serão preservados como "
            "estão (sem edição):"
        )

        for warning in questbook.warnings:

            print(f" - {warning}")

    # ----------------------------
    # Validar antes
    # ----------------------------

    validator = QuestbookValidator(questbook, profile.path)

    before = validator.validate()

    before.summary()

    # ----------------------------
    # Otimização
    #
    # v0.6: DependencyCleaner + ChapterCleaner unificados no
    # QuestOptimizer. Remove dependências órfãs e, na sequência,
    # capítulos que tenham ficado vazios por causa disso.
    # ----------------------------

    print("\nOtimizando questbook...")

    optimizer = QuestOptimizer(questbook)

    optimization = optimizer.optimize()

    print()

    print(f"Dependências removidas: {optimization.removed_dependencies}")

    print(f"Capítulos vazios removidos: {len(optimization.removed_chapters)}")

    if optimization.removed_chapters:

        for chapter_id in optimization.removed_chapters:

            print(f" - {chapter_id}")

    # ----------------------------
    # Salvar
    # ----------------------------

    context = EditContext()

    context.removed_dependencies = optimization.removed_dependencies

    context.removed_chapters = set(optimization.removed_chapters)

    writer = QuestbookWriter()

    writer.write(
        questbook,
        output,
        context
    )

    print("\nQuestbook limpo salvo:")

    print(output)
    print()

    print("Validando resultado final...")

    final_loader = FTBQuestsParser()

    final_questbook = final_loader.parse(output)

    final_validator = QuestbookValidator(final_questbook, output)

    final_report = final_validator.validate()

    final_report.summary()