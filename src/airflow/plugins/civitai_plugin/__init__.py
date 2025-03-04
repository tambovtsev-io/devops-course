from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint

from src.airflow.plugins.civitai_plugin.views.images_view import CivitaiImagesView

# Create Flask blueprint for static files and templates
civitai_blueprint = Blueprint(
    "CivitAI",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/civitai",
)


class CivitaiImagesPlugin(AirflowPlugin):
    """Plugin for displaying CivitAI image analytics"""

    name = "CivitAI Images Plugin"
    flask_blueprints = [civitai_blueprint]
    appbuilder_views = [
        {"name": "Top Images", "category": "CivitAI", "view": CivitaiImagesView()}
    ]
