from __future__ import annotations

import sys
from pathlib import Path

# Add project root to Python path once when plugin is loaded
project_root = str(Path(__file__).parents[2].absolute())
if project_root not in sys.path:
    sys.path.append(project_root)

from airflow.plugins_manager import AirflowPlugin
from flask import Blueprint

from plugins.civitai_images_plugin.views import CivitaiImagesView

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

    name = "CivitAI Analytics Plugin"
    flask_blueprints = [civitai_blueprint]
    appbuilder_views = [
        {"name": "Top Images", "category": "CivitAI", "view": CivitaiImagesView()}
    ]
