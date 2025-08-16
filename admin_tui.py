import os
import requests
from rich.prompt import Prompt
from kb import last, search, add_entry
from orchestrator import check_ceo

BUS_URL = os.environ.get('BUS_URL', 'http://127.0.0.1:7088')


def publish(target: str, text: str):
    requests.post(f"{BUS_URL}/publish", json={'topic': target, 'sender': 'ADMIN', 'text': text}, timeout=5)


def main():
    while True:
        cmd = Prompt.ask('admin')
        if cmd.startswith('chat'):
            _, rest = cmd.split(' ', 1)
            agent, msg = rest.split('::', 1)
            publish(agent.strip().upper(), msg.strip())
        elif cmd.startswith('check'):
            _, rest = cmd.split(' ', 1)
            agent, msg = rest.split('::', 1)
            if agent.strip().upper() == 'CEO':
                verdict = check_ceo(msg.strip())
                print(verdict)
        elif cmd.startswith('kb last'):
            parts = cmd.split('::')
            n = int(parts[1]) if len(parts) > 1 else 5
            for row in last(n):
                print(row)
        elif cmd.startswith('kb search'):
            q = cmd.split('::', 1)[1].strip()
            for row in search(q):
                print(row)
        elif cmd.startswith('kb memo'):
            topic, text = cmd.split('::', 1)[1].split('||', 1)
            add_entry('memo', topic.strip(), text.strip())
        else:
            print('unknown command')


if __name__ == '__main__':
    main()
