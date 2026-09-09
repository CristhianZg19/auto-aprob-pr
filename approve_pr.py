import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


ALLOWED_ORG_ENV = "ALLOWED_ORG"
ALLOWED_BASE_BRANCH_ENV = "ALLOWED_BASE_BRANCH"
ALLOWED_ORG = ""
ALLOWED_BASE_BRANCH = ""
EXIT_COMMANDS = {"exit", "salir", "quit", "q"}
YES_OPTIONS = {"s", "si", "sí"}
GH_TIMEOUT_SECONDS = 20
PR_JSON_FIELDS = [
    "number",
    "title",
    "author",
    "state",
    "isDraft",
    "headRefName",
    "baseRefName",
    "url",
    "mergedAt",
    "reviewDecision",
    "reviews",
]

console = Console(highlight=False)
UNICODE_ENABLED = True

BLOCK_FONT = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"],
    "O": ["111", "101", "101", "101", "111"],
    "P": ["110", "101", "110", "100", "100"],
    "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"],
    "X": ["101", "101", "010", "101", "101"],
    "'": ["1", "1", "0", "0", "0"],
    " ": ["000", "000", "000", "000", "000"],
}


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    pull_number: int
    original_url: str
    host: str

    @property
    def session_key(self) -> tuple[str, str, int]:
        return (self.owner.lower(), self.repo.lower(), self.pull_number)


@dataclass(frozen=True)
class GhResult:
    stdout: str
    stderr: str
    returncode: int


class GhError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def configure_console() -> None:
    """Helps Windows terminals render Spanish accents and emoji."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8")
            except Exception:
                pass


def setup_terminal() -> None:
    configure_console()

    global console, UNICODE_ENABLED
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "🚀╭━💙".encode(encoding)
        UNICODE_ENABLED = True
    except UnicodeEncodeError:
        UNICODE_ENABLED = False

    console = Console(highlight=False, emoji=UNICODE_ENABLED)


def icon(emoji_value: str, fallback: str = "") -> str:
    return emoji_value if UNICODE_ENABLED else fallback


def panel_box() -> box.Box:
    return box.ROUNDED if UNICODE_ENABLED else box.ASCII


def load_app_config() -> None:
    load_dotenv()

    allowed_org = os.getenv(ALLOWED_ORG_ENV, "").strip()
    allowed_base_branch = os.getenv(ALLOWED_BASE_BRANCH_ENV, "").strip()
    missing_keys = [
        key
        for key, value in (
            (ALLOWED_ORG_ENV, allowed_org),
            (ALLOWED_BASE_BRANCH_ENV, allowed_base_branch),
        )
        if not value
    ]

    if missing_keys:
        missing_list = "\n".join(f"- {key}" for key in missing_keys)
        raise GhError(
            "Faltan variables de configuración.\n\n"
            f"{missing_list}\n\n"
            "Crea un archivo .env a partir de .env.example o configura esas "
            "variables antes de ejecutar el programa."
        )

    global ALLOWED_ORG, ALLOWED_BASE_BRANCH
    ALLOWED_ORG = allowed_org
    ALLOWED_BASE_BRANCH = allowed_base_branch


def run_gh_command(args: list[str], timeout: int = GH_TIMEOUT_SECONDS) -> GhResult:
    try:
        completed = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise GhError(
            "GitHub CLI no está instalado o no está disponible en PATH.\n\n"
            "Instálalo y ejecuta:\n"
            "gh auth login"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GhError(
            "GitHub CLI tardó demasiado en responder. Revisa tu conexión o VPN corporativa."
        ) from exc

    return GhResult(
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        returncode=completed.returncode,
    )


def render_block_line(text_value: str, row_index: int) -> str:
    glyph = "█" if UNICODE_ENABLED else "#"
    pieces = []
    for char in text_value.upper():
        pattern = BLOCK_FONT.get(char, BLOCK_FONT[" "])[row_index]
        pieces.append("".join(glyph if bit == "1" else " " for bit in pattern))
    return " ".join(pieces)


def build_block_title() -> Group:
    segments = [
        ("APROBADOR", "bold cyan"),
        ("DE", "bold white"),
        ("PR'S", "bold magenta"),
        ("XD", "bold green"),
    ]
    rows = []

    for row_index in range(5):
        line = Text()
        for segment_index, (value, style) in enumerate(segments):
            if segment_index:
                line.append("     ")
            line.append(render_block_line(value, row_index), style=style)
        rows.append(Align.center(line))

    rows.append(Align.center(Text("Producto creado para aprobaciones rápidas xdd", style="bold white")))
    rows.append(Align.center(Text(f"Menos clicks, más código  {icon('⚡', '*')}", style="bright_black")))
    return Group(*rows)


def build_compact_title() -> Group:
    title = Text("Aprobador de PR's XD", style="bold cyan", justify="center")
    subtitle = Text("Producto creado para aprobaciones rápidas xdd", style="bold white", justify="center")
    tagline = Text(f"Menos clicks, más código  {icon('⚡', '*')}", style="bright_black", justify="center")
    return Group(Align.center(title), Align.center(subtitle), Align.center(tagline))


def build_logo() -> Group:
    if console.width >= 92:
        return build_block_title()
    return build_compact_title()


def build_mascot() -> Text:
    branch_text = f"{ALLOWED_BASE_BRANCH} only ! {icon('🚀', '>')}".strip()
    branch_text = branch_text[:22]
    if UNICODE_ENABLED:
        lines = [
            r"   /\_/\        ╭────────────────────────╮",
            r"  ( •_• )       │ ¡PRs a                 │",
            f"  / >🕶️         │ {branch_text:<22} │",
            r" /_____\        ╰────────────────────────╯",
        ]
    else:
        lines = [
            r"   /\_/\        +------------------------+",
            r"  ( o_o )       | PRs a                  |",
            f"  / >[]         | {branch_text:<22} |",
            r" /_____\        +------------------------+",
        ]
    return Text("\n".join(lines), style="bright_white")


def build_quote_box() -> Panel:
    quote = Text()
    quote.append('"Good PRs\n', style="bold white")
    quote.append("make a better\ntomorrow", style="bold white")
    quote.append(f"\"   {icon('💚', '<3')}", style="bold green")
    return Panel(
        Align.center(quote),
        border_style="cyan",
        box=box.SQUARE if UNICODE_ENABLED else box.ASCII,
        padding=(0, 2),
    )


def print_banner() -> None:
    console.print()

    if console.width >= 145:
        hero = Table.grid(expand=True)
        hero.add_column(width=38)
        hero.add_column(ratio=1)
        hero.add_column(width=30)
        hero.add_row(
            Align.left(build_mascot()),
            Align.center(build_logo(), vertical="middle"),
            Align.center(build_quote_box(), vertical="middle"),
        )
        console.print(hero)
    elif console.width >= 92:
        console.print(Align.center(build_logo()))
        console.print()
        side = Table.grid(expand=True)
        side.add_column(ratio=1)
        side.add_column(width=30)
        side.add_row(build_mascot(), build_quote_box())
        console.print(side)
    else:
        console.print(Align.center(build_logo()))
        console.print()
        console.print(build_mascot())

    console.print()
    console.print(Rule(style="bright_black"))
    console.print()


def build_status_cell(
    glyph: str,
    label: str,
    value: str | Text,
    icon_style: str,
    value_style: str = "bold white",
) -> Table:
    cell = Table.grid(padding=(0, 1))
    cell.add_column(width=4)
    cell.add_column(ratio=1)

    content = Text()
    content.append(f"{label}\n", style="bright_white")
    if isinstance(value, Text):
        content.append_text(value)
    else:
        content.append(value, style=value_style)

    cell.add_row(Text(glyph, style=icon_style), content)
    return cell


def print_startup_status(authenticated_user: str) -> None:
    branch_badge = Text(f" {ALLOWED_BASE_BRANCH} ", style="bold magenta on grey15")

    segments = [
        build_status_cell(icon("👤", "@"), "GitHub conectado como:", authenticated_user, "bold cyan", "bold green"),
        build_status_cell(icon("🏢", "ORG"), "Organización permitida:", ALLOWED_ORG, "bold white", "bold blue"),
        build_status_cell(icon("🔀", "BR"), "Solo destino:", branch_badge, "bold bright_blue"),
        build_status_cell(icon("🛡️", "OK"), "Listo para aprobar", "¡Dale con confianza!", "bold yellow", "bold green"),
    ]

    if console.width >= 118:
        status = Table.grid(expand=True)
        for index in range(7):
            if index % 2 == 0:
                status.add_column(ratio=1)
            else:
                status.add_column(width=1)
        status.add_row(
            segments[0],
            Text("│", style="bright_black"),
            segments[1],
            Text("│", style="bright_black"),
            segments[2],
            Text("│", style="bright_black"),
            segments[3],
        )
    else:
        status = Table.grid(expand=True)
        status.add_column(ratio=1)
        for segment in segments:
            status.add_row(segment)

    console.print(
        Panel(
            status,
            border_style="bright_blue",
            box=panel_box(),
            padding=(1, 2),
        )
    )
    console.print()


def print_how_to_use() -> None:
    left = Table.grid(padding=(0, 1))
    left.add_column()
    left.add_row(Text(f"{icon('💡', '?')}  ¿Cómo usar?", style="bold yellow"))

    steps = [
        "Te pasan la URL de un PR por WhatsApp",
        "La pegas aquí",
        "Revisas la info",
        "Confirmas y se aprueba",
        f"¡Y a seguir!  {icon('🚀', '>>')}",
    ]
    for number, step in enumerate(steps, start=1):
        row = Text()
        row.append(f" {number} ", style="bold black on bright_blue")
        row.append(f"  {step}", style="bright_white")
        left.add_row(row)

    quote = Text(justify="center")
    quote.append('"Automatiza lo repetitivo\n', style="italic bright_black")
    quote.append(f"para enfocarte en lo importante\"  {icon('😎', 'B-')}", style="italic bright_black")

    if console.width >= 100:
        content = Table.grid(expand=True)
        content.add_column(ratio=1)
        content.add_column(width=1)
        content.add_column(ratio=1)
        divider = Text("\n".join(["│"] * 8), style="bright_black")
        content.add_row(left, divider, Align.center(quote, vertical="middle"))
    else:
        content = Group(left, Text(""), Align.center(quote))

    console.print(
        Panel(
            content,
            border_style="bright_black",
            box=panel_box(),
            padding=(1, 2),
        )
    )
    console.print()


def print_footer() -> None:
    console.print(Rule(style="bright_black"))
    footer = Table.grid(expand=True)
    footer.add_column(ratio=1)
    footer.add_column(no_wrap=True)
    footer.add_row(
        Text(f"(づ｡◕‿‿◕｡)づ  Code. Review. Repeat.  {icon('♻️', '*')}", style="bright_black"),
    )
    console.print(footer)


def check_gh_installed() -> None:
    result = run_gh_command(["--version"])
    if result.returncode != 0:
        raise GhError(
            "GitHub CLI no está instalado o no está disponible en PATH.\n\n"
            "Instálalo y ejecuta:\n"
            "gh auth login"
        )


def get_authenticated_user() -> str:
    result = run_gh_command(["api", "user", "--jq", ".login"])
    if result.returncode != 0 or not result.stdout:
        raise GhError(
            "No hay una sesión activa de GitHub CLI.\n\n"
            "Ejecuta primero:\n"
            "gh auth login"
        )
    return result.stdout.splitlines()[0].strip()


def parse_pr_url(url: str) -> PullRequestRef:
    parsed = urlparse(url.strip())

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Ingresa una URL válida de GitHub.")

    path_parts = [unquote(part) for part in parsed.path.split("/") if part]
    if len(path_parts) < 4 or path_parts[2].lower() != "pull":
        raise ValueError("La URL debe tener el formato https://github.com/OWNER/REPO/pull/NUMERO.")

    owner, repo, pull_value = path_parts[0], path_parts[1], path_parts[3]
    if not pull_value.isdigit():
        raise ValueError("El número del Pull Request no es válido.")

    return PullRequestRef(
        owner=owner,
        repo=repo,
        pull_number=int(pull_value),
        original_url=url.strip(),
        host=parsed.netloc.lower(),
    )


def get_pr_info(pr_ref: PullRequestRef) -> dict[str, Any]:
    result = run_gh_command(
        [
            "pr",
            "view",
            pr_ref.original_url,
            "--json",
            ",".join(PR_JSON_FIELDS),
        ]
    )

    if result.returncode != 0:
        raise GhError(map_pr_view_error(result.stderr))

    try:
        pr_info = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GhError("GitHub CLI devolvió una respuesta JSON no válida.") from exc

    if not isinstance(pr_info, dict):
        raise GhError("GitHub CLI devolvió una respuesta inesperada.")

    return pr_info


def map_pr_view_error(stderr: str) -> str:
    detail = clean_stderr(stderr)
    lowered = detail.lower()

    if "authentication" in lowered or "not logged" in lowered or "login" in lowered:
        return "La sesión de GitHub CLI no es válida.\n\nEjecuta primero:\ngh auth login"

    if (
        "could not resolve" in lowered
        or "not found" in lowered
        or "http 404" in lowered
        or "graphql: not found" in lowered
    ):
        return "Pull Request no encontrado o no tienes acceso."

    if "http 403" in lowered or "forbidden" in lowered or "permission" in lowered:
        return "Pull Request no encontrado o no tienes acceso."

    if detail:
        return f"No se pudo consultar el Pull Request.\n{detail}"

    return "No se pudo consultar el Pull Request."


def clean_stderr(stderr: str) -> str:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    return "\n".join(lines)[:1000]


def print_error(message: str) -> None:
    console.print(
        Panel(
            Text(message, style="bright_white"),
            title=f"{icon('❌', '!')} ERROR",
            border_style="red",
            box=panel_box(),
        )
    )


def print_notice(title: str, message: str, border_style: str = "yellow") -> None:
    console.print(
        Panel(
            Text(message, style="bright_white"),
            title=title,
            border_style=border_style,
            box=panel_box(),
        )
    )


def print_pr_info(pr_ref: PullRequestRef, pr_info: dict[str, Any]) -> None:
    author = get_author_login(pr_info)
    state = str(pr_info.get("state") or "desconocido").upper()
    is_draft = "sí" if pr_info.get("isDraft") else "no"
    base_ref = get_base_ref_name(pr_info) or "desconocido"

    details = Table.grid(padding=(0, 1), expand=True)
    details.add_column(no_wrap=True, justify="right")
    details.add_column(ratio=1)
    details.add_row(f"{icon('📦', 'repo')} Repo", Text(pr_ref.repo, style="white"))
    details.add_row(f"{icon('🔢', '#')} PR", Text(f"#{pr_info.get('number', pr_ref.pull_number)}", style="bold blue"))
    details.add_row(f"{icon('👤', '@')} Autor", Text(author or "desconocido", style="white"))
    details.add_row(f"{icon('📝', 'txt')} Título", Text(str(pr_info.get("title") or "sin título"), style="white"))
    details.add_row("", "")
    details.add_row(f"{icon('🌱', 'from')} Origen", Text(str(pr_info.get("headRefName") or "desconocido"), style="cyan"))
    details.add_row(f"{icon('🎯', 'to')} Destino", Text(base_ref, style="bold green"))
    details.add_row(f"{icon('🟢', 'state')} Estado", Text(state, style="bold green"))
    details.add_row(f"{icon('📌', 'draft')} Draft", Text(is_draft, style="yellow" if pr_info.get("isDraft") else "green"))
    details.add_row(f"{icon('🔗', 'url')} URL", Text(str(pr_info.get("url") or pr_ref.original_url), style="blue"))

    console.print(
        Panel(
            details,
            title=f"{icon('🔍', '*')} PR ENCONTRADO",
            border_style="cyan",
            box=panel_box(),
            padding=(1, 2),
        )
    )
    console.print(f"{icon('👀', '->')} Échale un ojo antes de regalar el approve xdd", style="bold yellow")
    console.print()


def get_author_login(pr_info: dict[str, Any]) -> str:
    author = pr_info.get("author")
    if isinstance(author, dict):
        return str(author.get("login") or "")
    return ""


def get_base_ref_name(pr_info: dict[str, Any]) -> str:
    return str(pr_info.get("baseRefName") or "")


def is_pr_closed_or_merged(pr_info: dict[str, Any]) -> bool:
    state = str(pr_info.get("state") or "").upper()
    return state != "OPEN" or bool(pr_info.get("mergedAt"))


def has_allowed_base_branch(pr_info: dict[str, Any]) -> bool:
    return get_base_ref_name(pr_info) == ALLOWED_BASE_BRANCH


def print_invalid_base_branch(pr_info: dict[str, Any]) -> None:
    current_base_branch = get_base_ref_name(pr_info) or "desconocido"
    message = (
        "Este PR no apunta a la rama permitida.\n\n"
        f"Destino actual : {current_base_branch}\n"
        f"Destino válido : {ALLOWED_BASE_BRANCH}\n\n"
        f"Aquí no aprobamos cosas fuera de {ALLOWED_BASE_BRANCH} xdd\n\n"
        "No se realizó ninguna aprobación."
    )
    print_notice(f"{icon('🚨', '!!')} ALTO AHÍ XD", message, "red")


def has_user_approved(pr_info: dict[str, Any], authenticated_user: str) -> bool:
    reviews = pr_info.get("reviews")
    if not isinstance(reviews, list):
        return False

    authenticated_user = authenticated_user.lower()
    for review in reviews:
        if not isinstance(review, dict):
            continue

        author = review.get("author")
        author_login = ""
        if isinstance(author, dict):
            author_login = str(author.get("login") or "")

        state = str(review.get("state") or "").upper()
        if state == "APPROVED" and author_login.lower() == authenticated_user:
            return True

    return False


def approve_pr(pr_ref: PullRequestRef) -> None:
    result = run_gh_command(["pr", "review", pr_ref.original_url, "--approve"])
    if result.returncode == 0:
        return

    detail = clean_stderr(result.stderr)
    lowered = detail.lower()

    if "authentication" in lowered or "not logged" in lowered or "login" in lowered:
        raise GhError("La sesión de GitHub CLI no es válida.\n\nEjecuta primero:\ngh auth login")

    if "not found" in lowered or "http 404" in lowered:
        raise GhError("Pull Request no encontrado o no tienes acceso.")

    if (
        "http 403" in lowered
        or "forbidden" in lowered
        or "permission" in lowered
        or "resource not accessible" in lowered
    ):
        raise GhError("No tienes permisos para aprobar este Pull Request.")

    if "cannot approve your own pull request" in lowered or "can not approve your own pull request" in lowered:
        raise GhError("No puedes aprobar tu propio Pull Request.")

    if "validation failed" in lowered or "unprocessable" in lowered or "http 422" in lowered:
        raise GhError(
            "GitHub rechazó la aprobación.\n"
            "Puede existir una restricción del repositorio."
        )

    if detail:
        raise GhError(f"GitHub rechazó la aprobación.\n{detail}")

    raise GhError("GitHub rechazó la aprobación.")


def is_yes(value: str) -> bool:
    return value.strip().lower() in YES_OPTIONS


def print_prompt_area(first_prompt: bool) -> None:
    if first_prompt:
        prompt_label = "Pega la URL del PR:"
    else:
        console.print()
        console.print(Rule(style="bright_black"))
        console.print()
        console.print(f"{icon('🔥', '>>')} ¿Tenemos otro?", style="bold magenta")
        prompt_label = "Pega otra URL del PR:"

    print_footer()

    if console.width >= 96:
        layout = Table.grid(expand=True)
        layout.add_column(ratio=1)
        layout.add_column(width=1)
        layout.add_column(width=30)

        left = Text()
        left.append(f"{icon('🔗', '>>')}  ", style="bold cyan")
        left.append(prompt_label, style="bold cyan")

        right = Text()
        right.append(f"{icon('🚪', 'q')}  ", style="bold magenta")
        right.append("Escribe 'q'\n'salir' o 'exit'\npara terminar.", style="bright_black")

        layout.add_row(left, Text("│\n│\n│", style="bright_black"), right)
        console.print(layout)
    else:
        console.print(f"{icon('🔗', '>>')} {prompt_label}", style="bold cyan")
        console.print("Escribe 'q', 'salir' o 'exit' para terminar.", style="dim")


def prompt_for_pr_url(first_prompt: bool) -> str:
    print_prompt_area(first_prompt)
    return console.input("[bold white]> [/]").strip()


def prompt_for_confirmation() -> str:
    return console.input("[bold yellow]¿Aprobar este PR? [S/N]: [/]").strip()


def print_success(pr_number: int) -> None:
    message = Text(justify="center")
    message.append(f"{icon('✅', 'OK')} APPROVED\n", style="bold green")
    message.append("\n")
    message.append(f"PR #{pr_number} aprobado correctamente\n", style="white")
    message.append(f"{icon('🚀', '>>')} GG, siguiente", style="bold magenta")

    console.print(
        Panel(
            Align.center(message),
            border_style="green",
            box=panel_box(),
            padding=(1, 2),
        )
    )


def print_cancelled() -> None:
    console.print(f"{icon('😴', 'zz')} Cancelado. Ese PR se salvó por ahora xdd", style="yellow")
    console.print("No se realizó ninguna aprobación.", style="dim")


def print_exit() -> None:
    goodbye = Text(justify="center")
    goodbye.append(f"{icon('👋', 'bye')} Cerrando Aprobador XD\n", style="bold cyan")
    goodbye.append("\n")
    goodbye.append(f"Buenas reviews, pocos bugs {icon('🐛', '')}", style="green")
    console.print(
        Panel(
            Align.center(goodbye),
            border_style="magenta",
            box=panel_box(),
            padding=(1, 2),
        )
    )


def handle_pr_url(
    raw_url: str,
    authenticated_user: str,
    approved_this_session: set[tuple[str, str, int]],
) -> None:
    try:
        pr_ref = parse_pr_url(raw_url)
    except ValueError as exc:
        print_error(str(exc))
        return

    if pr_ref.owner.lower() != ALLOWED_ORG.lower():
        print_error(f"Solo se permiten Pull Requests de la organización configurada: {ALLOWED_ORG}.")
        return

    if pr_ref.session_key in approved_this_session:
        print_notice(
            f"{icon('⚠️', '!')} Ya pasó por caja",
            "Este PR ya fue aprobado durante esta sesión.",
            "yellow",
        )
        return

    pr_info = get_pr_info(pr_ref)

    if is_pr_closed_or_merged(pr_info):
        print_notice(
            f"{icon('🏁', 'done')} Llegaste tarde xdd",
            "Este Pull Request ya está cerrado o mergeado.",
            "yellow",
        )
        return

    if pr_info.get("isDraft"):
        print_notice(
            f"{icon('📝', 'draft')} Todavía está cocinándose...",
            "Este Pull Request está en Draft y no puede aprobarse todavía.",
            "yellow",
        )
        return

    author_login = get_author_login(pr_info)
    if author_login.lower() == authenticated_user.lower():
        print_notice(
            f"{icon('🤨', 'hmm')} Buen intento xdd",
            "No puedes aprobar tu propio Pull Request.",
            "yellow",
        )
        return

    if not has_allowed_base_branch(pr_info):
        print_invalid_base_branch(pr_info)
        return

    if has_user_approved(pr_info, authenticated_user):
        print_notice(
            f"{icon('😎', ':)')} Ese ya tiene tu bendición",
            "Ya aprobaste este Pull Request anteriormente.\n\nNo generar otra aprobación.",
            "green",
        )
        return

    print_pr_info(pr_ref, pr_info)

    confirmation = prompt_for_confirmation()
    if not is_yes(confirmation):
        print_cancelled()
        return

    approve_pr(pr_ref)
    approved_this_session.add(pr_ref.session_key)
    print_success(pr_ref.pull_number)


def main() -> int:
    setup_terminal()

    try:
        load_app_config()
        print_banner()
        check_gh_installed()
        authenticated_user = get_authenticated_user()
    except GhError as exc:
        print_error(exc.message)
        return 1

    print_startup_status(authenticated_user)
    print_how_to_use()

    approved_this_session: set[tuple[str, str, int]] = set()
    first_prompt = True

    while True:
        try:
            raw_url = prompt_for_pr_url(first_prompt)
        except (KeyboardInterrupt, EOFError):
            console.print()
            print_exit()
            return 0

        first_prompt = False

        if not raw_url:
            continue

        if raw_url.lower() in EXIT_COMMANDS:
            print_exit()
            return 0

        try:
            handle_pr_url(raw_url, authenticated_user, approved_this_session)
        except GhError as exc:
            print_error(exc.message)


if __name__ == "__main__":
    raise SystemExit(main())
