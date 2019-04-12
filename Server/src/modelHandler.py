# Ben Ryan C15507277

import logging

import tensorflow as tf


class ModelHandler():
	__instance = None

	def __init__(self):
		if ModelHandler.__instance is None:
			self.__model = tf.keras.models.load_model("../model/model.h5")
			self.__model._make_predict_function()
			self.__session = tf.keras.backend.get_session()
			self.__graph = tf.get_default_graph()
			self.__graph.finalize()
		else:
			logging.warning('Model Handler being directly instanstiated')

	@staticmethod
	def getInstance():
		if ModelHandler.__instance is None:
			ModelHandler.__instance = ModelHandler()

		return ModelHandler.__instance

	def getModel(self):
		return self.__model

	def getGraph(self):
		return self.__graph

	def getSession(self):
		return self.__session
