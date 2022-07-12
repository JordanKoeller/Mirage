from abc import ABC, abstractstaticmethod

class Registerable(ABC):

    @abstractstaticmethod
    def identifier() -> str:
        raise NotImplementedError("identifier not implemented")    

class Registry:

    def __init__(self):
        self._registry = {}

    def register(self, klass):
        self._registry[klass.identifier()] = klass
        return klass

    def get(self, identifier: str):
        return self._registry[identifier]

ReducerRegistry = Registry()