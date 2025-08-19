from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import pystac


REQUIREMENT_REGISTRY = {}


def register_requirement(cls):
    REQUIREMENT_REGISTRY[cls.__name__] = cls
    return cls


@dataclass
class ItemRequirementValidationResult:
    is_valid: bool
    message: Optional[str] = None


@dataclass
class BaseItemRequirement:
    def validate_item_against_requirement(
        self, item: pystac.Item
    ) -> ItemRequirementValidationResult:
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        raise NotImplementedError


@register_requirement
@dataclass
class ProjectionRequirement(BaseItemRequirement):
    epsg: Optional[int] = None

    def validate_item_against_requirement(
        self, item: pystac.Item
    ) -> ItemRequirementValidationResult:
        def _get_epsg_code_int(item: pystac.Item) -> Optional[int]:
            epsg_str = item.properties.get("proj:code", None)
            if epsg_str is None:
                return
            return int(epsg_str.split("EPSG:")[1])

        if self.epsg and _get_epsg_code_int(item) != self.epsg:
            return ItemRequirementValidationResult(
                False, "Item does not match required EPSG code."
            )
        return ItemRequirementValidationResult(True)

    def to_dict(self):
        return {"type": self.__class__.__name__, "epsg": self.epsg}

    @classmethod
    def from_dict(cls, data):
        return cls(epsg=data.get("epsg"))


@register_requirement
@dataclass
class AssetRequirement(BaseItemRequirement):
    asset_name: str
    media_type: Optional[str] = None

    def validate_item_against_requirement(
        self, item: pystac.Item
    ) -> ItemRequirementValidationResult:
        asset = item.assets.get(self.asset_name, None)

        if asset is None:
            return ItemRequirementValidationResult(
                False, f"Item is missing required asset: {self.asset_name}"
            )

        if self.media_type and asset.media_type != self.media_type:
            return ItemRequirementValidationResult(
                False,
                f"Asset '{self.asset_name}' does not match required media type: {self.media_type}",
            )

        return ItemRequirementValidationResult(True)


@dataclass
class Collection:
    stac_collection: pystac.Collection
    item_requirements: List[BaseItemRequirement]

    def validate_item(self, item: pystac.Item) -> ItemRequirementValidationResult:
        message = ""
        is_valid = True

        for requirement in self.item_requirements:
            result = requirement.validate_item_against_requirement(item)
            if not result.is_valid:
                is_valid = False
                message += f"{result.message} \n"

        return ItemRequirementValidationResult(
            is_valid=is_valid, message=message.strip()
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stac_collection": self.stac_collection.to_dict(),
            "item_requirements": [req.to_dict() for req in self.item_requirements],
        }

    def from_dict(cls, data: Dict[str, Any]) -> "Collection":
        stac_collection = pystac.Collection.from_dict(data["stac_collection"])
        item_requirements = [
            REQUIREMENT_REGISTRY[data["type"]].from_dict(data)
            for data in data.get("item_requirements", [])
        ]
        return cls(stac_collection=stac_collection, item_requirements=item_requirements)


def validate_item_against_requirements(
    item: pystac.Item, requirements: List[BaseItemRequirement]
) -> ItemRequirementValidationResult:
    message = ""
    is_valid = True

    for requirement in requirements:
        result = requirement.validate_item_against_requirement(item)
        if not result.is_valid:
            is_valid = False
            message += f"{result.message} \n"

    return ItemRequirementValidationResult(is_valid=is_valid, message=message.strip())
