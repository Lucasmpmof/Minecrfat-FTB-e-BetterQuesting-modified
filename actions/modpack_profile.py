import json
from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.analysis import QuestbookAnalyzer
from core.modpack_profile import ModpackProfile
from core.writer import QuestbookWriter
from core.edit_context import EditContext
from core.backup import BackupManager
from core.validator import QuestbookValidator
from core.profile_utils import (
    resolve_profiles,
    output_path_for,
    copy_loose_root_entries,
)


def modpack_profile(
    folder,
    mods_folder,
    output=None,
    dry_run: bool = False,
    report_file=None,
):

    folder = Path(folder)

    mods_folder = Path(mods_folder)

    print("Carregando questbook...\n")

    # ----------------------------
    # Detectar todos os perfis (challenge/classic/etc., se houver)
    # ----------------------------

    parser = QuestbookParser()

    profiles, loose_entries = resolve_profiles(parser, folder)

    multi = len(profiles) > 1

    for profile in profiles:

        if profile.type != "ftbquests":

            raise Exception(
                "Apenas FTB Quests suportado atualmente."
            )

    if multi:

        print(
            f"Múltiplos perfis detectados: {[p.name for p in profiles]}"
        )

    if loose_entries:

        print(
            "Arquivos/pastas soltos na raiz (não pertencem a nenhum "
            f"perfil, preservados): {[e.name for e in loose_entries]}"
        )

    # O backup precisa acontecer só uma vez (cobre a pasta inteira,
    # incluindo todos os perfis) e só se algum perfil for de fato
    # escrever algo em disco - fica marcado como "feito" na primeira
    # vez que algum perfil precisar.
    backup_state = {"done": dry_run or output is None}

    reports = []

    for profile in profiles:

        if multi:

            print()
            print("#" * 70)
            print(f"# Perfil: {profile.name}")
            print("#" * 70)

        profile_output = (
            output_path_for(Path(output), profile, multi)
            if output else None
        )

        profile_report_file = (
            _per_profile_path(report_file, profile.name)
            if (report_file and multi) else report_file
        )

        report = _modpack_profile_for(
            profile=profile,
            root_folder=folder,
            mods_folder=mods_folder,
            output=profile_output,
            dry_run=dry_run,
            report_file=profile_report_file,
            backup_state=backup_state,
        )

        reports.append(report)

    if backup_state["done"] and not (dry_run or output is None) and loose_entries:

        copy_loose_root_entries(loose_entries, Path(output))

        print(
            "\nArquivos/pastas soltos na raiz preservados: "
            f"{[e.name for e in loose_entries]}"
        )

    return reports


def _modpack_profile_for(
    profile,
    root_folder: Path,
    mods_folder: Path,
    output,
    dry_run: bool,
    report_file,
    backup_state: dict,
):

    path = profile.path

    # ----------------------------
    # Carregar
    # ----------------------------

    loader = FTBQuestsParser()

    questbook = loader.parse(path)

    if questbook.malformed_files:

        print(
            f"\nAVISO: {questbook.malformed_files} arquivo(s) de quest "
            "não puderam ser interpretados e serão preservados como "
            "estão (sem edição):"
        )

        for warning in questbook.warnings:

            print(f" - {warning}")

    QuestbookAnalyzer().analyze(questbook)

    print(f"Questbook: {questbook.name}")

    print(f"Quests antes: {questbook.total_quests()}")

    # ----------------------------
    # Calcular / Aplicar (ou simular)
    # ----------------------------
    #
    # apply() sempre executa a lógica completa (Editor + Optimizer).
    # Em dry_run=True, ela roda sobre uma cópia do QuestBook: nada
    # aqui é escrito em disco nem o QuestBook original é alterado.
    #

    print("\nLendo mods instalados em:", mods_folder)

    mp = ModpackProfile(questbook, mods_folder)

    report = mp.apply(dry_run=dry_run)

    print(f"Mods instalados detectados : {len(report.mods_installed)}")

    print(f"Mods utilizados pelo questbook : {len(report.mods_used)}")

    print(f"Mods ausentes : {len(report.missing_mods)}")

    if report.missing_mods_detail:

        print()

        for detail in report.missing_mods_detail:

            print(
                f" - {detail.mod}: "
                f"{detail.affected_quests} quest(s), "
                f"{detail.affected_chapters} capítulo(s)"
            )

    if dry_run:

        print("\nModo simulação ativado (--dry-run). Nenhum arquivo será escrito.")

    if not report.missing_mods:

        print("\nNenhum mod ausente. Questbook já compatível com o modpack.")

        _write_report_file(report, report_file)

        return report

    print("\nResultado da adaptação:")

    print(f"Quests removidas: {len(report.removed_quests)}")

    print(f"Capítulos afetados: {len(report.affected_chapters)}")

    print(f"Dependências removidas: {report.removed_dependencies}")

    print(f"Capítulos vazios removidos: {len(report.removed_chapters)}")

    if dry_run:

        _write_report_file(report, report_file)

        return report

    if not report.removed_quests:

        # Havia mods ausentes, mas nenhuma quest referenciava exatamente
        # esses mods (não deveria acontecer, mas por segurança).
        _write_report_file(report, report_file)

        return report

    if output is None:

        raise Exception(
            "--output é obrigatório fora do modo --dry-run."
        )

    output = Path(output)

    # ----------------------------
    # Backup (uma vez só, cobrindo a pasta raiz inteira)
    # ----------------------------

    if not backup_state["done"]:

        print("\nCriando backup...")

        backup = BackupManager()

        backup_path = backup.create_backup(root_folder)

        print(f"Backup criado em: {backup_path}")

        backup_state["done"] = True

    # ----------------------------
    # Salvar
    # ----------------------------

    context = EditContext()

    context.removed_mods = set(report.missing_mods)

    context.removed_quests = set(report.removed_quests)

    context.removed_dependencies = report.removed_dependencies

    context.removed_chapters = set(report.removed_chapters)

    writer = QuestbookWriter()

    writer.write(
        questbook,
        output,
        context
    )

    print(f"\nQuestbook salvo em: {output}")

    # ----------------------------
    # Validar resultado final
    # ----------------------------

    print("\nValidando resultado final...")

    final_questbook = FTBQuestsParser().parse(output)

    final_validator = QuestbookValidator(final_questbook, output)

    final_validator.validate().summary()

    # ----------------------------
    # Relatório
    # ----------------------------

    _write_report_file(report, report_file)

    return report


def _write_report_file(report, report_file) -> None:

    if not report_file:

        return

    with open(report_file, "w", encoding="utf8") as file:

        json.dump(
            report.to_dict(),
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nRelatório salvo em: {report_file}")


def _per_profile_path(path_str, profile_name):

    path = Path(path_str)

    return str(path.with_name(f"{path.stem}_{profile_name}{path.suffix}"))
