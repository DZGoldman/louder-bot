install:
	pip install -r requirements.txt

run:
	python main.py

test-email-auth:
	python email_client.py