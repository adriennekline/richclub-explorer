from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_initial_view_loads():
    app_path = Path(__file__).parents[1] / "app" / "streamlit_app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=20)
    assert not app.exception
    assert app.title[0].value == "RichClub Explorer"
    assert app.button[0].label == "Run rich-club analysis"
