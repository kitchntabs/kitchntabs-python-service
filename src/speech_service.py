import os
import threading
import sys
import pinoywok.speech    
from pinoywok.args import args
from pinoywok.config import config
from pinoywok.logging import log
from pinoywok.audio_player import AudioPlayer

#Set global arguments

#args.parser.add_argument('-i', '--id',  type=int, help='Order Id')
#args.parser.add_argument('-c', '--config', help='Config path',default='config.yaml')   
#args.parser.add_argument('-l', '--log', help='Log path',default='log.txt')  
#args.parse_args(sys.argv[1:])

# Set default values if arguments are not provided
args.set_key("json", sys.argv[1] if len(sys.argv) > 1 else None)
args.set_key("token", sys.argv[1] if len(sys.argv) > 2 else None)
args.set_key("config", sys.argv[3] if len(sys.argv) > 3 else 'config.dev.yaml')
args.set_key("log", sys.argv[4] if len(sys.argv) > 4 else 'log.txt')

#Load config
_args = args.get_args()
config.load_config(_args.config)

def speech_task_threaded(json, token,output,log, cfg):
    threading.Thread(target=pinoywok.speech.speech_task, args=(json,token,output,log,cfg)).start()

def speech_task(json,token,log,cfg):
        folder = log
        parent_folder = os.path.dirname(folder)
        grandparent_folder = os.path.dirname(parent_folder)
        output = os.path.join(grandparent_folder,"./output/")
        if not os.path.exists(output):
            os.mkdir(output)
        try:
            audio_player = AudioPlayer()
            message = json.get("notificationPayload", {}).get("message", "")
            audio_player.thread_generate_audio(message, "notification.mp3")
            return
        except Exception as e:
            print(f"speech_task - Error Speaking: {e}", flush=True)

def main() -> None:
    if _args.json:
        speech_task(_args.json,_args.token,_args.log,_args.config)
    else:
        log("No task id to speech")

if __name__ == "__main__":
    main()
















































































    