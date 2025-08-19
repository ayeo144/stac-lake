import datetime

import pystac
from pystac.extensions.projection import ProjectionExtension
import pytest

from stac_lake.collection import (
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
        assert result.message == "Item does not match required EPSG code."


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
    assert "Item does not match required EPSG code." in result.message
    assert (
        "Asset 'test_asset' does not match required media type: image/jpeg"
        in result.message
    )
