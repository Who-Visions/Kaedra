"""Story Engine Smoke Test - Validates modular components."""
from kaedra.story.emotions import EmotionEngine
from kaedra.story.tension import TensionCurve
from kaedra.story.structure import NarrativeStructure
from kaedra.story.veil import VeilManager
from kaedra.story.normalize import normalize_turn
from kaedra.story.config import EmotionConfig

def main():
    # EmotionEngine
    emo = EmotionEngine(EmotionConfig())
    emo.pulse("fear", 0.5)
    emo.tick()
    intensity = emo.intensity()
    assert 0.0 <= intensity <= 4.0, f"intensity {intensity} out of range"
    print(f"EmotionEngine: intensity={intensity:.2f}")

    # TensionCurve
    t = TensionCurve()
    t.tick(5)
    assert 0.0 <= t.current <= 1.0, f"tension {t.current} out of range"
    print(f"TensionCurve: current={t.current:.2f}")

    # NarrativeStructure
    s = NarrativeStructure()
    dirs = s.tick(5)
    assert 1 <= s.act <= 5, f"act {s.act} out of range"
    print(f"NarrativeStructure: act={s.act}, progress={s.progress:.2f}")

    # VeilManager
    v = VeilManager(is_active=True)
    directive = v.get_directive()
    assert isinstance(directive, str)
    print(f"VeilManager: directive={directive[:40]}...")

    # normalize_turn
    turn = normalize_turn({"role": "user", "parts": [{"text": "Hello"}]})
    assert turn["role"] == "user"
    assert turn["parts"][0]["text"] == "Hello"
    print(f"normalize_turn: {turn}")

    print()
    print("SMOKE_OK")

if __name__ == "__main__":
    main()
