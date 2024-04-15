from pymongo.collection import Collection
from typing import List


def delete_distribution_metadata(mongo_collection: Collection, distribution_ids: List[str]):
    pass

def remove_ids(obj):
    if isinstance(obj, dict):
        obj.pop('_id', None)
        for key, value in list(obj.items()):
            obj[key] = remove_ids(value)
    elif isinstance(obj, list):
        obj = [remove_ids(item) for item in obj]
    return obj
