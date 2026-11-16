from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=500,
    messages=[
        {"role": "user", "content": "Halo Claude! Jelasin dalam 1 kalimat kamu itu apa."}
    ],
)

print(message.content[0].text)