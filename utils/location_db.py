import io
import json
from typing import Dict, List, Any
from abc import ABC, abstractmethod

class LocationRepository(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def getLocationFromToken(self, token:str, country_hint="ES") -> Dict[str, Any]:
        pass

    async def getLocationFromTokens(self, tokens: List[str], country_hint="ES") -> Dict[str, Any]:
        result:Dict[str, str] = {}
        for token in tokens:
            result = {**result, **(await self.getLocationFromToken(token))}
        return result

class JSONLocationRepository(LocationRepository):
    db_path:str
    db:Dict[str, Dict[str, Any]]

    def __init__(self, path:str):
        self.db_path = path
        self.db = None

    async def getLocationFromToken(self, token:str, country_hint="ES") -> Dict[str, Any]:
        if self.db == None:
            with io.open(self.db_path, "r", encoding="utf-8") as fd:
                self.db = json.load(fd)
        if token in self.db:
            return self.db[token]
        else:
            return {}