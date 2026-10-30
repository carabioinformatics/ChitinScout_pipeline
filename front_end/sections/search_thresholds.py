"""Search thresholds section: e-value, identity % and coverage % sliders."""
from typing import Callable
from nicegui import ui
from front_end.components.slider_comp import labeled_slider
from front_end.components.text_comp import text

# Replace these placeholders with your real defaults.
DEFAULT_MAX_TRIMMING = 50
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
            text("Pipeline thresholds and specificity", "label")

            self._use_defaults = ui.checkbox(
                "Use default values", value=True, on_change=self._handle_defaults_toggle
            )

            text("Trimming related parameters", "label")

            self._max_trimming = labeled_slider(
                "Minimum '%' of sequence that should still be present after trimming",
                minimum=10, maximum=90, step=5,
                value=DEFAULT_MAX_TRIMMING, 
                info_msg=(
                    "Trimming removes low-quality bases from the start and end of reads. " \
                    "If after trimming, less than this percentage of the forward or reverse original " \
                    "sequence is left, this sample will not continue with the rest of the pipeline. " \
                    "This is done to prevent that sequences with very low quality reads waste time "
                    "continueing with the pipeline."
                ),
                format_value=lambda v: f"{int(v)}%",
            )

            self._trim_window_size = labeled_slider(
                "Trimming window size",
                minimum=2, maximum=20, step=1,
                value=DEFAULT_TRIM_WINDOW_SIZE, 
                format_value=lambda v: f"{int(v)}",
                info_msg=(
                    "The trimming algorithm using a sliding window approach to trim away low-quality reads. "
                    "The window size specified is the size of the sliding window. The average quality of this "
                    "window is calculated, of which the minimum quality allowed can be specified in the next "
                    "parameter. If the average of that sliding windows is below the allowed quality, then the "
                    "first nucleotide of that window is trimmed. This sliding window continues moving until the "
                    "average quality of a window is good enough. The algorithm first slides from the start and "
                    "trims away, and then moves to the back of the sequence and start trimming away nucleotides "
                    "from the back. This sliding window does not trim away sequences in the middle of the sequence. "
                    "These low quality reads rather get handled when making the consensus. A value of between 5 - 10 "
                    "is good for short reads, whereas 10-20 is smoother and conserves more reads."
                ),
            )

            self._quality_threshold = labeled_slider(
                "Trimming lowest quality threshold",
                minimum=10, maximum=30, step=1,
                value=DEFAULT_QUALITY_THRESHOLD, 
                format_value=lambda v: f"{int(v)}",
                info_msg=(
                    "This is the minimum allowed quality that a nucleotide needs to be to not get trimmed away. "
                    "This quality is found when looking at the phred score that can be read from the .ab1 file. "
                    "You can read more about the trimming algorithm in the trimming window size info box. This "
                    "threshold could go up to 30 for stricter trimming but 20 is the standard."
                ),
            )

            text("NCBI search related parameters", "label")

            self._ncbi_word_size = labeled_slider(
                "NCBI word size",
                minimum=7, maximum=25, step=1,
                value=DEFAULT_NCBI_WORD_SIZE,
                format_value=lambda v: f"{int(v)}",
                info_msg=(
                    "The NCBI word size is the word size BLASTn uses to find any matches. The smaller the word " \
                    "size could more broadly search for matches but there is a higher likelyhood that that random " \
                    "unrelated hits get found. Additional, the search time will also be longer. A longer word size " \
                    "can have a shorter search time but you could miss likely matches that get lost because of a single " \
                    "nucleotide difference."
                ),
            )

            self._time_limit = labeled_slider(
                "Time limit per sample (s)",
                minimum=100, maximum=400, step=10,
                value=DEFAULT_TIME_LIMIT, 
                format_value=lambda v: f"{int(v)}",
                info_msg=(
                    "This limit is to ensure that a single BLAST search does not take too long. Usually if a search takes " \
                    "longer than 200 seconds, it can either mean the consensus sequence's quality is not good or that NCBI " \
                    "is experiencing high traffic or connection problems. Instead of that sample wasting too much resources " \
                    "and time, the pipeline rather times out, terminates that sample, and then moves to the next."
                ),
            )

            text("NCBI result specificity related parameters", "label")

            self._evalue = labeled_slider(
                "Max e-value",
                minimum=-50, maximum=0, step=1,
                value=DEFAULT_EVALUE_EXPONENT,
                format_value=lambda v: f"1e{int(v)}",
                info_msg=(
                    "The BLAST search does a general BLAST search and then retrieves all hits found for that search. These hit " \
                    "results is then downloaded and saved. These saved results can then be filtered to create a more readable " \
                    "and relevant summary. This e-value parameter specifies that only entries that have e-values below this maximum " \
                    "specified is displayed in the summary."
                ),
            )

            self._identity = labeled_slider(
                "Min identity",
                minimum=0, maximum=100, step=1,
                value=DEFAULT_IDENTITY,
                format_value=lambda v: f"{int(v)}%",
                info_msg=(
                    "The BLAST search does a general BLAST search and then retrieves all hits found for that search. These hit " \
                    "results is then downloaded and saved. These saved results can then be filtered to create a more readable " \
                    "and relevant summary. This identity parameter specifies that only entries that have identity percentages higher "
                    "than this minimum specified is displayed in the summary."
                ),
            )

            self._coverage = labeled_slider(
                "Min coverage",
                minimum=0, maximum=100, step=1,
                value=DEFAULT_COVERAGE,
                format_value=lambda v: f"{int(v)}%",
                info_msg=(
                    "The BLAST search does a general BLAST search and then retrieves all hits found for that search. These hit " \
                    "results is then downloaded and saved. These saved results can then be filtered to create a more readable " \
                    "and relevant summary. This coverage parameter specifies that only entries that have coverage percentages higher "
                    "than this minimum specified is displayed in the summary."
                ),
            )

        self._update_slider_state()

    # ---- Event handlers
    def _handle_defaults_toggle(self, e) -> None:
        if e.value:
            # Ticking the box snaps the sliders back to the defaults
            self._evalue.value = DEFAULT_EVALUE_EXPONENT
            self._identity.value = DEFAULT_IDENTITY
            self._coverage.value = DEFAULT_COVERAGE
            self._max_trimming.value = DEFAULT_MAX_TRIMMING
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
        for slider in (self._evalue, self._identity, self._coverage, self._max_trimming, self._trim_window_size, self._quality_threshold, self._ncbi_word_size, self._time_limit):
            slider.set_enabled(sliders_enabled)

    # ---- What the page needs from this section
    def extra_args(self) -> list[str]:
        """Arguments for the pipeline: e-value, identity, coverage (in that order).

        Returns an empty list when defaults are in use, so the bash script
        falls back to its own default values."""
        if self._use_defaults.value:
            return []
        return [
            str(int(self._max_trimming)),
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
            for slider in (self._evalue, self._identity, self._coverage, self._max_trimming, self._trim_window_size, self._quality_threshold, self._ncbi_word_size, self._time_limit):
                slider.set_enabled(False)