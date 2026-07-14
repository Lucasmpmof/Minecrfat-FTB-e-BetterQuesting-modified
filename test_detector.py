"""
Testes exaustivos do ModDetector v0.6.

Cobre os bugs relatados:
  - detectar https como mod
  - detectar strings que não representam namespaces
  - aceitar texto livre
  - namespaces válidos ocultos em compostos NBT
"""

from core.detector import ModDetector


def run():
    d = ModDetector()
    failures = []

    def check(label, actual, expected):
        status = "OK" if actual == expected else "FAIL"
        if status == "FAIL":
            failures.append(label)
        print(f"[{status}] {label}: got={actual!r} expected={expected!r}")

    # ---------------------------------------------------------
    # extract_mod: casos básicos válidos
    # ---------------------------------------------------------
    check("mod valido simples", d.extract_mod("thermal:machine_frame"), "thermal")
    check("mod valido com ponto/traço", d.extract_mod("create.above_and_beyond:machine"), "create.above_and_beyond")
    check("mod valido com underscore", d.extract_mod("applied_energistics_2:cell"), "applied_energistics_2")
    check("minecraft filtrado (IGNORE_PREFIXES)", d.extract_mod("minecraft:diamond"), None)
    check("ftbquests filtrado (IGNORE_PREFIXES)", d.extract_mod("ftbquests:task"), None)

    # ---------------------------------------------------------
    # Bug 1: detectar https como mod
    # ---------------------------------------------------------
    check("URL https nao deve virar mod", d.extract_mod("https://example.com/path"), None)
    check("URL http nao deve virar mod", d.extract_mod("http://example.com"), None)
    check("URL ftp nao deve virar mod", d.extract_mod("ftp://files.example.com/x"), None)
    check("URL sem path apos host", d.extract_mod("https://example.com"), None)
    check("mailto nao deve virar mod", d.extract_mod("mailto:someone@example.com"), None)

    # ---------------------------------------------------------
    # Bug 2/3: strings que nao representam namespaces / texto livre
    # ---------------------------------------------------------
    check("texto livre com dois pontos", d.extract_mod("Note: this is important"), None)
    check("texto livre pt-br", d.extract_mod("Aviso: leia com atencao"), None)
    check("hora do dia nao e namespace", d.extract_mod("12:30"), None)
    check("chave-valor com espaco no path", d.extract_mod("mod: some text here"), None)
    check("placeholder chaves", d.extract_mod("{mod}:{item}"), None)
    check("placeholder colchetes", d.extract_mod("[mod]:[item]"), None)
    check("namespace maiusculo invalido", d.extract_mod("Thermal:machine_frame"), None)
    check("multiplos dois pontos", d.extract_mod("a:b:c"), None)
    check("string vazia", d.extract_mod(""), None)
    check("apenas dois pontos", d.extract_mod(":"), None)
    check("sem dois pontos", d.extract_mod("justtext"), None)
    check("valor nao string (int)", d.extract_mod(42), None)
    check("valor nao string (bool)", d.extract_mod(True), None)
    check("valor nao string (float)", d.extract_mod(3.14), None)
    check("valor nao string (None)", d.extract_mod(None), None)
    check("valor com aspas residuais", d.extract_mod('"thermal:machine_frame"'), "thermal")

    # ---------------------------------------------------------
    # Bug 4: namespaces validos ocultos em compostos NBT
    # ---------------------------------------------------------
    nested = {
        "tasks": [
            {
                "type": "item",
                "item": {
                    "Count": 1,
                    "id": "thermal:machine_frame",
                    "tag": {
                        "Damage": 0,
                        "ForgeCaps": {
                            "capability": "forge:energy",
                        },
                    },
                },
            }
        ],
        "rewards": [],
    }
    check("namespace oculto em NBT profundo (detect)", d.detect(nested), "thermal")
    all_mods = d.detect_all(nested)
    check("detect_all encontra thermal", "thermal" in all_mods, True)
    check("detect_all encontra forge", "forge" in all_mods, True)
    check("detect_all nao inclui minecraft", "minecraft" in all_mods, False)

    mixed = {
        "tasks": [
            {
                "type": "item",
                "item": "minecraft:diamond",
                "description": "Veja mais em https://example.com/wiki",
                "note": "Aviso: item raro",
            },
            {
                "type": "item",
                "item": "botania:mana_pool",
            },
        ]
    }
    all_mixed = d.detect_all(mixed)
    check("detect_all ignora URL", "https" not in all_mixed, True)
    check("detect_all ignora texto livre 'Aviso'", "Aviso" not in all_mixed, True)
    check("detect_all encontra botania", "botania" in all_mixed, True)
    check("detect_all ignora minecraft", "minecraft" not in all_mixed, True)

    # ---------------------------------------------------------
    # has_vanilla_reference
    # ---------------------------------------------------------
    check("has_vanilla_reference detecta minecraft:", d.has_vanilla_reference({"item": "minecraft:diamond"}), True)
    check("has_vanilla_reference detecta forge:", d.has_vanilla_reference({"cap": "forge:energy"}), True)
    check("has_vanilla_reference nao aciona com URL", d.has_vanilla_reference({"link": "https://minecraft.net"}), False)
    check("has_vanilla_reference falso para mod terceiro", d.has_vanilla_reference({"item": "thermal:machine_frame"}), False)
    check("has_vanilla_reference em estrutura aninhada", d.has_vanilla_reference(nested), True)

    # ---------------------------------------------------------
    # detect(): retorno "Unknown" quando nao ha nada
    # ---------------------------------------------------------
    check("detect retorna Unknown para vazio", d.detect({"tasks": [], "rewards": []}), "Unknown")
    check(
        "detect retorna Unknown quando so ha URLs/texto livre",
        d.detect({"tasks": [{"item": "https://example.com", "note": "Aviso: nada aqui"}], "rewards": []}),
        "Unknown",
    )

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
