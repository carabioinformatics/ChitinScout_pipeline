from datetime import datetime
from pathlib import Path
import pytest
import shutil

TESTING_DIR = Path(__file__).parent
RESOURCES_DIR = TESTING_DIR / "resources"
REPORTS_DIR = TESTING_DIR / "test_reports"
TEMP_OUTPUT_DIR = TESTING_DIR / "output"

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
        Creates a timestamped report folder and set the HTML report path.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = REPORTS_DIR/timestamp
    output_dir = TEMP_OUTPUT_DIR
    run_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config.run_dir = run_dir
    config.output_dir = output_dir

    # Name report after selected marker
    label = (config.option.markexpr or "all").replace(" ", "_")

    if not config.option.htmlpath:
        config.option.htmlpath = str(run_dir/f"report_{label}.html")

@pytest.fixture(scope="session")
def resource_dir() -> Path:
    """
        Folder with the resource directory's name.
    """
    return RESOURCES_DIR

@pytest.fixture(scope="session")
def run_dir(request) -> Path:
    """
        Folder with the run's output
    """
    return request.config.run_dir

@pytest.fixture(scope="session")
def output_dir(request) -> Path:
    """
        Returns the folder name of the temporary output created when running tests.
        The contents are deleted after the session while the folder is kept.
    """
    out = request.config.output_dir
    yield out

    for item in out.iterdir():
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
        else:
            item.unlink(missing_ok=True)