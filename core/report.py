import json
from core.models import QuestBook


def generate_report(qb: QuestBook) -> dict:

    mods = {}

    chapters = []

    for chapter in qb.chapters:

        chapter_mods = {}

        for quest in chapter.quests:

            #
            # Estatística global
            #

            mods[quest.mod] = mods.get(quest.mod, 0) + 1

            #
            # Estatística do capítulo
            #

            chapter_mods[quest.mod] = (
                chapter_mods.get(quest.mod, 0) + 1
            )

        chapters.append({

            "id": chapter.id,

            "title": chapter.title,

            "quests": len(chapter.quests),

            "mods": dict(
                sorted(
                    chapter_mods.items(),
                    key=lambda item: item[1],
                    reverse=True
                )
            )

        })

    return {

        "chapters": len(qb.chapters),

        "quests": qb.total_quests(),

        "mods": dict(
            sorted(
                mods.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ),

        "chapter_analysis": chapters

    }


def report_to_json(qb: QuestBook) -> str:

    return json.dumps(

        generate_report(qb),

        ensure_ascii=False,

        indent=2

    )