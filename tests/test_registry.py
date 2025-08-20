import datetime

import pystac

from staclake.collection import CollectionSchema, ProjectionRequirement
from staclake.registry import CollectionSchemaRegistry


def test_serialize_collection_schema_registry():
    pystac_collection = pystac.Collection(
        id="test-collection",
        description="A test collection",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[10, 10, 20, 20]]),
            temporal=pystac.TemporalExtent(
                [[datetime.datetime(2020, 1, 1), datetime.datetime(2020, 1, 2)]]
            ),
        ),
    )
    item_requirements = [
        ProjectionRequirement(epsg=4326),
    ]

    collection_schema = CollectionSchema(
        stac_collection=pystac_collection,
        item_requirements=item_requirements,
    )
    registry = CollectionSchemaRegistry()
    registry.add_schema(collection_schema)

    registry_dict = registry.to_dict()
    assert "schemas" in registry_dict
    assert "test-collection" in registry_dict["schemas"]
    assert (
        registry_dict["schemas"]["test-collection"]["stac_collection"]["id"]
        == "test-collection"
    )

    registry_from_dict = CollectionSchemaRegistry.from_dict(registry_dict)
    assert (
        registry_from_dict.get_schema("test-collection").stac_collection.id
        == "test-collection"
    )
