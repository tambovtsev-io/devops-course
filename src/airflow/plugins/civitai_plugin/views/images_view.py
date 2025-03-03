from typing import List

import pandas as pd
from airflow.models import DagRun, TaskInstance, XCom
from airflow.utils.session import create_session
from airflow.www.decorators import action_logging
from flask_appbuilder import BaseView, expose
from flask_appbuilder.security.decorators import has_access

from src.civitai_client import ImageData


class CivitaiImagesView(BaseView):
    """View for displaying CivitAI image analytics"""

    route_base = "/civitai"
    default_view = "list"

    def get_latest_run_data(self) -> List[ImageData]:
        """Get data from the latest DAG run"""
        with create_session() as session:
            # Get the latest successful DAG run
            latest_run = (
                session.query(DagRun)
                .filter(
                    DagRun.dag_id == "civitai_etl",
                    DagRun.state == "success",
                )
                .order_by(DagRun.execution_date.desc())
                .first()
            )

            if not latest_run:
                return []

            # Get the XCom data from the fetch task
            task_instance = (
                session.query(TaskInstance)
                .filter(
                    TaskInstance.dag_id == latest_run.dag_id,
                    TaskInstance.task_id == "fetch_data",
                    TaskInstance.run_id == latest_run.run_id,
                )
                .first()
            )

            if not task_instance:
                return []

            xcom_data = (
                session.query(XCom)
                .filter(
                    XCom.dag_id == task_instance.dag_id,
                    XCom.task_id == task_instance.task_id,
                    XCom.run_id == task_instance.run_id,
                    XCom.key == "image_response",
                )
                .first()
            )

            if not xcom_data or not xcom_data.value:
                return []

            return xcom_data.value.items

    def get_top_images(self, images: List[ImageData], n: int = 10) -> pd.DataFrame:
        """Get top N images by total reactions"""
        if not images:
            return pd.DataFrame()

        # Convert images to DataFrame
        records = []
        for img in images:
            record = {
                "id": img.id,
                "url": img.url,
                "username": img.username,
                "prompt": img.meta.prompt,
                "model": img.base_model,
                "total_reactions": (
                    img.stats.cry_count
                    + img.stats.laugh_count
                    + img.stats.like_count
                    + img.stats.heart_count
                ),
                "stats": img.stats.model_dump(),
                "parameters": img.meta.model_dump(exclude={"prompt"}),
            }
            records.append(record)

        df = pd.DataFrame(records)
        return df.nlargest(n, "total_reactions")

    @expose("/")
    @has_access
    @action_logging
    def list(self):
        """Display the top images view"""
        # Get latest data
        images = self.get_latest_run_data()
        df_top = self.get_top_images(images)

        # Prepare data for template
        image_data = []
        for _, row in df_top.iterrows():
            image_data.append(
                {
                    "url": row["url"],
                    "username": row["username"],
                    "prompt": row["prompt"],
                    "model": row["model"],
                    "total_reactions": row["total_reactions"],
                    "stats": row["stats"],
                    "parameters": {
                        k: v
                        for k, v in row["parameters"].items()
                        if v is not None and k != "additional_params"
                    },
                }
            )

        return self.render_template(
            "images.html",
            images=image_data,
        )
