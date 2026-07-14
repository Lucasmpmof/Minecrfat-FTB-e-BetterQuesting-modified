from core.models import QuestBook

from core.analysis import QuestbookAnalyzer


class QuestbookEditor:
    """
    Camada de edição do QuestBook.

    Responsável por alterar os modelos
    carregados em memória.

    Não manipula arquivos SNBT diretamente.
    """


    def __init__(
        self,
        questbook: QuestBook
    ):

        self.questbook = questbook



    # ------------------------------------------------------
    # Remove uma quest pelo ID
    # ------------------------------------------------------

    def remove_quest(
        self,
        quest_id: str
    ) -> bool:

        return self.remove_quests(
            [
                quest_id
            ]
        )



    # ------------------------------------------------------
    # Remove múltiplas quests
    # ------------------------------------------------------

    def remove_quests(
        self,
        quest_ids: list[str]
    ) -> int:


        if not quest_ids:

            return 0


        quest_ids = set(
            quest_ids
        )


        removed = 0


        for chapter in self.questbook.chapters:


            original_size = len(
                chapter.quests
            )


            chapter.quests = [

                quest

                for quest in chapter.quests

                if quest.id not in quest_ids

            ]


            removed += (

                original_size -

                len(chapter.quests)

            )


        if removed:

            self.rebuild()


        return removed



    # ------------------------------------------------------
    # Remove dependências inválidas
    #
    # v0.4.2
    #
    # Remove referências para quests
    # que não existem mais.
    #
    # ------------------------------------------------------

    def remove_invalid_dependencies(self) -> int:


        valid_ids = set(

            quest.id

            for quest in self.questbook.all_quests()

        )


        removed = 0


        for quest in self.questbook.all_quests():


            original_size = len(
                quest.dependencies
            )


            quest.dependencies = [

                dependency

                for dependency in quest.dependencies

                if dependency in valid_ids

            ]


            removed += (

                original_size -

                len(quest.dependencies)

            )


        if removed:

            self.rebuild()


        return removed



    # ------------------------------------------------------
    # Remove capítulos vazios
    # ------------------------------------------------------

    def remove_empty_chapters(self) -> int:


        original_size = len(
            self.questbook.chapters
        )


        self.questbook.chapters = [

            chapter

            for chapter in self.questbook.chapters

            if chapter.quests

        ]


        removed = (

            original_size -

            len(self.questbook.chapters)

        )


        if removed:

            self.rebuild()


        return removed



    # ------------------------------------------------------
    # Reconstrói índices
    # ------------------------------------------------------

    def rebuild(self):

        QuestbookAnalyzer().analyze(
            self.questbook
        )