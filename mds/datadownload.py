from typing import Literal, Union, Optional

from pydantic import Extra

from mds.utils import FairscapeBaseModel, UserCompactView, ComputationCompactView, EvidenceGraphCompactView


class DataDownload(FairscapeBaseModel):
    type: Literal["DataDownload"]
    owner: UserCompactView
    author: Union[str, UserCompactView]
    generatedBy: Optional[ComputationCompactView]
    evidencegraph: Optional[EvidenceGraphCompactView]
    contentSize: str
    contentUrl: str
    contentFormat: str

    class Config:
        extra = Extra.allow
        fields = {
            "generatedBy": {
                "alias": "evi:generatedBy"
            }
        }
