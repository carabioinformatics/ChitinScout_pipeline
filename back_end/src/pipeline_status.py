def report_step(sample: str, step: str, status: str, message: str = "") -> None:
    """
        Used by UI in pipeline to report what stage is currently busy. If run using the command line, 
        there are just printed.
        Status is either running, done or failed.
    """
    message = " ".join(str(message).split())
    print(f"@@STEP|{sample}|{step}|{status}|{message}", flush=True)