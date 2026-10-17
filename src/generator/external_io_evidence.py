"""Check declared citation locations without inferring external I/O semantics."""

from pathlib import Path

from src.generator.external_io_contract import ExternalIOContract, ExternalIOContractError


def _line_count(root: Path, relative: str) -> int:
    try:
        source = (root / relative).resolve()
        if not source.is_relative_to(root):
            raise ExternalIOContractError(f"cited source escapes repository: {relative}")
        if not source.is_file():
            raise ExternalIOContractError(f"cited source is not a file: {relative}")
        with source.open(encoding="utf-8") as stream:
            return sum(1 for _ in stream)
    except (OSError, UnicodeError, RuntimeError) as error:
        raise ExternalIOContractError(f"cannot read cited source {relative}: {error}") from error


def verify_external_io_sources(contract: ExternalIOContract, root: Path) -> None:
    """Require real files and line ranges; this does not corroborate the claims."""
    try:
        repository = root.resolve(strict=True)
        if not repository.is_dir():
            raise ExternalIOContractError("external I/O repository must be a directory")
    except (OSError, RuntimeError) as error:
        raise ExternalIOContractError(f"cannot inspect external I/O repository: {error}") from error
    counts: dict[str, int] = {}
    for observation in contract.surfaces:
        for evidence in observation.evidence:
            if evidence.path not in counts:
                counts[evidence.path] = _line_count(repository, evidence.path)
            if (evidence.end_line or evidence.start_line) > counts[evidence.path]:
                raise ExternalIOContractError(f"citation exceeds source line count: {evidence.path}")
