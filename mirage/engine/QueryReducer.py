from abc import ABC, abstractmethod, abstractproperty

class QueryReducer(ABC):
    """
    Abstract class for performing a query and collecting the results.
    """

    @abstractmethod
    def merge(self, other):
        """
        Merge this reducer's result with the result from another.
        """
        pass

    @abstractmethod
    def query_points(self):
        """
        Returns an iterator, where each element is a tuple.

        The first element of each tuple is a unique ID for that query point.
        It should be passed into the `set_query_magnitude` method to save the
        result of that query.

        The second element of each tuple is the query's information as a
        (location, radius) tuple.
        """
        pass

    @abstractmethod
    def set_query_magnitude(self, query_id, value):
        """
        Given a query location's id and value, save the result into the reducer's
        internal storage.
        """
        pass

    @abstractproperty
    def value(self):
        pass