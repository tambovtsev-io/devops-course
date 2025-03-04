import io
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import requests
from PIL import Image


def fetch_image(url: str) -> Image.Image:
    """
    Fetch image from URL and return PIL Image object.

    Args:
        url: Image URL to fetch

    Returns:
        PIL Image object
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def fetch_image_and_show(
    url: str,
    figsize: Optional[Tuple[float, float]] = None,
) -> None:
    """
    Fetch image from URL and display it using matplotlib.

    Args:
        url: Image URL to fetch
        figsize: Optional figure size (width, height) in inches
        title: Optional title for the plot
    """
    image = fetch_image(url)

    # Calculate default figure size if not provided
    if not figsize:
        width, height = image.size
        aspect_ratio = height / width
        figsize = (10.0, 10 * aspect_ratio)

    # Create figure and display image
    plt.figure(figsize=figsize)
    plt.imshow(image)

    # Remove axes and add title if provided
    plt.axis("off")

    plt.show()