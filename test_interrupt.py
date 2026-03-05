import sys
import uuid
import json

# Add project root to sys.path so we can import src
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.agent import create_coding_agent

def test_interrupt():
    try:
        agent, checkpointer = create_coding_agent()
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        input_val = {"messages": [{"role": "user", "content": "run the execute tool with command 'ls'"}]}
        
        print("Starting agent stream...")
        for event in agent.stream(input_val, config=config, stream_mode="updates", subgraphs=True):
            namespace, evt = event if isinstance(event, tuple) and len(event) == 2 else ((), event)
            if not isinstance(evt, dict): continue
            for node_name, node_data in evt.items():
                if node_name == "__interrupt__":
                    print("\n=== INTERRUPT HIT ===")
                    intr = node_data[0] if isinstance(node_data, list) else node_data
                    
                    val = getattr(intr, "value", None)
                    print(f"Type: {type(val)}")
                    
                    if isinstance(val, dict):
                        print("It is a dict!")
                        print(f"Keys: {list(val.keys())}")
                    else:
                        print("Not a dict.")
                        print(f"Dir: {dir(val)}")
                        try:
                            print(f"Action requests: {val['action_requests']}")
                        except Exception as e:
                            print(f"Error accessing as dict: {e}")
                    sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_interrupt()
