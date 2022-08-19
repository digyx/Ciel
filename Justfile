test:
	- pdm run pytest --cov
	rm data/ciel.db

lint:
    pdm run black .
