# STACLake

Bringing **lakehouse-style schema enforcement** to geospatial raster data lakes using the [STAC](https://stacspec.org/) standard.

## Why?

Managing large stores of raster data is hard — metadata gets messy, multiple satellites and processing levels introduce inconsistency, and enforcing quality is tricky.  

STACLake builds on STAC (SpatioTemporal Asset Catalog), an open metadata standard, to provide **schema and metadata governance** for raster data lakes. The goal is to make it easier to ensure consistent metadata and enforce validation rules at scale.

## The Model

Think of STACLake like a data lakehouse for rasters:

- **STAC Collection** → equivalent of a **table**  
- **STAC Items** → equivalent of **rows** in that table  
- **Schema Requirements** → equivalent of **constraints** (e.g., projection must be EPSG:4326, certain assets must exist)

This approach makes metadata more reliable, discoverable, and enforceable.

## Quickstart

```python
import datetime
import pystac
from pystac.extensions.projection import ProjectionExtension

from staclake.collection import (
    CollectionSchema,
    ProjectionRequirement,
    AssetRequirement,
)

# --- Create a basic STAC Collection ---
collection = pystac.Collection(
    id="my-collection",
    description="Example collection of raster data",
    extent=pystac.Extent(
        spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
        temporal=pystac.TemporalExtent([[datetime.datetime(2020, 1, 1), None]]),
    ),
)

# --- Define schema requirements ---
requirements = [
    ProjectionRequirement(epsg=4326),
    AssetRequirement(asset_name="visual", media_type="image/png"),
]

collection_schema = CollectionSchema(
    stac_collection=collection,
    item_requirements=requirements,
)

# --- Create a STAC Item ---
item = pystac.Item(
    id="example-item",
    geometry={
        "type": "Polygon",
        "coordinates": [[[10, 10], [20, 10], [20, 20], [10, 20], [10, 10]]],
    },
    bbox=[10, 10, 20, 20],
    datetime=datetime.datetime(2020, 1, 1),
    properties={},
)

# Add projection info via STAC Projection extension
proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
proj_ext.epsg = 4326

# Add an asset
item.add_asset(
    "visual",
    pystac.Asset(
        href="http://example.com/visual.png",
        media_type="image/png",
    ),
)

# --- Validate the item against the schema ---
result = collection_schema.validate_item(item)

print(result.is_valid)   # True
print(result.message)    # None if valid, or error messages if invalid
```