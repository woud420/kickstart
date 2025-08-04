from rich import print


def info(msg: str) -> None:
    print(f"[cyan]➤ {msg}")


def success(msg: str) -> None:
    print(f"[green]✔ {msg}")


def warn(msg: str) -> None:
    print(f"[yellow]⚠ {msg}")


def error(msg: str) -> None:
    print(f"[red]✖ {msg}")
