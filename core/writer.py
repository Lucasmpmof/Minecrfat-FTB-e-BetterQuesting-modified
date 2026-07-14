from pathlib import Path
import shutil

from core.models import QuestBook, Chapter, Quest
from core.snbt_writer import SNBTWriter
from core.snbt_cleaner import SNBTCleaner
from core.edit_context import EditContext
from core.chapter_writer import ChapterWriter


class QuestbookWriter:
    """
    Responsável por escrever um QuestBook
    modificado para uma nova pasta.

    A escrita dos arquivos SNBT passa pelo
    SNBTWriter e pode aplicar limpeza através
    do SNBTCleaner.
    """



    def __init__(self):

        self.snbt_writer = SNBTWriter()

        self.chapter_writer = ChapterWriter()

        self.cleaner = SNBTCleaner()



    # ------------------------------------------------------
    # Escrever QuestBook
    # ------------------------------------------------------

    def write(
        self,
        questbook: QuestBook,
        output: Path,
        context: EditContext | None = None
    ):


        output.mkdir(
            parents=True,
            exist_ok=True
        )


        for chapter in questbook.chapters:


            self.write_chapter(

                chapter,

                output,

                questbook,

                context

            )


        self.write_extra_root_entries(
            questbook,
            output
        )


        return output



    # ------------------------------------------------------
    # Preservar arquivos/pastas não modelados pelo Parser
    # (file.snbt, reward_tables/, chapters/index.snbt, etc.)
    # ------------------------------------------------------

    def write_extra_root_entries(
        self,
        questbook: QuestBook,
        output: Path
    ):

        if questbook.source_folder is None:

            return


        for entry in questbook.extra_root_entries:

            relative = entry.relative_to(
                questbook.source_folder
            )

            destination = output / relative

            if entry.is_dir():

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                shutil.copytree(
                    entry,
                    destination,
                    dirs_exist_ok=True
                )

            else:

                self.copy_file(
                    entry,
                    destination
                )



    # ------------------------------------------------------
    # Escrever capítulo
    # ------------------------------------------------------

    def write_chapter(
        self,
        chapter: Chapter,
        output: Path,
        questbook: QuestBook,
        context: EditContext | None = None
    ):


        if chapter.source_folder is None:

            return



        chapter_output = (

            output /

            "chapters" /

            chapter.id

        )


        chapter_output.mkdir(

            parents=True,

            exist_ok=True

        )



        for file in chapter.source_folder.iterdir():


            if file.name == "chapter.snbt":


                if chapter.chapter_malformed:

                    # chapter.snbt não é NBT válido (ou não existe) -
                    # tentar reparsear/reescrever via ChapterWriter
                    # falharia do mesmo jeito. Copiamos os bytes como
                    # estão, preservando o arquivo original.

                    self.copy_file(

                        file,

                        chapter_output / file.name

                    )

                    continue


                self.chapter_writer.write(

                    file,

                    chapter_output / file.name,

                    chapter

                )


                continue



            if file.suffix != ".snbt":


                self.copy_file(

                    file,

                    chapter_output / file.name

                )

                continue


            # Quest cujo SNBT o Parser não conseguiu interpretar
            # (ver core/ftbquests.py). Preservamos o arquivo original
            # sem tocar nele - a alternativa (não escrever nada) apaga
            # a quest do jogador silenciosamente na próxima escrita.

            if file.stem in chapter.malformed_quest_ids:

                self.copy_file(

                    file,

                    chapter_output / file.name

                )



        for quest in chapter.quests:


            self.write_quest(

                quest,

                chapter_output,

                questbook,

                context

            )



    # ------------------------------------------------------
    # Escrever quest
    # ------------------------------------------------------

    def write_quest(
        self,
        quest: Quest,
        output: Path,
        questbook: QuestBook,
        context: EditContext | None = None
    ):


        if quest.source_file is None:

            return



        destination = (

            output /

            quest.source_file.name

        )



        def modifier(data):


            if context is None:

                return data



            valid_ids = set(

                questbook.quest_index.keys()

            )



            self.cleaner.clean_dependencies(

                data,

                valid_ids

            )


            self.cleaner.clean_rewards(

                data,

                context.removed_mods

            )


            return data



        self.snbt_writer.rewrite(

            quest.source_file,

            destination,

            modifier

        )



    # ------------------------------------------------------
    # Copiar arquivos não SNBT
    # ------------------------------------------------------

    def copy_file(
        self,
        source: Path,
        destination: Path
    ):


        destination.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        shutil.copy2(

            source,

            destination

        )