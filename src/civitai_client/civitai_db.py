from datetime import datetime, timezone
from typing import Dict, Optional

import pandas as pd
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import select
from sqlalchemy.sql.schema import MetaData

from src.civitai_client.civitai_client import (
    GenerationParameters,
    ImageData,
    ImageResponse,
)
from src.civitai_client.config import DatabaseSettings, get_db_settings


class InitModel:
    """Class with initialization of parameters"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


Base = declarative_base(metadata=MetaData())


class ImageDB(InitModel, Base):
    """
    SQLAlchemy model for images table.
    This table stores unique images.
    """

    __tablename__ = "images"

    id = Column(BigInteger, primary_key=True)
    url = Column(String)
    base_model = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    nsfw = Column(Boolean)
    nsfw_level = Column(String(10))
    created_at = Column(DateTime)
    post_id = Column(BigInteger)
    username = Column(String(255))

    @classmethod
    def from_pydantic(cls, image: ImageData) -> "ImageDB":
        return cls(
            id=image.id,
            url=image.url,
            base_model=image.base_model,
            width=image.width,
            height=image.height,
            nsfw=image.nsfw,
            nsfw_level=image.nsfw_level,
            created_at=image.created_at,
            post_id=image.post_id,
            username=image.username,
        )


class ImageStatsHistoryDB(InitModel, Base):
    """
    SQLAlchemy model for image stats history.
    This table aims to track the activity for images.
    """

    __tablename__ = "image_stats_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    image_id = Column(BigInteger, ForeignKey("images.id"))
    cry_count = Column(Integer)
    laugh_count = Column(Integer)
    like_count = Column(Integer)
    heart_count = Column(Integer)
    comment_count = Column(Integer)
    collected_at = Column(DateTime, default=datetime.now(timezone.utc))

    @classmethod
    def from_pydantic(cls, image: ImageData) -> "ImageStatsHistoryDB":
        return cls(
            image_id=image.id,
            cry_count=image.stats.cry_count,
            laugh_count=image.stats.laugh_count,
            like_count=image.stats.like_count,
            heart_count=image.stats.heart_count,
            comment_count=image.stats.comment_count,
        )


class GenerationParametersDB(InitModel, Base):
    """
    SQLAlchemy model for generation parameters.
    This table stores generation parameters for images.
    """

    __tablename__ = "generation_parameters"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    image_id = Column(BigInteger, ForeignKey("images.id"))
    model = Column(String(255))
    prompt = Column(String)
    negative_prompt = Column(String)
    sampler = Column(String(50))
    schedule_type = Column(String(30))
    cfg_scale = Column(Float)
    steps = Column(Integer)
    seed = Column(BigInteger)
    size = Column(String(20))
    clip_skip = Column(Integer)
    additional_params = Column(JSON)

    @classmethod
    def from_pydantic(
        cls, image_id: int, params: GenerationParameters
    ) -> "GenerationParametersDB":
        return cls(
            image_id=image_id,
            model=params.model,
            prompt=params.prompt,
            negative_prompt=params.negative_prompt,
            sampler=params.sampler,
            schedule_type=params.schedule_type,
            cfg_scale=params.cfg_scale,
            steps=params.steps,
            seed=params.seed,
            size=params.size,
            clip_skip=params.clip_skip,
            additional_params=params.additional_params,
        )


class Database:
    """Async database management class"""

    def __init__(self, settings: Optional[DatabaseSettings] = None):
        """Initialize database connection"""
        self.settings = settings or get_db_settings()

        postgres_url = self.settings.get_url(use_async=False)
        self.engine = create_engine(
            postgres_url, echo=True, pool_size=5, max_overflow=10
        )
        self.session = sessionmaker(
            self.engine,
            # class_=AsyncSession,
            # expire_on_commit=False
        )

    def init_db(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)  # pyright: ignore[reportAttributeAccessIssue] # fmt: skip

    def save_image_data(self, image_data: ImageResponse):
        """Save image and related data to database"""
        images = image_data.items
        if not images:
            return

        with self.session() as session:
            with session.begin():  # pyright: ignore[reportGeneralTypeIssues]
                for image in images:
                    # Get or create image record
                    db_image = session.get(ImageDB, image.id)
                    if db_image is None:
                        db_image = ImageDB.from_pydantic(image)
                        session.add(db_image)
                    else:
                        # Update existing image
                        for key, value in ImageDB.from_pydantic(image).__dict__.items():
                            if key != "_sa_instance_state":
                                setattr(db_image, key, value)

                    # Always add new stats record
                    stats = ImageStatsHistoryDB.from_pydantic(image)
                    session.add(stats)

                    # Update or create generation parameters
                    stmt = select(GenerationParametersDB).where(
                        GenerationParametersDB.image_id == image.id
                    )
                    result = session.execute(stmt)
                    db_params = result.scalar_one_or_none()

                    if db_params is None:
                        db_params = GenerationParametersDB.from_pydantic(
                            image_id=image.id, params=image.meta
                        )
                        session.add(db_params)
                    else:
                        # Update existing parameters
                        new_params = GenerationParametersDB.from_pydantic(
                            image_id=image.id, params=image.meta
                        )
                        for key, value in new_params.__dict__.items():
                            if key != "_sa_instance_state":
                                setattr(db_params, key, value)
                session.commit()

    def get_table(self, table_class) -> Dict[str, list]:
        """
        Get all records from a table as a dictionary of columns

        Args:
            table_class: SQLAlchemy model class (ImageDB, ImageStatsHistoryDB, or GenerationParametersDB)

        Returns:
            Dict[str, list]: Dictionary where keys are column names and values are lists of column values
        """
        with self.session() as session:
            query = select(table_class)
            result = session.execute(query)
            rows = [row[0].__dict__ for row in result.all()]

            if not rows:
                return dict()

            # Convert rows to columns
            columns = {}
            for key in rows[0].keys():
                if key != "_sa_instance_state":
                    columns[key] = [row[key] for row in rows]

            return columns

    def get_table_df(self, table_class) -> pd.DataFrame:
        """
        Get data from a single table as pandas DataFrame

        Args:
            table_class: SQLAlchemy model class (ImageDB, ImageStatsHistoryDB, or GenerationParametersDB)

        Returns:
            pandas.DataFrame: Data from the specified table
        """
        columns = self.get_table(table_class)
        if columns:
            return pd.DataFrame(columns)
        return pd.DataFrame()

    def get_images_with_params(self) -> pd.DataFrame:
        """
        Get images data joined with their generation parameters

        Returns:
            pandas.DataFrame: Joined data from images and generation_parameters tables
        """
        df_images = self.get_table_df(ImageDB)
        df_params = self.get_table_df(GenerationParametersDB)

        # Merge dataframes on image_id
        df_merged = pd.merge(
            df_images, df_params, left_on="id", right_on="image_id", how="left"
        )

        # Clean up merged dataframe
        if not df_merged.empty:
            df_merged = df_merged.drop(["image_id", "id_y"], axis=1)
            df_merged = df_merged.rename(columns={"id_x": "id"})

        return df_merged

    def get_images_with_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get images data joined with their latest stats

        Args:
            start_date: Optional start date for filtering stats
            end_date: Optional end date for filtering stats

        Returns:
            pandas.DataFrame: Joined data from images and image_stats_history tables
        """
        df_images = self.get_table_df(ImageDB)
        df_stats = self.get_table_df(ImageStatsHistoryDB)

        # Apply date filters if provided
        if start_date:
            df_stats = df_stats[df_stats["collected_at"] >= start_date]
        if end_date:
            df_stats = df_stats[df_stats["collected_at"] <= end_date]

        # Get the latest stats for each image
        if isinstance(df_stats, pd.DataFrame) and not df_stats.empty:
            latest_stats = (
                df_stats.sort_values("collected_at")
                .groupby("image_id")
                .last()
                .reset_index()
            )

            # Merge with images data
            df_merged = pd.merge(
                df_images, latest_stats, left_on="id", right_on="image_id", how="left"
            )

            # Clean up merged dataframe
            if not df_merged.empty:
                df_merged = df_merged.drop(["image_id", "id_y"], axis=1)
                df_merged = df_merged.rename(columns={"id_x": "id"})
        else:
            df_merged = df_images

        return df_merged


def init_database():
    """Initialize database schema using SQLAlchemy models"""
    db = Database()
    db.init_db()
    # with db.engine.begin() as conn:
    #     conn.run_sync(Base.metadata.drop_all)
    #     conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    init_database()
