import pydase.version
import toml


def test_project_version() -> None:
    pyproject = toml.load("pyproject.toml")
    pydase_pyroject_version = pyproject["tool"]["poetry"]["version"]
    assert pydase.version.__version__ == pydase_pyroject_version
