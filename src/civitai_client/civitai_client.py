import aiohttp
from typing import Dict, Optional, List, Union
from datetime import datetime
from enum import Enum
import logging


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
        page: Optional[int] = None
    ) -> Dict:
        """Fetch data from /images endpoint from CivitAI API"""
        endpoint = f"{self.BASE_URL}/images"

        params = {
            "limit": min(limit, 200),
            "sort": sort.value,
            "period": period.value
        }

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
            return await response.json()
