all: check_dependencies unit functional integration

filename=unclebob-`python -c 'import unclebob;print unclebob.version'`.tar.gz

export UNCLEBOB_DEPENDENCIES:= nose django south sure
export DJANGO_SETTINGS_MODULE:= djangounclebob.settings

check_dependencies:
	@echo "Checking for dependencies to run tests ..."
	@rm -f .coverage
	@for dependency in `echo $$UNCLEBOB_DEPENDENCIES`; do \
		python -c "import $$dependency" 2>/dev/null || (echo "You must install $$dependency in order to run unclebob's tests" && exit 3) ; \
		done

unit: clean
	@echo "Running unit tests ..."
	@python manage.py test --unit
	@nosetests -s --verbosity=2 --with-coverage --cover-inclusive tests/unit --cover-package=unclebob

functional: clean
	@echo "Running functional tests ..."
	@python manage.py test --functional
	@nosetests -s --verbosity=2 --cover-erase tests/functional

integration: clean
	@echo "Running integration tests ..."
	@python manage.py test --integration
	@nosetests -s --verbosity=2 --cover-erase tests/integration

clean:
	@printf "Cleaning up files that are already in .gitignore... "
	@for pattern in `cat .gitignore`; do find . -name "$$pattern" -delete; done
	@echo "OK!"

release: clean unit functional integration
	@make clean
	@printf "Exporting to $(filename)... "
	@tar czf $(filename) unclebob setup.py README.md
	@echo "DONE!"
