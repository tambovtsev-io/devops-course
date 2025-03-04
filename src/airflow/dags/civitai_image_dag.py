import asyncio
from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator

from airflow import DAG
from src.civitai_client import (
    CivitAIClient,
    Database,
    ImageResponse,
    SortType,
    TimePeriod,
)


async def fetch_images(
    limit: int = 100, sort: SortType = SortType.NEWEST
) -> ImageResponse:
    """Fetch images from CivitAI API"""
    async with CivitAIClient() as client:
        return await client.get_images(
            limit=limit,
            sort=sort,
            period=TimePeriod.DAY,
        )


def fetch_images_task(**context):
    """Wrapper for async fetch function"""
    response = asyncio.run(
        fetch_images(
            limit=context["params"].get("limit", 100),
            sort=SortType(context["params"].get("sort", SortType.MOST_REACTIONS.value)),
        )
    )
    context["task_instance"].xcom_push(key="image_response", value=response)


def load_data_task(**context):
    """Load fetched data into database"""
    image_response = context["task_instance"].xcom_pull(
        task_ids="fetch_data", key="image_response"
    )
    if not image_response:
        raise ValueError("No data received from fetch task")

    response = image_response
    db = Database()
    db.save_image_data(response)


with DAG(
    "civitai_etl",
    description="Fetch and load CivitAI data",
    schedule_interval="0 7,18 * * *",
    start_date=datetime(2024, 1, 1, 7, 0, 0),
    catchup=False,
    params=dict(
        limit=100,
        sort=SortType.MOST_REACTIONS.value,
    ),
    default_args=dict(
        owner="Ilia",
        retries=3,  # 30 minutes gap to perform the task
        retry_delay=timedelta(minutes=10),
    ),
) as dag:
    fetch_data = PythonOperator(
        task_id="fetch_data",
        python_callable=fetch_images_task,
    )

    load_db = PythonOperator(
        task_id="load_database",
        python_callable=load_data_task,
    )

    fetch_data >> load_db  # pyright: ignore
