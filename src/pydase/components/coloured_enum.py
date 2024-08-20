from enum import Enum


class ColouredEnum(Enum):
    """
    Represents a UI element that can display colour-coded text based on its value.

    This class extends the standard Enum but requires its values to be valid CSS
    colour codes. Supported colour formats include:

    - Hexadecimal colours
    - Hexadecimal colours with transparency
    - RGB colours
    - RGBA colours
    - HSL colours
    - HSLA colours
    - Predefined/Cross-browser colour names

    Refer to the this website for more details on colour formats:
    (https://www.w3schools.com/cssref/css_colours_legal.php)

    The behavior of this component in the UI depends on how it's defined in the data
    service:

    - As property with a setter or as attribute: Renders as a dropdown menu, allowing
    users to select and change its value from the frontend.
    - As property without a setter: Displays as a coloured box with the key of the
    `ColouredEnum` as text inside, serving as a visual indicator without user
    interaction.

    Example:
        ```python
        import pydase.components as pyc
        import pydase

        class MyStatus(pyc.ColouredEnum):
            PENDING = "#FFA500"  # Orange
            RUNNING = "#0000FF80"  # Transparent Blue
            PAUSED = "rgb(169, 169, 169)"  # Dark Gray
            RETRYING = "rgba(255, 255, 0, 0.3)"  # Transparent Yellow
            COMPLETED = "hsl(120, 100%, 50%)"  # Green
            FAILED = "hsla(0, 100%, 50%, 0.7)"  # Transparent Red
            CANCELLED = "SlateGray"  # Slate Gray

        class StatusExample(pydase.DataService):
            _status = MyStatus.RUNNING

            @property
            def status(self) -> MyStatus:
                return self._status

            @status.setter
            def status(self, value: MyStatus) -> None:
                # Custom logic here...
                self._status = value

        # Example usage:
        my_service = StatusExample()
        my_service.status = MyStatus.FAILED
        ```

    Note:
        Each enumeration name and value must be unique. This means that you should use
        different colour formats when you want to use a colour multiple times.
    """
