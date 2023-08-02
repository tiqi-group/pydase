from .data_service import DataService


class NumberSlider(DataService):
    def __init__(
        self,
        value: float | int = 0,
        min: int = 0,
        max: int = 100,
        step_size: float = 1.0,
    ) -> None:
        self.min = min
        self.max = max
        self.value = value
        self.step_size = step_size
        super().__init__()
