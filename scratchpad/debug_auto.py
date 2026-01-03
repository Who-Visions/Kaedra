from kaedra.worlds.automations import run_automations_on_world
try:
    print("Running automations...")
    logs = run_automations_on_world("world_bee9d6ac")
    print("Logs:", logs)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
