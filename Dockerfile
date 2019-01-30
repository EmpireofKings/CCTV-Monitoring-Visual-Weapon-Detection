#ALLOWS EASY USE OF GPU
FROM nvidia/cuda:9.0-base

MAINTAINER Ben Ryan (ben96ryan@gmail.com)

#REQUIRED FILES FOR SERVER
COPY ./Server ./Server
COPY ./Models ./Models

#REQUIRED PACKAGES
RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y libsm6 libxrender1 libfontconfig1 libxext6 libglib2.0-0
RUN apt-get install -y cuda9.0 cuda-cublas-9-0 cuda-cufft-9-0 cuda-curand-9-0 \
			    cuda-cusolver-9-0 cuda-cusparse-9-0 libcudnn7=7.2.1.38-1+cuda9.0 \
			    libnccl2=2.2.13-1+cuda9.0 cuda-command-line-tools-9-0

#REQUIRED MODULES
RUN python3 -m pip install --upgrade pip==18.1.0
RUN python3 -m pip install opencv-python==3.4.3.18
RUN python3 -m pip install numpy==1.16.0
RUN python3 -m pip install tensorflow-gpu==1.11.0
RUN python3 -m pip install zmq

#PORTS USED TO COMM WITH CLIENT
EXPOSE 5000

#RUN SERVER APP IN UNBUFFERED MODE
CMD ["python3", "-u", "./Server/server-proto.py"]

