"""Search thresholds section: e-value, identity % and coverage % sliders."""
from typing import Callable
from nicegui import ui
from front_end.components.slider_comp import labeled_slider
from front_end.components.text_comp import text

# Replace these placeholders with your real defaults.
DEFAULT_TRIM_WINDOW_SIZE = 5
DEFAULT_QUALITY_THRESHOLD = 20
DEFAULT_EVALUE_EXPONENT = -15    # means 1e-15
DEFAULT_IDENTITY = 90           # percent
DEFAULT_COVERAGE = 90           # percent
DEFAULT_NCBI_WORD_SIZE = 11     # number
DEFAULT_TIME_LIMIT = 200        # ms


class SearchThresholds:
    """Owns the threshold sliders and the 'use defaults' checkbox."""

    def __init__(self, log: Callable[[str], None]) -> None:
        self._log = log
        self._build()

    # ---- UI
    def _build(self) -> None:
        with ui.card().classes("w-full rounded-xl shadow-md p-6 gap-4"):
            text("Search thresholds", "label")

            self._use_defaults = ui.checkbox(
                "Use default values", value=True, on_change=self._handle_defaults_toggle
            )

            self._evalue = labeled_slider(
                "Max e-value",
                minimum=-50, maximum=0, step=1,
                value=DEFAULT_EVALUE_EXPONENT,
                format_value=lambda v: f"1e{int(v)}",
            )
            self._identity = labeled_slider(
                "Min identity",
                minimum=0, maximum=100, step=1,
                value=DEFAULT_IDENTITY,
                format_value=lambda v: f"{int(v)}%",
            )
            self._coverage = labeled_slider(
                "Min coverage",
                minimum=0, maximum=100, step=1,
                value=DEFAULT_COVERAGE,
                format_value=lambda v: f"{int(v)}%",
            )

            self._trim_window_size = labeled_slider(
                "Trimming window size",
                minimum=2, maximum=20, step=1,
                value=DEFAULT_TRIM_WINDOW_SIZE, 
                format_value=lambda v: f"{int(v)}"
            )

            self._quality_threshold = labeled_slider(
                "Trimming lowest quality threshold",
                minimum=10, maximum=30, step=1,
                value=DEFAULT_QUALITY_THRESHOLD, 
                format_value=lambda v: f"{int(v)}"
            )

            self._ncbi_word_size = labeled_slider(
                "NCBI word size",
                minimum=7, maximum=25, step=1,
                value=DEFAULT_NCBI_WORD_SIZE,
                format_value=lambda v: f"{int(v)}"
            )

            self._time_limit = labeled_slider(
                "Time limit per sample (ms)",
                minimum=100, maximum=400, step=10,
                value=DEFAULT_TIME_LIMIT, 
                format_value=lambda v: f"{int(v)}"
            )

        self._update_slider_state()

    # ---- Event handlers
    def _handle_defaults_toggle(self, e) -> None:
        if e.value:
            # Ticking the box snaps the sliders back to the defaults
            self._evalue.value = DEFAULT_EVALUE_EXPONENT
            self._identity.value = DEFAULT_IDENTITY
            self._coverage.value = DEFAULT_COVERAGE
            self._trim_window_size.value = DEFAULT_TRIM_WINDOW_SIZE
            self._quality_threshold.value = DEFAULT_QUALITY_THRESHOLD
            self._ncbi_word_size.value = DEFAULT_NCBI_WORD_SIZE
            self._time_limit.value = DEFAULT_TIME_LIMIT
            self._log("Using default search thresholds")
        else:
            self._log("Using custom search thresholds")
        self._update_slider_state()

    def _update_slider_state(self) -> None:
        sliders_enabled = not self._use_defaults.value
        for slider in (self._evalue, self._identity, self._coverage, self._trim_window_size, self._quality_threshold, self._ncbi_word_size, self._time_limit):
            slider.set_enabled(sliders_enabled)

    # ---- What the page needs from this section
    def extra_args(self) -> list[str]:
        """Arguments for the pipeline: e-value, identity, coverage (in that order).

        Returns an empty list when defaults are in use, so the bash script
        falls back to its own default values."""
        if self._use_defaults.value:
            return []
        return [
            str(int(self._trim_window_size)),
            str(int(self._quality_threshold)),
            f"1e{int(self._evalue.value)}",
            str(int(self._identity.value)),
            str(int(self._coverage.value)),
            str(int(self._ncbi_word_size.value)),
            str(int(self._time_limit)),
        ]

    def describe(self) -> str:
        """A one-line summary for the output log."""
        if self._use_defaults.value:
            return "Using the pipeline's default search thresholds"
        e_value, identity, coverage = self.extra_args()
        return (
            f"Search thresholds: max e-value {e_value}, "
            f"min identity {identity}%, min coverage {coverage}%"
        )
    
    def set_enabled(self, enabled: bool) -> None:
        """Lock or unlock the whole section (used while the pipeline runs)."""
        self._use_defaults.set_enabled(enabled)
        if enabled:
            self._update_slider_state()   # restore based on the checkbox
        else:
            for slider in (self._evalue, self._identity, self._coverage, self._trim_window_size, self._quality_threshold, self._ncbi_word_size, self._time_limit):
                slider.set_enabled(False)