"""Domain address structures."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedAddress:
    """Structured address parts extracted from a raw address."""

    country: str | None = None
    region: str | None = None
    city: str | None = None
    postal_code: str | None = None
    address_line: str | None = None

    @property
    def is_complete(self) -> bool:
        """Return whether parsed address is enough for normalized display."""
        result = all(
            (
                self.country,
                self.city,
                self.address_line,
            )
        )

        return result

    @property
    def has_data(self) -> bool:
        """Return whether at least one address part was parsed."""
        result = any(
            (
                self.country,
                self.region,
                self.city,
                self.postal_code,
                self.address_line,
            )
        )

        return result
