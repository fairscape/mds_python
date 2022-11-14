from mds.models import Dataset, Software, Computation
from mds.models.compact.software import SoftwareCompactView
from mds.models.compact.dataset import DatasetCompactView
from mds.database import mongo, minio
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION

from mds.compute.main import app

from typing import List, Optional, Union
from pydantic import Extra
from datetime import datetime
from time import sleep
from kubernetes import client, config, watch
from celery.utils.log import get_task_logger
from celery import Task


class JobTask(Task):
    _v1 = None
    _batch = None
    _mongo_client = None


    @property
    def v1(self): 
        if self._v1 is None:
            config.load_incluster_config()
            self._v1 = client.CoreV1Api()
        return self._v1


    @property
    def batch(self):
        if self._batch is None:
            config.load_incluster_config()
            self._batch = client.BatchV1Api()
        return self._batch


    @property
    def mongo_client(self):
        if self._mongo_client is None:
            self._mongo_client = mongo.GetConfig()
        return self._mongo_client


task_logger = get_task_logger(__name__)

FAIRSCAPE_NAMESPACE = "clarklab"
FAIRSCAPE_IMAGE = "ghcr.io/fairscape/mds_python:main"

class ComputationNotFound(Exception):
    def __init__(self, computation_id, message="Computation Metadata Not Found"):
        self.computation_id = computation_id
        self.message = message

        # ensure exception can be pickled by celery
        super().__init__(self, self.computation_id, self.message)



def create_job(computation_id: str):
    res = download_job(computation_id) | run_job(computation_id) | register_job(computation_id)()

    # TODO check that job was started against celery
    return res


@app.task(name="download_job", base=JobTask)
def download_job(computation_id: str):

    # get job metadata
    mongo_db = download_job._mongo_client[MONGO_DATABASE]
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

    create_pvc = download_job._v1.create_namespaced_persistent_volume_claim(
        namespace=FAIRSCAPE_NAMESPACE, 
        body=pvc_manifest
    )

    task_logger.info(f"Computation: {computation_id}\tCreating Persistant Volume Claim {pvc_name}")

    download_job_manifest = create_download_job(
        job_name = job_name, 
        computation_id = computation_id,
        pvc_name = pvc_name
    )

    download_job_metadata = download_job._batch.create_namespaced_job(
        namespace=FAIRSCAPE_NAMESPACE, 
        body= download_job_manifest
    )

    task_logger.info(f"Computation: {computation_id}\tCreating Download Job {job_name}")

    # wait for job to finish
    in_progress=True
    while in_progress==True:

        try:
            job_read = download_job._batch.read_namespaced_job(
                namespace=FAIRSCAPE_NAMESPACE, 
                name=job_name
                )
            job_status = job_read.status

            # if job succeeded 
            if job_status.succeeded == 0:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Succeeded")

                # TODO update metadata with download job logs
                
                # clean up the job
                cleanup_job(
                    job_name, 
                    batch_api= download_job._batch, 
                    v1_api=download_job._v1
                    )
                return True


            # if job failed
            if job_status.failed != None:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Failed")

                # TODO get the logs of any pod

                # TODO update the metadata

                # clean up the job
                cleanup_job(
                    job_name, 
                    batch_api= download_job._batch, 
                    v1_api=download_job._v1
                    )
                return False



            # if job running
            if job_status.active != None:
                continue

        except Exception as e:
            task_logger.info(f"Batch Job Not Found {str(e)}")

        sleep(10)
    

@app.task(name="run_job", base=JobTask)
def run_job(success: bool, computation_id: str):

    # if the previous step fails stop execution
    if success == False:
        return False

    # get job metadata
    mongo_db = run_job._mongo_client[MONGO_DATABASE]
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

    compute_job_metadata = run_job._batch.create_namespaced_job(
        namespace=FAIRSCAPE_NAMESPACE, 
        body=compute_job_manifest
    )
 

    # wait for job to finish
    in_progress=True
    while in_progress==True:

        try:
            job_read = run_job._batch.read_namespaced_job(
                namespace=FAIRSCAPE_NAMESPACE, 
                name=compute_job_name
                )
            job_status = job_read.status

            # if job succeeded 
            if job_status.succeeded != 0:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Succeeded")

                # TODO update metadata with download job logs
                
                # clean up the job
                cleanup_job(
                    compute_job_name, 
                    batch_api=run_job._batch, 
                    v1_api=run_job._v1
                    )
                return True


            # if job failed
            if job_status.failed != None:
                in_progress = False
                task_logger.info(f"Computation: {computation_id}\tDownload Job Failed")

                # TODO get the logs of any pod

                # TODO update the metadata

                # clean up the job
                cleanup_job(
                    compute_job_name, 
                    batch_api=run_job._batch, 
                    v1_api=run_job._v1
                    )
                return False



            # if job running
            if job_status.active != None:
                continue

        except Exception as e:
            task_logger.info(f"Batch Job Not Found {str(e)}")
        sleep(10) 


@app.task(name="register_job", base=JobTask)
def register_job(success: bool, computation_id: str):

    # if the previous step fails stop execution
    if success == False:
        return False

    mongo_db = register_job._mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    # get job metadata
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
            if job_status.succeeded == 0:
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

        sleep(9)


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
        limits={"cpu": "300m", "memory": "1500Mi"}
    )

    job_container = client.V1Container(
        name='job-download', 
        image=FAIRSCAPE_IMAGE,
        image_pull_policy= "Always",
        command=["python2", "/mnt/script/download.py"],
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
                "value": "9.250.124.184"
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
                "value": "27016"
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


def create_compute_job(computation_identifier: str, job_name: str, script_name: str, pvc_name: str, image, command):

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

    container_resources = client.V1ResourceRequirements(
        requests={"cpu": "100m", "memory": "5000Mi"}, 
        limits={"cpu": "500m", "memory": "7500Mi"}
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
                "value": computation_identifier
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

    prefix, org, proj, job_key = computation_identifier.split("/")
    
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

    job_configmap_source = client.V1Volume(
        name="script", 
        config_map=client.V1ConfigMapVolumeSource(name="registration-script")
    )

    # launch a pod mounted with the test-job-pvc
    container_resources = client.V1ResourceRequirements(
        requests={"cpu": "100m", "memory": "5000Mi"}, 
        limits={"cpu": "500m", "memory": "7500Mi"}
    )

    job_container = client.V1Container(
        name='job-download', 
        image=FAIRSCAPE_IMAGE,
        image_pull_policy= "Always",
        command=["python3", "/mnt/script/register.py"],
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
                "value": "9.250.124.184"
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
                "value": "27016"
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

    prefix, org, proj, job_key = computation_id.split("/")

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


def cleanup_job(job_name, batch_api, v1_api):
  """
  """
  try:
      batch_api.delete_namespaced_job(
          namespace="clarklab", 
          name=job_name
      )
  except Exception as e:
      print(e)
      
  live_pod_names = list(
      filter(
          lambda x: True if job_name in x else False,
          map(
              lambda x: x.metadata.name, v1_api.list_namespaced_pod(namespace='clarklab').items
          )
      )
  )

  for pod in live_pod_names:
      v1_api.delete_namespaced_pod(namespace="clarklab", name=pod)

