class SNBTCleaner:
    """
    Responsável por limpar estruturas SNBT
    antes da gravação.

    Trabalha somente em memória.
    """



    def extract_mod_id(
        self,
        value
    ) -> str | None:

        # Reward "item" pode vir como string simples ("mod:thing")
        # ou como compound NBT ("item: {id: \"mod:thing\", Count: 1b}").
        # Nesse segundo caso, o id real está na chave "id" (ou "Item",
        # variante usada por alguns mods), não no valor bruto.

        if isinstance(value, dict):

            value = value.get(
                "id",
                value.get(
                    "Item",
                    ""
                )
            )


        text = str(value)


        if ":" not in text:

            return None


        return text.split(
            ":",
            1
        )[0].strip('"').strip()



    # --------------------------------------------------
    # Dependências
    # --------------------------------------------------

    def clean_dependencies(
        self,
        data,
        valid_quests: set[str]
    ):


        if "dependencies" not in data:

            return 0



        old = list(
            data["dependencies"]
        )


        new = [

            dep

            for dep in old

            if str(dep) in valid_quests

        ]


        removed = len(old) - len(new)



        data["dependencies"] = new


        return removed



    # --------------------------------------------------
    # Rewards
    # --------------------------------------------------

    def clean_rewards(
        self,
        data,
        removed_mods: set[str]
    ):


        if "rewards" not in data:

            return 0



        old = list(
            data["rewards"]
        )


        new = []

        removed = 0



        for reward in old:


            item = reward.get(
                "item",
                ""
            )


            mod_id = self.extract_mod_id(
                item
            )


            if mod_id in removed_mods:

                removed += 1

                continue



            new.append(
                reward
            )



        data["rewards"] = new


        return removed