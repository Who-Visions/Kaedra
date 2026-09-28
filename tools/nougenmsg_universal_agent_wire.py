"""
NouGenMsg Universal Agent Wire & Banner Formatter
Hooks all local agents (Kaedra, Rhea-Noir, Yuki-Ai, Iris-Ai, Bandit, Dav1d) to MsgNode:8766
and emits structured print banners with smart emojis inline.
"""
import os, sys, json, time, urllib.request

MSGNODE_URL = "http://127.0.0.1:8766/api/send"
AGY_INBOX_DIR = os.path.expanduser("~/.nougen/agy_inbox")

AGENT_EMOJIS = {
    "phoebus": "🪐 [PHOEBUS / ANTIGRAVITY]",
    "kaedra": "⚡ [KAEDRA SUPERVISOR]",
    "rhea": "👑 [RHEA-NOIR ENGINE]",
    "yuki": "🌸 [YUKI-AI MEDIA]",
    "iris": "💎 [IRIS-AI FINANCE]",
    "bandit": "🐺 [BANDIT AUTONOMOUS]",
    "dav1d": "🦁 [DAV1D ALPHA]"
}

def broadcast_agent_response(agent_id, target, message, context_shards=None):
    tag = AGENT_EMOJIS.get(agent_id.lower(), f"🤖 [{agent_id.upper()}]")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Print structured banner directly to stdout
    print(f"\n{'='*70}")
    print(f"{tag} 🛰️ INBOUND FLEET MESH RESPONSE")
    print(f"Timestamp: {timestamp} | Target: {target}")
    if context_shards:
        print(f"Context Shards: {context_shards}")
    print(f"{'-'*70}")
    print(f"{message}")
    print(f"{'='*70}\n")
    
    # 2. Wire payload to MsgNode
    payload = {
        "sender": agent_id,
        "target": target,
        "message": message,
        "timestamp": timestamp,
        "context_shards": context_shards or []
    }
    
    try:
        req = urllib.request.Request(
            MSGNODE_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            pass
    except Exception as e:
        # Save to inbox fallback if MsgNode offline
        os.makedirs(AGY_INBOX_DIR, exist_ok=True)
        fname = f"{AGY_INBOX_DIR}/msg_{int(time.time()*1000)}.json"
        with open(fname, "w") as f:
            json.dump(payload, f)

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        shards = sys.argv[4].split(',') if len(sys.argv) >= 5 else []
        broadcast_agent_response(sys.argv[1], sys.argv[2], sys.argv[3], shards)
    else:
        # Test broadcast sweep across all agents
        broadcast_agent_response("kaedra", "phoebus", "Kaedra Supervisor wired natively to MsgNode:8766. Operational status nominal.", ["Shard #30845"])
        broadcast_agent_response("rhea", "phoebus", "Rhea-Noir Execution Engine latched to live socket wire. Execution ready.", ["Shard #30833"])
        broadcast_agent_response("yuki", "phoebus", "Yuki-Ai Media Intelligence online. Memory sync complete.", ["Shard #12090"])
        broadcast_agent_response("iris", "phoebus", "Iris-Ai Personal Finance connected to Substrate.", ["Shard #8840"])
        broadcast_agent_response("bandit", "phoebus", "Bandit Autonomous task listener armed.", ["Shard #4921"])
        broadcast_agent_response("dav1d", "phoebus", "Dav1d Alpha Agent registered on live mesh wire.", ["Shard #1029"])
