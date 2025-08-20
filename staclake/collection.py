from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import pystac
from pystac.extensions.projection import ProjectionExtension


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
    """
    Abstract base class for all item-level validation requirements.

    Subclasses implement specific rules that a `pystac.Item` must satisfy
    (e.g., projection, asset properties). Each requirement is responsible
    for validating one aspect of an item and returning a structured result.

    When implementing a new requirement, the class should be decorated with
    `@register_requirement` to ensure it is registered in the global requirements
    registry. This allows the `CollectionSchema` to dynamically load and
    deserialize requirements from their dictionary representation.

    Methods
    -------
    validate_item_against_requirement(item: pystac.Item) -> ItemRequirementValidationResult
        Validate a STAC Item against this requirement. Must be implemented by
        subclasses.
    to_dict() -> Dict[str, Any]
        Serialize the requirement definition to a dictionary, including a
        `type` field used for deserialization.
    from_dict(data: Dict[str, Any]) -> BaseItemRequirement
        Class method to restore a requirement instance from its serialized
        dictionary form.
    """

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
    """
    Requirement enforcing that a STAC Item has a specific projection.

    This requirement uses the STAC Projection Extension (`proj:epsg`) to
    verify that the item's EPSG code matches the expected value.

    Attributes
    ----------
    epsg : int, optional
        The required EPSG code. If None, no projection validation is applied.

    Methods
    -------
    validate_item_against_requirement(item: pystac.Item) -> ItemRequirementValidationResult
        Check whether the item's EPSG code matches the required EPSG.
    to_dict() -> Dict[str, Any]
        Serialize the requirement to a dictionary, including type and epsg.
    from_dict(data: Dict[str, Any]) -> ProjectionRequirement
        Restore a requirement from a serialized dictionary.
    """

    epsg: Optional[int] = None

    def validate_item_against_requirement(
        self, item: pystac.Item
    ) -> ItemRequirementValidationResult:
        item_proj_ext = ProjectionExtension.ext(item, add_if_missing=False)

        if self.epsg and item_proj_ext.epsg != self.epsg:
            return ItemRequirementValidationResult(
                False, f"Item EPSG is {item_proj_ext.epsg}, expected {self.epsg}"
            )

        return ItemRequirementValidationResult(True)

    def to_dict(self):
        return {"type": self.__class__.__name__, "epsg": self.epsg}

    @classmethod
    def from_dict(cls, data):
        return cls(epsg=data["epsg"])


@register_requirement
@dataclass
class AssetRequirement(BaseItemRequirement):
    """
    Requirement enforcing the presence and properties of a specific asset.

    This requirement ensures that an item contains a named asset and that
    optional constraints such as media type are satisfied.

    Attributes
    ----------
    asset_name : str
        The required name of the asset (key in `item.assets`).
    media_type : str, optional
        The required media type (e.g., "image/png"). If None, any media type
        is accepted.

    Methods
    -------
    validate_item_against_requirement(item: pystac.Item) -> ItemRequirementValidationResult
        Check that the item contains the required asset and that its
        properties (e.g., media type) match the requirement.
    to_dict() -> Dict[str, Any]
        Serialize the requirement to a dictionary, including type, asset name,
        and media type if present.
    from_dict(data: Dict[str, Any]) -> AssetRequirement
        Restore a requirement from a serialized dictionary.
    """

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "asset_name": self.asset_name,
            "media_type": self.media_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetRequirement":
        return cls(
            asset_name=data["asset_name"],
            media_type=data["media_type"],
        )


@dataclass
class CollectionSchema:
    """
    Schema wrapper around a STAC Collection that enforces validation rules on items.

    This class combines a core STAC Collection definition (via `pystac.Collection`)
    with a set of item-level requirements. These requirements are applied to each
    `pystac.Item` to ensure the data ingested into the collection meets expected
    standards (e.g., projection, asset types, GSD).

    Typical usage:
        >>> schema = CollectionSchema.from_dict(schema_dict)
        >>> result = schema.validate_item(item)
        >>> if not result.is_valid:
        ...     print(result.message)

    Attributes
    ----------
    stac_collection : pystac.Collection
        The underlying STAC Collection object that defines spatial, temporal, and
        descriptive metadata.
    item_requirements : List[BaseItemRequirement]
        A list of validation requirements applied to items in the collection.
        Each requirement encapsulates a rule (e.g., expected EPSG code,
        mandatory asset) and returns a validation result.

    Methods
    -------
    validate_item(item: pystac.Item) -> ItemRequirementValidationResult
        Validate a single STAC Item against all defined requirements. Returns
        a result indicating whether the item passed and any associated messages.

    to_dict() -> Dict[str, Any]
        Serialize the schema (collection + requirements) to a dictionary for
        persistence (e.g., JSON serialization).

    from_dict(collection_data: Dict[str, Any]) -> CollectionSchema
        Class method to reconstruct a CollectionSchema from a dictionary,
        typically loaded from JSON. Uses the requirement registry to restore
        requirement subclasses.
    """

    stac_collection: pystac.Collection
    item_requirements: List[BaseItemRequirement]

    def validate_item(self, item: pystac.Item) -> ItemRequirementValidationResult:
        return validate_item_against_requirements(
            item=item, requirements=self.item_requirements
        )

    def get_id(self) -> str:
        return self.stac_collection.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stac_collection": self.stac_collection.to_dict(),
            "item_requirements": [req.to_dict() for req in self.item_requirements],
        }

    @classmethod
    def from_dict(cls, collection_data: Dict[str, Any]) -> "CollectionSchema":
        stac_collection = pystac.Collection.from_dict(
            collection_data["stac_collection"]
        )
        item_requirements = [
            REQUIREMENT_REGISTRY[requirement["type"]].from_dict(requirement)
            for requirement in collection_data.get("item_requirements", [])
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
