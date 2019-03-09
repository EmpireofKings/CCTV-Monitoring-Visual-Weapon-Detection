import zmq
import shutil
import os

class CertificateHandler():
	def __init__(self, id):
		self.id = id
		self.basePath = '../Certificates'

		self.publicFolderPath = (
			self.basePath +
			'/Public-' +
			str(id) +
			'/')

		self.privateFolderPath = (
			self.basePath +
			'/Private-' +
			str(id) +
			'/')

		self.publicFilePath = (
			self.publicFolderPath +
			"server-" +
			self.id +
			".key")

		self.privateFilePath = (
			self.privateFolderPath +
			"server-" +
			self.id +
			".key_secret")

	def _generateCertificates(self):
		if os.path.exists(self.publicFolderPath):
			shutil.rmtree(self.publicFolderPath)

		if os.path.exists(self.privateFolderPath):
			shutil.rmtree(self.privateFolderPath)

		if not os.path.exists(self.basePath):
			os.mkdir(self.basePath)

		os.mkdir(self.publicFolderPath)
		os.mkdir(self.privateFolderPath)

		public, private = zmq.auth.create_certificates(
			self.basePath,
			"server-" + self.id)
		print("PATHS:", public, private)
		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	def getCertificatesPaths(self):
		if (not os.path.exists(self.publicFilePath) or
			not os.path.exists(self.privateFilePath)):
			print("Generating new keys, clients will need access to public key.")
			self._generateCertificates()

		return self.publicFolderPath, self.privateFolderPath

	def cleanup(self):
		shutil.rmtree(self.publicFolderPath)
		shutil.rmtree(self.privateFolderPath)
