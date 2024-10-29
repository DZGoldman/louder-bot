install:
	pip install -r requirements.txt

run-headless:
	python main.py --headless True

run:
	python main.py

test-email-auth:
	python email_client.py