from typing import Literal

from pydantic import Extra

from mds.utils import FairscapeBaseModel, UserCompactView


class EvidenceGraph(FairscapeBaseModel):
    type: Literal["evi:EvidenceGraph"]
    owner: UserCompactView
    graph: str

    class Config:
        extra = Extra.allow
        fields = {
            "graph": {
                "graph": "@graph"
            }
        }
