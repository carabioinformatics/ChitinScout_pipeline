"""Entry point. Start the whole application with:  python app.py"""
from nicegui import ui, app
from front_end.pages.home_page import home_page

# Register the home page at the root URL ("/")
ui.page("/")(home_page)
app.add_static_files("/assets", "front_end/assets")

# The __mp_main__ check is required: native mode and background
# processes re-import this file, and this guard stops ui.run() from
# running twice.
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Sequencing Pipeline",
        native=False,
        reload=False,
    )