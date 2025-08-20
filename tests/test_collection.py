import datetime

import pystac
from pystac.extensions.projection import ProjectionExtension
import pytest

from stac_lake.collection import (
    CollectionSchema,
    ProjectionRequirement,
    AssetRequirement,
    validate_item_against_requirements,
)


@pytest.fixture
def base_item() -> pystac.Item:
    return pystac.Item(
        id="test-item",
        properties={},
        geometry={
            "type": "Polygon",
            "coordinates": [
                [
                    [10, 10],
                    [20, 10],
                    [20, 20],
                    [10, 20],
                    [10, 10],
                ]
            ],
        },
        bbox=[10, 10, 20, 20],
        datetime=datetime.datetime(year=2020, month=1, day=1),
    )


class TestProjectionRequirement:
    def test_validate_item_with_matching_epsg(self, base_item):
        requirement = ProjectionRequirement(epsg=4326)

        item = base_item
        item_proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        item_proj_ext.epsg = 4326

        result = requirement.validate_item_against_requirement(item)

        assert result.is_valid
        assert result.message is None

    def test_validate_item_with_non_matching_epsg(self, base_item):
        requirement = ProjectionRequirement(epsg=4326)

        item = base_item
        item_proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
        item_proj_ext.epsg = 3786

        result = requirement.validate_item_against_requirement(item)

        assert not result.is_valid
        assert result.message == "Item EPSG is 3786, expected 4326"


class TestAssetRequirement:
    def test_validate_item_with_matching_asset(self, base_item):
        requirement = AssetRequirement(asset_name="test_asset", media_type="image/png")

        item = base_item
        item.add_asset(
            "test_asset",
            pystac.Asset(href="http://example.com/test.png", media_type="image/png"),
        )

        result = requirement.validate_item_against_requirement(item)

        assert result.is_valid

    def test_validate_item_with_missing_asset(self, base_item):
        requirement = AssetRequirement(asset_name="test_asset")

        item = base_item

        result = requirement.validate_item_against_requirement(item)

        assert not result.is_valid
        assert result.message == "Item is missing required asset: test_asset"

    def test_validate_item_with_non_matching_media_type(self, base_item):
        requirement = AssetRequirement(asset_name="test_asset", media_type="image/png")

        item = base_item
        item.add_asset(
            "test_asset",
            pystac.Asset(href="http://example.com/test.jpg", media_type="image/jpeg"),
        )

        result = requirement.validate_item_against_requirement(item)

        assert not result.is_valid
        assert (
            result.message
            == "Asset 'test_asset' does not match required media type: image/png"
        )


def test_collection_schema_serialization():
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

    collection = CollectionSchema(
        stac_collection=pystac_collection,
        item_requirements=item_requirements,
    )

    collection_dict = collection.to_dict()

    assert collection_dict["stac_collection"]["id"] == "test-collection"
    assert collection_dict["item_requirements"][0]["type"] == "ProjectionRequirement"
    assert collection_dict["item_requirements"][0]["epsg"] == 4326

    collection_from_dict = CollectionSchema.from_dict(collection_dict)

    assert collection_from_dict.stac_collection.id == "test-collection"
    assert isinstance(collection_from_dict.item_requirements[0], ProjectionRequirement)


def test_validate_item_against_requirements(base_item):
    item = base_item
    item.add_asset(
        "test_asset",
        pystac.Asset(href="http://example.com/test.png", media_type="image/png"),
    )
    item_proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
    item_proj_ext.epsg = 3786

    requirements = [
        ProjectionRequirement(epsg=4326),
        AssetRequirement(asset_name="test_asset", media_type="image/jpeg"),
    ]

    result = validate_item_against_requirements(item, requirements)

    assert not result.is_valid
    assert "Item EPSG is 3786, expected 4326" in result.message
    assert (
        "Asset 'test_asset' does not match required media type: image/jpeg"
        in result.message
    )
