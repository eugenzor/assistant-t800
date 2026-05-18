"""Textual-додаток ``AssistantApp``: TUI-інтерфейс для асистента T800.

Складається з двох панелей: ліва — для відображення контактів та довільної
інформації, права — для чату з AI-агентом. Запит користувача обробляється
у фоновому воркері, щоб не блокувати UI.
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Input, RichLog
from textual.worker import Worker, WorkerState

from assistant_t800.ai.agent import run_chat
from assistant_t800.ai.deps import AgentDeps
from assistant_t800.interfaces.textual.presenter import TextualPresenter
from assistant_t800.repositories.contacts import ContactsRepository
from assistant_t800.services.contacts import ContactsService


class AssistantApp(App):
    """Textual-застосунок асистента з двопанельним інтерфейсом.

    Ліва панель (``#display-pane``) показує контакти або довільний
    текст від агента. Права панель (``#chat-pane``) містить історію
    чату та поле вводу запиту користувача.
    """

    # CSS для розкладки інтерфейсу
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
    }

    #chat-pane {
        width: 30%;
        border: round $accent;
    }

    #chat-log {
        height: 1fr;
        padding: 1;
    }

    #chat-input {
        dock: bottom;
        height: 3;
    }
    """

    # Заголовок і підзаголовок вікна
    TITLE = "Асистент T800"
    SUB_TITLE = "Режим ШІ"

    def compose(self) -> ComposeResult:
        """Складає розкладку віджетів: заголовок, дві панелі та футер."""
        yield Header()
        with Horizontal(id="main"):
            yield RichLog(id="display-pane", markup=True, highlight=True, wrap=True)
            with Vertical(id="chat-pane"):
                yield RichLog(id="chat-log", markup=True, wrap=True)
                yield Input(placeholder="Запитайте T800...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        """Ініціалізує службові об'єкти після монтування інтерфейсу."""
        # Кешуємо посилання на віджети, щоб не шукати їх щоразу
        self._chat_log: RichLog = self.query_one("#chat-log", RichLog)
        self._display_log: RichLog = self.query_one("#display-pane", RichLog)
        self._input: Input = self.query_one("#chat-input", Input)
        # Прапорець, який блокує паралельну обробку нового повідомлення
        self._busy = False

        # Створюємо доменні об'єкти та залежності, що передаються агенту
        self._repo = ContactsRepository()
        self._service = ContactsService(self._repo)
        self._presenter = TextualPresenter(self._display_log, self)
        self._deps = AgentDeps(
            contacts_service=self._service, presenter=self._presenter
        )

        # Привітальне повідомлення українською
        self._chat_log.write(
            "[bold green]T800:[/bold green] Готовий до роботи. "
            "Спробуйте: «Додай контакт на ім'я Аліса»."
        )
        # Передаємо фокус у поле вводу
        self._input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обробник підтвердження вводу у полі чату."""
        message = event.value.strip()
        if not message:
            # Ігноруємо порожні повідомлення
            return
        if self._busy:
            # Поки виконується попередній запит — попереджаємо користувача
            self._chat_log.write(
                "[yellow](ще обробляю попереднє повідомлення...)[/yellow]"
            )
            return
        # Скидаємо поле вводу та фіксуємо повідомлення в історії чату
        self._input.value = ""
        self._chat_log.write(f"[bold cyan]Ви:[/bold cyan] {message}")
        self._busy = True
        self._run_agent(message)

    def _run_agent(self, message: str) -> None:
        """Запускає виклик AI-агента у фоновому потоці."""

        def _call() -> str:
            # Обгортка, що ловить помилки та перетворює їх на текст відповіді
            try:
                return run_chat(message, self._deps)
            except Exception as exc:
                return f"[error] {type(exc).__name__}: {exc}"

        # Виконуємо у фоновому воркері, щоб не блокувати UI
        self.run_worker(_call, thread=True, exclusive=True, name="agent")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Реагує на зміни стану фонового воркера й оновлює UI."""
        if event.worker.name != "agent":
            # Нас цікавить лише воркер агента
            return
        if event.state is WorkerState.SUCCESS:
            reply = event.worker.result or ""
            if reply.startswith("[error]"):
                # Внутрішня помилка під час виклику агента
                self._chat_log.write(f"[bold red]T800:[/bold red] {reply}")
            else:
                self._chat_log.write(f"[bold green]T800:[/bold green] {reply}")
            self._busy = False
        elif event.state is WorkerState.ERROR:
            # Збій воркера — повідомляємо користувача українською
            self._chat_log.write(
                f"[bold red]T800:[/bold red] збій воркера: {event.worker.error}"
            )
            self._busy = False


def run_textual() -> None:
    """Створює та запускає Textual-застосунок асистента."""
    AssistantApp().run()
