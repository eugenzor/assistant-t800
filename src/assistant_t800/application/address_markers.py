"""Static address parsing markers and country display formats."""

import re
from enum import Enum
from typing import Final


class CountryAddressFormat(Enum):
    """Country-specific address display format rules."""

    UA = ("Україна", "{value} обл.", "м. {value}")
    PL = ("Polska", "{value}", "{value}")
    CZ = ("Česko", "{value}", "{value}")
    SK = ("Slovensko", "{value}", "{value}")
    DE = ("Deutschland", "{value}", "{value}")
    AT = ("Österreich", "{value}", "{value}")
    CH = ("Schweiz", "{value}", "{value}")
    NL = ("Nederland", "{value}", "{value}")
    BE = ("België", "{value}", "{value}")
    FR = ("France", "{value}", "{value}")
    IT = ("Italia", "{value}", "{value}")
    ES = ("España", "{value}", "{value}")
    PT = ("Portugal", "{value}", "{value}")
    IE = ("Ireland", "{value}", "{value}")
    GB = ("United Kingdom", "{value}", "{value}")
    US = ("USA", "{value}", "{value}")
    CA = ("Canada", "{value}", "{value}")
    MD = ("Moldova", "{value}", "{value}")
    RO = ("România", "{value}", "{value}")
    HU = ("Magyarország", "{value}", "{value}")
    LT = ("Lietuva", "{value}", "{value}")
    LV = ("Latvija", "{value}", "{value}")
    EE = ("Eesti", "{value}", "{value}")

    def __init__(
        self,
        country: str,
        region_template: str,
        city_template: str,
    ) -> None:
        self._country = country
        self._region_template = region_template
        self._city_template = city_template

    @property
    def country(self) -> str:
        """Return normalized country display name."""
        return self._country

    def region(self, value: str) -> str:
        """Format region for this country."""
        result = self._region_template.format(value=value)

        return result

    def city(self, value: str) -> str:
        """Format city for this country."""
        result = self._city_template.format(value=value)

        return result


class AddressMarkers:
    """Grouped marker datasets used by deterministic address parser."""

    COUNTRY_ALIASES: Final[dict[CountryAddressFormat, tuple[str, ...]]] = {
        CountryAddressFormat.UA: (
            "ua",
            "ukr",
            "ukraine",
            "україна",
            "украина",
        ),
        CountryAddressFormat.PL: (
            "pl",
            "pol",
            "polska",
            "poland",
            "польща",
            "польша",
        ),
        CountryAddressFormat.CZ: (
            "cz",
            "cze",
            "česko",
            "cesko",
            "czechia",
            "czech republic",
            "чехія",
            "чехия",
        ),
        CountryAddressFormat.SK: (
            "sk",
            "svk",
            "slovensko",
            "slovakia",
            "словаччина",
            "словакия",
        ),
        CountryAddressFormat.DE: (
            "de",
            "ger",
            "deutschland",
            "germany",
            "німеччина",
            "германія",
            "германия",
        ),
        CountryAddressFormat.AT: (
            "at",
            "aut",
            "österreich",
            "osterreich",
            "austria",
            "австрія",
            "австрия",
        ),
        CountryAddressFormat.CH: (
            "ch",
            "che",
            "schweiz",
            "suisse",
            "switzerland",
            "швейцарія",
            "швейцария",
        ),
        CountryAddressFormat.NL: (
            "nl",
            "nld",
            "nederland",
            "netherlands",
            "нідерланди",
            "нидерланды",
        ),
        CountryAddressFormat.BE: (
            "be",
            "bel",
            "belgium",
            "belgië",
            "belgie",
            "бельгія",
            "бельгия",
        ),
        CountryAddressFormat.FR: (
            "fr",
            "fra",
            "france",
            "франція",
            "франция",
        ),
        CountryAddressFormat.IT: (
            "it",
            "ita",
            "italia",
            "italy",
            "італія",
            "италия",
        ),
        CountryAddressFormat.ES: (
            "es",
            "esp",
            "españa",
            "espana",
            "spain",
            "іспанія",
            "испания",
        ),
        CountryAddressFormat.PT: (
            "pt",
            "prt",
            "portugal",
            "португалія",
            "португалия",
        ),
        CountryAddressFormat.IE: (
            "ie",
            "irl",
            "ireland",
            "ірландія",
            "ирландия",
        ),
        CountryAddressFormat.GB: (
            "gb",
            "uk",
            "united kingdom",
            "great britain",
            "britain",
            "британія",
            "британия",
        ),
        CountryAddressFormat.US: (
            "us",
            "usa",
            "united states",
            "united states of america",
            "сша",
        ),
        CountryAddressFormat.CA: (
            "ca",
            "can",
            "canada",
            "канада",
        ),
        CountryAddressFormat.MD: (
            "md",
            "mda",
            "moldova",
            "молдова",
        ),
        CountryAddressFormat.RO: (
            "ro",
            "rou",
            "românia",
            "romania",
            "румунія",
            "румыния",
        ),
        CountryAddressFormat.HU: (
            "hu",
            "hun",
            "magyarország",
            "magyarorszag",
            "hungary",
            "угорщина",
            "венгрия",
        ),
        CountryAddressFormat.LT: (
            "lt",
            "ltu",
            "lietuva",
            "lithuania",
            "литва",
        ),
        CountryAddressFormat.LV: (
            "lv",
            "lva",
            "latvija",
            "latvia",
            "латвія",
            "латвия",
        ),
        CountryAddressFormat.EE: (
            "ee",
            "est",
            "eesti",
            "estonia",
            "естонія",
            "эстония",
        ),
    }

    REGION: Final[frozenset[str]] = frozenset(
        {
            "обл",
            "область",
            "район",
            "р-н",
            "region",
            "province",
            "state",
            "county",
            "woj",
            "województwo",
            "wojewodztwo",
            "pow",
            "powiat",
            "kraj",
            "okres",
            "bundesland",
            "land",
        }
    )

    CITY: Final[frozenset[str]] = frozenset(
        {
            "м",
            "місто",
            "с",
            "село",
            "смт",
            "city",
            "town",
            "village",
            "miasto",
            "město",
            "mesto",
            "obec",
            "stadt",
            "ort",
            "gemeinde",
            "ville",
            "commune",
            "ciudad",
            "città",
            "citta",
            "cidade",
        }
    )

    STREET: Final[frozenset[str]] = frozenset(
        {
            "вул",
            "вулиця",
            "просп",
            "проспект",
            "пров",
            "провулок",
            "площа",
            "бул",
            "бульвар",
            "шосе",
            "узвіз",
            "набережна",
            "street",
            "st",
            "avenue",
            "ave",
            "road",
            "rd",
            "boulevard",
            "blvd",
            "drive",
            "dr",
            "lane",
            "ln",
            "court",
            "ct",
            "place",
            "pl",
            "square",
            "sq",
            "ul",
            "ulica",
            "aleja",
            "al",
            "plac",
            "ulice",
            "náměstí",
            "namesti",
            "námestie",
            "namestie",
            "třída",
            "trida",
            "straße",
            "strasse",
            "str",
            "platz",
            "weg",
            "allee",
            "gasse",
            "ring",
            "rue",
            "chemin",
            "route",
            "via",
            "viale",
            "piazza",
            "corso",
            "calle",
            "avenida",
            "praça",
            "praca",
            "rua",
        }
    )

    POSTAL_CODE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
        re.compile(r"\b\d{2}-\d{3}\b"),
        re.compile(r"\b\d{3}\s?\d{2}\b"),
        re.compile(r"\b\d{5}(?:-\d{4})?\b"),
        re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.IGNORECASE),
    )

    CITY_COUNTRY_HINTS: Final[dict[str, CountryAddressFormat]] = {
        "київ": CountryAddressFormat.UA,
        "kyiv": CountryAddressFormat.UA,
        "kiev": CountryAddressFormat.UA,
        "львів": CountryAddressFormat.UA,
        "lviv": CountryAddressFormat.UA,
        "варшава": CountryAddressFormat.PL,
        "warszawa": CountryAddressFormat.PL,
        "warsaw": CountryAddressFormat.PL,
        "krakow": CountryAddressFormat.PL,
        "kraków": CountryAddressFormat.PL,
        "wroclaw": CountryAddressFormat.PL,
        "wrocław": CountryAddressFormat.PL,
        "prague": CountryAddressFormat.CZ,
        "praha": CountryAddressFormat.CZ,
        "brno": CountryAddressFormat.CZ,
        "berlin": CountryAddressFormat.DE,
        "munich": CountryAddressFormat.DE,
        "münchen": CountryAddressFormat.DE,
        "wien": CountryAddressFormat.AT,
        "vienna": CountryAddressFormat.AT,
        "bratislava": CountryAddressFormat.SK,
        "new york": CountryAddressFormat.US,
        "london": CountryAddressFormat.GB,
    }

    @classmethod
    def normalize_marker(cls, value: str) -> str:
        """Normalize marker token for lookup."""
        result = value.strip().casefold().rstrip(".")

        return result

    @classmethod
    def resolve_country(cls, value: str) -> CountryAddressFormat | None:
        """Resolve country address format by grouped aliases."""
        candidate = value.strip().casefold()
        result = None

        if candidate:
            for country, aliases in cls.COUNTRY_ALIASES.items():
                if candidate in aliases:
                    result = country
                    break

        return result
