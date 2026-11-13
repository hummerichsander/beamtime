"""Running a plan: one change after the other, stopping at the first that fails."""

from collections.abc import Callable

from beamtime.setup.plan import Change


class ApplyError(Exception):
    """A change failed; what ran before it stays done."""

    def __init__(self, *, done: list[Change], failed: Change, error: Exception) -> None:
        """Record where the apply stopped.

        :param done: The changes that ran.
        :param failed: The change that raised.
        :param error: What it raised."""
        super().__init__(f"{failed.label}: {error}")
        self.done = done
        self.failed = failed
        self.error = error


def apply(changes: list[Change], say: Callable[[str], None] | None = None) -> list[Change]:
    """Run the changes in order and say one line for each as it is done.

    :param changes: The plan.
    :param say: Called with each line; default silent.
    :return: The changes done.
    :raises ApplyError: A change raised; the later ones did not run."""
    done: list[Change] = []
    for change in changes:
        try:
            result = change.run()
        except Exception as e:
            raise ApplyError(done=done, failed=change, error=e) from e
        done.append(change)
        if say is not None:
            say(f"{change.label}: {result}" if result else change.label)
    return done
