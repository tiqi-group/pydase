import enum


class TaskStatus(enum.Enum):
    """Possible statuses of a [`Task`][pydase.task.task.Task]."""

    RUNNING = "running"
    NOT_RUNNING = "not_running"
