from pydantic import Extra
from typing import Literal
from mds.utils import FairscapeBaseModel, UserCompactView, EvidenceGraphCompactView


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
