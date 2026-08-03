from agent import get_dh_agent

def run_cli():
    print("DigitalHub Agent Initialized. Type your command below (or 'exit' to quit):\n")
    agent = get_dh_agent()

    while True:
        try:
            user_input = input("User > ")
            if user_input.strip().lower() in ["exit", "quit"]:
                print("Exiting DigitalHub Agent. Goodbye!")
                break
            if not user_input.strip():
                continue

            inputs = {"messages": [("user", user_input)]}
            config = {"configurable": {"thread_id": "cli-session"}}
            print("\nAgent > ", end="", flush=True)
            for chunk, metadata in agent.stream(inputs, stream_mode="messages", config=config):
                if chunk.content:
                    print(chunk.content, end="", flush=True)
            print("\n")
        except KeyboardInterrupt:
            print("\nExiting DigitalHub Agent.")
            break
        except Exception as e:
            print(f"\nError executing request: {e}\n")

if __name__ == "__main__":
    run_cli()
