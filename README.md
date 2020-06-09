# ColabHelper
A wrapper useful to work with Colab, but some of the methods like pushover notification should work on any jupyter notebook.
The module contains some utilities for an improved experience with Colab, like persistency of tensoboard log or dataframes by using your free google drive, encapsulated in the ColabHelper class.

# Features
As of now the module is able to help in the following scenarios:
- Easily backup/restore the tensorboard log directory to your google drive
- Get information about the hosting machine (CPU, RAM, HDD, GPU)
- Play a sound notification to alert you when a job is done
- Get a custom notification with your [Pushover](https://pushover.net/) API (in future could be nice to support other services) useful to have some sort of notification also when you are away from PC.

# Usage
## Import module on colab notebook
```python
import os
if not os.path.isdir('./ColabHelper'):
  !git clone https://github.com/Emmunaf/ColabHelper.git
  
from ColabHelper.colabhelper import ColabHelper
```

## Tensorboard easy backup/restore to/from Google Drive
To make a backup you can use the following snippet:
```python
ch = ColabHelper(backup_folder="/content/drive/My Drive/MyProjectFolder/")
# or just use ch = ColabHelper() and the default folder named ColabHelper will be used.

ch.tensorboard_backup()

# or, if you want to specify a different logdir directory:
# ch.tensorboard_backup(tensorboard_logdir="./runs/")
# tensorboard_logdir is the log folder used by the colab istance of tensorboard. 
# Keep in mind that this correspond to --logdir option specified when starting tensorboard (usually logs or runs).
```
And to restore:
```python
ch = ColabHelper(backup_folder="/content/drive/My Drive/MyProjectFolder/")
# or just use ch = ColabHelper() and the default folder named ColabHelper will be used.

ch.tensorboard_restore()
# or you can use the following if you have choosen a different name
# ch.tensorboard_restore(tensorboard_logdir="./runs/")
```
The logs are saved in a subfolder of *backup_folder* called by default *runs*.
You can change this bahaviour and set a custom subfolder name by calling set_tensorboard_backup_folder_name(newname).
BTW this is not suggested, when you have many files a better idea is to change *backup_folder* for each new project and then mantaining the same internal structure.
## Generate sound notification
```python
ch = ColabHelper()

# Play a beep 3 times (default is 2)
ch.beep(times=3)
```

## Send a push notification by using third party services
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

## Save (both locally and remotely) a copy of a dataframe and restore it
```python
import pandas

ch = ColabHelper()

# Get some working dataframes
a = pandas.DataFrame({"a":[1,2,3,4]})
ch.backup_dataframe(a, "a_dump")

```
Then, to restore your saved dataframe you can just use:
```python
import pandas

ch = ColabHelper()

a_restored = ch.restore_dataframe("a_dump")
```
The dataframes are saved in a subfolder of *<backup_folder>* called *dataframes*.
