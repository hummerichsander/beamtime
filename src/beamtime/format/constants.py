"""File names, reserved names, statuses and limits of the storage format."""

from typing import Literal

RUN = "_run.json"
CONFIG = "_config.json"
CARD = "_run_card.json"
PREVIEW = "_preview.json"
METRICS = "_metrics.jsonl"
DATA = "_data.jsonl"
DATA_DIR = "_data"
EVENTS = "_events.jsonl"
OUTPUT = "_output.log"
OUTPUT_TAIL = "_output.tail.log"
OUTPUT_TAIL_PREV = "_output.tail.prev.log"
ARTIFACTS = "_artifacts.jsonl"
ENV_DIR = "_env"
TRASH = "_trash"

PROPOSAL = "proposal"
NOTES = "notes"
VIEW = "view"
MEMORY = "memory"
BLOCKS = "blocks"
AUTHORED = frozenset({PROPOSAL, NOTES, VIEW, MEMORY, BLOCKS})
RUN_ONLY = frozenset({"artifacts", "checkpoints"})

RunStatus = Literal["running", "finished", "failed", "killed"]
DerivedStatus = Literal["running", "finished", "failed", "killed", "lost"]
DataKind = Literal["table", "image", "text"]

HEARTBEAT_S = 30
LOST_AFTER_S = 300
CARD_EVERY_S = 180
MAX_BUCKETS = 512
EMA_SMOOTHING = 0.9
INLINE_CELLS = 1000
INLINE_TEXT = 4096
OUTPUT_CAP = 10 * 1024 * 1024


def key_to_path(key: str) -> str:
    """Turn a logged key into a path segment.

    :param key: A key such as ``grads/layer3``.
    :return: The segment used below ``_data/``, such as ``grads__layer3``."""
    return key.replace("/", "__")


def output_names(rank: int = 0) -> tuple[str, str, str]:
    """Name the head, tail and previous tail of a rank's captured output.

    :param rank: The rank; 0 is the main process.
    :return: The three file names."""
    if rank == 0:
        return OUTPUT, OUTPUT_TAIL, OUTPUT_TAIL_PREV
    return (
        f"_output.rank{rank}.log",
        f"_output.rank{rank}.tail.log",
        f"_output.rank{rank}.tail.prev.log",
    )
