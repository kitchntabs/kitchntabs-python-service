import threading
import simpleaudio as sa
from gtts import gTTS
import tempfile
import os

# Note: pyaudio import removed - it was only used for audio INPUT (microphone)
# which triggered unnecessary microphone permission requests on macOS.
# TTS playback only needs audio OUTPUT which simpleaudio handles.

# Optional imports for audio pitch shifting
# These may not be available on ARMv7l due to llvmlite/numba compatibility
try:
    import audiomentations
    import librosa
    import soundfile as sf
    PITCH_SHIFT_AVAILABLE = True
except ImportError:
    PITCH_SHIFT_AVAILABLE = False
    print("Note: librosa/audiomentations not available - pitch shifting disabled")

class AudioPlayer:
    def __init__(self):
        # Initialize state variables first
        self._audio_playing = False
        self._playing_salute = False
        
        # Note: We don't need PyAudio for TTS playback - simpleaudio handles output.
        # Removing the input stream initialization to avoid unnecessary microphone 
        # permission requests on macOS. The input stream was never used anyway.
        self.p = None
        self.stream = None

    def thread_generate_audio(self, text, audio_file=None, lang='es'):
        threading.Thread(target=self.generate_audio, args=(text, audio_file, lang)).start()

    def generate_audio(self, text, audio_file=None, lang='es'):
        try:
            # Use temp directory if no file specified (for packaged apps)
            if audio_file is None:
                temp_dir = tempfile.gettempdir()
                audio_file = os.path.join(temp_dir, f"tts_audio_{os.getpid()}.mp3")
            
            tts = gTTS(text=text, lang=lang)
            tts.save(audio_file)
            self.play_audio(audio_file)
            
            # Clean up temp file after playing
            try:
                if audio_file.startswith(tempfile.gettempdir()):
                    os.remove(audio_file)
            except:
                pass
        except Exception as e:
            print(f"Error generating audio: {e}")
        
    def play_audio(self,audio_file):
        if not self._audio_playing:
            temp_files = []  # Track temp files to clean up
            try:
                self._audio_playing = True
                temp_dir = tempfile.gettempdir()
                
                if PITCH_SHIFT_AVAILABLE:
                    # Use librosa + audiomentations for pitch shifting
                    sound, sr = librosa.load(audio_file)
                    augment = audiomentations.Compose([
                        audiomentations.PitchShift(min_semitones=2, max_semitones=4, p=1.0),
                        audiomentations.Resample(sr, int(sr * 1))
                    ])
                    pitched_sound = augment(samples=sound, sample_rate=sr)
                    pitched_file = os.path.join(temp_dir, f"pitched_audio_{os.getpid()}.wav")
                    temp_files.append(pitched_file)
                    sf.write(pitched_file, pitched_sound, int(sr * 1))
                    wave_obj = sa.WaveObject.from_wave_file(pitched_file)
                else:
                    # Fallback: play audio without pitch shifting
                    # Convert mp3 to wav if needed using pydub or just try to play
                    if audio_file.endswith('.mp3'):
                        # Use simpleaudio directly - it may not support mp3
                        # For mp3 files, we need to convert first
                        try:
                            from pydub import AudioSegment
                            audio = AudioSegment.from_mp3(audio_file)
                            temp_wav = os.path.join(temp_dir, f"temp_audio_{os.getpid()}.wav")
                            temp_files.append(temp_wav)
                            audio.export(temp_wav, format="wav")
                            wave_obj = sa.WaveObject.from_wave_file(temp_wav)
                        except ImportError:
                            print("pydub not available, trying direct playback")
                            wave_obj = sa.WaveObject.from_wave_file(audio_file)
                    else:
                        wave_obj = sa.WaveObject.from_wave_file(audio_file)
                
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                print(f"Error playing audio: {e}")
            finally:
                self._audio_playing = False
                self._playing_salute = False
                # Clean up temp files
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except:
                        pass

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
