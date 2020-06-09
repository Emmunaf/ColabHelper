# ColabHelper
A wrapper useful to work with colab or Jupiter notebook in general.

# Features
As of now the class is able to help in the following scenario:
- Easily backup/restore the tensorboard log dir to your google drive
- Get information about the hosting machine (CPU, RAM, HDD, GPU)
- Play a sound notification to alert you when a job is done
- Get a custom notification on pushbullet (in future maybe other services) useful to have some sort of notification also when away from PC

# Usage
## Import module on colab notebook
```python
import os
if not os.path.isdir('./ColabHelper'):
  !git clone https://github.com/Emmunaf/ColabHelper.git
  
from ColabHelper.colabhelper import ColabHelper
```

## Tensorboard easy backup/restore to/from Google Drive
```python
ch = ColabHelper(tensorboard_backup_p="/content/drive/My Drive/<YOUR_CUSTOM_FOLDER_IN_DRIVE>")

ch.tensorboard_backup(tensorboard_logdir="./runs/")
ch.tensorboard_restore(tensorboard_logdir="./runs/")
ch.notify(extra="Backup Restore")
```
## Generate sound notification
```python
ch = ColabHelper()

# Play a beep 3 times (default is 2)
ch.beep(times=3)
```

## Generate a push notification with third party services
```python
ch = ColabHelper()

# Set the parameters by passing service we want to use(pushover in this example) and the parameters needed for authentication  to the set_notification_params() method.
# For pushover we need two values: user_token and app_token.
pushover_params = {"user_token":"<YOUR_USER_TOKEN>", "app_token":"<YOUR_APP_TOKEN>"}
ch.set_notification_params(service="pushover", pushover_params)
# ... run some time intensive job
ch.notify(notification_type="DONE", extra="Experiment XYZ!") # leads to ->  [<DONE>]\n<Extra>
```

## Print information about the runtime
```python
ch = ColabHelper()

# Print system info
ch.get_cpu_info()
ch.get_gpu_info()
ch.get_hdd_usage()
ch.get_ram_usage()
```
