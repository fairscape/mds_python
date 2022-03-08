from pydantic import  Extra
from typing import List, Literal, Union
from mds.utils import FairscapeBaseModel, UserCompactView, ComputationCompactView


class Software(FairscapeBaseModel, extra=Extra.allow):
    type: Literal["evi:Software"]
    owner: UserCompactView
    author: Union[str, UserCompactView]
    downloadUrl: str
    citation: str
    usedBy: List[ComputationCompactView]

    class Config:
        fields = {
            "usedBy": {
                "alias": "evi:usedBy"
            }
        }


