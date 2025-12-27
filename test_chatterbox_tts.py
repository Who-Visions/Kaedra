"""
Test Chatterbox Turbo TTS standalone.
"""

import time

def test_chatterbox():
    print("[*] Loading Chatterbox Turbo TTS...")
    
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    import torchaudio as ta
    
    # Load model
    model = ChatterboxTurboTTS.from_pretrained(device="cuda")
    print(f"[*] Model loaded. Sample rate: {model.sr}")
    
    # Test with Kaedra-style text including paralinguistic tags
    text = "Aight bet [chuckle], Kaedra online and locked in. What we working on today fam?"
    
    print(f"[*] Generating: '{text}'")
    start = time.time()
    wav = model.generate(text)
    elapsed = time.time() - start
    
    print(f"[*] Generation took {elapsed:.2f}s")
    
    # Save to file
    output_path = "kaedra_test.wav"
    ta.save(output_path, wav, model.sr)
    print(f"[*] Saved to {output_path}")
    print("[*] Play the file to verify voice quality and [chuckle] tag!")
    
    return output_path


if __name__ == "__main__":
    test_chatterbox()
