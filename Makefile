.PHONY: install
install:
	poetry install

.PHONY: run
run:
	poetry run tidal-top7 --artists-file artists.txt --playlist-name "Top 7 de mis bandas favoritas"