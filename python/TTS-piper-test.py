#!/usr/bin/env python3
from piper import PiperVoice
import sys
import os
import wave

def main():
    if len(sys.argv) < 4:
        print("Usage: piper_test.py <model_dir> <text> <output.wav>")
        sys.exit(1)

    model_dir = sys.argv[1]
    text = sys.argv[2]
    out_path = sys.argv[3]

    # Find ONNX model
    onnx_files = [f for f in os.listdir(model_dir) if f.endswith(".onnx")]
    if not onnx_files:
        print("No .onnx model found in directory.")
        sys.exit(1)

    model_path = os.path.join(model_dir, onnx_files[0])
    print(f"Loading model: {model_path}")

    voice = PiperVoice.load(model_path)

    # Let Piper handle chunking and WAV formatting
    with wave.open(out_path, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    print(f"Saved audio to {out_path}")

if __name__ == "__main__":
    main()
