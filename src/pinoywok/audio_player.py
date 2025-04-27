import threading
import pyaudio
import audiomentations
import soundfile as sf
import librosa
import simpleaudio as sa
from gtts import gTTS

class AudioPlayer:
    def __init__(self):
        # Initialize state variables first
        self._audio_playing = False
        self._playing_salute = False
        
        try:
            self.p = pyaudio.PyAudio()
            
            # Check if any input devices exist
            device_count = self.p.get_device_count()
            has_input_device = False
            
            for i in range(device_count):
                device_info = self.p.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    has_input_device = True
                    break
            
            if has_input_device:
                try:
                    self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
                except OSError as e:
                    print(f"Error opening audio stream: {e}")
                    self.stream = None
            else:
                print("No audio input devices found. Audio input disabled.")
                self.stream = None
        except Exception as e:
            print(f"Failed to initialize audio system: {e}")
            self.p = None
            self.stream = None

    def thread_generate_audio(self,text,audio_file):
        threading.Thread(target=self.generate_audio, args=(text, audio_file)).start()

    def generate_audio(self,text,audio_file="motion.mp3"):
        try:
            tts = gTTS(text=text, lang='es')
            tts.save(audio_file)
            self.play_audio(audio_file)
        except Exception as e:
            print(f"Error generating audio: {e}")
        
    def play_audio(self,audio_file):
        if not self._audio_playing:
            try:
                self._audio_playing = True
                sound, sr = librosa.load(audio_file)
                augment = audiomentations.Compose([
                    audiomentations.PitchShift(min_semitones=2, max_semitones=4, p=1.0),
                    audiomentations.Resample(sr, int(sr * 1))
                ])
                pitched_sound = augment(samples=sound, sample_rate=sr)
                sf.write("pitched_audio.wav", pitched_sound, int(sr * 1))  # Save with the new sample rate
                wave_obj = sa.WaveObject.from_wave_file("pitched_audio.wav")
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                print(f"Error playing audio: {e}")
            finally:
                self._audio_playing = False
                self._playing_salute = False

    @property
    def audio_playing(self):
        return self._audio_playing

    @audio_playing.setter
    def audio_playing(self, value):
        self._audio_playing = value

    @property
    def playing_salute(self):
        return self._playing_salute

    @playing_salute.setter
    def playing_salute(self, value):
        self._playing_salute = value
