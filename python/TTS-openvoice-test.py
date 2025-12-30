from openvoice import OpenVoiceV2

model = OpenVoiceV2.load("checkpoints_v2")

audio = model.synthesize(
    text="Hello, this is OpenVoice V2.",
    speaker="default",
    language="en"
)

model.save(audio, "output.wav")
print("Audio saved to output.wav")