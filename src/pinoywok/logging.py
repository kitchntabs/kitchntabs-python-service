# logging.py
import time
import sys
from pinoywok.args import args 


def log(message):
  _args = args.get_args()
  LOGFILE = _args.log 
  # Handle Unicode encoding issues on Windows
  try:
    print(message, flush=True)
  except UnicodeEncodeError:
    # Fallback: encode with 'replace' to handle unsupported characters
    safe_message = message.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
    print(safe_message, flush=True)
  try:
    with open(LOGFILE,'a', encoding='utf-8') as f:
        m = "{0} {1}\n".format(time.asctime( time.localtime(time.time())),message) 
        f.write(m)
  except Exception as e:
    return