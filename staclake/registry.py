from typing import Dict, Any, List

from staclake.collection import CollectionSchema


class CollectionSchemaRegistry:
    """
    Registry of CollectionSchemas.

    Acts as a central contract for the lakehouse metadata layer.
    """

    def __init__(self) -> None:
        self._collection_schemas: Dict[str, CollectionSchema] = {}

    def add_schema(self, collection_schema: CollectionSchema):
        """Add or replace a CollectionSchema in the registry."""
        collection_id = collection_schema.get_id()
        self._collection_schemas[collection_id] = collection_schema

    def get_schema(self, collection_id: str) -> CollectionSchema:
        """Retrieve a CollectionSchema by collection ID."""
        return self._collection_schemas.get(collection_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the registry into a serializable dictionary."""
        return {
            "schemas": {
                collection_id: collection_schema.to_dict()
                for collection_id, collection_schema in self._collection_schemas.items()
            }
        }

    @classmethod
    def from_dict(cls, registry_data: Dict[str, Any]) -> "CollectionSchemaRegistry":
        """Reconstruct a registry from a serialized dictionary."""
        registry_cls = cls()
        for schema in registry_data.get("schemas", {}).values():
            registry_cls.add_schema(CollectionSchema.from_dict(schema))
        return registry_cls

    def list_schemas(self) -> List[str]:
        """Return all registered collection IDs."""
        return list(self._collection_schemas.keys())
