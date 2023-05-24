from mds.compute.tasks import download_job, run_job, register_job, ComputationNotFound
import pytest

class TestErrors():

    def test_cleanup_job():
        pass

    def test_compute_job_not_found():
        with pytest.raises(ComputationNotFound):
            download_job(
                computation_id = "ark:99999/not-a-real-identifier"
            )

