from pathlib import Path

from nbtlib import parse_nbt

from core.models import QuestBook
from core.models import Chapter
from core.models import Quest

from core.detector import ModDetector



class FTBQuestsParser:
    """
    Parser do FTB Quests.

    Responsável apenas por:

    - Ler arquivos SNBT
    - Construir os modelos em memória
    - Registrar warnings

    A detecção de mods fica a cargo do ModDetector.
    """



    def __init__(self):

        self.detector = ModDetector()



    def parse(
        self,
        folder: Path
    ) -> QuestBook:


        questbook = QuestBook(
            name=folder.name
        )

        questbook.source_folder = folder


        chapters_dir = folder / "chapters"


        if not chapters_dir.exists():

            raise FileNotFoundError(
                f"Pasta de capítulos não encontrada: {chapters_dir}"
            )


        # Qualquer coisa na raiz do questbook além de "chapters/" não é
        # modelada pelo Parser (ex.: file.snbt, reward_tables/), mas
        # ainda faz parte de um questbook completo e autoconsistente -
        # preservamos o caminho para o Writer copiar como está.

        for entry in sorted(
            folder.iterdir()
        ):

            if entry.name == "chapters":

                continue

            questbook.extra_root_entries.append(
                entry
            )


        # Dentro de "chapters/", qualquer entrada que não seja uma
        # pasta de capítulo (ex.: chapters/index.snbt, que define a
        # ordem/agrupamento dos capítulos) também não é modelada -
        # mesmo tratamento.

        for entry in sorted(
            chapters_dir.iterdir()
        ):

            if entry.is_dir():

                continue

            questbook.extra_root_entries.append(
                entry
            )



        for chapter_folder in sorted(
            chapters_dir.iterdir()
        ):


            if not chapter_folder.is_dir():

                continue



            chapter = self.load_chapter(
                chapter_folder,
                questbook
            )


            if chapter is not None:

                questbook.chapters.append(
                    chapter
                )


        return questbook



    # ------------------------------------------------------
    # Chapter
    # ------------------------------------------------------

    def load_chapter(
        self,
        folder: Path,
        questbook: QuestBook
    ) -> Chapter | None:


        chapter_file = folder / "chapter.snbt"

        chapter_malformed = False


        try:

            data = parse_nbt(
                chapter_file.read_text(
                    encoding="utf8"
                )
            )


        except Exception as ex:

            questbook.malformed_files += 1

            questbook.warnings.append(
                f"Malformed chapter: {chapter_file} ({ex})"
            )

            # Não descartamos o capítulo: um chapter.snbt corrompido
            # não implica que as quests dentro da pasta também
            # estejam. Construímos um Chapter "degradado" (id/title
            # a partir do nome da pasta) só para que o Writer saiba
            # que precisa preservar a pasta inteira como está, em vez
            # de perder silenciosamente todas as quests dela.

            data = {}
            chapter_malformed = True



        chapter = Chapter(

            id=folder.name,

            title=str(
                data.get(
                    "title",
                    folder.name
                )
            ),

            source_folder=folder,

            chapter_malformed=chapter_malformed

        )



        for quest_file in sorted(
            folder.glob("*.snbt")
        ):


            if quest_file.name == "chapter.snbt":

                continue



            quest = self.load_quest(

                quest_file,

                questbook,

                chapter.id

            )



            if quest:

                chapter.quests.append(
                    quest
                )

            else:

                chapter.malformed_quest_ids.append(
                    quest_file.stem
                )



        return chapter



    # ------------------------------------------------------
    # Quest
    # ------------------------------------------------------

    def load_quest(
        self,
        quest_file: Path,
        questbook: QuestBook,
        chapter_id: str
    ) -> Quest | None:


        try:

            data = parse_nbt(
                quest_file.read_text(
                    encoding="utf8"
                )
            )


        except Exception as ex:


            questbook.malformed_files += 1


            questbook.warnings.append(

                f"Malformed quest: {quest_file} ({ex})"

            )


            return None



        quest = Quest(

            id=quest_file.stem,

            title=str(
                data.get(
                    "title",
                    quest_file.stem
                )
            ),

            chapter_id=chapter_id,

            dependencies=[

                str(dep)

                for dep in data.get(
                    "dependencies",
                    []
                )

            ],

            source_file=quest_file

        )



        questbook.loaded_files += 1



        self.detect_task_types(
            data,
            quest
        )



        self.detect_reward_types(
            data,
            quest
        )



        quest.mod = self.detector.detect(
            data
        )
        quest.mods = self.detector.detect_all(
            data
        )
        quest.references_vanilla = (
            self.detector.has_vanilla_reference(data)
        )


        return quest



    # ------------------------------------------------------
    # Tasks
    # ------------------------------------------------------

    def detect_task_types(
        self,
        data,
        quest
    ):


        for task in data.get(
            "tasks",
            []
        ):


            task_type = str(
                task.get(
                    "type",
                    "unknown"
                )
            )


            quest.task_types.append(
                task_type
            )



    # ------------------------------------------------------
    # Rewards
    # ------------------------------------------------------

    def detect_reward_types(
        self,
        data,
        quest
    ):


        for reward in data.get(
            "rewards",
            []
        ):


            reward_type = str(

                reward.get(
                    "type",
                    "unknown"
                )

            )


            quest.reward_types.append(
                reward_type
            )