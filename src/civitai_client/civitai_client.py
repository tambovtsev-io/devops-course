import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel, Field, model_validator


class NSFWLevel(str, Enum):
    """NSFW levels supported by CivitAI"""

    NONE = "None"
    SOFT = "Soft"
    MATURE = "Mature"
    X = "X"


class SortType(str, Enum):
    """Sorting options for images"""

    MOST_REACTIONS = "Most Reactions"
    MOST_COMMENTS = "Most Comments"
    NEWEST = "Newest"


class TimePeriod(str, Enum):
    """Time period options for filtering"""

    ALL_TIME = "AllTime"
    YEAR = "Year"
    MONTH = "Month"
    WEEK = "Week"
    DAY = "Day"


class ImageStats(BaseModel):
    """Image statistics model"""

    cry_count: int = Field(..., alias="cryCount")
    laugh_count: int = Field(..., alias="laughCount")
    like_count: int = Field(..., alias="likeCount")
    heart_count: int = Field(..., alias="heartCount")
    comment_count: int = Field(..., alias="commentCount")


class SearchMetaData(BaseModel):
    """Metadata for pagination"""

    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    current_page: Optional[str] = Field(None, alias="currentPage")
    page_size: Optional[str] = Field(None, alias="pageSize")
    next_page: Optional[str] = Field(None, alias="nextPage")


class GenerationParameters(BaseModel):
    """Model for image generation parameters"""

    # Core parameters
    model: Optional[str] = Field(None, alias="Model")
    prompt: Optional[str] = Field(None)
    negative_prompt: Optional[str] = Field(None, alias="negativePrompt")
    sampler: Optional[str] = Field(None)
    schedule_type: Optional[str] = Field(
        None, alias="Schedule type", description="Scheduler used"
    )
    cfg_scale: Optional[float] = Field(None, alias="cfgScale")
    steps: Optional[int] = Field(None)
    seed: Optional[int] = Field(None)
    size: Optional[str] = Field(None, alias="Size")

    # Common additional parameters
    clip_skip: Optional[int] = Field(
        None, alias="clipSkip", description="Number of CLIP layers to skip"
    )
    hires_upscale: Optional[str] = Field(
        None, alias="Hires upscale", description="Hires upscale factor"
    )
    hires_upscaler: Optional[str] = Field(
        None, alias="Hires upscaler", description="Upscaler used for hi-res fix"
    )
    denoising_strength: Optional[float] = Field(
        None,
        alias="Denoising strength",
    )

    # Additional parameters that don't fit the standard fields
    additional_params: Dict[str, Any] = Field(
        default_factory=dict, description="Any additional generation parameters"
    )

    @model_validator(mode="before")
    def extract_parameters(cls, values: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract known parameters and store the rest in additional_params"""
        known_fields = {
            field.alias if field.alias else name: name
            for name, field in cls.model_fields.items()
            if name != "additional_params"
        }

        result = {}
        additional = {}

        if values is None:
            return dict()

        for key, value in values.items():
            if key in known_fields:
                result[known_fields[key]] = value
            else:
                additional[key] = value

        result["additional_params"] = additional
        return result


class ImageData(BaseModel):
    """Image data model"""

    id: int
    url: str
    hash: str
    width: int
    height: int
    nsfw: bool
    nsfw_level: NSFWLevel = Field(..., alias="nsfwLevel")
    created_at: datetime = Field(..., alias="createdAt")
    post_id: int = Field(..., alias="postId")
    stats: ImageStats
    meta: GenerationParameters
    base_model: Optional[str] = Field(None, alias="baseModel")
    username: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def get_all_generation_params(self) -> Dict[str, Any]:
        """Get all generation parameters including additional ones"""
        params = self.meta.model_dump(exclude_none=True)
        params.update(params.pop("additional_params", {}))
        return params


class ImageResponse(BaseModel):
    """Response model for images endpoint"""

    items: List[ImageData]
    metadata: SearchMetaData


class CivitAIClient:
    """Async client for CivitAI API interactions"""

    BASE_URL = "https://civitai.com/api/v1"

    def __init__(self):
        """Initialize client with base URL and session"""
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()

    async def get_images(
        self,
        limit: int = 100,
        post_id: Optional[int] = None,
        model_id: Optional[int] = None,
        model_version_id: Optional[int] = None,
        username: Optional[str] = None,
        nsfw: Optional[Union[bool, NSFWLevel]] = None,
        sort: SortType = SortType.MOST_REACTIONS,
        period: TimePeriod = TimePeriod.DAY,
        page: Optional[int] = None,
    ) -> ImageResponse:
        """Fetch data from /images endpoint from CivitAI API"""
        endpoint = f"{self.BASE_URL}/images"

        params = {"limit": min(limit, 200), "sort": sort.value, "period": period.value}

        # Add optional parameters if provided
        if post_id:
            params["postId"] = post_id
        if model_id:
            params["modelId"] = model_id
        if model_version_id:
            params["modelVersionId"] = model_version_id
        if username:
            params["username"] = username
        if nsfw is not None:
            params["nsfw"] = nsfw.value if isinstance(nsfw, NSFWLevel) else nsfw
        if page:
            params["page"] = page

        if not self._session:
            raise Exception("Session not initialized")

        async with self._session.get(endpoint, params=params) as response:
            if response.status != 200:
                logging.error(f"Error fetching images: {response.status}")
                raise Exception(f"API request failed with status {response.status}")
            data = await response.json()
            return ImageResponse(**data)
