poetry.lock: pyproject.toml
	$(eval CID := $(shell docker run -dit --rm python:3.9))
	docker exec $(CID) mkdir /app
	docker cp pyproject.toml $(CID):app/pyproject.toml
	docker cp poetry.lock $(CID):app/poetry.lock
	docker exec $(CID) pip install poetry
	docker exec -w /app $(CID) poetry lock
	docker cp $(CID):app/poetry.lock poetry.lock
	docker stop $(CID)
