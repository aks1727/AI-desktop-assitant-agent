import json
import platform
import urllib.request

API = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3:4b"


def get_system_info():
    """Return actual CPU, RAM and OS information."""
    cpu = "Unknown"
    with open("/proc/cpuinfo") as f:
        for line in f:
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break

    memory = {}
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith(("MemTotal:", "MemAvailable:")):
                key, value = line.split(":", 1)
                memory[key] = value.strip()

    return {
        "cpu": cpu,
        "architecture": platform.machine(),
        "os": platform.platform(),
        "ram": memory,
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get actual CPU, RAM and operating system information.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
]


def chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": TOOLS,
        "stream": False,
        "think": False,
        "options": {"temperature": 0.2},
    }

    request = urllib.request.Request(
        API,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read())


def main():
    messages = [
        {
            "role": "system",
            "content": "You are Anvaya, a concise personal assistant. Use available tools when needed. Never expose internal reasoning. Give short, direct answers.",
        },
        {
            "role": "user",
            "content": "Use get_system_info to check my actual system specifications. "
                       "Do not guess."
        }
    ]

    print("Asking Qwen3...")

    response = chat(messages)
    assistant_message = response["message"]
    tool_calls = assistant_message.get("tool_calls") or []

    if not tool_calls:
        print("No tool call was generated.")
        print("Model response:", assistant_message.get("content", ""))
        return

    messages.append(assistant_message)

    for call in tool_calls:
        name = call["function"]["name"]
        arguments = call["function"].get("arguments", {})

        if name != "get_system_info":
            raise RuntimeError(f"Blocked unknown tool: {name}")

        if arguments:
            raise RuntimeError("Unexpected arguments for this tool.")

        print(f"Executing real Python tool: {name}")
        result = get_system_info()

        messages.append({
            "role": "tool",
            "tool_name": name,
            "content": json.dumps(result),
        })

    print("\nSending tool result back to Qwen3...")
    final_response = chat(messages)

    print("\n===== AKS JARVIS RESPONSE =====\n")
    print(final_response["message"].get("content", ""))


if __name__ == "__main__":
    main()
