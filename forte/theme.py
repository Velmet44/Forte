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
    "bg_base":        "#FBFAF7",
    "bg_panel":       "#F1EFEA",
    "bg_elevated":    "#FFFFFF",
    "bg_scrubber":    "#E4E1DA",
    "accent":         "#D9821B",
    "accent_dim":     "#B66E10",
    "text_primary":   "#211F1B",
    "text_secondary": "#6E6A61",
    "text_disabled":  "#ABA69B",
    "border":         "#DEDAD1",
    "danger":         "#C0392B",
}


def build_stylesheet(theme: dict) -> str:
    """Build a PyQt6 QSS stylesheet string from a colour-token dict.

    All colours come exclusively from the supplied token dict so no UI file
    needs to hardcode a hex value.
    """
    return f"""
    QMainWindow, QWidget {{
        background-color: {theme['bg_base']};
        color: {theme['text_primary']};
        font-family: "Inter", "Segoe UI", sans-serif;
    }}

    QWidget#titleBar {{
        background-color: {theme['bg_panel']};
        border-bottom: 1px solid {theme['border']};
    }}
    QLabel#titleLabel {{
        color: {theme['text_primary']};
        font-size: 12px;
    }}
    QPushButton#titleButton {{
        background-color: transparent;
        border: none;
        color: {theme['text_secondary']};
        font-size: 14px;
        padding: 0 8px;
    }}
    QPushButton#titleButton:hover {{
        color: {theme['accent']};
    }}

    QWidget#divider {{
        background-color: {theme['border']};
    }}

    QWidget#statusBar {{
        background-color: {theme['bg_panel']};
        border-top: 1px solid {theme['border']};
    }}
    QLabel#statusLabel {{
        color: {theme['text_secondary']};
        font-size: 11px;
    }}

    QListView {{
        background-color: {theme['bg_panel']};
        color: {theme['text_primary']};
        border: none;
        border-radius: 0px;
        padding: 0px;
    }}

    QScrollBar:vertical {{
        background-color: {theme['bg_scrubber']};
        width: 6px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {theme['border']};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {theme['text_disabled']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
        height: 0px;
        width: 0px;
    }}
    QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: {theme['bg_scrubber']};
        height: 6px;
        border: none;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {theme['border']};
        border-radius: 3px;
        min-width: 20px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {theme['text_disabled']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        height: 0px;
        width: 0px;
    }}
    QScrollBar::sub-page:horizontal, QScrollBar::add-page:horizontal {{
        background: none;
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

    QPushButton#iconButton {{
        background-color: transparent;
        border: none;
        padding: 0px;
    }}
    QPushButton#iconButton:hover {{
        background-color: transparent;
        color: {theme['text_primary']};
    }}
    QPushButton#iconButton:pressed {{
        background-color: transparent;
        border: none;
    }}
    QPushButton#iconButton:disabled {{
        background-color: transparent;
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

    QLabel#nowTitle {{
        color: {theme['text_primary']};
    }}
    QLabel#nowArtist {{
        color: {theme['text_secondary']};
    }}
    QLabel#nowAlbum {{
        color: {theme['text_secondary']};
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

    QSlider#volumeSlider {{
        height: 16px;
    }}
    QSlider#volumeSlider::groove:horizontal {{
        background-color: {theme['bg_scrubber']};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider#volumeSlider::sub-page:horizontal {{
        background-color: {theme['accent']};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider#volumeSlider::add-page:horizontal {{
        background-color: {theme['bg_scrubber']};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider#volumeSlider::handle:horizontal {{
        background-color: {theme['accent']};
        width: 12px;
        height: 12px;
        border-radius: 6px;
        margin: -4px 0;
    }}
    QSlider#volumeSlider::handle:horizontal:hover {{
        background-color: {theme['accent_dim']};
    }}
    """
