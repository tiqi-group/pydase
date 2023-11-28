from importlib.metadata import distribution

__version__ = distribution("pydase").version
__major__, __minor__, __patch__ = (int(v) for v in __version__.split("."))
