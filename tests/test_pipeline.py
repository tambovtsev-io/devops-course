import asyncio
import logging

from src.civitai_client import CivitAIClient, Database, SortType, TimePeriod

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_and_store_images(
    limit: int = 10,
    sort: SortType = SortType.NEWEST,
    period: TimePeriod = TimePeriod.DAY,
) -> None:
    """
    Test pipeline that fetches images from CivitAI and stores them in database
    """
    try:
        # Initialize database
        db = Database()
        logger.info("Initializing database...")
        db.init_db()

        # Fetch data from API
        logger.info(f"Fetching {limit} images from CivitAI API...")
        async with CivitAIClient() as client:
            response = await client.get_images(limit=limit, sort=sort, period=period)

        if not response.items:
            logger.warning("No images received from API")
            return

        logger.info(f"Received {len(response.items)} images")

        # Store data in database
        logger.info("Storing images in database...")
        db.save_image_data(response)

        # Verify storage by fetching a random image
        sample_image = response.items[0]
        logger.info(f"Verifying storage for image ID: {sample_image.id}")

        with db.session() as session:
            from sqlalchemy import select

            from src.civitai_client.civitai_db import (
                GenerationParametersDB,
                ImageDB,
                ImageStatsHistoryDB,
            )

            # Check image data
            stmt = select(ImageDB).where(ImageDB.id == sample_image.id)
            result = session.execute(stmt)
            stored_image = result.scalar_one_or_none()

            if stored_image:
                logger.info(f"Successfully verified image storage: {stored_image.id}")

                # Check stats
                stmt = select(ImageStatsHistoryDB).where(
                    ImageStatsHistoryDB.image_id == sample_image.id
                )
                result = session.execute(stmt)
                stats = result.scalar_one_or_none()
                if stats:
                    logger.info(
                        f"Found stats: likes={stats.like_count}, hearts={stats.heart_count}"
                    )

                # Check generation parameters
                stmt = select(GenerationParametersDB).where(
                    GenerationParametersDB.image_id == sample_image.id
                )
                result = session.execute(stmt)
                params = result.scalar_one_or_none()
                if params:
                    logger.info(
                        f"Found generation parameters: model={params.model}, steps={params.steps}"
                    )
            else:
                logger.error(f"Failed to find stored image with ID: {sample_image.id}")

    except Exception as e:
        logger.error(f"Error in pipeline: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(fetch_and_store_images(limit=10))
