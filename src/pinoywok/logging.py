# logging.py
import time
import sys
from pinoywok.args import args 


def log(message):
  _args = args.get_args()
  LOGFILE = _args.log 
  # Convert message to string if it's not
  if not isinstance(message, str):
    message = str(message)
  # Sanitize message: remove/replace non-printable and problematic Unicode characters for Windows console
  import re
  # Remove emoji and other problematic Unicode characters (keep basic Latin, accented chars, punctuation)
  safe_message = re.sub(r'[\U00010000-\U0010ffff]', '', message)  # Remove emoji
  safe_message = safe_message.encode('ascii', errors='ignore').decode('ascii')  # Keep only ASCII for console
  # Handle Unicode encoding issues on Windows
  try:
    print(safe_message, flush=True)
  except (UnicodeEncodeError, UnicodeDecodeError, Exception):
    # Fallback: try to print something
    try:
      print(safe_message.encode('ascii', errors='replace').decode('ascii'), flush=True)
    except Exception:
      print("Error logging message", flush=True)
  # Write full unicode to file (file handles utf-8 fine)
  try:
    with open(LOGFILE,'a', encoding='utf-8') as f:
        m = "{0} {1}\n".format(time.asctime( time.localtime(time.time())),message) 
        f.write(m)
  except Exception as e:
    return