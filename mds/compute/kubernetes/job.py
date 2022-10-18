from mds.models import Dataset, Software
from mds.models.compact.user import UserCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.models.compact.dataset import DatasetCompactView

from typing import List, Optional
from pydantic import Extra
from datetime import datetime


class KubernetesJob():
  context = {"@vocab": "https://schema.org/", "evi": "https://w3id.org/EVI#"}
  type = "evi:Computation"
  owner: UserCompactView
  dateCreated: Optional[datetime]
  dateFinished: Optional[datetime]
  container: str
  command: Optional[str]
  usedSoftware: SoftwareCompactView
  usedDataset: List[DatasetCompactView]
  podId: Optional[str]
  status: Optional[str]
  logs: Optional[str]


  def run(self):
    """
      
    """

    # read in service account file

    # using kubernetes API from environment variable
    
    return None


  def stop(self):
    return None


def FindJob(id: str) -> Job:
  return Job()