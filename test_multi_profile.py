"""
Teste funcional da detecção multi-perfil (core/parser.py + core/profile_utils.py).

Cobre o bug real encontrado em produção: uma pasta ftbquests/ com dois
perfis irmãos (challenge/ e classic/) só tinha o primeiro processado,
e qualquer arquivo solto na raiz (ex.: um .md) era ignorado.
"""

import shutil
import tempfile
from pathlib import Path

from core.parser import QuestbookParser
from core.profile_utils import (
    resolve_profiles,
    output_path_for,
    copy_loose_root_entries,
)


def make_ftbquests_profile(base: Path, name: str) -> None:

    (base / name / "chapters" / "ch1").mkdir(parents=True)

    (base / name / "reward_tables").mkdir(parents=True)


def run():

    failures = []

    def check(label, actual, expected):

        status = "OK" if actual == expected else "FAIL"

        if status == "FAIL":
            failures.append(label)

        print(f"[{status}] {label}: got={actual!r} expected={expected!r}")

    tmp = Path(tempfile.mkdtemp())

    try:

        parser = QuestbookParser()

        # ------------------------------------------------------
        # Caso 1: dois perfis irmãos + um arquivo solto na raiz
        # (o bug real reportado: challenge/ + classic/ + um .md)
        # ------------------------------------------------------

        multi_root = tmp / "ftbquests"

        make_ftbquests_profile(multi_root, "challenge")
        make_ftbquests_profile(multi_root, "classic")

        (multi_root / "notes.md").write_text("contexto do modpack")

        profiles, loose = resolve_profiles(parser, multi_root)

        check("multi: numero de perfis", len(profiles), 2)

        check(
            "multi: nomes dos perfis",
            sorted(p.name for p in profiles),
            ["challenge", "classic"],
        )

        check(
            "multi: todos tipados como ftbquests",
            all(p.type == "ftbquests" for p in profiles),
            True,
        )

        check(
            "multi: arquivo solto detectado",
            [p.name for p in loose],
            ["notes.md"],
        )

        # detect() (compat) não deve levantar erro, mas só cobre o
        # primeiro perfil - documentado, não é o caminho recomendado.
        compat_type, compat_path = parser.detect(multi_root)

        check("multi: detect() compat retorna ftbquests", compat_type, "ftbquests")

        check(
            "multi: detect() compat aponta pra um dos perfis",
            compat_path in {p.path for p in profiles},
            True,
        )

        # output_path_for deve separar cada perfil em sua própria
        # subpasta, para não sobrescrever um perfil com o outro.
        out = tmp / "saida"

        multi = len(profiles) > 1

        out_paths = {
            p.name: output_path_for(out, p, multi) for p in profiles
        }

        check(
            "multi: saida do challenge isolada",
            out_paths["challenge"],
            out / "challenge",
        )

        check(
            "multi: saida do classic isolada",
            out_paths["classic"],
            out / "classic",
        )

        # O arquivo solto da raiz deve ser preservado na saída, não
        # descartado silenciosamente.
        copy_loose_root_entries(loose, out)

        check(
            "multi: notes.md preservado na saida",
            (out / "notes.md").exists(),
            True,
        )

        check(
            "multi: conteudo do notes.md preservado",
            (out / "notes.md").read_text(),
            "contexto do modpack",
        )

        # ------------------------------------------------------
        # Caso 2: modpack single-profile (comportamento antigo,
        # sem subpasta de perfil) precisa continuar funcionando
        # igual - sem virar output/<nome>/.
        # ------------------------------------------------------

        single_root = tmp / "single"

        (single_root / "chapters" / "ch1").mkdir(parents=True)

        single_profiles, single_loose = resolve_profiles(parser, single_root)

        check("single: numero de perfis", len(single_profiles), 1)

        check("single: perfil sem nome (root == questbook)", single_profiles[0].name, None)

        check("single: nenhum arquivo solto", single_loose, [])

        single_multi = len(single_profiles) > 1

        single_out = output_path_for(out, single_profiles[0], single_multi)

        check(
            "single: saida vai direto pra output/ (compat retroativa)",
            single_out,
            out,
        )

        # ------------------------------------------------------
        # Caso 3: pasta com um único perfil dentro de uma pasta-pai
        # (ex.: só "normal/" dentro de ftbquests/) também não deve
        # virar subpasta - só existe 1 perfil.
        # ------------------------------------------------------

        one_sibling_root = tmp / "ftbquests_one"

        make_ftbquests_profile(one_sibling_root, "normal")

        one_profiles, one_loose = resolve_profiles(parser, one_sibling_root)

        check("um-perfil-irmao: quantidade", len(one_profiles), 1)

        check("um-perfil-irmao: nome preservado", one_profiles[0].name, "normal")

        one_multi = len(one_profiles) > 1

        check(
            "um-perfil-irmao: nao vira subpasta (so 1 perfil)",
            output_path_for(out, one_profiles[0], one_multi),
            out,
        )

    finally:

        shutil.rmtree(tmp, ignore_errors=True)

    print()

    if failures:

        print(f"FALHAS: {len(failures)}")

        for f in failures:
            print(f" - {f}")

        raise SystemExit(1)

    else:

        print("Todos os testes passaram.")


if __name__ == "__main__":

    run()
