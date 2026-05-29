"""Prompt history file helpers."""

from pathlib import Path


def cleanup_history_file(path: str | Path, max_entries: int) -> None:
    """Trim prompt_toolkit history file to the last max_entries commands."""
    history_path = Path(path)

    if not history_path.is_file():
        return

    lines = history_path.read_text(encoding="utf-8").splitlines()

    entries: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("# "):
            if current:
                entries.append(current)

            current = [line]
        elif current:
            current.append(line)

    if current:
        entries.append(current)

    if len(entries) > max_entries:
        trimmed_entries = entries[-max_entries:]
        content = "\n".join("\n".join(entry) for entry in trimmed_entries)

        history_path.write_text(
            f"\n{content}\n",
            encoding="utf-8",
            newline="\n",
        )
