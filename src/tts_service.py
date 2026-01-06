#!/usr/bin/env python3
"""
Simple Text-to-Speech Service for KitchnTabs
Can be run standalone or called from Electron via IPC

Usage:
    python tts_service.py "message to speak" [language]
    python tts_service.py "Hola mundo" es
    python tts_service.py "Hello world" en

Arguments:
    message: The text to speak
    language: Language code (default: 'es' for Spanish)
              Supported: es, en, pt, fr, de, it, etc.
"""

import sys
import os
import time

def log(message):
    """Helper function to log messages with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"[{timestamp}] {message}", flush=True)
    except (UnicodeEncodeError, UnicodeDecodeError):
        safe_message = str(message).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        print(f"[{timestamp}] {safe_message}", flush=True)

def speak(message, lang='es'):
    """
    Speak a message using Google Text-to-Speech
    
    Args:
        message: The text to speak
        lang: Language code (default: 'es')
    """
    try:
        from gtts import gTTS
        import tempfile
        
        log(f"Generating speech: '{message}' (lang: {lang})")
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            audio_file = tmp_file.name
        
        # Generate the speech
        tts = gTTS(text=message, lang=lang)
        tts.save(audio_file)
        
        log(f"Audio saved to: {audio_file}")
        
        # Play the audio
        play_audio(audio_file)
        
        # Clean up
        try:
            os.remove(audio_file)
        except:
            pass
            
        log("Speech completed")
        return True
        
    except ImportError as e:
        log(f"Error: Missing dependency - {e}")
        log("Install with: pip install gtts")
        return False
    except Exception as e:
        log(f"Error generating speech: {e}")
        return False

def play_audio(audio_file):
    """
    Play an audio file using available system method
    """
    import platform
    system = platform.system()
    
    if system == 'Windows':
        # On Windows, try multiple methods to avoid opening external programs
        
        # Method 1: Use pydub + winsound (requires ffmpeg for mp3)
        try:
            from pydub import AudioSegment
            import winsound
            
            # Convert mp3 to wav
            audio = AudioSegment.from_mp3(audio_file)
            wav_file = audio_file.replace('.mp3', '.wav')
            audio.export(wav_file, format='wav')
            
            # Play the WAV file directly
            winsound.PlaySound(wav_file, winsound.SND_FILENAME)
            
            # Clean up wav file
            try:
                os.remove(wav_file)
            except:
                pass
            log("Audio played via winsound + pydub")
            return
        except Exception as e:
            log(f"Winsound+pydub failed: {e}")
        
        # Method 2: Try simpleaudio with pydub conversion
        try:
            import simpleaudio as sa
            from pydub import AudioSegment
            
            audio = AudioSegment.from_mp3(audio_file)
            wav_file = audio_file.replace('.mp3', '.wav')
            audio.export(wav_file, format='wav')
            
            wave_obj = sa.WaveObject.from_wave_file(wav_file)
            play_obj = wave_obj.play()
            play_obj.wait_done()
            
            try:
                os.remove(wav_file)
            except:
                pass
            log("Audio played via simpleaudio + pydub")
            return
        except Exception as e:
            log(f"Simpleaudio+pydub failed: {e}")
        
        # Method 3: Try pygame (can handle mp3 directly)
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            log("Audio played via pygame")
            return
        except Exception as e:
            log(f"Pygame failed: {e}")
        
        # Method 4: Use Windows Media Control (no external window)
        try:
            import ctypes
            from ctypes import wintypes
            
            winmm = ctypes.windll.winmm
            
            # MCI command to play mp3
            mci_send = winmm.mciSendStringW
            mci_send.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
            mci_send.restype = wintypes.DWORD
            
            buf = ctypes.create_unicode_buffer(255)
            
            # Open and play the audio file
            audio_path = audio_file.replace('/', '\\')
            mci_send(f'open "{audio_path}" type mpegvideo alias tts_audio', buf, 254, 0)
            mci_send('play tts_audio wait', buf, 254, 0)
            mci_send('close tts_audio', buf, 254, 0)
            
            log("Audio played via Windows MCI")
            return
        except Exception as e:
            log(f"Windows MCI failed: {e}")
        
        # If all Windows methods fail, log error but DON'T open external program
        log("ERROR: All Windows audio playback methods failed. Audio will not play.")
        return
    
    # Non-Windows platforms (macOS, Linux)
    try:
        # Try simpleaudio first (cross-platform)
        try:
            import simpleaudio as sa
            from pydub import AudioSegment
            
            # Convert mp3 to wav for simpleaudio
            audio = AudioSegment.from_mp3(audio_file)
            wav_file = audio_file.replace('.mp3', '.wav')
            audio.export(wav_file, format='wav')
            
            wave_obj = sa.WaveObject.from_wave_file(wav_file)
            play_obj = wave_obj.play()
            play_obj.wait_done()
            
            # Clean up wav file
            try:
                os.remove(wav_file)
            except:
                pass
            return
        except ImportError:
            pass
        
        # Fallback: Try pygame
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            return
        except ImportError:
            pass
        
        # Fallback: Try playsound
        try:
            from playsound import playsound
            playsound(audio_file)
            return
        except ImportError:
            pass
        
        # Fallback: Use system commands
        import subprocess
        
        if system == 'Darwin':  # macOS
            subprocess.run(['afplay', audio_file], check=True)
        elif system == 'Linux':
            # Try various Linux audio players
            for player in ['mpg123', 'mpg321', 'play', 'aplay']:
                try:
                    subprocess.run([player, audio_file], check=True, capture_output=True)
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            log("Warning: No audio player found on Linux")
            
    except Exception as e:
        log(f"Error playing audio: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    message = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else 'es'
    
    log(f"TTS Service started")
    log(f"Message: {message}")
    log(f"Language: {lang}")
    
    success = speak(message, lang)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
