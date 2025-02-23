from datetime import datetime, timezone
from typing import Any, Dict

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
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Image(Base):
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


class ImageStatsHistory(Base):
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


class GenerationParameters(Base):
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

    def __init__(self, connection_url: str):
        """Initialize database connection"""
        self.engine = create_async_engine(connection_url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save_image_data(self, image_data: Dict[str, Any]):
        """Save image and related data to database"""
        async with self.async_session() as session:
            # Create image record
            image = Image(
                id=image_data["id"],
                url=image_data["url"],
                width=image_data["width"],
                height=image_data["height"],
                nsfw=image_data["nsfw"],
                nsfw_level=image_data["nsfwLevel"],
                created_at=datetime.fromisoformat(
                    image_data["createdAt"].replace("Z", "+00:00")
                ),
                post_id=image_data["postId"],
                username=image_data["username"],
            )

            # Create stats history record
            stats = ImageStatsHistory(
                image_id=image_data["id"],
                cry_count=image_data["stats"]["cryCount"],
                laugh_count=image_data["stats"]["laughCount"],
                like_count=image_data["stats"]["likeCount"],
                heart_count=image_data["stats"]["heartCount"],
                comment_count=image_data["stats"]["commentCount"],
            )

            # Create generation parameters record
            meta = image_data.get("meta", {})
            gen_params = GenerationParameters(
                image_id=image_data["id"],
                model=meta.get("Model"),
                prompt=meta.get("prompt"),
                negative_prompt=meta.get("negativePrompt"),
                sampler=meta.get("sampler"),
                cfg_scale=meta.get("cfgScale"),
                steps=meta.get("steps"),
                seed=meta.get("seed"),
                size=meta.get("Size"),
                additional_params={
                    k: v for k, v in meta.items() if k not in self.GUARANTEED_PARAMETERS
                },
            )

            session.add_all([image, stats, gen_params])
            await session.commit()
