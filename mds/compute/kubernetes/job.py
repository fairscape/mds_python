from mds.models import Dataset, Software, Computation
from mds.models.compact.user import UserCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.models.compact.dataset import DatasetCompactView
from typing import List, Optional, Union
from pydantic import Extra
from datetime import datetime
from mds.database import mongo, minio
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION

from time import sleep
from kubernetes import client, config, watch
from celery.utils.log import get_task_logger
from mds.compute.celery import workflow


# setup client configuration
config.load_incluster_config()
v1 = client.CoreV1Api()
batch = client.BatchV1Api()


task_logger = get_task_logger(__name__)

FAIRSCAPE_NAMESPACE = "clarklab"

class ComputationNotFound(Exception):
    def __init__(self, computation_id, message="Computation Metadata Not Found"):
        self.computation_id = computation_id
        self.message = message

        # ensure exception can be pickled by celery
        super().__init__(self, self.computation_id, self.message)


@workflow.task(name="download_job")
def download_job(computation_id):

    # get job metadata
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]
    computation = Computation.construct(id=computation_id)
    read_status = computation.read(mongo_collection)

    if read_status.success!=True:
        raise ComputationNotFound(
            computation_id, 
            message=f"Computation Metadata Not Found for identifier {computation_id}"
            )


    job_name = computation.name + "-download-job"
    pvc_name = computation.name + "-pvc" 


    pvc_manifest = create_persistant_volume(
        pvc_name,
        computation.requirements.storage.requests,
        computation.requirements.storage.limits 
    )

    create_pvc = v1.create_namespaced_persistent_volume_claim(
        namespace=FAIRSCAPE_NAMESPACE, 
        body=pvc_manifest
    )

    task_logger.info(f"Computation: {computation_id}\tCreating Persistant Volume Claim {pvc_name}")

    download_job_manifest = create_download_job(
        job_name = job_name, 
        computation_id = computation_id,
        pvc_name = pvc_name
    )

    download_job_metadata = batch.create_namespaced_job(
        namespace=FAIRSCAPE_NAMESPACE, 
        body= download_job_manifest
    )

    task_logger.info(f"Computation: {computation_id}\tCreating Download Job {job_name}")

    # wait for job to finish
    in_progress=True
    while in_progress==True:

        try:
            job_read = batch.read_namespaced_job(namespace=FAIRSCAPE_NAMESPACE, name=job_name)
            job_status = job_read.status

            # if job succeeded 
            if job_status.succeeded == 1:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Succeeded")

                # TODO update metadata with download job logs
                
                # clean up the job
                cleanup_job(job_name)
                return True


            # if job failed
            if job_status.failed != None:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Failed")

                # TODO get the logs of any pod

                # TODO update the metadata

                # clean up the job
                cleanup_job(job_name)
                return False



            # if job running
            if job_status.active != None:
                continue

        except Exception as e:
            task_logger.info(f"Batch Job Not Found {str(e)}")

        sleep(10)
    

@workflow.task(name="run_job")
def run_job(computation_id):

    # get job metadata
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]
    computation = Computation.construct(id=computation_id)
    read_status = computation.read(mongo_collection)

    if read_status.success!=True:
        raise ComputationNotFound(
            computation_id, 
            message=f"Computation Metadata Not Found for identifier {computation_id}"
            )

    pvc_name = computation.name + "-pvc" 
    compute_job_name = computation.name + "-compute-job"

    compute_job_manifest = create_compute_job(
        job_name=compute_job_name, 
        pvc_name=pvc_name, 
        image=computation.image, 
        command=computation.command
        )

    #computation.requirements.cpu.requests,
    #computation.requirements.cpu.limits,
    #computation.requirements.mem.requests,
    #computation.requirements.mem.limits 

    compute_job_metadata = batch.create_namespaced_job(
        namespace=FAIRSCAPE_NAMESPACE, 
        body=compute_job_manifest
    )
 

    # wait for job to finish
    in_progress=True
    while in_progress==True:

        try:
            job_read = batch.read_namespaced_job(namespace=FAIRSCAPE_NAMESPACE, name=compute_job_name)
            job_status = job_read.status

            # if job succeeded 
            if job_status.succeeded == 1:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Succeeded")

                # TODO update metadata with download job logs
                
                # clean up the job
                cleanup_job(compute_job_name)
                return True


            # if job failed
            if job_status.failed != None:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Failed")

                # TODO get the logs of any pod

                # TODO update the metadata

                # clean up the job
                cleanup_job(compute_job_name)
                return False



            # if job running
            if job_status.active != None:
                continue

        except Exception as e:
            task_logger.info(f"Batch Job Not Found {str(e)}")

        sleep(10) 


@workflow.task(name="register_job")
def register_job(computation_id):

    # get job metadata
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]
    computation = Computation.construct(id=computation_id)
    read_status = computation.read(mongo_collection)

    if read_status.success!=True:
        raise ComputationNotFound(
            computation_id, 
            message=f"Computation Metadata Not Found for identifier {computation_id}"
            )

    pvc_name = computation.name + "-pvc" 
    register_job_name = computation.name + "-register-job"


    register_job_manifest = create_registration_job(
        job_name=register_job_name, 
        computation_id=computation_id, 
        pvc_name=pvc_name 
    )

    register_job_metadata = batch.create_namespaced_job(
        namespace="clarklab", 
        body=register_job_manifest
    )

    # wait for job execute
    in_progress=True
    while in_progress==True:

        try:
            job_read = batch.read_namespaced_job(namespace=FAIRSCAPE_NAMESPACE, name=compute_job_name)
            job_status = job_read.status

            # if job succeeded 
            if job_status.succeeded == 1:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Succeeded")

                # TODO update metadata with download job logs
                
                # clean up the job
                cleanup_job(compute_job_name)
                return True


            # if job failed
            if job_status.failed != None:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Failed")

                # TODO get the logs of any pod

                # TODO update the metadata

                # clean up the job
                cleanup_job(compute_job_name)
                return False



            # if job running
            if job_status.active != None:
                continue

        except Exception as e:
            task_logger.info(f"Batch Job Not Found {str(e)}")

        sleep(10)


def create_persistant_volume(name, storage_requests, storage_limits):
    
    pvc_spec = client.V1PersistentVolumeClaimSpec(
        access_modes=["ReadWriteOnce"], 
        resources=client.V1ResourceRequirements(
            requests={"storage": storage_requests}, 
            limits={"storage": storage_limits}
        )
    )
    
    pvc_metadata = client.V1ObjectMeta(
        name=name
    )
    
    pvc = client.V1PersistentVolumeClaim(metadata=pvc_metadata, spec=pvc_spec)
    return pvc


def create_download_job(job_name: str, computation_id: str, pvc_name: str):
    
    job_volume_source = client.V1Volume(
        name="job-volume", 
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
            claim_name=pvc_name
        )
    )

    job_configmap_source = client.V1Volume(
        name="script", 
        config_map=client.V1ConfigMapVolumeSource(name="download-script")
    )

    # launch a pod mounted with the test-job-pvc
    container_resources = client.V1ResourceRequirements(
        requests={"cpu": "100m", "memory": "1000Mi"}, 
        limits={"cpu": "150m", "memory": "1500Mi"}
    )

    job_container = client.V1Container(
        name='job-download', 
        image=FAIRSCAPE_IMAGE,
        image_pull_policy= "Always",
        command=["python3", "/mnt/script/download.py"],
        volume_mounts= [
            {"mountPath": "/mnt/job", "name": "job-volume"}, 
            {"mountPath": "/mnt/script", "name": "script"}
        ],
        resources=container_resources,
        env= [
            {
                "name": "COMPUTATION_IDENTIFIER", 
                "value": computation_id
            },
            {
                "name": "MONGO_HOST", 
                "value": "10.250.124.184"
            },
            {
                "name": "MONGO_DATABASE", 
                "value": "clarklab"
            },
            {
                "name": "MONGO_COLLECTION", 
                "value": "fairscape"
            },
            {
                "name": "MONGO_PORT",
                "value": "27017"
            },
            {
                "name": "MINIO_URI", 
                "value": "minio.uvarc.io"
            },
            {
                "name": "MINIO_BUCKET", 
                "value": "clarklab"
            },
            {
                "name": "MONGO_ACCESS_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "mongo-access-key"
                    }
                }
            },
            {
                "name": "MONGO_SECRET_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "mongo-secret-key"
                    }
                }
            },
            {
                "name": "MINIO_ACCESS_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "minio-access-key"
                    }
                }
            },
            {
                "name": "MINIO_SECRET_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "minio-secret-key"
                    }
                }
            }
        ]
    )

    pod_spec = client.V1PodSpec(
        containers=[job_container], 
        image_pull_secrets= [client.V1LocalObjectReference(name="ghcr-secret")],
        volumes=[
            job_volume_source,
            job_configmap_source
        ], 
        restart_policy="Never"
    )

    prefix, org, proj, job_key =computation_id.split("/")

    job_pod_template_spec = client.V1PodTemplateSpec(spec=pod_spec)
    job_spec = client.V1JobSpec(template=job_pod_template_spec, completions=1)
    job_metadata = client.V1ObjectMeta(
        name=job_name, 
        namespace="clarklab", 
        labels={
            "organization": org,
            "project": proj,
            "computation": job_key,
            "stage": "download"
        }
    )

    job = client.V1Job(
        api_version="batch/v1", 
        kind="Job", 
        spec=job_spec, 
        metadata=job_metadata
    )
    
    return job


def create_compute_job(job_name: str, script_name: str, pvc_name: str, image, command):
    job_volume_source = client.V1Volume(
        name="job-volume", 
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
            claim_name=pvc_name
        )
    )

    job_configmap_source = client.V1Volume(
        name="script", 
        config_map=client.V1ConfigMapVolumeSource(name=script_name)
    )

    # launch a pod mounted with the test-job-pvc
    container_resources = client.V1ResourceRequirements(
        requests={"cpu": "1000m", "memory": "5000Mi"}, 
        limits={"cpu": "10000m", "memory": "7500Mi"}
    )
    
    job_container = client.V1Container(
        name='job-compute', 
        image=image,
        image_pull_policy= "Always",
        command=command,
        volume_mounts= [
            {"mountPath": "/mnt/job", "name": "job-volume"}, 
            {"mountPath": "/mnt/script", "name": "script"}
        ],
        resources=container_resources,
        env= [
            {
                "name": "COMPUTATION_IDENTIFIER", 
                "value": computation_id
            }
        ]
    )
    
    pod_spec = client.V1PodSpec(
        containers=[job_container], 
        image_pull_secrets= [client.V1LocalObjectReference(name="ghcr-secret")],
        volumes=[
            job_volume_source,
            job_configmap_source
        ], 
        restart_policy="Never"
    )


    job_pod_template_spec = client.V1PodTemplateSpec(spec=pod_spec)
    job_spec = client.V1JobSpec(template=job_pod_template_spec, completions=1)
    job_metadata = client.V1ObjectMeta(name=job_name, namespace="clarklab")

    prefix, org, proj, job_key =computation_id.split("/")
    
    job_metadata = client.V1ObjectMeta(
        name=job_name, 
        namespace="clarklab", 
          labels={
            "organization": org,
            "project": proj,
            "computation": job_key,
            "stage": "compute"
        }
    )
    
    job = client.V1Job(
        api_version="batch/v1", 
        kind="Job", 
        spec=job_spec, 
        metadata=job_metadata
    )
    
    return job


def create_registration_job(job_name: str, computation_id: str, pvc_name: str):
    
    job_volume_source = client.V1Volume(
        name="job-volume", 
        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
            claim_name=pvc_name
        )
    )

    #job_configmap_source = client.V1Volume(
    #    name="script", 
    #    config_map=client.V1ConfigMapVolumeSource(name="registration-script")
    #)

    # launch a pod mounted with the test-job-pvc
    container_resources = client.V1ResourceRequirements(
        requests={"cpu": "1000m", "memory": "5000Mi"}, 
        limits={"cpu": "10000m", "memory": "7500Mi"}
    )

    job_container = client.V1Container(
        name='job-download', 
        image=FAIRSCAPE_IMAGE,
        image_pull_policy= "Always",
        #command=["python3", "/mnt/script/register.py"],
        command=["sleep", "1d"],
        volume_mounts= [
            {"mountPath": "/mnt/job", "name": "job-volume"}, 
            #{"mountPath": "/mnt/script", "name": "script"}
        ],
        resources=container_resources,
        env= [
            {
                "name": "COMPUTATION_IDENTIFIER", 
                "value": computation_id
            },
            {
                "name": "MONGO_HOST", 
                "value": "10.250.124.184"
            },
            {
                "name": "MONGO_DATABASE", 
                "value": "clarklab"
            },
            {
                "name": "MONGO_COLLECTION", 
                "value": "fairscape"
            },
            {
                "name": "MONGO_PORT",
                "value": "27017"
            },
            {
                "name": "MINIO_URI", 
                "value": "minio.uvarc.io"
            },
            {
                "name": "MINIO_BUCKET", 
                "value": "clarklab"
            },
            {
                "name": "MONGO_ACCESS_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "mongo-access-key"
                    }
                }
            },
            {
                "name": "MONGO_SECRET_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "mongo-secret-key"
                    }
                }
            },
            {
                "name": "MINIO_ACCESS_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "minio-access-key"
                    }
                }
            },
            {
                "name": "MINIO_SECRET_KEY", 
                "valueFrom": {
                    "secretKeyRef": {
                        "name": "fairscape-secrets", 
                        "key": "minio-secret-key"
                    }
                }
            }
        ]
    )

    pod_spec = client.V1PodSpec(
        containers=[job_container], 
        image_pull_secrets= [client.V1LocalObjectReference(name="ghcr-secret")],
        volumes=[
            job_volume_source,
            #job_configmap_source
        ], 
        restart_policy="Never"
    )

    prefix, org, proj, job_key =computation_id.split("/")

    job_pod_template_spec = client.V1PodTemplateSpec(spec=pod_spec)
    job_spec = client.V1JobSpec(template=job_pod_template_spec, completions=1)
    job_metadata = client.V1ObjectMeta(
        name=job_name, 
        namespace="clarklab", 
        labels={
            "organization": org,
            "project": proj,
            "computation": job_key,
            "stage": "download"
        }
    )

    job = client.V1Job(
        api_version="batch/v1", 
        kind="Job", 
        spec=job_spec, 
        metadata=job_metadata
    )
    
    return job


def cleanup_job(job_name):
  """
  """
  try:
      batch.delete_namespaced_job(
          namespace="clarklab", 
          name=job_name
      )
  except Exception as e:
      print(e)
      
  live_pod_names = list(
      filter(
          lambda x: True if job_name in x else False,
          map(
              lambda x: x.metadata.name, v1.list_namespaced_pod(namespace='clarklab').items
          )
      )
  )

  for pod in live_pod_names:
      v1.delete_namespaced_pod(namespace="clarklab", name=pod)


class KubernetesJob():
  usedSoftware: Union[str, SoftwareCompactView]
  usedDataset: List[Union[str, DatasetCompactView]]
  downloadJob: dict = {}
  computeJob: dict = {}
  registrationJob: dict = {}

  def __init__(self, computation):
    self.computation = computation
    self.stage = "download"
    self.status = "running"
    



  def run(self):
    """
      
    """

    # read in service account file

    # using kubernetes API from environment variable
    
    return None




  def stop(self):
    return None
