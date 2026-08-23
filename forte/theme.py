from __future__ import annotations

DARK_THEME = {
    "bg_base":        "#1A1A1E",
    "bg_panel":       "#212127",
    "bg_elevated":    "#2A2A32",
    "bg_scrubber":    "#18181C",
    "accent":         "#E8A838",
    "accent_dim":     "#C48A22",
    "text_primary":   "#F0EDE8",
    "text_secondary": "#8E8C88",
    "text_disabled":  "#4A4847",
    "border":         "#2E2E38",
    "danger":         "#C0392B",
}

LIGHT_THEME = {
    "bg_base":        "#F5F3EF",
    "bg_panel":       "#ECEAE6",
    "bg_elevated":    "#E0DDD8",
    "bg_scrubber":    "#DDDAD5",
    "accent":         "#E8A838",
    "accent_dim":     "#C48A22",
    "text_primary":   "#1A1A1E",
    "text_secondary": "#6A6866",
    "text_disabled":  "#B0ADA8",
    "border":         "#CCCAC6",
    "danger":         "#C0392B",
}


def build_stylesheet(theme: dict) -> str:
    """Build a PyQt6 QSS stylesheet string from a colour-token dict."""
    return f"""
    QMainWindow, QWidget {{
        background-color: {theme['bg_base']};
        color: {theme['text_primary']};
        font-family: "Inter", "Segoe UI", sans-serif;
    }}

    QListView {{
        background-color: {theme['bg_panel']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 4px;
    }}
    QListView::item:selected {{
        background-color: {theme['accent_dim']};
        color: {theme['bg_base']};
    }}
    QListView::item:hover {{
        background-color: {theme['bg_elevated']};
    }}

    QScrollBar:vertical {{
        background-color: {theme['bg_scrubber']};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {theme['text_disabled']};
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {theme['text_secondary']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QPushButton {{
        background-color: {theme['bg_elevated']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 6px;
        padding: 6px 14px;
    }}
    QPushButton:hover {{
        background-color: {theme['accent_dim']};
        color: {theme['bg_base']};
    }}
    QPushButton:pressed {{
        background-color: {theme['accent']};
    }}
    QPushButton:disabled {{
        color: {theme['text_disabled']};
    }}

    QSlider::groove:horizontal {{
        background-color: {theme['bg_scrubber']};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background-color: {theme['accent']};
        width: 14px;
        height: 14px;
        border-radius: 7px;
        margin: -4px 0;
    }}

    QLabel {{
        color: {theme['text_primary']};
    }}

    QLineEdit {{
        background-color: {theme['bg_elevated']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 4px;
        padding: 4px 8px;
    }}

    QDialog {{
        background-color: {theme['bg_panel']};
        color: {theme['text_primary']};
    }}

    QMenu {{
        background-color: {theme['bg_panel']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {theme['accent_dim']};
        color: {theme['bg_base']};
    }}
    """
