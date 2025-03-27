import wave
import numpy as np
import os

# Create a 5-second silence WAV file
silence_length = 5  # seconds
sample_rate = 44100
silence = np.zeros(sample_rate * silence_length, dtype=np.int16)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

with wave.open('downloads/silence.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(silence.tobytes())

print('Created silence.wav in downloads directory') 