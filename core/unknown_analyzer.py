from core.models import QuestBook


class UnknownAnalyzer:
    """
    Classifica todas as quests do QuestBook em uma das categorias:

    - vanilla: não tem mod de terceiros detectado, mas referencia
      minecraft/forge/neoforge (quest.references_vanilla).
    - ftb_internal: o mod principal é um módulo interno do FTB
      (ftblibrary, ftbteams, ftbchunks - "ftbquests" já é filtrado
      pelo próprio ModDetector).
    - detected_mod: tem um mod de terceiros detectado
      (quest.mod != "Unknown" e não é FTB interno).
    - manual: não tem mod, não referencia vanilla, não tem rewards e
      só possui tasks manuais/narrativas (checkmark) ou nenhuma task.
    - unknown: nenhuma das anteriores (nenhum mod detectado, sem
      referência vanilla, e não se encaixa como manual).

    Diferente da versão anterior, TODAS as quests são classificadas
    (não apenas as que têm quest.mod == "Unknown"), usando sempre
    quest.mod/quest.mods como fonte de verdade - nunca uma lógica de
    detecção paralela baseada em texto livre.
    """

    FTB_IDS = {
        "ftblibrary",
        "ftbteams",
        "ftbchunks",
    }

    def __init__(self, questbook: QuestBook):

        self.questbook = questbook

    def analyze(self):

        result = {
            "vanilla": [],
            "ftb_internal": [],
            "detected_mod": [],
            "manual": [],
            "unknown": [],
        }

        for quest in self.questbook.all_quests():

            category = self.classify(quest)

            result[category].append(
                {
                    "id": quest.id,
                    "title": quest.title,
                    "tasks": quest.task_types,
                    "rewards": quest.reward_types,
                    "mods": list(quest.mods),
                    "dependencies": quest.dependencies,
                }
            )

        return result

    def classify(self, quest) -> str:

        mod = quest.mod

        #
        # FTB interno: verificado primeiro, pois é um mod "conhecido"
        # mais específico que qualquer detecção genérica de terceiros.
        #
        if mod in self.FTB_IDS:

            return "ftb_internal"

        #
        # Mod de terceiros detectado: quest.mod (derivado de
        # quest.mods) é a única fonte de verdade aqui.
        #
        if mod and mod != "Unknown":

            return "detected_mod"

        #
        # Vanilla: nenhum mod de terceiros, mas referencia minecraft/
        # forge/neoforge.
        #
        if getattr(quest, "references_vanilla", False):

            return "vanilla"

        #
        # Quest manual/narrativa: sem mods, sem rewards, e só tasks
        # manuais (checkmark) ou nenhuma task.
        #
        if (
            not quest.mods
            and not quest.reward_types
            and (
                "checkmark" in quest.task_types
                or len(quest.task_types) == 0
            )
        ):

            return "manual"

        return "unknown"
