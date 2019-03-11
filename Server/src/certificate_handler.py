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
	def __init__(self, id):
		self.id = id
		self.basePath = '../Certificates'

		self.publicFolderPath = (
			self.basePath +
			'/Public-' +
			str(self.id) +
			'/')

		self.privateFolderPath = (
			self.basePath +
			'/Private-' +
			str(self.id) +
			'/')

		self.publicFilePath = (
			self.publicFolderPath +
			"server-" +
			str(self.id) +
			".key")

		self.privateFilePath = (
			self.privateFolderPath +
			"server-" +
			str(self.id) +
			".key_secret")

		self.clientKeysFolderPath = (
			self.basePath +
			'/Clients-' +
			str(self.id) +
			'/')

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

		shutil.move(public, self.publicFilePath)
		shutil.move(private, self.privateFilePath)

	def getCertificatesPaths(self):
		if (not os.path.exists(self.publicFilePath) or
			not os.path.exists(self.privateFilePath)):
			self._generateCertificates()

		return self.publicFolderPath, self.privateFolderPath

	def getCertificateFilePaths(self):
		return self.publicFilePath, self.privateFilePath

	def getKeys(self):
		_, privatePath = self.getCertificateFilePaths()

		publicKey, privateKey = zmq.auth.load_certificate(privatePath)

		return publicKey, privateKey

	def getClientKeysPath(self):
		if not os.path.exists(self.clientKeysFolderPath):
			os.mkdir(self.clientKeysFolderPath)

		return self.clientKeysFolderPath

	def saveClientKey(self, key):
		try:
			print("tryin")
			path = "{0}.key".format(str(self.getClientKeysPath() + uuid.uuid4().hex))
			print("after")
		except:
			logging.error('Exception while formatting', exc_info=True)

		print(path)
		print(key)
		now = datetime.datetime.now()
		print(now)

		try:
			print("trying to save")
			zmq.auth.certs._write_key_file(path, zmq.auth.certs._cert_public_banner.format(now), key)
			logging.debug('Client key saved')
		except:
			logging.error('Exception while writing file', exc_info=True)

		# fileContents = 'metadata\ncurve\n    public-key = \"' + key + '\"'

		# print("FILE CONTENTS\n", fileContents)
		# with open(path, 'w') as fp:
		# 	fp.write(fileContents)

	def cleanup(self):
		shutil.rmtree(self.publicFolderPath)
		shutil.rmtree(self.privateFolderPath)
