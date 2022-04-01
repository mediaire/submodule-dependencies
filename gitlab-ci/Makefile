.DEFAULT_GOAL := update_common_library

venv:
	python3 -m venv venv
	. venv/bin/activate && pip3 install -r requirements.txt

.PHONY: update_common_library
update_common_library: venv
	. venv/bin/activate && python3 -m automations.update_common_library_config
