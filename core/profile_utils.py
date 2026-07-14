"""
Helpers compartilhados pelas actions para lidar com pastas de
questbook que contêm múltiplos perfis irmãos (ex.: challenge/ e
classic/ dentro de ftbquests/).

Mantém as actions individuais finas: elas só chamam resolve_profiles()
e, quando forem escrever algo em disco, output_path_for().
"""

from __future__ import annotations

import shutil
from pathlib import Path

from core.parser import QuestbookParser, QuestbookProfile


def resolve_profiles(
    parser: QuestbookParser,
    folder: Path,
) -> tuple[list[QuestbookProfile], list[Path]]:
    """
    Detecta todos os perfis de questbook dentro de `folder` e quaisquer
    arquivos/pastas soltos na raiz que não pertencem a nenhum perfil
    (ex.: um .md). Nunca ignora perfis irmãos silenciosamente.
    """

    profiles = parser.detect_all(folder)

    loose_entries = parser.loose_root_entries(folder, profiles)

    return profiles, loose_entries


def output_path_for(
    output: Path,
    profile: QuestbookProfile,
    multi: bool,
) -> Path:
    """
    Decide onde escrever a saída de um perfil.

    multi=False (só um perfil, modo single-profile de sempre):
    escreve direto em `output`, mantendo compatibilidade retroativa.

    multi=True (mais de um perfil irmão): escreve em
    `output/<nome-do-perfil>/`, para não sobrescrever um perfil com
    o outro.
    """

    if not multi:
        return output

    return output / profile.name


def copy_loose_root_entries(
    loose_entries: list[Path],
    output: Path,
) -> None:
    """
    Copia arquivos/pastas soltos da raiz (não pertencentes a nenhum
    perfil) para a saída, sem interpretá-los - mesmo espírito de
    QuestBook.extra_root_entries, mas um nível acima (raiz da pasta
    que contém os perfis, não raiz de um questbook individual).
    """

    if not loose_entries:
        return

    output.mkdir(parents=True, exist_ok=True)

    for entry in loose_entries:

        destination = output / entry.name

        if entry.is_dir():

            shutil.copytree(entry, destination, dirs_exist_ok=True)

        else:

            shutil.copy2(entry, destination)
