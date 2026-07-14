from collections import defaultdict

from core.models import (
    QuestBook,
    Chapter,
    Quest,
    ModAnalysis
)


class QuestbookAnalyzer:
    """
    Responsável por construir todos os índices e estatísticas
    do QuestBook.

    Esta classe NÃO altera o parser.
    Ela apenas analisa os modelos carregados.
    """

    def analyze(self, questbook: QuestBook):

        self.build_quest_index(questbook)

        self.build_dependency_graph(questbook)

        self.build_chapter_analysis(questbook)

        self.build_mod_analysis(questbook)

        self.build_reference_mod_analysis(
            questbook
        )

        return questbook

    # ---------------------------------------------------------

    def build_quest_index(self, questbook: QuestBook):

        questbook.quest_index.clear()

        for chapter in questbook.chapters:

            for quest in chapter.quests:

                questbook.quest_index[quest.id] = quest

    # ---------------------------------------------------------

    def build_dependency_graph(self, questbook: QuestBook):

        questbook.dependency_graph.clear()

        for quest in questbook.all_quests():

            questbook.dependency_graph[quest.id] = list(
                quest.dependencies
            )

    # ---------------------------------------------------------

    def build_chapter_analysis(self, questbook: QuestBook):

        for chapter in questbook.chapters:

            analysis = chapter.analysis

            analysis.total_quests = len(chapter.quests)

            analysis.mods.clear()

            analysis.task_types.clear()

            analysis.reward_types.clear()

            analysis.dependencies = 0

            for quest in chapter.quests:

                analysis.mods.add(quest.mod)

                analysis.dependencies += len(
                    quest.dependencies
                )

                analysis.task_types.update(
                    quest.task_types
                )

                analysis.reward_types.update(
                    quest.reward_types
                )

    # ---------------------------------------------------------

    def build_mod_analysis(self, questbook: QuestBook):

        questbook.mod_index.clear()

        for chapter in questbook.chapters:

            for quest in chapter.quests:

                if quest.mod not in questbook.mod_index:

                    questbook.mod_index[quest.mod] = ModAnalysis(
                        name=quest.mod
                    )

                mod = questbook.mod_index[quest.mod]

                mod.quests += 1

                mod.chapters.add(
                    chapter.title
                )

    # ---------------------------------------------------------

    def summary(self, questbook: QuestBook):

        return {

            "chapters": len(
                questbook.chapters
            ),

            "quests": questbook.total_quests(),

            "mods": len(
                questbook.mod_index
            ),

            "dependencies": sum(
                len(q.dependencies)
                for q in questbook.all_quests()
            )
        }
        # ---------------------------------------------------------

    def build_reference_mod_analysis(
        self,
        questbook: QuestBook
    ):

        questbook.reference_mod_index.clear()


        for chapter in questbook.chapters:

            for quest in chapter.quests:


                for mod_name in quest.mods:


                    if mod_name not in questbook.reference_mod_index:

                        questbook.reference_mod_index[mod_name] = ModAnalysis(
                            name=mod_name
                        )


                    mod = questbook.reference_mod_index[mod_name]


                    mod.quests += 1


                    mod.chapters.add(
                        chapter.title
                    )