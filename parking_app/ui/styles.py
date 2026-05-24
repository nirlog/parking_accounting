from __future__ import annotations

import os
import platform

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


def detect_windows_app_theme() -> str:
    if platform.system() != "Windows":
        return "light"
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "dark" if int(value) == 0 else "light"
    except Exception:
        return "light"


def resolve_theme_mode(mode: str | None = None) -> str:
    env_mode = (os.environ.get("PARKING_APP_THEME") or "").strip().lower()
    if env_mode in {"light", "dark", "system"}:
        mode = env_mode

    value = (mode or "system").strip().lower()
    if value in {"light", "dark"}:
        return value
    if value == "system":
        return detect_windows_app_theme()
    return detect_windows_app_theme()


def _table_palette(theme: str) -> dict[str, str]:
    if theme == "dark":
        return {
            "table_bg": "#1f2937",
            "table_alt_bg": "#273447",
            "table_fg": "#f9fafb",
            "grid": "#4b5563",
            "header_bg": "#111827",
            "header_fg": "#f9fafb",
            "border": "#4b5563",
            "widget_bg": "#0f172a",
            "widget_fg": "#f9fafb",
            "input_bg": "#111827",
            "input_fg": "#f9fafb",
        }
    return {
        "table_bg": "#ffffff",
        "table_alt_bg": "#f3f4f6",
        "table_fg": "#111827",
        "grid": "#d1d5db",
        "header_bg": "#e5e7eb",
        "header_fg": "#111827",
        "border": "#d1d5db",
        "widget_bg": "#f9fafb",
        "widget_fg": "#111827",
        "input_bg": "#ffffff",
        "input_fg": "#111827",
    }


def build_accessible_stylesheet(theme: str) -> str:
    palette = _table_palette(theme)
    return f"""
    QWidget {{
        font-size: 13pt;
        color: {palette['widget_fg']};
        background-color: {palette['widget_bg']};
    }}

    QPushButton {{
        min-height: 44px;
        padding: 8px 16px;
        font-size: 13pt;
    }}

    QLineEdit,
    QComboBox,
    QDateEdit,
    QTextEdit {{
        min-height: 40px;
        padding: 6px 10px;
        font-size: 13pt;
        color: {palette['input_fg']};
        background-color: {palette['input_bg']};
        border: 1px solid {palette['border']};
    }}

    QTableView,
    QTableWidget {{
        background-color: {palette['table_bg']};
        alternate-background-color: {palette['table_alt_bg']};
        color: {palette['table_fg']};
        gridline-color: {palette['grid']};
        selection-background-color: #2d85b3;
        selection-color: #ffffff;
        border: 1px solid {palette['border']};
        font-size: 12pt;
    }}

    QTableView::item,
    QTableWidget::item {{
        padding: 8px;
        color: {palette['table_fg']};
    }}

    QHeaderView::section {{
        min-height: 40px;
        padding: 8px;
        font-size: 12pt;
        font-weight: 700;
        background-color: {palette['header_bg']};
        color: {palette['header_fg']};
        border: 1px solid {palette['border']};
    }}
    """


def apply_large_accessible_style(app: "QApplication" | Any, theme: str | None = None) -> None:
    from PySide6.QtGui import QFont

    font = QFont("Segoe UI", 13)
    app.setFont(font)
    resolved = resolve_theme_mode(theme)
    app.setStyleSheet(build_accessible_stylesheet(resolved))
