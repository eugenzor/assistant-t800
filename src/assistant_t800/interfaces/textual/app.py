"""Textual-додаток ``AssistantApp``: TUI-інтерфейс для асистента Арні.

Складається з двох панелей: ліва — для відображення контактів та довільної
інформації, права — для чату з AI-агентом. Запит користувача обробляється
у фоновому воркері, щоб не блокувати UI.
"""

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

    # Заголовок і підзаголовок вікна
    TITLE = "Асистент T800"
    SUB_TITLE = "Режим ШІ"

    # Гарячі клавіші, показані у футері.
    # Текст у панелях можна виділити мишею, а потім скопіювати через Ctrl+C.
    # Вихід винесено на Ctrl+Q, щоб Ctrl+C відповідав за копіювання.
    BINDINGS = [
        Binding("ctrl+c", "screen.copy_text", "Копіювати", show=True),
        Binding("ctrl+q", "quit", "Вихід", show=True),
    ]

    # Кадри анімації текстового лоадера (спінер Брайля)
    _LOADER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def compose(self) -> ComposeResult:
        """Складає розкладку віджетів: заголовок, дві панелі та футер."""
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
                # Історія чату — скрол-контейнер із окремих повідомлень,
                # щоб лоадер можна було показати на місці відповіді й потім
                # замінити його текстом відповіді.
                yield VerticalScroll(id="chat-log")
                yield Input(placeholder="Запитайте Арні...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        """Ініціалізує службові об'єкти після монтування інтерфейсу."""
        # Кешуємо посилання на віджети, щоб не шукати їх щоразу
        self._chat_log: VerticalScroll = self.query_one("#chat-log", VerticalScroll)
        self._display_log: RichLog = self.query_one("#display-pane", RichLog)
        self._input: Input = self.query_one("#chat-input", Input)
        # Прапорець, який блокує паралельну обробку нового повідомлення
        self._busy = False
        # Стан анімації текстового лоадера у вікні чату
        self._loader: Static | None = None
        self._loader_frame = 0
        self._loader_timer = None

        # Створюємо доменні об'єкти та залежності, що передаються агенту
        self._repo = ContactsRepository()
        self._service = ContactsService(self._repo)
        self._presenter = TextualPresenter(self._display_log, self)
        self._deps = AgentDeps(
            contacts_service=self._service, presenter=self._presenter
        )

        # Привітальне повідомлення українською
        self._add_message(
            "[bold green]Арні:[/bold green] Готовий до роботи. "
            "Спробуйте: «Додай контакт на ім'я Аліса»."
        )
        # Передаємо фокус у поле вводу
        self._input.focus()

    def _add_message(self, markup: str) -> Static:
        """Додає нове повідомлення у вікно чату й прокручує його донизу."""
        message = Static(markup, markup=True, classes="chat-message")
        self._chat_log.mount(message)
        # Прокручуємо до кінця після того, як віджет змонтується та розкладеться
        self.call_after_refresh(self._chat_log.scroll_end, animate=False)
        return message

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обробник підтвердження вводу у полі чату."""
        message = event.value.strip()
        if not message:
            # Ігноруємо порожні повідомлення
            return
        if self._busy:
            # Поки виконується попередній запит — попереджаємо користувача
            self._add_message(
                "[yellow](ще обробляю попереднє повідомлення...)[/yellow]"
            )
            return
        # Скидаємо поле вводу та фіксуємо повідомлення в історії чату
        self._input.value = ""
        self._add_message(f"[bold cyan]Ви:[/bold cyan] {message}")
        self._busy = True
        self._start_loader()
        self._run_agent(message)

    def _start_loader(self) -> None:
        """Показує анімований лоадер на місці майбутньої відповіді Арні."""
        self._loader_frame = 0
        # Заглушка-повідомлення, яку потім замінимо текстом відповіді
        self._loader = self._add_message("")
        self._loader_timer = self.set_interval(0.1, self._tick_loader)
        self._tick_loader()

    def _tick_loader(self) -> None:
        """Перемальовує один кадр анімації лоадера."""
        if self._loader is None:
            return
        spinner = self._LOADER_FRAMES[self._loader_frame % len(self._LOADER_FRAMES)]
        self._loader_frame += 1
        self._loader.update(
            f"[bold green]Арні:[/bold green] [italic]{spinner} обробляю запит…[/italic]"
        )

    def _finish_loader(self, markup: str) -> None:
        """Зупиняє анімацію та замінює лоадер фінальним текстом відповіді."""
        if self._loader_timer is not None:
            self._loader_timer.stop()
            self._loader_timer = None
        if self._loader is not None:
            # Лоадер «перетворюється» на повідомлення з відповіддю
            self._loader.update(markup)
            self._loader = None
        else:
            self._add_message(markup)
        self.call_after_refresh(self._chat_log.scroll_end, animate=False)

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
                self._finish_loader(f"[bold red]Арні:[/bold red] {reply}")
            else:
                self._finish_loader(f"[bold green]Арні:[/bold green] {reply}")
            self._busy = False
        elif event.state is WorkerState.ERROR:
            # Збій воркера — повідомляємо користувача українською
            self._finish_loader(
                f"[bold red]Арні:[/bold red] збій воркера: {event.worker.error}"
            )
            self._busy = False


def run_textual() -> None:
    """Створює та запускає Textual-застосунок асистента."""
    AssistantApp().run()
