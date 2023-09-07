import unittest
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder


root_url = "https://fairscape.pods.uvarc.io"
data_release_crate_folder = "/com.docker.devenvironments.code/tests/data/crates/data_release/zipped"
us2os_folder = "/com.docker.devenvironments.code/tests/data/crates/U2OS"

def upload_zipped_crate(crate_path: str) -> requests.Response:
    """ Function to upload rocrate specified by path
    """

    mp_encoder = MultipartEncoder(
        fields={        
            'file': ('test-rocrate', open(crate_path, 'rb'), 'application/zip')
        }
    )

    # upload a rocrate to minio object store
    rocrate_transfer = requests.post(
        url=f"{root_url}/rocrate/upload",
        data=mp_encoder,                              
        # The MultipartEncoder provides the content-type header with the boundary:
        headers={'Content-Type': mp_encoder.content_type}
    )

    return rocrate_transfer


def assert_upload_success(file_path):
        api_response = upload_zipped_crate(file_path)
        response_json = api_response.json()
        assert response_json.get("error") is None
        assert api_response.status_code == 201


class TestUploadDataRelease(unittest.TestCase):

    def test_0_upload_untreated_if(self):
        untreated_if_path = data_release_crate_folder + "/cm4ai_chromatin_mda-mb-468_untreated_ifimage_0.1_alpha.zip"
        assert_upload_success(untreated_if_path)

    def test_1_upload_untreated_apms(self):
        zip_path = data_release_crate_folder + "/cm4ai_chromatin_mda-mb-468_untreated_apms_0.1_alpha.zip"
        assert_upload_success(zip_path)

    def test_2_upload_paclitaxel_if(self):
        zip_path = data_release_crate_folder + "/cm4ai_chromatin_mda-mb-468_paclitaxel_ifimage_0.1_alpha.zip"
        assert_upload_success(zip_path)

    def test_3_upload_vorinostat_if(self):
        zip_path = data_release_crate_folder + "/cm4ai_chromatin_mda-mb-468_vorinostat_ifimage_0.1_alpha.zip"
        assert_upload_success(zip_path)


class TestUploadU2OS(unittest.TestCase):

    def test_0_upload_ppi_download(self):
        zip_path = us2os_folder + "/1.ppi_download.zip"  
        assert_upload_success(zip_path)

    def test_1_upload_ppi_embedding(self):
        zip_path = us2os_folder + "/2.ppi_embedding.zip"   
        assert_upload_success(zip_path)

    def test_2_upload_coembedding(self):
        zip_path = us2os_folder + "/3.coembedding.zip"
        assert_upload_success(zip_path)

    def test_3_upload_hierarchy(self):
        zip_path = us2os_folder + "/4.hierarchy.zip"
        assert_upload_success(zip_path)