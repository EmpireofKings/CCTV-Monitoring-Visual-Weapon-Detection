#ALLOWS EASY USE OF GPU
FROM nvidia/cuda:9.0-base

MAINTAINER Ben Ryan (ben96ryan@gmail.com)

#REQUIRED FILES FOR SERVER
COPY ./Server ./Server
COPY ./CommonFiles ./CommonFiles

#REQUIRED PACKAGES
RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y libsm6 libxrender1 libfontconfig1 libxext6 libglib2.0-0
RUN apt-get install -y cuda9.0 cuda-cublas-9-0 cuda-cufft-9-0 cuda-curand-9-0 \
			    cuda-cusolver-9-0 cuda-cusparse-9-0 libcudnn7=7.2.1.38-1+cuda9.0 \
			    libnccl2=2.2.13-1+cuda9.0 cuda-command-line-tools-9-0
RUN apt-get install -y python3-mysqldb

#REQUIRED MODULES
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install opencv-python==4.0.0.21
RUN python3 -m pip install numpy==1.16.0
RUN python3 -m pip install tensorflow-gpu==1.12.0
RUN python3 -m pip install pyzmq==18.0.1
RUN python3 -m pip install argon2-cffi
RUN python3 -m pip install mysql-connector-python


#PORTS USED TO COMM WITH CLIENT
EXPOSE 5000-5002
EXPOSE 49151-65535

#RUN SERVER APP IN UNBUFFERED MODE
CMD ["python3", "-u", "./server.py"]

