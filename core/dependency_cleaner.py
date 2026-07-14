from core.models import QuestBook


class DependencyCleaner:
    """
    Responsável por validar e limpar
    dependências quebradas entre quests.
    """

    def __init__(self):

        self.removed = []


    # ------------------------------------------------------

    def find_broken_dependencies(
        self,
        questbook
    ):

        broken = []


        valid_ids = set()

        for quest in questbook.all_quests():

            valid_ids.add(
                quest.id
            )


        for quest in questbook.all_quests():

            for dependency in quest.dependencies:

                if dependency not in valid_ids:

                    broken.append(
                        {
                            "quest": quest.id,
                            "dependency": dependency
                        }
                    )


        return broken


    # ------------------------------------------------------

    def clean(
        self,
        questbook: QuestBook
    ):

        valid_ids = {
            quest.id
            for quest in questbook.all_quests()
}


        removed = 0


        for quest in questbook.all_quests():

            original = list(
                quest.dependencies
            )


            quest.dependencies = [

                dep

                for dep in quest.dependencies

                if dep in valid_ids

            ]


            removed += (
                len(original)
                -
                len(quest.dependencies)
            )


        self.removed = removed


        return removed