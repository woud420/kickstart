from rich import print
from rich.text import Text


def info(msg: str) -> None:
    print(Text(f"➤ {msg}", style="cyan"))


def success(msg: str) -> None:
    print(Text(f"✔ {msg}", style="green"))


def warn(msg: str) -> None:
    print(Text(f"⚠ {msg}", style="yellow"))


def error(msg: str) -> None:
    print(Text(f"✖ {msg}", style="red"))
