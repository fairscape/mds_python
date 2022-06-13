# select docker image
IMAGE_NAME = "python"
IMAGE_TAG = "alpine"
IMAGE = f"{IMAGE_NAME}:{IMAGE_TAG}"

# Volume mapping in the container
SOURCE_VOL = '/home/sadnan/compute-test'
DATA_VOL = SOURCE_VOL + '/data'
OUTPUT_VOL = SOURCE_VOL + '/outputs'

MOUNT_VOL = '/cont/vol/script'
MOUNT_DATA_VOL = MOUNT_VOL + '/data'
MOUNT_OUTPUT_VOL = MOUNT_VOL + '/outputs'

# script to run
SCRIPT_NAME = 'sum_script.py'

# command to run python script 'python3 /path/to/script/in/mounted/container/vol'
COMMAND = ['python', f'{MOUNT_VOL}/{SCRIPT_NAME}']

CONTAINER_NAME = "compute-service-custom-container"