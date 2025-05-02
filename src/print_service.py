import os
import threading
import sys
import json as json_module
import pinoywok.print
from pinoywok.args import args
from pinoywok.config import config
from pinoywok.logging import log

args.set_key("tab_id", sys.argv[1] if len(sys.argv) > 1 else None)
args.set_key("token", sys.argv[2] if len(sys.argv) > 2 else None)
args.set_key("config", sys.argv[3] if len(sys.argv) > 3 else 'config.dev.yaml')
args.set_key("log", sys.argv[4] if len(sys.argv) > 4 else 'log.txt')

#Load config
_args = args.get_args()
config.load_config(_args.config)

def print_order_threaded(tab_id, token, output, log, cfg):
    print(f"tab_id: {tab_id}", flush=True)
    if tab_id is not None:
        threading.Thread(target=pinoywok.print.print_order, args=(tab_id,token,output,log,cfg)).start()
    else:
        print("Error: tab_id not found", flush=True)

def print_order(tab_id,token,log,cfg):
        folder = log
        parent_folder = os.path.dirname(folder)
        grandparent_folder = os.path.dirname(parent_folder)
        output = os.path.join(grandparent_folder,"./output/")
        if not os.path.exists(output):
            os.mkdir(output)
        try:
            print_order_threaded(tab_id,token,output,log,cfg)
            return
        except Exception as e:
            print(f"print_order - Error Printing: {e}", flush=True)

def main() -> None:
    if _args.tab_id:
        print_order(_args.tab_id,_args.token,_args.log,_args.config)
    else:
        log("No order id to print")

if __name__ == "__main__":
    main()