FROM nvidia/cuda:9.0-base

MAINTAINER Ben Ryan (ben96ryan@gmail.com)

COPY ./server ./server

COPY ./keyboard ./etc/default/keyboard

RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y libsm6 libxrender1 libfontconfig1 libxext6 libglib2.0-0
RUN apt-get install -y cuda9.0 cuda-cublas-9-0 cuda-cufft-9-0 cuda-curand-9-0 \
			    cuda-cusolver-9-0 cuda-cusparse-9-0 libcudnn7=7.2.1.38-1+cuda9.0 \
			    libnccl2=2.2.13-1+cuda9.0 cuda-command-line-tools-9-0

RUN python3 -m pip install opencv-python
RUN python3 -m pip install numpy
RUN python3 -m pip install tensorflow-gpu

CMD ["nvidia-smi"]

