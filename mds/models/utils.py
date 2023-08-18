from pymongo.collection import Collection
from typing import List


def list_dataset(mongo_collection: Collection):
    cursor = mongo_collection.find(
        filter={"@type": "evi:Dataset"},
        projection={"_id": False}
    )
    dataset_list = [
            {
                "@id": dataset.get("@id"), 
                "@type": "evi:Dataset", 
                "name": dataset.get("name")
            } for dataset in cursor
        ]
    return {"datasets": dataset_list }


def delete_distribution_metadata(mongo_collection: Collection, distribution_ids: List[str]):
    pass
