from ui.theme import (
    ACCENT, ACCENT_HOVER, ACCENT_MUTED,
    BG_BASE, BG_ELEVATED, BG_OVERLAY, BG_SURFACE,
    BORDER, BORDER_FOCUS,
    ERROR, TEXT_DISABLED, TEXT_PRIMARY, TEXT_SECONDARY,
    Radius, Spacing, Typography,
)


def get_global_stylesheet() -> str:
    r = Radius
    s = Spacing
    t = Typography
    return f"""
    /* ---- Base ---- */
    QMainWindow, QWidget {{
        background-color: {BG_BASE};
        color: {TEXT_PRIMARY};
        font-family: "Segoe UI", "Inter", system-ui, sans-serif;
        font-size: {t.SIZE_MD}px;
    }}

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* ---- Scrollbars ---- */
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border: none;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_ELEVATED};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {BORDER_FOCUS};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none; height: 0; width: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        border: none;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {BG_ELEVATED};
        border-radius: 3px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {BORDER_FOCUS};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none; height: 0; width: 0;
    }}

    /* ---- Buttons ---- */
    QPushButton {{
        border: none;
        border-radius: {r.MD}px;
        padding: {s.SM}px {s.MD}px;
        font-size: {t.SIZE_MD}px;
        font-weight: {t.WEIGHT_MEDIUM};
        min-height: 36px;
        outline: none;
    }}

    QPushButton[variant="primary"] {{
        background-color: {ACCENT};
        color: #FFFFFF;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton[variant="primary"]:pressed {{
        background-color: {ACCENT};
    }}
    QPushButton[variant="primary"]:disabled {{
        background-color: {BG_ELEVATED};
        color: {TEXT_DISABLED};
    }}
    QPushButton[variant="primary"]:focus {{
        border: 2px solid {ACCENT_HOVER};
    }}

    QPushButton[variant="secondary"] {{
        background-color: transparent;
        color: {ACCENT};
        border: 1px solid {ACCENT};
    }}
    QPushButton[variant="secondary"]:hover {{
        background-color: {ACCENT_MUTED};
    }}
    QPushButton[variant="secondary"]:pressed {{
        background-color: {BG_ELEVATED};
    }}
    QPushButton[variant="secondary"]:disabled {{
        color: {TEXT_DISABLED};
        border-color: {BORDER};
    }}

    QPushButton[variant="ghost"] {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        padding: {s.XS}px;
    }}
    QPushButton[variant="ghost"]:hover {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
    }}
    QPushButton[variant="ghost"]:pressed {{
        background-color: {BG_OVERLAY};
    }}

    QPushButton[variant="danger"] {{
        background-color: {ERROR};
        color: #FFFFFF;
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: #E87080;
    }}
    QPushButton[variant="danger"]:pressed {{
        background-color: {ERROR};
    }}
    QPushButton[variant="danger"]:disabled {{
        background-color: {BG_ELEVATED};
        color: {TEXT_DISABLED};
    }}

    /* ---- Inputs ---- */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: {r.MD}px;
        padding: {s.SM}px {s.MD}px;
        font-size: {t.SIZE_MD}px;
        selection-background-color: {ACCENT_MUTED};
        selection-color: {TEXT_PRIMARY};
        min-height: 36px;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {BORDER_FOCUS};
    }}
    QLineEdit:disabled, QTextEdit:disabled {{
        color: {TEXT_DISABLED};
        background-color: {BG_SURFACE};
        border-color: {BORDER};
    }}
    QLineEdit[error="true"] {{
        border-color: {ERROR};
    }}

    /* ---- ComboBox ---- */
    QComboBox {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: {r.MD}px;
        padding: {s.SM}px {s.MD}px;
        font-size: {t.SIZE_MD}px;
        min-height: 36px;
    }}
    QComboBox:focus, QComboBox:hover {{
        border-color: {BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        border: none;
        width: {s.LG}px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_OVERLAY};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        selection-background-color: {ACCENT_MUTED};
        selection-color: {ACCENT};
        outline: none;
        padding: {s.XS}px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 32px;
        padding: {s.XS}px {s.SM}px;
    }}

    /* ---- Tree Widget ---- */
    QTreeWidget {{
        background-color: transparent;
        color: {TEXT_PRIMARY};
        border: none;
        font-size: {t.SIZE_SM}px;
        outline: none;
        show-decoration-selected: 0;
    }}
    QTreeWidget::item {{
        padding: {s.XS}px {s.SM}px;
        min-height: 28px;
    }}
    QTreeWidget::item:hover {{
        background-color: {BG_ELEVATED};
        border-radius: {r.SM}px;
    }}
    QTreeWidget::item:selected {{
        background-color: {ACCENT_MUTED};
        color: {TEXT_PRIMARY};
        border-radius: {r.SM}px;
    }}
    QTreeWidget::branch {{
        background: transparent;
    }}

    /* ---- Labels ---- */
    QLabel {{
        background-color: transparent;
        color: {TEXT_PRIMARY};
    }}
    QLabel[class="page-title"] {{
        font-size: {t.SIZE_2XL}px;
        font-weight: {t.WEIGHT_BOLD};
    }}
    QLabel[class="section-header"] {{
        font-size: {t.SIZE_LG}px;
        font-weight: {t.WEIGHT_SEMIBOLD};
        color: {TEXT_SECONDARY};
    }}
    QLabel[class="caption"] {{
        font-size: {t.SIZE_SM}px;
        color: {TEXT_SECONDARY};
    }}
    QLabel[class="empty-title"] {{
        font-size: {t.SIZE_LG}px;
        font-weight: {t.WEIGHT_SEMIBOLD};
        color: {TEXT_SECONDARY};
    }}
    QLabel[class="empty-subtitle"] {{
        font-size: {t.SIZE_MD}px;
        color: {TEXT_DISABLED};
    }}

    /* ---- Tab Widget ---- */
    QTabWidget::pane {{
        border: none;
        background-color: transparent;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {TEXT_SECONDARY};
        padding: {s.SM}px {s.MD}px;
        font-size: {t.SIZE_MD}px;
        font-weight: {t.WEIGHT_MEDIUM};
        border: none;
        border-bottom: 2px solid transparent;
        min-width: 80px;
    }}
    QTabBar::tab:selected {{
        color: {ACCENT};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        color: {TEXT_PRIMARY};
        background-color: {BG_ELEVATED};
        border-radius: {r.SM}px;
    }}

    /* ---- Cards ---- */
    QFrame[class="card"] {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: {r.LG}px;
    }}
    QFrame[class="card"]:hover {{
        border-color: {BORDER_FOCUS};
    }}

    /* ---- Dialog ---- */
    QDialog {{
        background-color: {BG_SURFACE};
    }}

    /* ---- Separator ---- */
    QFrame[frameShape="4"] {{
        background-color: {BORDER};
        border: none;
        max-height: 1px;
    }}
    QFrame[frameShape="5"] {{
        background-color: {BORDER};
        border: none;
        max-width: 1px;
    }}
    """
