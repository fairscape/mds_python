from mds.models.fairscape_base import *
from typing import Optional


class DataDownloadCompactView(FairscapeBaseModel):
    type = "DataDownload"
    contentUrl: Optional[str]

