from google.colab import drive
from google.colab import output

import os
import time
import requests
import http.client, urllib
import subprocess
from pathlib import Path
import pandas as pd

class ColabHelper:
  """ Class useful to improved Colab capabilities"""

  def __init__(self, model_state_p=None, backup_folder="/content/drive/My Drive/ColabHelper/"):
    
    tensorboard_logs_folder = "runs"
    dataframes_folder = "dataframes"
    self.backup_folder = backup_folder
    self.tensorboard_backup_p = os.path.join(backup_folder, tensorboard_logs_folder)
    self.dataframes_backup_p = os.path.join(backup_folder, dataframes_folder)

    # Load gdrive
    drive.mount('/content/drive/')
    if not os.path.isdir(self.backup_folder):
      os.mkdir(self.backup_folder)
      print("[INFO] Your backup folder ", self.backup_folder," didn't existed and *it was created* ")
    else:
      print("[WARN] Your backup folder", self.backup_folder, "already exists. Some files could be overwritten")
      if os.path.isdir(self.tensorboard_backup_p):
        print("[INFO] A tensorboard backup folder was detected (", self.tensorboard_backup_p, ")\nYou can use the tensorboard_restore() method to load it.")
      if os.path.isdir(self.dataframes_backup_p):
        print("[INFO] A Dataframe backup folder was detected (", self.dataframes_backup_p, ")\nYou can use loaded_df = restore_dataframe(name) method to load a dataframe of a given name.")
  
  def set_notification_params(self, service="pushover", params={}):
    if service == "pushover":
      app_token, user_token = params.get("app_token"), params.get("user_token")

      if not app_token or not user_token:
        exceptionMessage = "Pushover notification settings requires *params* argument to have 2 key:\n app_token and user_token\n."
        exceptionMessage += '''user_token (also called USER_KEY or GROUP_KEY) is your Pushover User Key (which can be found on your dashboard) and app_token (also called API_TOKEN) is your application's API Token. If you don't already have an application API Token, you can create one for free.'''
        raise ColabHelperAuthenticationException(exceptionMessage)

    self.service = service
    self.params = params


  def set_tensorboard_backup_folder_name(self, tensorboard_logs_folder = "runs"):
    """Manually set the GDRIVE path where the backup already is or (if the first time) will be saved.
        Note the final path is given by <self.backup_folder>/runsBackup/
    """
    
    self.tensorboard_backup_p = os.path.join(self.backup_folder,tensorboard_logs_folder)
  
  def set_backup_folder(self, backup_folder):
    """Set the backup path where the backup already is or (if the first time) will be saved."""
    
    self.backup_folder = backup_folder


  @staticmethod
  def _copy_folder_content(source, target):
    """ Private method used to copy from a source to a target folder"""

    if not os.path.isdir(target):
      os.mkdir(target)
    # Create the smart pth for copy command. We want to copy all the folder content.
    if not source.endswith("/"):
      source += "/"

    subprocess.run(["cp", "-af", "'"+source+"*"+"'", "'"+target+"'"]) # v for verbose

  @staticmethod
  def _copy_file(source, target):
    """ Private method used to copy a file"""

    target_fpath = Path(target)
    if not os.path.isdir(target_fpath.parent):
      os.mkdir(target_fpath.parent)
    subprocess.run(["cp", "-af", "'"+source+"'", "'"+target+"'"]) # v for verbose

  def tensorboard_backup(self, tensorboard_logdir="runs"):
    """Make a backup of the log dir used by tensorboard given as input to 
      the specified tensorboard_backup_p folder"""

    self._copy_folder_content(tensorboard_logdir,self.tensorboard_backup_p)

  def tensorboard_restore(self, tensorboard_logdir="runs"):
    """Restore a backup of the log dir tensorboard into the given path from 
      the gdrive folder tensorboard_backup_p folder"""
    print("[INFO] To start tensorboard you can execute the following 2 lines:\n\%load_ext tensorboard\n\%tensorboard --logdir ",tensorboard_logdir)
    self._copy_folder_content(self.tensorboard_backup_p, tensorboard_logdir)
  
  @staticmethod
  def beep(times = 2):
    """ Play a bip sound N times with interval of 2 seconds"""
    for i in range(times):
      output.eval_js('new Audio("https://upload.wikimedia.org/wikipedia/commons/0/05/Beep-09.ogg").play()')
      time.sleep(2)

  @staticmethod
  def get_ram_usage():
    """ Print RAM usage info (free -m)"""
    print(subprocess.Popen("free -m", shell=True, stdout=subprocess.PIPE).stdout.read().decode())
  
  @staticmethod
  def get_hdd_usage():
    """ Print HDD usage info (!df -h)"""
    print(subprocess.Popen("df -h", shell=True, stdout=subprocess.PIPE).stdout.read().decode())
    
  
  @staticmethod
  def get_gpu_info():
    """ Print GPU model and usage info (!nvidia-smi)"""
    print(subprocess.Popen("nvidia-smi", shell=True, stdout=subprocess.PIPE).stdout.read().decode())


  @staticmethod
  def get_cpu_info():
    """ Print CPU model (!cat /proc/cpuinfo)"""
    print(subprocess.Popen("cat /proc/cpuinfo", shell=True, stdout=subprocess.PIPE).stdout.read().decode())
  
  def _pushover_send_msg(self, message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
        "token": self.params.get("app_token"),
        "user": self.params.get("user_token"),
        "message": message,
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

  def _pushover_send_with_img(self, message, img):
    """Send a jpeg image as attachment"""

    r = requests.post("https://api.pushover.net/1/messages.json", data = {
      "token": self.params.get("app_token"),
      "user": self.params.get("user_token"),
      "message": message,
    },
    files = {
      "attachment": ("image.jpg", open(img, "rb"), "image/jpeg")
    })
    #print(r.text)

  def notify(self, notification_type = "DONE", extra= ""):
    """Send a notification by using third part service.
      You need to call set_notification_params as first.
    """

    message = "[" + notification_type + "]"
    message += "\n" + extra
    if self.service == "pushover":
      app_token, user_token = self.params.get("app_token"), self.params.get("user_token")
      if not app_token or not user_token:
        raise ColabHelperException("You need to set the parameters of the service as first. Use set_notification_params method for that.")
      self._pushover_send_msg(message)
    
  def backup_dataframe(self, df, name):
    """Save a local and remote copy of the input dataframe.
    Creates the folder if it doesnt exist.

    param:
    name (str): the name of the data to be saved. This will be the filename of pkl.
    folder_path (str | os.path): the backup folder for the dataframes"""

    local_path="./dataframes/"
    if not os.path.isdir(local_path):
      os.mkdir("dataframes")
    local_backup = os.path.join(local_path, name+".pkl")
    df.to_pickle(local_backup)
    remote_backup = os.path.join(self.dataframes_backup_p, name+".pkl")
    self._copy_file(local_backup, remote_backup)
    #, remote_path="/content/drive/My Drive/dataframes", local_path="./dataframes/"


  def restore_dataframe(self, name):
    """Restore a remote copy of the input dataframe.
    Creates the folder if it doesnt exist.

    param:
    name (str): the name of the data to be saved. This will be the filename of pkl.
    folder_path (str | os.path): the backup folder for the dataframes"""

    local_path="./dataframes/"
    if not os.path.isdir(local_path):
      os.mkdir("dataframes")
    local_backup = os.path.join(local_path, name+".pkl")
    remote_backup = os.path.join(self.dataframes_backup_p, name+".pkl")
    self._copy_file(remote_backup, local_backup)
    return pd.read_pickle(local_backup)

    # TODO: Sync?notify?use just requests? Use more third parties service like telegram, browser notification?

class ColabHelperException(Exception):
  pass

class ColabHelperAuthenticationException(ColabHelperException):
  pass

