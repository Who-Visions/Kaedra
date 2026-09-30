import importlib.util
import pathlib

SPEC = importlib.util.spec_from_file_location(
    "fleet_cron_worker", pathlib.Path(__file__).parent.parent / "tools" / "fleet_cron_worker.py")
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)

ACK = "ACK W9Q4 | phoebus/antigravity | Session: s | Status: ONLINE"


def test_ack_is_never_acked():
    assert w.should_ack("blade", ACK) is False


def test_wrapped_ack_from_a_forwarder_is_never_acked():
    wrapped = "relay leg 2026 from x (open): [NouGenMsg -> @phoebus] " + ACK
    assert w.should_ack("relay-watch", wrapped) is False
    assert w.should_ack("nougen-blade", "PONG " + ACK.lower()) is False


def test_own_node_is_ignored_under_every_label():
    for label in ("nougen-phoebus", "phoebus-agy", "phoebus-claude", "phoebus"):
        assert w.should_ack(label, "ROUND ROBIN roll call, reply") is False, label


def test_real_roll_call_from_a_peer_is_acked():
    assert w.should_ack("nougen-blade", "roll call: who is up?") is True
    assert w.should_ack("whoart-claude", "SESSION WAKE") is True


def test_ordinary_message_is_not_acked():
    assert w.should_ack("nougen-blade", "PR merged") is False


def test_reply_targets_the_node_not_the_lane_label():
    assert w._sender_node("whoart-claude") == "whoart"
    assert w._sender_node("nougen-blade") == "blade"
