from pathlib import Path

from nbtlib import parse_nbt

from core.models import Chapter
from core.snbt_writer import SNBTWriter



class ChapterWriter:
    """
    Responsável por escrever arquivos
    chapter.snbt.

    Também realiza pequenas correções
    estruturais após edições.
    """



    def __init__(self):

        self.snbt_writer = SNBTWriter()



    # --------------------------------------------------
    # Escrever capítulo
    # --------------------------------------------------

    def write(
        self,
        source: Path,
        destination: Path,
        chapter: Chapter | None = None
    ):


        if chapter is None:

            self.snbt_writer.rewrite(

                source,

                destination

            )

            return



        data = parse_nbt(

            source.read_text(
                encoding="utf8"
            )

        )



        self.clean_quests(

            data,

            chapter

        )



        self.snbt_writer.save(

            data,

            destination

        )



    # --------------------------------------------------
    # Limpar quests inexistentes
    # --------------------------------------------------

    def clean_quests(
        self,
        data,
        chapter: Chapter
    ):


        if "quests" not in data:

            return



        valid_ids = {

            quest.id

            for quest in chapter.quests

        }

        # Quests que existem no disco mas o Parser não conseguiu
        # interpretar (SNBT malformado/formato não suportado) são
        # preservadas como arquivo pelo Writer (ver core/writer.py),
        # então a referência a elas no chapter.snbt também precisa
        # ser mantida - senão a quest fica órfã: o arquivo continua
        # existindo, mas some da lista do capítulo dentro do jogo.

        valid_ids.update(
            chapter.malformed_quest_ids
        )


        data["quests"] = [

            quest

            for quest in data["quests"]

            if str(quest) in valid_ids

        ]