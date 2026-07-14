from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


class ModDetector:
    """
    Responsável por detectar mods utilizados por quests.

    Possui:

    detect()
        Retorna o mod principal.

    detect_all()
        Retorna todos os mods encontrados.

    has_vanilla_reference()
        Detecta referências vanilla minecraft.

    A detecção é baseada em "resource locations" válidas do Minecraft
    (namespace:path), aceitando apenas namespaces que respeitem
    [a-z0-9_.-]+ e rejeitando URLs, placeholders, texto livre e
    qualquer estrutura que não represente uma registry real.
    """

    IGNORE_PREFIXES = {
        "",
        "ftbquests",
        "minecraft",
    }

    VANILLA_IDS = {
        "minecraft",
        "forge",
        "neoforge",
    }

    SIMPLE_KEYS = {
        "item",
        "block",
        "fluid",
        "entity",
        "id",
        "name",
    }

    # Namespace: apenas minúsculas, dígitos, '_', '.', '-'
    _NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")

    # Path: minúsculas, dígitos, '_', '.', '-', '/'
    _PATH_RE = re.compile(r"^[a-z0-9_./-]+$")

    # Esquemas de URL / protocolos que jamais são namespaces de mod
    _URL_SCHEMES = {
        "http",
        "https",
        "ftp",
        "ftps",
        "ws",
        "wss",
        "mailto",
        "file",
        "urn",
        "data",
    }

    # ==========================================================
    # Detecção principal
    # ==========================================================

    def detect(self, quest_data: Any) -> str:
        """
        Retorna o mod principal da quest.

        Para nunca divergir de `detect_all()` (a fonte de verdade para
        `quest.mods`), o mod principal é sempre um elemento do mesmo
        conjunto retornado por `detect_all()`. A ordem de prioridade
        legada (tasks -> rewards -> busca ampla) é preservada apenas
        para decidir QUAL mod, dentre os encontrados, é o principal —
        nunca para decidir SE algum mod foi encontrado.
        """

        mods = self.detect_all(quest_data)

        if not mods:
            return "Unknown"

        primary = self._find_primary_candidate(quest_data)

        if primary in mods:
            return primary

        # Segurança: caso a busca priorizada não encontre nada (não
        # deveria acontecer, já que usa a mesma extração), cai para o
        # menor mod em ordem alfabética, mantendo o resultado
        # determinístico e sempre coerente com `mods`.
        return min(mods)

    def _find_primary_candidate(self, quest_data: Any) -> str | None:
        """
        Lógica de prioridade legada usada apenas para desempate entre
        os mods já encontrados por `detect_all()`: primeiro mod
        encontrado nas tasks, depois nas rewards, depois em qualquer
        outro lugar da quest.
        """

        for task in quest_data.get("tasks", []):
            mod = self.detect_task(task)
            if mod:
                return mod

        for reward in quest_data.get("rewards", []):
            mod = self.detect_reward(reward)
            if mod:
                return mod

        return self.search_recursive(quest_data)

    # ==========================================================
    # Todos os mods
    # ==========================================================

    def detect_all(self, quest_data: Any) -> set[str]:
        mods: set[str] = set()
        self.collect_recursive(quest_data, mods)
        return mods

    # ==========================================================
    # Tasks / Rewards
    # ==========================================================

    def detect_task(self, task):
        return self.search_recursive(task)

    def detect_reward(self, reward):
        return self.search_recursive(reward)

    # ==========================================================
    # Busca simples (retorna o primeiro mod encontrado)
    # ==========================================================

    def search_recursive(self, value):
        if isinstance(value, Mapping):
            for key, val in value.items():
                mod = self.extract_mod(key)
                if mod:
                    return mod

                if key in self.SIMPLE_KEYS:
                    mod = self.extract_mod(val)
                    if mod:
                        return mod

                mod = self.search_recursive(val)
                if mod:
                    return mod

        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for element in value:
                mod = self.search_recursive(element)
                if mod:
                    return mod

        elif isinstance(value, str):
            mod = self.extract_mod(value)
            if mod:
                return mod

        return None

    # ==========================================================
    # Coleta completa (todos os mods encontrados)
    # ==========================================================

    def collect_recursive(self, value, result: set[str]):
        if isinstance(value, Mapping):
            for key, val in value.items():
                mod = self.extract_mod(key)
                if mod:
                    result.add(mod)

                if key in self.SIMPLE_KEYS:
                    mod = self.extract_mod(val)
                    if mod:
                        result.add(mod)

                self.collect_recursive(val, result)

        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for element in value:
                self.collect_recursive(element, result)

        elif isinstance(value, str):
            mod = self.extract_mod(value)
            if mod:
                result.add(mod)

    # ==========================================================
    # Vanilla detector
    # ==========================================================

    def has_vanilla_reference(self, value) -> bool:
        if isinstance(value, Mapping):
            for key, val in value.items():
                namespace = self.extract_namespace_raw(key)
                if namespace in self.VANILLA_IDS:
                    return True

                if self.has_vanilla_reference(val):
                    return True

        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                if self.has_vanilla_reference(item):
                    return True

        elif isinstance(value, str):
            namespace = self.extract_namespace_raw(value)
            if namespace in self.VANILLA_IDS:
                return True

        return False

    # ==========================================================
    # Extração bruta de namespace (sem filtragem de IGNORE_PREFIXES)
    # ==========================================================

    def extract_namespace_raw(self, value) -> str | None:
        """
        Extrai o namespace de uma "resource location" válida do
        Minecraft (namespace:path), sem aplicar IGNORE_PREFIXES.

        Retorna None para:
          - valores que não sejam strings;
          - URLs (http://, https://, etc.);
          - placeholders e texto livre;
          - qualquer string que não siga o formato namespace:path
            com caracteres válidos em ambas as partes.
        """

        if not isinstance(value, str):
            return None

        text = value.strip()

        # Remove aspas residuais de literais SNBT (ex: "\"minecraft:diamond\"")
        text = text.strip("\"'")
        text = text.strip()

        if not text or ":" not in text:
            return None

        # URLs (scheme://...) nunca são namespaces
        if "//" in text:
            return None

        prefix, _, rest = text.partition(":")
        prefix = prefix.strip()
        rest = rest.strip()

        if not prefix or not rest:
            return None

        # Namespaces têm apenas um segmento (não pode haver outro ':' no meio)
        if ":" in rest:
            # NBT paths com múltiplos ':' (ex: "a:b:c") não são resource locations válidas
            return None

        if not self._NAMESPACE_RE.match(prefix):
            return None

        # Um namespace real sempre contém ao menos uma letra (evita falsos
        # positivos com strings puramente numéricas, como horários "12:30")
        if not any(c.isalpha() for c in prefix):
            return None

        if prefix in self._URL_SCHEMES:
            return None

        # A parte do path também deve ter formato de registry (evita texto livre
        # como "Note: this is important" ou "Aviso: leia com atenção").
        #
        # Alguns mods (ex.: GregTech) serializam itens como
        # "namespace:path meta count" (ex.: "gregtech:machine 1 511"),
        # onde só o primeiro token é o registry path real e o restante
        # são tokens numéricos (meta/count). Nesse caso, validamos
        # apenas o primeiro token como path e exigimos que os tokens
        # seguintes sejam puramente numéricos — em vez de rejeitar o
        # valor inteiro só por conter espaço.

        path_tokens = rest.split()

        path = path_tokens[0]

        extra_tokens = path_tokens[1:]

        if not self._PATH_RE.match(path):
            return None

        if extra_tokens and not all(
            token.isdigit() for token in extra_tokens
        ):
            return None

        return prefix

    # ==========================================================
    # Extrair namespace de mod (com filtragem de IGNORE_PREFIXES)
    # ==========================================================

    def extract_mod(self, value) -> str | None:
        namespace = self.extract_namespace_raw(value)

        if namespace is None:
            return None

        if namespace in self.IGNORE_PREFIXES:
            return None

        return namespace