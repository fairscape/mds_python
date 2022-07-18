import minio
from mds.database.config import MINIO_URI, MINIO_USER, MINIO_PASS
from minio.error import S3Error

class MinioConfig():
	def __init__(self, hostname: str, access_key: str, secret_key: str, secure: bool = False) -> None:
		self.hostname   = hostname
		self.access_key = access_key
		self.secret_key = secret_key 
		self.secure = secure

	def connect(self) -> minio.Minio:
		return minio.Minio(
			self.hostname, 
			access_key= self.access_key, 
			secret_key= self.secret_key,
			secure= self.secure
			)

def GetMinioConfig():
	return MinioConfig(
		f"{MINIO_URI}:9000",
		MINIO_USER,
		MINIO_PASS,
	).connect()
