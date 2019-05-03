IMAGE_SPEC = berkeleydsep/fetch-course-emails
VERSION = $(shell git rev-parse --short HEAD)


build:
	docker build -t $(IMAGE_SPEC):$(VERSION) .

push:
	docker push $(IMAGE_SPEC):$(VERSION)
