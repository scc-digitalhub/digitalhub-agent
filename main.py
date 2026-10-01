from agent import get_dh_agent

def run_cli():
    print("DigitalHub Agent Initialized. Type your command below (or 'exit' to quit):\n")
    agent = get_dh_agent(with_memory=True)
    session_input_tokens = 0
    session_output_tokens = 0

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
            
            total_input_tokens = 0
            total_output_tokens = 0

            for chunk, metadata in agent.stream(inputs, stream_mode="messages", config=config):
                if chunk.content:
                    print(chunk.content, end="", flush=True)

                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    u = chunk.usage_metadata
                    total_input_tokens += u.get("input_tokens", 0)
                    total_output_tokens += u.get("output_tokens", 0)

                elif hasattr(chunk, "response_metadata") and chunk.response_metadata:
                    rm = chunk.response_metadata
                    u = rm.get("token_usage") or rm.get("usage") or rm.get("message", {}).get("usage")
                    if u:
                        total_input_tokens += u.get("prompt_tokens") or u.get("input_tokens", 0)
                        total_output_tokens += u.get("completion_tokens") or u.get("output_tokens", 0)

            print("\n")

            turn_tokens = total_input_tokens + total_output_tokens
            session_input_tokens += total_input_tokens
            session_output_tokens += total_output_tokens
            session_total_tokens = session_input_tokens + session_output_tokens

            if turn_tokens > 0:
                print(
                    f"--- [Turn: {turn_tokens} (Input: {total_input_tokens} | Output: {total_output_tokens}) | "
                    f"Session: {session_total_tokens} (Input: {session_input_tokens} | Output: {session_output_tokens})] ---\n"
                )

        except KeyboardInterrupt:
            print("\nExiting DigitalHub Agent.")
            break
        except Exception as e:
            print(f"\nError executing request: {e}\n")

if __name__ == "__main__":
    run_cli()
