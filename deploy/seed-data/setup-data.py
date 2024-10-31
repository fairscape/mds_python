from dotenv import dotenv_values
import os
import pathlib
import requests

class FairscapeRequest():

	def __init__(self, username: str, password: str, rootURL: str):
		self.username = username
		self.password = password
		self.rootURL = rootURL
		self.tokenString = None

	def getTokenString(self):
		"""
		Login a User to Fairscape
		"""
		loginResponse = requests.post(
			self.rootURL + 'login', 
			data={
				"username": self.username, 
				"password": self.password
				})
		loginResponseBody = loginResponse.json()
		self.tokenString = loginResponseBody['access_token']

	def uploadCrate(self, cratePath: pathlib.Path):
		fileName = cratePath.name
		crateUpload = {
			'crate': (fileName, open(str(cratePath), 'rb'), 'application/zip')
			}
    
		uploadResponse = requests.post(
        self.rootURL + 'rocrate/upload-async',
        files=crateUpload,
        headers={"Authorization": f"Bearer {self.tokenString}"}
    )
		return uploadResponse

	def checkUploadStatus(self, requestID: str) -> dict:
		uploadStatusResponse = requests.get(
        self.rootURL + 'rocrate/upload/status/' + requestID,
        headers={
					"Authorization": f"Bearer {self.tokenString}"
					}
    )
		return uploadStatusResponse.json()

def uploadCrates():


	configValues = {
		**dotenv_values(dotenv_path="./setup.env"),
		**os.environ
	} 
	fairscapeRootURL = configValues['FAIRSCAPE_API_URL']
	userEmail = configValues['USER_EMAIL']
	userPassword = configValues['USER_PASSWORD']

	fairscapeAPI = FairscapeRequest(
		username=userEmail,
		password=userPassword,
		rootURL=fairscapeRootURL
	)

	# get a fairscape token
	fairscapeAPI.getTokenString()

	# list all crates and upload
	uploadedCrates = pathlib.Path('/data')
	allUploadedCrates = list(pathlib.Path(uploadedCrates).glob('*.zip'))
	transactionIds = []

	for crate in allUploadedCrates:
		uploadResponse = fairscapeAPI.uploadCrate(crate)

		# check for success
		assert uploadResponse.status_code == 201

		uploadJSON = uploadResponse.json()
		transactionIds.append(uploadJSON.get("transactionFolder"))

	# TODO check all request guids are finished
	while len(transactionIds) != 0:
		for idx, uploadStatus in enumerate(map(fairscapeAPI.checkUploadStatus, transactionIds)):

			if uploadStatus.get("completed"):	
				completedTransactionID = transactionIds.pop(idx)
				
				if uploadStatus.get("success"):
					# TODO log success
					print(f"Upload Success: {completedTransactionID}")
					pass

				else:
					# TODO log failure
					print(f"Upload Failure: {completedTransactionID}")
					pass

			continue

	# TODO: check that downloads are functional for ROcrates

	# TODO: check that access controls apply

	# TODO: check that api endpoints work

	pass

if __name__ == "__main__":
	uploadCrates()