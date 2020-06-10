from google.colab import drive
from google.colab import output
from google.colab import auth
from google.colab import files  # Required for downloading file from colab

import os
import time
import requests
import http.client, urllib
import subprocess
from pathlib import Path
import pandas as pd
from distutils.dir_util import copy_tree
from shutil import copyfile

import functools

#gsheet export
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client.client import GoogleCredentials

# Note: To save the state of the models, maybe just using pickle without using torch?
import torch

class ColabHelper:
  """ Improve Colab productivity by reducing the amount of code you need for everything you need."""

  def __init__(self, model_state_p=None, backup_folder="/content/drive/My Drive/ColabHelper/"):
    
    tensorboard_logs_folder = "runs"
    dataframes_folder = "dataframes"
    if not backup_folder.startswith("/content/drive/"):
      backup_folder = F"/content/gdrive/My Drive/{backup_folder}" 
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
    
    return len(copy_tree(source, target)) > 1

  @staticmethod
  def _copy_file(source, target):
    """ Private method used to copy a file"""

    target_fpath = Path(target)
    if not os.path.isdir(target_fpath.parent):
      os.mkdir(target_fpath.parent)
    copyfile(source, target)

  def tensorboard_backup(self, tensorboard_logdir="runs"):
    """Make a backup of the log dir used by tensorboard given as input to 
      the specified tensorboard_backup_p folder"""

    self._copy_folder_content(tensorboard_logdir,self.tensorboard_backup_p)

  def tensorboard_restore(self, tensorboard_logdir="runs"):
    """Restore a backup of the log dir tensorboard into the given path from 
      the gdrive folder tensorboard_backup_p folder"""
    print("[INFO] To start tensorboard you can execute the following 2 lines:\n%load_ext tensorboard\n%tensorboard --logdir ",tensorboard_logdir)
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
  
  @staticmethod
  def download_from_colab(colab_path="sample_data/README.md"):
    """ Download a file from Colab."""
    files.download(colab_path) 
    
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
    
  def export_dataframe_to_gsheet(self, df, name):
    """Export a dataframe to a new google sheet. 
    
    param
      df:   dataframe to be exported as sheet
      name: name that will be given to the sheet and to the worksheet 
            that will be *created* on google sheet.
            
    note
      you can't never overwrite a google sheet,
      every time this method is called a new sheet is created.
    """
    
    auth.authenticate_user()
    default_app = GoogleCredentials.get_application_default()
    gc = gspread.authorize(default_app)
    # HP: auth ok
    spreadsheet_name = name
    worksheet_output = name
    # Note: a new sheet is always created, there is no overwriting
    spreadsheet = gc.create(spreadsheet_name)
    spreadsheet.add_worksheet(worksheet_output, 1, 1)
    spreadsheet = gc.open(spreadsheet_name)
    worksheet_out = spreadsheet.worksheet(title=worksheet_output)
    set_with_dataframe(worksheet_out, df)
    
  def torch_model_state_backup(self, model, model_name):
    """Save a model state to <backup_folder>/models_states/ .
    
    param:
    model: the model which state should be saved.
    model_name: the name of the generated file required for restoring.
    
    Note: this supports pythorch only as of now.
    this uses the torch.save() to generate the output.
    """
    
    model_file_name = model_name
    model_folder = "models_states"
    folder_path = os.path.join(self.backup_folder, model_folder)
    file_path = os.path.join(folder_path, model_file_name)
    if not os.path.isdir(folder_path):
      os.mkdir(folder_path)
    
    torch.save({'state_dict': model.state_dict()}, file_path)
    
  def torch_model_state_restore(self, model, model_name):
    """Restore a model state from <backup_folder>/models_states/ .
    
    param:
    model: the model which state should be loaded.
    model_name: the name of the model state to restore.
    
    Note: this supports pythorch only as of now.
    ** Model class must be defined somewhere ***
    this uses the torch.load() to restore a saved state.
    """
    
    model_file_name = model_name
    model_folder = "models_states"
    folder_path = os.path.join(self.backup_folder, model_folder)
    file_path = os.path.join(folder_path, model_file_name)
    
    state_dict = torch.load(file_path)['state_dict']
    model.load_state_dict(state_dict)

    #model.load(file_path)
    #model.eval()
    
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

    
# Define @timeme decorator
def timeme(func):
  """Print the runtime of the decorated function"""
  
  @functools.wraps(func)
  def wrapper_timer(*args, **kwargs):
      start_time = time.perf_counter()
      value = func(*args, **kwargs)
      end_time = time.perf_counter()
      run_time = end_time - start_time
      print(f"Execution finished {func.__name__!r} in {run_time:.4f} secs")
      return value
  return wrapper_timer #  no "()" here, return obj
  
class ColabHelperException(Exception):
  pass

class ColabHelperAuthenticationException(ColabHelperException):
  pass

