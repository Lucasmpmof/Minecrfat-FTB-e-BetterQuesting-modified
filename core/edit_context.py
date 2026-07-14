from dataclasses import dataclass, field


@dataclass
class EditContext:
    """
    Guarda informações sobre uma operação de edição.

    Evita passar dezenas de parâmetros entre:
    Editor -> Writer -> Cleaner.

    Futuramente será usado por:
    - remove-mod
    - replace-chapter
    - merge-chapter
    """

    removed_mods: set[str] = field(
        default_factory=set
    )

    removed_quests: set[str] = field(
        default_factory=set
    )

    removed_dependencies: int = 0

    removed_rewards: int = 0

    removed_chapters: set[str] = field(
        default_factory=set
    )


    def add_removed_mod(
        self,
        mod: str
    ):

        self.removed_mods.add(
            mod
        )


    def add_removed_quest(
        self,
        quest_id: str
    ):

        self.removed_quests.add(
            quest_id
        )