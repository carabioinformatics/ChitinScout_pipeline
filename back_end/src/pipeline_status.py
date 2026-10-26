"""Lets the pipeline scripts report which stage they are in. The UI reads these
lines; run from the command line they just print one extra line each."""


def report_step(sample: str, step: str, status: str, message: str = "") -> None:
    """status is 'running', 'done' or 'failed'. Messages must stay on one line."""
    message = " ".join(str(message).split())
    print(f"@@STEP|{sample}|{step}|{status}|{message}", flush=True)