from unittest import TestCase
from abc import ABC, abstractmethod

from mirage.util import DelegateRegistry


class TestDelegateRegistry(TestCase):

    def testDelegate(self):
        @DelegateRegistry.register
        class Subtype(Supertype):

            def greet(self):
                return "pass"

        self.assertTrue(DelegateRegistry.has_supertype(Supertype))
        delegate = DelegateRegistry.get_typedef(Supertype, "Subtype")
        self.assertEqual(delegate, Subtype)


class Supertype(ABC):

    @abstractmethod
    def greet(self):
        pass
