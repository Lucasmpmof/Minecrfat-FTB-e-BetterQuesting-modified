from __future__ import annotations

import json
import zipfile
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - fallback para Python < 3.11
    tomllib = None


class InstalledModsScanner:
    """
    Responsável por detectar quais mods estão realmente instalados
    em uma pasta `mods/` de uma instância Minecraft.

    Lê os metadados de dentro de cada `.jar` (META-INF/mods.toml para
    Forge/NeoForge, fabric.mod.json para Fabric, quilt.mod.json para
    Quilt) em vez de confiar no nome do arquivo, que é pouco confiável
    (versões, sufixos, etc.).

    Se um jar não expõe nenhum desses metadados (raro, mas acontece
    com libs auxiliares), cai em um fallback baseado no nome do
    arquivo.
    """

    def scan(self, mods_folder: Path) -> set[str]:

        mods_folder = Path(mods_folder)

        if not mods_folder.exists():

            raise FileNotFoundError(
                f"Pasta de mods não encontrada: {mods_folder}"
            )

        installed: set[str] = set()

        for jar_file in sorted(mods_folder.glob("*.jar")):

            installed.update(
                self.extract_mod_ids(jar_file)
            )

        return installed

    # ------------------------------------------------------
    # Extrai os mod ids de dentro de um .jar
    # ------------------------------------------------------

    def extract_mod_ids(self, jar_file: Path) -> set[str]:

        mod_ids: set[str] = set()

        try:

            with zipfile.ZipFile(jar_file) as jar:

                namelist = jar.namelist()

                mod_ids.update(self._from_forge(jar, namelist))
                mod_ids.update(self._from_fabric(jar, namelist))
                mod_ids.update(self._from_quilt(jar, namelist))

        except (zipfile.BadZipFile, OSError):

            return set()

        if not mod_ids:

            mod_ids.add(
                self._guess_from_filename(jar_file)
            )

        return mod_ids

    # ------------------------------------------------------
    # Forge / NeoForge
    # ------------------------------------------------------

    def _from_forge(self, jar: zipfile.ZipFile, namelist: list[str]) -> set[str]:

        if tomllib is None or "META-INF/mods.toml" not in namelist:

            return set()

        try:

            data = tomllib.loads(
                jar.read("META-INF/mods.toml").decode("utf8")
            )

        except Exception:

            return set()

        return {
            str(mod.get("modId"))
            for mod in data.get("mods", [])
            if mod.get("modId")
        }

    # ------------------------------------------------------
    # Fabric
    # ------------------------------------------------------

    def _from_fabric(self, jar: zipfile.ZipFile, namelist: list[str]) -> set[str]:

        if "fabric.mod.json" not in namelist:

            return set()

        try:

            data = json.loads(
                jar.read("fabric.mod.json").decode("utf8")
            )

        except Exception:

            return set()

        mod_id = data.get("id")

        return {mod_id} if mod_id else set()

    # ------------------------------------------------------
    # Quilt
    # ------------------------------------------------------

    def _from_quilt(self, jar: zipfile.ZipFile, namelist: list[str]) -> set[str]:

        if "quilt.mod.json" not in namelist:

            return set()

        try:

            data = json.loads(
                jar.read("quilt.mod.json").decode("utf8")
            )

        except Exception:

            return set()

        mod_id = data.get("quilt_loader", {}).get("id")

        return {mod_id} if mod_id else set()

    # ------------------------------------------------------
    # Fallback: nome do arquivo
    # ------------------------------------------------------

    def _guess_from_filename(self, jar_file: Path) -> str:

        return jar_file.stem.split("-")[0].lower()
