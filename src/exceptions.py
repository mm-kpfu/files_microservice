from typing import Any


class RecordNotFound(Exception):
    def __init__(self, pk: Any, resource_name: str):
        self.pk = pk
        self.resource_name = resource_name
