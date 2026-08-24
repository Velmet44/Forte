import sys

from PyQt6.QtWidgets import QApplication

from forte.state import SessionState
from forte.theme import DARK_THEME, LIGHT_THEME, build_stylesheet
from forte.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Forte")
    app.setOrganizationName("Forte")

    state = SessionState()
    session = state.load()

    theme = DARK_THEME if session.get("theme", "dark") == "dark" else LIGHT_THEME
    app.setStyleSheet(build_stylesheet(theme))

    window = MainWindow(session=session, state=state, theme=theme)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
