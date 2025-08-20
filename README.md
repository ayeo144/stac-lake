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