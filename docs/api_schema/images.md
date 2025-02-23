# Images
GET /api/v1/images
Endpoint URL: https://civitai.com/api/v1/images

## Query Parameters

| Name                      | Type                                         | Description                                                                                                                           |
|------                     |------                                        |-------------                                                                                                                          |
| limit (OPTIONAL)          | number                                       | The number of results to be returned per page. This can be a number between 0 and 200. By default, each page will return 100 results. |
| postId (OPTIONAL)         | number                                       | The ID of a post to get images from                                                                                                   |
| modelId (OPTIONAL)        | number                                       | The ID of a model to get images from (model gallery)                                                                                  |
| modelVersionId (OPTIONAL) | number                                       | The ID of a model version to get images from (model gallery filtered to version)                                                      |
| username (OPTIONAL)       | string                                       | Filter to images from a specific user                                                                                                 |
| nsfw (OPTIONAL)           | boolean or enum (None, Soft, Mature, X)      | Filter to images that contain mature content flags or not (undefined returns all)                                                     |
| sort (OPTIONAL)           | enum (Most Reactions, Most Comments, Newest) | The order in which you wish to sort the results                                                                                       |
| period (OPTIONAL)         | enum (AllTime, Year, Month, Week, Day)       | The time frame in which the images will be sorted                                                                                     |
| page (OPTIONAL)           | number                                       | The page from which to start fetching creators                                                                                        |

## Response Fields

| Name                 | Type                         | Description                                             |
|------                |------                        |-------------                                            |
| id                   | number                       | The id of the image                                     |
| url                  | string                       | The url of the image at it's source resolution          |
| hash                 | string                       | The blurhash of the image                               |
| width                | number                       | The width of the image                                  |
| height               | number                       | The height of the image                                 |
| nsfw                 | boolean                      | If the image has any mature content labels              |
| nsfwLevel            | enum (None, Soft, Mature, X) | The NSFW level of the image                             |
| createdAt            | date                         | The date the image was posted                           |
| postId               | number                       | The ID of the post the image belongs to                 |
| stats.cryCount       | number                       | The number of cry reactions                             |
| stats.laughCount     | number                       | The number of laugh reactions                           |
| stats.likeCount      | number                       | The number of like reactions                            |
| stats.heartCount     | number                       | The number of heart reactions                           |
| stats.commentCount   | number                       | The number of comment reactions                         |
| meta                 | object                       | The generation parameters parsed or input for the image |
| username             | string                       | The username of the creator                             |
| metadata.nextCursor  | number                       | The id of the first image in the next batch             |
| metadata.currentPage | number                       | The the current page you are at (if paging)             |
| metadata.pageSize    | number                       | The the size of the batch (if paging)                   |
| metadata.nextPage    | string                       | The url to get the next batch of items                  |

## Example

The following example shows a request to get the first image:
```
curl https://civitai.com/api/v1/images?limit=1 \
-H "Content-Type: application/json" \
-X GET
```
This would yield the following response:
```
{
  "items": [
    {
      "id": 469632,
      "url": "https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/cc5caabb-e05f-4976-ff3c-7058598c4e00/width=1024/cc5caabb-e05f-4976-ff3c-7058598c4e00.jpeg",
      "hash": "UKHU@6H?_ND*_3M{t84o^+%MD%xuXSxasAt7",
      "width": 1024,
      "height": 1536,
      "nsfw": false,
      "nsfwLevel": "None",
      "createdAt": "2023-04-11T15:33:12.500Z",
      "postId": 138779,
      "stats": {
        "cryCount": 0,
        "laughCount": 0,
        "likeCount": 0,
        "dislikeCount": 0,
        "heartCount": 0,
        "commentCount": 0
      },
      "meta": {
        "Size": "512x768",
        "seed": 234871805,
        "Model": "Meina",
        "steps": 35,
        "prompt": "<lora:setsunaTokage_v10:0.6>, green hair, long hair, standing, (ribbed dress), zettai ryouiki, choker, (black eyes), looking at viewer, adjusting hair, hand in own hair, street, grin, sharp teeth, high ponytail, [Style of boku no hero academia]",
        "sampler": "DPM++ SDE Karras",
        "cfgScale": 7,
        "Clip skip": "2",
        "Hires upscale": "2",
        "Hires upscaler": "4x-AnimeSharp",
        "negativePrompt": "(worst quality, low quality, extra digits:1.3), easynegative,",
        "Denoising strength": "0.4"
      },
      "username": "Cooler_Rider"
    }
  ],
  "metadata": {
    "nextCursor": 101,
    "currentPage": 1,
    "pageSize": 100,
    "nextPage": "https://civitai.com/api/v1/images?page=2"
  }
}
```

Notes:
  - On July 2, 2023 we switch from a paging system to a cursor based system due to the volume of data and requests for this endpoint.
  - Whether you use paging or cursors, you can use metadata.nextPage to get the next page of results
