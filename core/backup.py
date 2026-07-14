from pathlib import Path
from datetime import datetime
import shutil



class BackupManager:


    def __init__(
        self,
        backup_folder="backup"
    ):

        self.backup_folder = Path(
            backup_folder
        )



    def create_backup(
        self,
        source
    ):

        source = Path(source)


        if not source.exists():

            raise FileNotFoundError(
                f"Origem não encontrada: {source}"
            )



        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )


        destination = (
            self.backup_folder
            /
            timestamp
        )


        destination.mkdir(
            parents=True,
            exist_ok=True
        )


        target = (
            destination
            /
            source.name
        )


        shutil.copytree(
            source,
            target
        )


        return target