"""Collect creation step failures before success or remote side effects."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from src.utils.error_handling import ErrorCollector


@dataclass(frozen=True)
class CreateStep:
    """A required local operation and the failure reported to the user."""

    operation: Callable[[], bool]
    failure_message: str


def run_create_steps(steps: Sequence[CreateStep]) -> ErrorCollector:
    """Run each step once, recording false results and raised exceptions alike."""
    collector = ErrorCollector("Project creation")
    for step in steps:
        collector.increment_total()
        try:
            succeeded = step.operation()
        except Exception as error:
            collector.add_error(f"{step.failure_message}: {error}")
        else:
            if succeeded:
                collector.increment_success()
            else:
                collector.add_error(step.failure_message)
    return collector
