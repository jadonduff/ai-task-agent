IMAGE_NAME := ai-task-agent
CONTAINER_NAME := ai-task-agent
PORT := 6573

.PHONY: build run stop clean rebuild

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --rm \
		--name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		$(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME)

clean:
	docker image rm $(IMAGE_NAME)

rebuild:
	docker build --no-cache -t $(IMAGE_NAME) .
