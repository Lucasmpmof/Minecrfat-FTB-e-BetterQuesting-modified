from dataclasses import dataclass
from pathlib import Path


@dataclass
class QuestbookProfile:
    """
    Um questbook detectado dentro da pasta fornecida.

    name=None quando a própria pasta fornecida já É o questbook
    (modo single-profile, sem subpasta de perfil). Nesse caso ela é
    o único item retornado por detect_all().

    name="challenge" / "classic" / etc. quando a pasta fornecida é
    uma pasta-pai contendo um ou mais perfis irmãos (ex.:
    ftbquests/challenge/, ftbquests/classic/).
    """

    name: str | None
    type: str
    path: Path


class QuestbookParser:
    """
    Detecta o(s) questbook(s) (FTB Quests, BetterQuesting, etc.)
    a partir da pasta fornecida.

    Um modpack pode ter mais de um questbook irmão na mesma pasta
    (ex.: ftbquests/challenge/ e ftbquests/classic/) - detect_all()
    retorna todos eles. detect() é mantido só por compatibilidade e
    retorna apenas o primeiro; prefira detect_all() em código novo.
    """

    def _questbook_type(self, folder: Path) -> str | None:

        # BetterQuesting
        if (folder / "DefaultQuests.json").exists():
            return "betterquesting"

        # FTB Quests
        if (folder / "chapters").exists():
            return "ftbquests"

        return None

    def detect(self, folder: Path):
        """
        Compatibilidade retroativa: retorna só (tipo, pasta) do
        primeiro perfil encontrado. Se a pasta tiver mais de um
        perfil irmão (ex.: challenge/ + classic/), os demais são
        silenciosamente ignorados por quem chamar isto - use
        detect_all() para processar todos.
        """

        profiles = self.detect_all(folder)

        first = profiles[0]

        return first.type, first.path

    def detect_all(self, folder: Path) -> list[QuestbookProfile]:

        if not folder.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {folder}")

        # A própria pasta já é um questbook (modo single-profile).
        root_type = self._questbook_type(folder)

        if root_type:
            return [QuestbookProfile(name=None, type=root_type, path=folder)]

        # Procura perfis irmãos (challenge, classic, normal, expert...).
        profiles = []

        for sub in sorted(folder.iterdir()):

            if not sub.is_dir():
                continue

            sub_type = self._questbook_type(sub)

            if sub_type:
                profiles.append(
                    QuestbookProfile(name=sub.name, type=sub_type, path=sub)
                )

        if not profiles:
            raise Exception("Questbook não reconhecido.")

        return profiles

    def loose_root_entries(
        self,
        folder: Path,
        profiles: list[QuestbookProfile],
    ) -> list[Path]:
        """
        Arquivos/pastas soltos na raiz verdadeira (ex.: um .md) que
        não pertencem a nenhum perfil detectado. Só existe quando a
        pasta fornecida é uma pasta-pai de múltiplos perfis - no
        modo single-profile a própria pasta É o questbook, então não
        há nada "solto" fora dele.
        """

        if len(profiles) == 1 and profiles[0].name is None:
            return []

        profile_dirs = {profile.path for profile in profiles}

        return [
            entry
            for entry in sorted(folder.iterdir())
            if entry not in profile_dirs
        ]
