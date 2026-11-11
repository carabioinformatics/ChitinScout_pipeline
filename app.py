from nicegui import ui, app
from front_end.pages.home_page import home_page

# Register the home page at the root URL ("/")
ui.page("/")(home_page)
# Load graphics to be used
app.add_static_files("/assets", "front_end/assets")

if __name__ in {"__main__", "__mp_main__"}:
    """
        Starts up the Graphic User interface platform. Ensures
        ui.run() does not run twice.
    """
    ui.run(
        title="SporeOver Pipeline",
        native=False,
        reload=False,
    )