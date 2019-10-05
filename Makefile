all: autograder.zip

.PHONY: autograder.zip

autograder.zip:
	zip -r autograder.zip ssh run_autograder setup.sh scripts/
