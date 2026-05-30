"""Rich rendering helpers for the Textual interface.

These builders are decoupled from the CLI presenter: they accept the Rich
classes (``panel_cls``, ``text_cls``, ``table_cls``) and an explicit ``width``
so they can render into a Textual ``RichLog`` sized by its pane rather than the
terminal.
"""
