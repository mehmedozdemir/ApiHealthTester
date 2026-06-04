"""Design tokens — single source of truth for all UI constants."""


# ---------------------------------------------------------------------------
# Colors — Dark Theme
# ---------------------------------------------------------------------------

BG_BASE = "#0F1117"
BG_SURFACE = "#1A1D27"
BG_ELEVATED = "#22263A"
BG_OVERLAY = "#2A2F47"

ACCENT = "#5B8AF0"
ACCENT_HOVER = "#7BA3FF"
ACCENT_MUTED = "#1E2D5A"

TEXT_PRIMARY = "#F0F2FF"
TEXT_SECONDARY = "#8B90A8"
TEXT_DISABLED = "#4A4F6A"

BORDER = "#2E3248"
BORDER_FOCUS = "#5B8AF0"

SUCCESS = "#4CAF80"
WARNING = "#F0A84A"
ERROR = "#E05C6A"
INFO = "#5B8AF0"

SUCCESS_MUTED = "#1A3D2B"
WARNING_MUTED = "#3D2E10"
ERROR_MUTED = "#3D1A20"


# ---------------------------------------------------------------------------
# Spacing — 4px grid
# ---------------------------------------------------------------------------

class Spacing:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


# ---------------------------------------------------------------------------
# Border radius
# ---------------------------------------------------------------------------

class Radius:
    SM = 4
    MD = 8
    LG = 12
    XL = 16
    FULL = 9999


# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

class Typography:
    FONT_FAMILY = "Inter, Segoe UI, system-ui, sans-serif"

    SIZE_XS = 10
    SIZE_SM = 12
    SIZE_MD = 14
    SIZE_LG = 16
    SIZE_XL = 20
    SIZE_2XL = 28
    SIZE_3XL = 36

    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
