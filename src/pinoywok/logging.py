# logging.py
import time
from pinoywok.args import args 


def log(message):
  _args = args.get_args()
  LOGFILE = _args.log 
  print(message, flush=True)     
  try:
    with open(LOGFILE,'a') as f:
        m = "{0} {1}\n".format(time.asctime( time.localtime(time.time())),message) 
        f.write(m)
  except Exception as e:
    return