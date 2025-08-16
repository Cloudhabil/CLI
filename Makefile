.PHONY: run ideas docs

run:
	python3 loop_agent.py

# Auto-approve first mission (demo)
ideas:
	echo "y" | python3 loop_agent.py

# Quick doc demo (approve, title, body)
docs:
	echo -e "y\ncloudhabil_cli_overview\nThis is an auto-doc.\n" | python3 loop_agent.py
