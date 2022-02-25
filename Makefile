Pipfile.lock: Pipfile setup.py
	$(eval CID := $(shell docker run -dit --rm python:3.9))
	docker exec $(CID) mkdir /app
	docker cp Pipfile $(CID):app/Pipfile
	docker cp setup.py $(CID):app/setup.py
	docker exec $(CID) pip install pipenv
	docker exec -e PIPENV_PIPFILE=/app/Pipfile $(CID) pipenv lock --dev
	docker cp $(CID):app/Pipfile.lock Pipfile.lock
	docker stop $(CID)
