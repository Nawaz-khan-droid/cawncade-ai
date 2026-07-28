import json

transcript_path = r'C:\Users\ks919\.gemini\antigravity\brain\71ce5e4c-66e4-4166-91e9-e5a2107447d6\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get('type') == 'USER_INPUT':
                content = data.get('content', '')
                print("--- USER INPUT ---")
                print(content.encode('ascii', 'ignore').decode('ascii'))
        except json.JSONDecodeError:
            pass
