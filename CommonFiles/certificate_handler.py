import zmq
import shutil
import os
import uuid

import datetime
import glob
import io
from zmq.utils.strtypes import bytes, unicode, b, u
import logging


class CertificateHandler():
	def __init__(self, certID, mode):
		self.certID = certID
		self.mode = mode

		self.basePath = '../Certificates'

		self.publicFolderPath = (
			self.basePath + '/' + mode +
			'-public-' + str(self.certID) + '/')

		self.privateFolderPath = (
			self.basePath + '/' + mode +
			'-private-' + str(self.certID) + '/')

		self.publicFilePath = (
			self.publicFolderPath + mode + '-' +
			str(self.certID) + ".key")

		self.privateFilePath = (
			self.privateFolderPath + mode + '-' +
			str(self.certID) + ".key_secret")

		if mode == 'client':
			self.enrolledKeysFolderPath = (
				self.basePath + '/server-keys-' +
				str(self.certID) + '/')
		elif mode == 'server':
			self.enrolledKeysFolderPath = (
				self.basePath + '/client-keys-' +
				str(self.certID) + '/')

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
			"server-" + self.certID)

		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	def getCertificatesPaths(self):
		if (not os.path.exists(self.publicFilePath) or
			not os.path.exists(self.privateFilePath)):
			self._generateCertificates()

		return self.publicFolderPath, self.privateFolderPath

	def getCertificateFilePaths(self):
		return self.publicFilePath, self.privateFilePath

	def getKeyPair(self):
		_, privatePath = self.getCertificateFilePaths()

		publicKey, privateKey = zmq.auth.load_certificate(privatePath)

		return publicKey, privateKey

	def getEnrolledKeysPath(self):
		if not os.path.exists(self.enrolledKeysFolderPath):
			os.mkdir(self.enrolledKeysFolderPath)

		return self.enrolledKeysFolderPath

	def getEnrolledKeys(self):
		path = self.getEnrolledKeysPath()
		certificates = zmq.auth.load_certificates(path)

		# client will only have single server key
		if self.mode == 'client':
			for key, val in certificates.items():
				if val:
					return key

		return certificates

	def savePublicKey(self, key):
		path = self.getEnrolledKeysPath() + str(uuid.uuid4().hex) + '.key'
		print(path)
		now = datetime.datetime.now()

		try:
			zmq.auth.certs._write_key_file(path, zmq.auth.certs._cert_public_banner.format(now), key)
			logging.debug('Enrolled key saved')
		except:
			logging.error('Exception while writing file', exc_info=True)

	def prep(self):
		self._generateCertificates()

		if os.path.exists(self.enrolledKeysFolderPath):
			shutil.rmtree(self.enrolledKeysFolderPath)

		os.mkdir(self.enrolledKeysFolderPath)

	def cleanup(self):
		shutil.rmtree(self.publicFolderPath)
		shutil.rmtree(self.privateFolderPath)
		shutil.rmtree(self.enrolledKeysFolderPath)
