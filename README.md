# Automated Surveillance Using a Machine Learning Assisted Computer Vision Application to Detect Handheld Weapons in Images and Video

This project aimed to tackle some of the problems of automated surveillance with weapon detection as the central automated feature. The core goal was to make these kinds of system more accessible to the masses, making it purerly visual, not requiring special hardware, and using the cloud to offload heavy processing so powerful, dedicated hardware is not required onsite. Some demonstration videos can be seen in [this YouTube playlist](https://www.youtube.com/playlist?list=PLK5DhDZQB1eEay-w90M8QicF_nWRFuBye "Project Demonstration"). Some screenshots of the final system can be seen below.

### Live Feed Processing Screen
![Live Feed Processing](https://imgur.com/4xWsxDp.jpg "Live Feed Processing")

### Deferred Feed Processing Screen
![Deferred Feed Processing](https://imgur.com/MyN2LTX.jpg "Deferred Feed Processing")

### Configuration Screen
![Configuration Screen](https://imgur.com/4vnF5Ec.jpg "Configuration Screen")

### Sample Detection 1
![Sample Detection 1](https://imgur.com/nGr7kal.jpg "Sample Detection 1")

### Sample Detection 2
![Sample Detection 2](https://imgur.com/8qnA2DY.jpg "Sample Detection 2")

### Sample Detection 3
![Sample Detection 3](https://imgur.com/mTuIPff.jpg "Sample Detection 3")


## Repository Structure

1. Client - Contains code/data for client side application (Options  are debug, info, warning, error or critical for logging levels)
```sh
    python3 client.py <option> 
```
	
2. CommonFiles - Contains code that is used in multiple components, not to be executed directly.
3. Data-Acquistion - Contains the code/data used in acquring the dataset
```sh
    python3 scrapelinks.py
    python3 downloadimages.py
    python3 sortimages.py
```
4. Data-Prep-and-Training - Contains the code used to prepare data and train the model (Options are start or resume)
```sh
    python3 prepareData.py <option>
    python3 trainModel.py
```

5. Server - Contains the code/data used for the server side application (Options  are debug, info, warning, error or critical for logging levels)
```sh
    python3 server.py <option>
```

6. Testing - Contains some of the testing scripts used. (Options are  motion, CNN, alertSystem blob, canny, harris, ridge, sobel for each manual testing case)
```sh
    python3 tester.py <option>
    python3 automated_test.py
```

7. Dockerfile - Set up for running the server application in Docker
```sh
    sudo docker run --workdir="/Server/src/" --runtime=nvidia --env-file="../envFile" --network=host server-image
```
      

## Setting up the Development Environment

The following instructions detail how the development environment was set up.
1. Google Cloud Instance Specifications
    * Ubuntu 18.04 LTS Base Image
    * CUDA API Enabled NVIDIA GPU (K80, P4 and V100 tested)
    * 8+ vCPUs, any platform.
    * 16GB+ RAM
    * 50GB HDD boot disk.
    * 1TB SSD attached while training model.
    * Preemptible instance used throughout development to save on cost.


2. Software Set Up
    * Perform general upgrades
    ```sh
        sudo apt-get update
        sudo apt-get upgrade
    ```

    * Install Python modules
    ```sh
        sudo apt-get install python3-pip
        python3 -m pip install --upgrade pip
        python3 -m pip install opencv-python==4.0.0.21
        python3 -m pip install numpy==1.16.0
        python3 -m pip install tensorflow-gpu==1.12.0
        python3 -m pip install pyzmq==18.0.1
        python3 -m pip install argon2-cffi
        python3 -m pip install mysql-connector-python
    ```

	* Compression Software (For dataset handling)
    ```sh
        sudo apt-get install p7zip-ful
        7z x -o<target path> archive.7z
    ```	
	* Database Software
    ```sh
        sudo apt-get install mysql-server
        mysql -h <IP> -u root -p (details saved in environment variables)
    ```
	* Monitoring Software
    ```sh
        sudo apt-get install iotop
        htop should already be installed
        nvidia-smi should already be installed
    ```
	* Install latest NVIDIA drivers
    ```sh
        sudo apt-get install ubuntu-drivers-common
        ubuntu-drivers devices
        sudo apt-get install nvidia-driver-<latest>
        May require reboot
        nvidia-smi to confirm success
    ```
	* Install CUDA API
    ```sh
        sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
        wget http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_9.1.85-1_amd64.deb
        sudo apt install ./cuda-repo-ubuntu1604_9.1.85-1_amd64.deb
        wget http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1604/x86_64/nvidia-machine-learning-repo-ubuntu1604_1.0.0-1_amd64.deb
        sudo apt install ./nvidia-machine-learning-repo-ubuntu1604_1.0.0-1_amd64.deb
        sudo apt update
        sudo apt install cuda9.0 cuda-cublas-9-0 cuda-cufft-9-0 cuda-curand-9-0 \
        cuda-cusolver-9-0 cuda-cusparse-9-0 libcudnn7=7.2.1.38-1+cuda9.0 \
        libnccl2=2.2.13-1+cuda9.0 cuda-command-line-tools-9-0
        sudo apt update
        sudo apt install libnvinfer4=4.1.2-1+cuda9.0
    ```
	* Install Docker CE (Prerequisite for NVIDIA Docker)
    ```sh
        sudo apt-get install \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg2 \
            software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo apt-key fingerprint 0EBFCD88 (output: 9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88)
        sudo add-apt-repository \
            "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
            $(lsb_release -cs) \
            stable"
        sudo apt-get update
        sudo apt-get install docker-ce
    ```	
	* Install NVIDIA Docker
    ```sh
        curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
            sudo apt-key add -
        distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
        curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
            sudo tee /etc/apt/sources.list.d/nvidia-docker.list
        sudo apt-get update
        sudo apt-get install -y nvidia-docker2
        sudo pkill -SIGHUP dockerd
        test using: docker run --runtime=nvidia --rm nvidia/cuda:9.0-base nvidia-smi
    ```
	* Useful Docker Commands
    ```sh
        sudo docker build -t server-image.
        sudo docker run --workdir="/Server/src/" --runtime=nvidia --env-file="../envFile" --network=host server-image
        sudo docker save server-image > server-image.tar
        sudo docker load < server-image.tar
    ```	
	* Install GCSFUSE for GCP 
    ```sh
        export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`
        echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list
        curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
        sudo apt-get update
        sudo apt-get install gcsfuse
    ```
	* Monting/Unmounting Buckets
    ```sh
        sudo gcsfuse <bucket-name> <mount-dir>
        sudo umount <mount-dir>
    ```
		
	* Setting up temporary disk (1TB SSD for training)
    ```sh
        run lsblk to get device id
        sudo mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/<device-id>
        sudo mount -o discard,defaults /dev/<device-id> /mnt/<mount-dir>
        sudo chmod a+w /mnt/disks/<mount-dir>
        programs expect /Dataset and /Prepared-Data to exist on drive
    ```
