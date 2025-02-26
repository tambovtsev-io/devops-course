from datetime import datetime, timezone
from typing import Any, Dict, Optional

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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import select
from sqlalchemy.sql.schema import MetaData

from src.civitai_client.civitai_client import (
    GenerationParameters,
    ImageModel,
    ImageResponse,
)
from src.civitai_client.config import DatabaseSettings, get_db_settings


class InitModel:
    """Class with initialization of parameters"""

    def __init__(self, **kwargs):
        """Initialize model with kwargs"""
        for key, value in kwargs.items():
            setattr(self, key, value)


Base = declarative_base(metadata=MetaData())


class ImageDB(InitModel, Base):
    """SQLAlchemy model for images table"""

    __tablename__ = "images"

    id = Column(BigInteger, primary_key=True)
    url = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    nsfw = Column(Boolean)
    nsfw_level = Column(String(10))
    created_at = Column(DateTime)
    post_id = Column(BigInteger)
    username = Column(String(255))

    @classmethod
    def from_pydantic(cls, image: ImageModel) -> "ImageDB":
        """Create SQLAlchemy model from Pydantic model"""
        return cls(
            id=image.id,
            url=image.url,
            width=image.width,
            height=image.height,
            nsfw=image.nsfw,
            nsfw_level=image.nsfw_level,
            created_at=image.created_at,
            post_id=image.post_id,
            username=image.username,
        )


class ImageStatsHistoryDB(InitModel, Base):
    """SQLAlchemy model for image stats history"""

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
    def from_pydantic(cls, image: ImageModel) -> "ImageStatsHistoryDB":
        """Create SQLAlchemy model from Pydantic model"""
        return cls(
            image_id=image.id,
            cry_count=image.stats.cry_count,
            laugh_count=image.stats.laugh_count,
            like_count=image.stats.like_count,
            heart_count=image.stats.heart_count,
            comment_count=image.stats.comment_count,
        )


class GenerationParametersDB(InitModel, Base):
    """SQLAlchemy model for generation parameters"""

    __tablename__ = "generation_parameters"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    image_id = Column(BigInteger, ForeignKey("images.id"))
    model = Column(String(255))
    prompt = Column(String)
    negative_prompt = Column(String)
    sampler = Column(String(50))
    cfg_scale = Column(Float)
    steps = Column(Integer)
    seed = Column(BigInteger)
    size = Column(String(20))
    additional_params = Column(JSON)

    @classmethod
    def from_pydantic(
        cls, image_id: int, params: GenerationParameters
    ) -> "GenerationParametersDB":
        """Create SQLAlchemy model from Pydantic model"""
        return cls(
            image_id=image_id,
            model=params.model,
            prompt=params.prompt,
            negative_prompt=params.negative_prompt,
            sampler=params.sampler,
            cfg_scale=params.cfg_scale,
            steps=params.steps,
            seed=params.seed,
            size=params.size,
            additional_params=params.additional_params,
        )


class Database:
    """Async database management class"""

    GUARANTEED_PARAMETERS = [
        "Model",
        "prompt",
        "negativePrompt",
        "sampler",
        "cfgScale",
        "steps",
        "seed",
        "Size",
    ]

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
        Base.metadata.create_all(self.engine)

    def save_image_data(self, image_data: ImageResponse):
        """Save image and related data to database"""
        images = image_data.items
        if not images:
            return

        with self.session() as session:
            with session.begin():
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


def init_database():
    """Initialize database schema using SQLAlchemy models"""
    db = Database()
    db.init_db()
    # with db.engine.begin() as conn:
    #     conn.run_sync(Base.metadata.drop_all)
    #     conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    init_database()
