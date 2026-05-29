"""Unit tests for CLI command registry metadata."""

from assistant_t800.interfaces.cli.commands import build_registry


def test_registry_contains_edit_tags_command():
    registry = build_registry()

    assert "edit-tags" in registry
    command = registry["edit-tags"]
    assert command.name == "edit-tags"
    assert command.parse_args is False
    assert command.syntax == "edit-tags <name> [tags]"


def test_registry_does_not_expose_legacy_tag_commands():
    registry = build_registry()

    assert "add-tag" not in registry
    assert "remove-tag" not in registry
