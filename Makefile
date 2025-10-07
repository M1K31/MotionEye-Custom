
# MotionEye Custom - Build and Development Tasks

.PHONY: all clean test install dev-install localization help

# Default target
all: localization

# Localization targets
localization: motioneye/locale/*/LC_MESSAGES/motioneye.mo motioneye/static/js/motioneye.*.json

# Development targets  
dev-install:
	pip install -e .
	pip install pytest pytest-cov black flake8 pre-commit

test:
	python -m pytest -v

test-coverage:
	python -m pytest --cov=motioneye --cov-report=html

format:
	black motioneye/ tests/

lint:
	flake8 motioneye/ tests/

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ .pytest_cache/ htmlcov/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

install:
	pip install .

# Docker targets
docker-build:
	docker build -f docker/Dockerfile -t motioneye-custom .

docker-run:
	docker run -d -p 8765:8765 --name motioneye motioneye-custom

help:
	@echo "MotionEye Custom - Available Make Targets:"
	@echo ""
	@echo "Development:"
	@echo "  dev-install    Install in development mode with dev dependencies"
	@echo "  test          Run test suite"
	@echo "  test-coverage Run tests with coverage report"
	@echo "  format        Format code with Black"
	@echo "  lint          Lint code with flake8"
	@echo "  clean         Clean build artifacts and cache files"
	@echo ""
	@echo "Installation:"
	@echo "  install       Install package"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"
	@echo ""
	@echo "Localization:"
	@echo "  localization  Build all translation files"
	@echo ""

# Localization build targets
%.mo: %.po
	msgfmt -f $*.po -o $*.mo

%/motioneye.po: motioneye/locale/motioneye.pot
	msgmerge --no-wrap -N -U $@ $<
	# Disable Google Translator usage for now, which does rarely work from GitHub CI due to rate limiting.
	# Also Weblate supports auto-translation from various sources as well.
	#l10n/traduki_po.sh $@

motioneye/static/js/motioneye.%.json: motioneye/locale/%/LC_MESSAGES/motioneye.js.po
	l10n/po2json motioneye/locale/$*/LC_MESSAGES/motioneye.js.po motioneye/static/js/motioneye.$*.json

%/motioneye.js.po: motioneye/locale/motioneye.js.pot
	msgmerge --no-wrap -N -U $@ $<
	# Disable Google Translator usage for now, which does rarely work from GitHub CI due to rate limiting.
	# Also Weblate supports auto-translation from various sources as well.
	#l10n/traduki_po.sh $@

motioneye/locale/motioneye.js.pot: motioneye/static/js/*.js l10n/*.js
	xgettext --no-wrap --from-code=UTF-8 -o motioneye/locale/motioneye.js.pot motioneye/static/js/*.js l10n/*.js

motioneye/locale/motioneye.pot: motioneye/*.py motioneye/*/*.py motioneye/templates/*.html
	pybabel extract -F l10n/babel.cfg -o motioneye/locale/motioneye.pot motioneye/
	# Remove trailing empty line to satisfy pre-commit
	sed -i '$${/^$$/d}' motioneye/locale/motioneye.pot

#####
# regulo por krei novan tradukon
# ekz. : uzi "make initro" por krei la rumana traduko.
#####
init%:
	mkdir motioneye/locale/$*
	mkdir motioneye/locale/$*/LC_MESSAGES
	msginit --no-wrap -i motioneye/locale/motioneye.js.pot -o motioneye/locale/$*.js.tmp -l$* --no-translator
	#l10n/traduki_po.sh motioneye/locale/$*.js.tmp
	mv motioneye/locale/$*.js.tmp motioneye/locale/$*/LC_MESSAGES/motioneye.js.po
	make motioneye/static/js/motioneye.$*.json
	msginit --no-wrap -i motioneye/locale/motioneye.pot -o motioneye/locale/$*.tmp -l$* --no-translator
	#l10n/traduki_po.sh motioneye/locale/$*.tmp
	mv motioneye/locale/$*.tmp motioneye/locale/$*/LC_MESSAGES/motioneye.po
	make motioneye/locale/$*/LC_MESSAGES/motioneye.mo
	#msgattrib --no-wrap --set-fuzzy --clear-obsolete locale/$*.tmp -o locale/$*/LC_MESSAGES/motioneye.po

traduki:
	find motioneye/locale -name "*.po" -exec l10n/traduki_po.sh {} \;
