from rich import print

def info(msg): print(f"[cyan]➤ {msg}")
def success(msg): print(f"[green]✔ {msg}")
def warn(msg): print(f"[yellow]⚠ {msg}")
def error(msg): print(f"[red]✖ {msg}")
