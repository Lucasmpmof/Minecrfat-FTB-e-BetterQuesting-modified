from core.models import QuestBook
from core.analysis import QuestbookAnalyzer


class ChapterCleaner:
    """
    Responsável por detectar e remover capítulos vazios do QuestBook.

    Segue a convenção do projeto: um Cleaner repara a estrutura de
    dados, nunca deleta quests. Aqui ele apenas remove capítulos que
    já não contêm nenhuma quest (geralmente como consequência de uma
    remoção anterior feita pelo Editor).
    """

    def __init__(self):

        self.removed_chapters: list[str] = []

    # ------------------------------------------------------
    # Sensor: nunca modifica o QuestBook
    # ------------------------------------------------------

    def find_empty_chapters(self, questbook: QuestBook) -> list[str]:

        return [
            chapter.id
            for chapter in questbook.chapters
            if not chapter.quests
            and not chapter.malformed_quest_ids
            and not chapter.chapter_malformed
        ]

    # ------------------------------------------------------
    # Remove capítulos vazios e reconstrói índices
    # ------------------------------------------------------

    def clean(self, questbook: QuestBook) -> int:

        empty_ids = self.find_empty_chapters(questbook)

        self.removed_chapters = empty_ids

        if not empty_ids:
            return 0

        empty_ids_set = set(empty_ids)

        questbook.chapters = [
            chapter
            for chapter in questbook.chapters
            if chapter.id not in empty_ids_set
        ]

        QuestbookAnalyzer().analyze(questbook)

        return len(empty_ids)