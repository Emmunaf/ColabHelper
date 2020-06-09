from google.colab import drive
from google.colab import output

import os
import time
import requests
import http.client, urllib

class ColabHelper:
  """ Class useful to improved Colab capabilities"""

  def __init__(self, model_state_p=None, tensorboard_backup_p="/content/drive/My Drive/MLDS/runlog2/"):
    
    self.tensorboard_backup_p = tensorboard_backup_p
    # Load gdrive
    drive.mount('/content/drive/')
    if not os.path.isdir(tensorboard_backup_p):
      print("[INFO] Your backup folder {} doesnt exist", tensorboard_backup_p)
    else:
      print("[WARN] Your backup folder {} already exists. Some files can be overwritten", tensorboard_backup_p)
  
  def set_notification_params(self, service="pushover", params={}):
    if service == "pushover":
      app_token, user_token = params.get("app_token"), params.get("user_token")

      if not app_token or not user_token:
        exceptionMessage = "Pushover notification settings requires *params* argument to have 2 key:\n app_token and user_token\n."
        exceptionMessage += '''user_token (also called USER_KEY or GROUP_KEY) is your Pushover User Key (which can be found on your dashboard) and app_token (also called API_TOKEN) is your application's API Token. If you don't already have an application API Token, you can create one for free.'''
        raise ColabHelperAuthenticationException(exceptionMessage)

    self.service = service
    self.params = params


  @staticmethod
  def _copy_folder_content(source, target):
    """ Private method used to execute copy from a source to a target folder"""

    if not os.path.isdir(target):
      !mkdir $target
    # Create the smart pth for copy command. We want to copy all the folder content.
    if not source.endswith("/"):
      source += "/"
    !cp -af '$source'* '$target'   # v for verbose debug

  def tensorboard_backup(self, tensorboard_logdir="./runs/"):
    """Make a backup of the log dir used by tensorboard given as input to 
      the specified tensorboard_backup_p folder"""

    self._copy_folder_content(tensorboard_logdir,self.tensorboard_backup_p)

  def tensorboard_restore(self, tensorboard_logdir="./runs/"):
    """Restore a backup of the log dir tensorboard into the given path from 
      the gdrive folder tensorboard_backup_p folder"""
      
    self._copy_folder_content(self.tensorboard_backup_p, tensorboard_logdir)
  
  @staticmethod
  def beep(times = 2):
    """ Play a bip sound N times with interval of 2 seconds"""
    for i in range(times):
      output.eval_js('new Audio("https://upload.wikimedia.org/wikipedia/commons/0/05/Beep-09.ogg").play()')
      time.sleep(2)

  @staticmethod
  def get_free_ram():
    """ Print RAM usage info"""
    !free -m
  
  @staticmethod
  def get_hdd_usage():
    """ Print HDD usage info"""
    !df -h
  
  @staticmethod
  def get_gpu_info():
    """ Print GPU model and usage info"""
    !nvidia-smi

  @staticmethod
  def get_cpu_info():
    """ Print CPU model"""
    !cat /proc/cpuinfo
  
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
    
  # TODO: Sync?notify?use just requests? Use more third parties service like telegram, browser notification?

class ColabHelperException(Exception):
  pass

class ColabHelperAuthenticationException(ColabHelperException):
  pass
