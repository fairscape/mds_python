import minio
from minio.error import S3Error

class MinioConfig():
	def __init__(self, hostname: str, access_key: str, secret_key: str) -> None:
		self.hostname   = hostname
		self.access_key = access_key
		self.secret_key = secret_key 

	def connect(self) -> minio.Client:
		return minio.Minio(
			self.hostname, 
			access_key= self.access_key, 
			secret_key= self.secret_key
			)

def GetMinioConfig():
	return MinioConfig(
		"localhost:9000",
		"test",
		"test"
	).connect()
