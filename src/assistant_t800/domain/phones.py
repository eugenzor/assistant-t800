"""Domain phone structures."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedPhone:
    """Structured phone metadata returned by rule or AI normalization."""

    normalized: str
    country: str | None = None
    owner: str | None = None
    is_mobile: bool | None = None
    is_valid: bool = False

    @property
    def has_owner(self) -> bool:
        """Return whether operator or city was identified."""
        result = bool(self.owner)

        return result
