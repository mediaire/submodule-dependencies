.DEFAULT_GOAL := run

IMAGE_NAME = mediaire-submodule-demo:latest

.PHONY: init
init:
	git submodule init
	git submodule update

.PHONY: build
build: init
	docker build -t $(IMAGE_NAME) . 

.PHONY: run
run: build
	docker run $(IMAGE_NAME)
