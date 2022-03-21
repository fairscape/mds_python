from typing import Literal, List, Union
from mds.utils import FairscapeBaseModel, UserCompactView, DatasetCompactView, ComputationCompactView, SoftwareCompactView, EvidenceGraphCompactView


class Project(FairscapeBaseModel):
    type: Literal["Project"]
    owner: UserCompactView
    datasets: List[DatasetCompactView]
    computations: List[ComputationCompactView]
    software: List[SoftwareCompactView]
    evidencegraphs: List[EvidenceGraphCompactView]

