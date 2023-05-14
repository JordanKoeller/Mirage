from typing import List, Dict, Optional, Type, Any
from inspect import getmro, isabstract


class DelegateRegistry:
    __delegate_registry: Dict[str, Dict[str, type]] = {}

    @staticmethod
    def register(klass):
        """
        This method is a decorator that should be wrapped around classes that implement
        an abstract class.

        It will add the class definition to a registry, useful for deserializing dictionaries
        into registered class instances.
        """
        type_resolution = getmro(klass)
        immediate_supertype = type_resolution[1]
        if isabstract(immediate_supertype):
            supertype_name = immediate_supertype.__name__
            subtype_name = klass.__name__
            if not supertype_name in DelegateRegistry.__delegate_registry:
                DelegateRegistry.__delegate_registry[supertype_name] = {}
            DelegateRegistry.__delegate_registry[supertype_name][subtype_name] = klass
        return klass

    @staticmethod
    def get_typedef(supertype: Type[Any], delegate_name: str) -> Optional[type]:
        """
        Get a type definition from the delegate registry by name.

        Args:

          + supertype (Type[Any]): The supertype to search the registry for a delegate.
          + delegate_name (str): The delegate name to look up.

        Returns:

          + Optional[type] The delegate definition found in the registry, if found.
        """
        supertype_tree = DelegateRegistry.__delegate_registry.get(
            supertype.__name__, None
        )
        if supertype_tree:
            return supertype_tree.get(delegate_name, None)
        return None

    @staticmethod
    def has_supertype(supertype: Type[Any]) -> bool:
        return supertype.__name__ in DelegateRegistry.__delegate_registry
