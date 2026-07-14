from pathlib import Path

from nbtlib import parse_nbt
from nbtlib import serialize_tag
from nbtlib import Compound
from nbtlib import List



class SNBTWriter:


    def load(
        self,
        file: Path
    ):

        return parse_nbt(
            file.read_text(
                encoding="utf8"
            )
        )



    def normalize(
        self,
        value
    ):


        if isinstance(value, dict):

            return Compound(
                {
                    key: self.normalize(item)

                    for key, item in value.items()
                }
            )


        if isinstance(value, list):

            return List(
                [
                    self.normalize(item)

                    for item in value
                ]
            )


        return value



    def save(
        self,
        data,
        file: Path
    ):


        file.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        data = self.normalize(
            data
        )


        file.write_text(

            serialize_tag(data),

            encoding="utf8"

        )



    def rewrite(
        self,
        source: Path,
        destination: Path,
        modifier=None
    ):


        data = self.load(
            source
        )


        if modifier:

            data = modifier(
                data
            )


        self.save(
            data,
            destination
        )


        return data