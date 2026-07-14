from pathlib import Path
from collections import Counter

from core.models import QuestBook
from core.validator_report import ValidationReport
from core.unknown_analyzer import UnknownAnalyzer



class QuestbookValidator:


    def __init__(
        self,
        questbook: QuestBook,
        profile_folder: Path
    ):

        self.questbook = questbook

        self.profile_folder = profile_folder



    # ======================================================
    # Contagem de arquivos
    # ======================================================

    def count_quest_files(self):

        chapters = self.profile_folder / "chapters"

        total = 0


        if not chapters.exists():

            return 0



        for folder in chapters.iterdir():


            if not folder.is_dir():

                continue



            for file in folder.glob("*.snbt"):


                if file.name == "chapter.snbt":

                    continue



                total += 1



        return total



    # ======================================================
    # Estatísticas de mods
    # ======================================================

    def mod_statistics(self):

        counter = Counter()


        for quest in self.questbook.all_quests():

            counter[quest.mod] += 1



        return dict(counter)



    # ======================================================
    # Unknown antigo
    # ======================================================

    def unknown_tasks(self):

        tasks = set()



        for quest in self.questbook.all_quests():


            if quest.mod != "Unknown":

                continue



            tasks.update(
                quest.task_types
            )



        return sorted(tasks)



    def unknown_count(self):

        total = 0



        for quest in self.questbook.all_quests():


            if quest.mod == "Unknown":

                total += 1



        return total



    # ======================================================
    # Validação principal
    # ======================================================

    def validate(self):


        report = ValidationReport()



        files = self.count_quest_files()

        loaded = self.questbook.total_quests()



        # -------------------------------
        # Quests
        # -------------------------------

        report.set(
            "quests",
            "files",
            files
        )


        report.set(
            "quests",
            "loaded",
            loaded
        )


        report.set(
            "quests",
            "missing",
            files - loaded
        )



        # -------------------------------
        # Dependências
        # -------------------------------

        broken = self.broken_dependencies()



        report.set(
            "dependencies",
            "broken",
            len(broken)
        )


        report.set(
            "dependencies",
            "details",
            broken
        )



        # -------------------------------
        # Unknown Analyzer
        # -------------------------------

        unknown_analysis = UnknownAnalyzer(
            self.questbook
        ).analyze()



        #
        # unknown_analysis agora classifica TODAS as quests (não
        # apenas as que têm quest.mod == "Unknown"), então "count"
        # deve refletir o total de quests analisadas, para que as
        # cinco categorias (vanilla/ftb_internal/detected_mod/manual/
        # unknown) somem exatamente esse valor.
        #
        report.set(
            "unknown",
            "count",
            self.questbook.total_quests()
        )



        report.set(
            "unknown",
            "tasks",
            self.unknown_tasks()
        )



        report.set(
            "unknown",
            "analysis",
            {

                "vanilla":
                    len(
                        unknown_analysis["vanilla"]
                    ),


                "ftb_internal":
                    len(
                        unknown_analysis["ftb_internal"]
                    ),


                "detected_mod":
                    len(
                        unknown_analysis["detected_mod"]
                    ),


                "manual":
                    len(
                        unknown_analysis["manual"]
                    ),


                "unknown":
                    len(
                        unknown_analysis["unknown"]
                    )

            }
        )



        # -------------------------------
        # Capítulos
        # -------------------------------

        report.set(
            "chapters",
            "empty",
            self.empty_chapters()
        )


        report.set(
            "chapters",
            "missing",
            self.quests_without_chapter()
        )



        # -------------------------------
        # Informações extras
        # -------------------------------

        report.data["mods"] = (
            self.mod_statistics()
        )


        report.data["warnings"] = (
            self.questbook.warnings
        )



        report.data["status"] = (

            files == loaded

            and self.questbook.malformed_files == 0

        )



        return report



    # ======================================================
    # Dependências quebradas
    # ======================================================

    def broken_dependencies(self):

        broken = []



        existing = {

            quest.id

            for quest in self.questbook.all_quests()

        }



        for quest in self.questbook.all_quests():


            for dependency in quest.dependencies:


                if dependency not in existing:


                    broken.append(

                        {
                            "quest": quest.id,

                            "dependency": dependency

                        }

                    )



        return broken



    # ======================================================
    # Quests sem capítulo
    # ======================================================

    def quests_without_chapter(self):

        result = []



        for quest in self.questbook.all_quests():


            if not quest.chapter_id:


                result.append(
                    quest.id
                )



        return result



    # ======================================================
    # Capítulos vazios
    # ======================================================

    def empty_chapters(self):

        empty = []



        for chapter in self.questbook.chapters:


            if (

                len(chapter.quests) == 0

                and not chapter.malformed_quest_ids

                and not chapter.chapter_malformed

            ):


                empty.append(
                    chapter.id
                )



        return empty