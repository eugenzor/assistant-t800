"""Textual TUI application for the T800 assistant."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, RichLog, Static
from textual.worker import Worker, WorkerState

from assistant_t800.ai.agent import run_chat
from assistant_t800.ai.deps import AgentDeps
from assistant_t800.interfaces.textual.presenter import TextualPresenter
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService
from assistant_t800.storage import AssistantStorage


class AssistantApp(App):
    """Two-pane Textual application with contact display (``#display-pane``)
    and AI chat (``#chat-pane``).
    """

    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        height: 1fr;
    }

    #display-pane {
        width: 70%;
        border: round $accent;
        padding: 1;
        overflow-x: hidden;
    }

    #chat-pane {
        width: 30%;
        border: round $accent;
    }

    #chat-log {
        height: 1fr;
        padding: 1;
        overflow-x: hidden;
    }

    .chat-message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #chat-input {
        dock: bottom;
        height: 3;
    }
    """

    TITLE = "Асистент T800"
    SUB_TITLE = "Режим ШІ"

    # Keep Ctrl+C available for text copying; application exit uses Ctrl+Q.
    BINDINGS = [
        Binding("ctrl+c", "screen.copy_text", "Копіювати", show=True),
        Binding("ctrl+q", "quit", "Вихід", show=True),
    ]

    _LOADER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, contacts_repository: ContactsRepository) -> None:
        """Initialize the application with shared contacts repository."""
        super().__init__()
        self._initial_repo = contacts_repository

    def compose(self) -> ComposeResult:
        """Build the application layout."""
        yield Header()

        with Horizontal(id="main"):
            yield RichLog(
                id="display-pane",
                markup=True,
                highlight=True,
                wrap=True,
                min_width=0,
            )

            with Vertical(id="chat-pane"):
                yield VerticalScroll(id="chat-log")
                yield Input(placeholder="Запитайте Арні...", id="chat-input")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize UI state and runtime dependencies."""
        self._chat_log: VerticalScroll = self.query_one("#chat-log", VerticalScroll)
        self._display_log: RichLog = self.query_one("#display-pane", RichLog)
        self._input: Input = self.query_one("#chat-input", Input)

        self._busy = False
        self._loader: Static | None = None
        self._loader_frame = 0
        self._loader_timer = None

        self._repo = self._initial_repo
        self._service = ContactsService(self._repo)
        self._presenter = TextualPresenter(self._display_log, self)
        self._deps = AgentDeps(
            contacts_service=self._service,
            presenter=self._presenter,
        )

        self._add_message(
            "[bold green]Арні:[/bold green] Готовий до роботи. "
            "Спробуйте: «Додай контакт на ім'я Аліса»."
        )
        self._input.focus()

    def _add_message(self, markup: str) -> Static:
        """Append a chat message and scroll the chat log to the bottom."""
        message = Static(markup, markup=True, classes="chat-message")
        self._chat_log.mount(message)
        self.call_after_refresh(self._chat_log.scroll_end, animate=False)

        return message

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle submitted chat input."""
        message = event.value.strip()

        if not message:
            return

        if self._busy:
            self._add_message(
                "[yellow](ще обробляю попереднє повідомлення...)[/yellow]"
            )
            return

        self._input.value = ""
        self._add_message(f"[bold cyan]Ви:[/bold cyan] {message}")

        self._busy = True
        self._start_loader()
        self._run_agent(message)

    def _start_loader(self) -> None:
        """Show an animated placeholder for the pending AI response."""
        self._loader_frame = 0
        # TODO: should be replaced with reply text in future
        self._loader = self._add_message("")
        self._loader_timer = self.set_interval(0.1, self._tick_loader)
        self._tick_loader()

    def _tick_loader(self) -> None:
        """Render the next loader animation frame."""
        if self._loader is None:
            return

        spinner = self._LOADER_FRAMES[self._loader_frame % len(self._LOADER_FRAMES)]
        self._loader_frame += 1
        self._loader.update(
            f"[bold green]Арні:[/bold green] [italic]{spinner} обробляю запит…[/italic]"
        )

    def _finish_loader(self, markup: str) -> None:
        """Replace the loader placeholder with the final response."""
        if self._loader_timer is not None:
            self._loader_timer.stop()
            self._loader_timer = None

        if self._loader is not None:
            self._loader.update(markup)
            self._loader = None
        else:
            self._add_message(markup)

        self.call_after_refresh(self._chat_log.scroll_end, animate=False)

    def _run_agent(self, message: str) -> None:
        """Run the AI agent call in a background worker."""

        def _call() -> str:
            """Execute the agent call and convert errors to UI-safe text."""
            try:
                return run_chat(message, self._deps)
            except Exception as exc:
                return f"[error] {type(exc).__name__}: {exc}"

        self.run_worker(_call, thread=True, exclusive=True, name="agent")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Update the UI after background worker state changes."""
        if event.worker.name != "agent":
            return

        if event.state is WorkerState.SUCCESS:
            reply = event.worker.result or ""

            if reply.startswith("[error]"):
                self._finish_loader(f"[bold red]Арні:[/bold red] {reply}")
            else:
                self._finish_loader(f"[bold green]Арні:[/bold green] {reply}")

            self._busy = False

        elif event.state is WorkerState.ERROR:
            self._finish_loader(
                f"[bold red]Арні:[/bold red] збій воркера: {event.worker.error}"
            )
            self._busy = False


def run_textual(pickle_db: Path) -> None:
    """Run the Textual assistant application."""

    with AssistantStorage(path=pickle_db) as repository:
        AssistantApp(repository).run()
