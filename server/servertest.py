import cv2
import numpy
import tensorflow as tf
import queue
from threading import Thread

config = tf.ConfigProto()
config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU
sess = tf.Session(config=config)
tf.keras.backend.set_session(sess)

print("A OK")
