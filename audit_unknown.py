"""
Sensor de auditoria (somente leitura).

Gera `unknown_dump.json` com todas as quests classificadas como
"Unknown" pelo UnknownAnalyzer, reutilizando o Parser e o
UnknownAnalyzer existentes tal como estão. Não altera nenhum
arquivo do QuestBook e não modifica nenhuma lógica do projeto.

Uso:
    python audit_unknown.py --questbook "<caminho para a pasta ftbquests>"

Saída:
    unknown_dump.json (na pasta atual)
"""

import argparse
import json
from pathlib import Path

from core.parser import QuestbookParser
from core.ftbquests import FTBQuestsParser
from core.analysis import QuestbookAnalyzer
from core.unknown_analyzer import UnknownAnalyzer


def main():

    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument("--questbook", required=True)

    arg_parser.add_argument(
        "--output",
        default="unknown_dump.json",
        help="Arquivo JSON de saída (padrão: unknown_dump.json)",
    )

    args = arg_parser.parse_args()

    folder = Path(args.questbook)

    # ----------------------------
    # Carregar (somente leitura)
    # ----------------------------

    parser = QuestbookParser()

    questbook_type, path = parser.detect(folder)

    if questbook_type != "ftbquests":

        raise Exception("Apenas FTB Quests suportado atualmente.")

    questbook = FTBQuestsParser().parse(path)

    QuestbookAnalyzer().analyze(questbook)

    # ----------------------------
    # Classificar (somente leitura)
    # ----------------------------

    analysis = UnknownAnalyzer(questbook).analyze()

    unknown_quests = analysis["unknown"]

    # ----------------------------
    # Montar dump com os campos pedidos
    # ----------------------------

    dump = []

    quest_index = {quest.id: quest for quest in questbook.all_quests()}

    for entry in unknown_quests:

        quest = quest_index.get(entry["id"])

        if quest is None:

            continue

        dump.append(
            {
                "id": quest.id,
                "title": quest.title,
                "chapter_id": quest.chapter_id,
                "task_types": quest.task_types,
                "reward_types": quest.reward_types,
                "mods": sorted(quest.mods),
                "dependencies": quest.dependencies,
                "references_vanilla": quest.references_vanilla,
            }
        )

    with open(args.output, "w", encoding="utf8") as file:

        json.dump(dump, file, indent=2, ensure_ascii=False)

    print(f"{len(dump)} quests 'Unknown' salvas em {args.output}")


if __name__ == "__main__":

    main()