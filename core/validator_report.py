class ValidationReport:


    def __init__(self):

        self.data = {

            "quests": {

                "files": 0,

                "loaded": 0,

                "missing": 0

            },


            "dependencies": {

                "broken": 0,

                "details": []

            },


            "unknown": {

                "count": 0,

                "tasks": [],

                "analysis": {

                    "vanilla": 0,

                    "ftb_internal": 0,

                    "detected_mod": 0,

                    "manual": 0,

                    "unknown": 0

                }

            },


            "chapters": {

                "empty": [],

                "missing": []

            },


            "mods": {},


            "warnings": [],


            "status": True

        }



    # ======================================================
    # Alterar valores
    # ======================================================

    def set(
        self,
        category,
        key,
        value
    ):

        self.data[category][key] = value



    # ======================================================
    # Warnings
    # ======================================================

    def add_warning(
        self,
        warning
    ):

        self.data["warnings"].append(
            warning
        )



    # ======================================================
    # Export
    # ======================================================

    def to_dict(self):

        return self.data


    # ======================================================
    # Salvar JSON
    # ======================================================

    def save_json(self, path):

        import json

        with open(path, "w", encoding="utf8") as file:

            json.dump(self.data, file, indent=2, ensure_ascii=False)



    # ======================================================
    # Resumo terminal
    # ======================================================

    def summary(self):

        quests = self.data["quests"]

        deps = self.data["dependencies"]

        unknown = self.data["unknown"]



        print("\n================================")

        print(" Questbook Validation Report")

        print("================================")



        # ------------------------------
        # QUESTS
        # ------------------------------

        print("\nQUESTS")


        print(
            f" Files: {quests['files']}"
        )


        print(
            f" Loaded: {quests['loaded']}"
        )


        print(
            f" Missing: {quests['missing']}"
        )



        # ------------------------------
        # DEPENDENCIES
        # ------------------------------

        print("\nDEPENDENCIES")


        print(
            f" Broken: {deps['broken']}"
        )



        # ------------------------------
        # UNKNOWN ANALYSIS
        # ------------------------------

        print("\nUNKNOWN")


        analysis = unknown.get(
            "analysis",
            {}
        )


        print(
            f" Total quests: {unknown.get('count',0)}"
        )


        print(
            f" Vanilla: {analysis.get('vanilla',0)}"
        )


        print(
            f" FTB Internal: {analysis.get('ftb_internal',0)}"
        )


        print(
            f" Detected Mods: {analysis.get('detected_mod',0)}"
        )


        print(
            f" Manual: {analysis.get('manual',0)}"
        )


        print(
            f" Real Unknown: {analysis.get('unknown',0)}"
        )



        # ------------------------------
        # STATUS
        # ------------------------------

        print("\nSTATUS")


        if self.data["status"]:

            print(" OK")

        else:

            print(" FAILED")



        print("================================\n")