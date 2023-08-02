import toml

pyproject = toml.load("pyproject.toml")
__version__ = pyproject["tool"]["poetry"]["version"]
__major__, __minor__, __patch__ = [int(v) for v in __version__.split(".")]
