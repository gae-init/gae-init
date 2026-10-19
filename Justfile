# determine standard shell used to run commands,
# in this case `bash` supports `source` (used in `dbg` target)
set shell := ["bash", "-uc"]

# loading environment variables from `.env` file
# (to keep API Key details out of source code control)
set dotenv-load := true

# default settings if not present in .env
project_id := env("PROJECT_ID", "gae-init")
auth_domain := env("AUTH_DOMAIN", "google.com")
host := env("SERVER_NAME", "127.0.0.1")
port := env("SERVER_PORT", "8080")
redis_config := env("REDIS_CONFIG", "")
dc_host := replace_regex(redis_config, '^([^:]*):([^:]*):([^:]*):([^:]*)$', '$1')
dc_port := replace_regex(redis_config, '^([^:]*):([^:]*):([^:]*):([^:]*)$', '$2')
dc_db := replace_regex(redis_config, '^([^:]*):([^:]*):([^:]*):([^:]*)$', '$3')
dc_auth := replace_regex(redis_config, '^([^:]*):([^:]*):([^:]*):([^:]*)$', '$4')
ds_host := env("DEV_DATASTORE_HOST", "127.0.0.1")
ds_port := env("DEV_DATASTORE_PORT", "8081")
ds_data_dir := absolute_path(env("DEV_DATASTORE_DIR", "./ds-data/"))

# export settings for further use (based on .env or above defaults)
export PROJECT_ID := f"{{project_id}}"
export AUTH_DOMAIN := f"{{auth_domain}}"
export REDIS_CONFIG := f"{{redis_config}}"
export DATASTORE_EMULATOR_HOST := f"{{ds_host}}:{{ds_port}}"
export DATASTORE_DATASET := f"{{project_id}}"
export DATASTORE_PROJECT_ID := f"{{project_id}}"
export FLASK_APP := "main/main.py"
export FLASK_ENV := "development"
export FLASK_DEBUG := "1"
export GOOGLE_CLOUD_PROJECT := f"{{project_id}}"
export HTTP_HOST := f"{{host}}:{{port}}"
export SERVER_NAME := f"{{host}}"
export SERVER_PORT := f"{{port}}"

# define variables for JS bundles
ext_js := "\
node_modules/dayjs/dayjs.min.js \
node_modules/dayjs/plugin/utc.js \
node_modules/dayjs/plugin/relativeTime.js \
node_modules/dayjs/plugin/advancedFormat.js \
node_modules/bootstrap/dist/js/bootstrap.bundle.min.js"
app_js := "\
main/static/src/script/common/util.js \
main/static/src/script/common/api.js \
main/static/src/script/site/*.js"

# show the just commands available
default:
	@just --list

# security audit
audit:
	uv run pip-audit

# build for production
build: _build-min

# build for development/testing
build-dev: yarn _copy-ext-fonts
	# build-ext-dev:
	mkdir -p main/static/dev/script
	cat {{ext_js}} > main/static/dev/script/ext.js
	# build-script-dev:
	mkdir -p main/static/dev/script
	cat {{app_js}} > main/static/dev/script/script.js
	# build-style-dev:
	mkdir -p main/static/dev/style
	node_modules/.bin/sass --quiet-deps --load-path=node_modules --silence-deprecation=import main/static/src/style/style.scss main/static/dev/style/style.css

# build minified (production like) for development/testing
build-dev-min: yarn _copy-ext-fonts
	# build-ext-dev-min:
	mkdir -p main/static/dev/script
	cat {{ext_js}} | node_modules/.bin/esbuild --minify > main/static/dev/script/ext.js
	# build-script-dev-min:
	mkdir -p main/static/dev/script
	cat {{app_js}} | node_modules/.bin/esbuild --minify > main/static/dev/script/script.js
	# build-style-dev-min:
	mkdir -p main/static/dev/style
	node_modules/.bin/sass --quiet-deps --load-path=node_modules --silence-deprecation=import main/static/src/style/style.scss | node_modules/.bin/esbuild --loader=css --minify > main/static/dev/style/style.css

_build-min: yarn _copy-ext-fonts
	# build-ext-min:
	mkdir -p main/static/min/script
	cat {{ext_js}} | node_modules/.bin/esbuild --minify > main/static/min/script/ext.js
	# build-script-min:
	mkdir -p main/static/min/script
	cat {{app_js}} | node_modules/.bin/esbuild --minify > main/static/min/script/script.js
	# build-style-min:
	mkdir -p main/static/min/style
	node_modules/.bin/sass --quiet-deps --load-path=node_modules --silence-deprecation=import main/static/src/style/style.scss | node_modules/.bin/esbuild --loader=css --minify > main/static/min/style/style.css

# remove basic artifacts
_clean-base:
	# remove all __pycache__ folders
	find . -type d -name "__pycache__" -exec rm -r {} +
	# remove all .ruff_cache folders
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	# remove all .pyc and .pyo files
	find . -type f -name "*.pyc" -exec rm -f {} +
	find . -type f -name "*.pyo" -exec rm -f {} +
	# remove specific caches
	rm -rf .pytest_cache/

# remove build artifacts (development, minified and external)
clean-build: _clean-base
	rm -rf main/static/dev/
	rm -rf main/static/min/
	rm -rf main/static/ext/

# remove virtual environment
_clean-venv:
	rm -rf .venv/

# remove all artifacts
clean-all: _clean-base clean-build _clean-venv dc-clean
	# remove the node/bower artifacts
	rm -rf node_modules/

_copy-ext-fonts:
	# copy-ext-font-awesome:
	mkdir -p main/static/ext/font-awesome/fonts
	cp node_modules/font-awesome/fonts/* main/static/ext/font-awesome/fonts/ || true

# deploy to Google App Engine
deploy: clean-build build export-reqs
	# NOTE: need the "beta" part for the Direct VPC Egress (as that is in preview)
	#       otherwise those network settings could be stripped from app.yaml
	gcloud beta app deploy main/app.yaml --no-promote

# deploy Datastore indexes to Google App Engine
deploy-index:
	gcloud app deploy main/index.yaml

# deploy Task Queues to Google App Engine
deploy-queue:
	gcloud app deploy main/queue.yaml

# start local development Flask server
dev: build-dev
	echo {{redis_config}}
	@if ! nc -z {{ds_host}} {{ds_port}}; then echo "Datastore emulator is not running on {{ds_host}}:{{ds_port}}" && exit 1; fi
	uv run flask run -p {{port}}

# start local development Gunicorn server with minimized assets
dev-min: build-dev-min
	@if ! nc -z {{ds_host}} {{ds_port}}; then echo "Datastore emulator is not running on {{ds_host}}:{{ds_port}}" && exit 1; fi
	uv run gunicorn --chdir main -c main/gunicorn.conf.py -b {{host}}:{{port}} main:app

# start local redis in docker
dc-start:
	#!/usr/bin/env bash
	set -euo pipefail
	if nc -z {{dc_host}} {{dc_port}}; then
		echo "Local redis is already running on {{dc_host}}:{{dc_port}}"
	else
		docker start redis-dev 2>/dev/null || docker run -d \
			--name redis-dev -p {{dc_port}}:{{dc_port}} redis:7.2 \
			redis-server --maxmemory 10mb --maxmemory-policy allkeys-lru
	fi

# connect to local redis with redis-cli
dc-cli:
	#!/usr/bin/env bash
	set -euo pipefail
	if ! nc -z {{dc_host}} {{dc_port}}; then
		echo "Local redis is not running on {{dc_host}}:{{dc_port}}"
		exit 1
	fi
	docker exec -it redis-dev redis-cli

# stop local redis in docker
dc-stop:
	docker stop redis-dev 2>/dev/null || true

# remove local redis in docker
dc-clean: dc-stop
	docker rm redis-dev 2>/dev/null || true

# start datastore emulator (can import data, or set ds_import_dir=none for a clean datastore)
ds-start ds_import_dir=ds_data_dir:
	#!/usr/bin/env bash
	set -euo pipefail
	if nc -z {{ds_host}} {{ds_port}}; then
		echo "Datastore emulator is already running on {{ds_host}}:{{ds_port}}" && exit 1
	fi
	TARGET="{{ds_import_dir}}"
	IMPORT_FLAG=""
	if [ "$TARGET" != "new" ] && [ -n "$TARGET" ]; then
		if [ -d "$TARGET" ]; then
			METADATA_FILE=$(find "$TARGET" -maxdepth 2 -name "*.overall_export_metadata" | sort -r | head -n 1)
			if [ -z "$METADATA_FILE" ]; then
				echo "Error: No .overall_export_metadata file found in '$TARGET'" >&2
				echo "Consider starting a new datastore using: just ds-start new"
				echo "or import another (exported) datastore:  just ds-start ./datastore-export/"
				exit 1
			fi
		elif [ -f "$TARGET" ]; then
			METADATA_FILE="$TARGET"
		else
			echo "Error: Import target does not exist: $TARGET" >&2
			exit 1
		fi
		echo "Starting Firestore Emulator (in Datastore mode) with $METADATA_FILE..."
		IMPORT_FLAG="--import-data=$METADATA_FILE"
	else
		echo "Starting fresh Firestore Emulator (in Datastore mode)..."
	fi
	gcloud emulators firestore start \
		--database-mode=datastore-mode \
		--host-port="{{ds_host}}:{{ds_port}}" \
		$IMPORT_FLAG

# export current datastore state
ds-save:
	#!/usr/bin/env bash
	set -euo pipefail
	if ! nc -z {{ds_host}} {{ds_port}}; then
		echo "Error: Datastore emulator is not running on {{ds_host}}:{{ds_port}}" >&2
		exit 1
	fi
	TMP_DIR=$(mktemp -d -t ds-export-XXXXXX)
	trap 'rm -rf "$TMP_DIR"' EXIT

	echo "Exporting data from {{ds_host}}:{{ds_port}} to {{ds_data_dir}}..."
	HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://{{ds_host}}:{{ds_port}}/emulator/v1/projects/{{project_id}}:export" \
		-H "Content-Type: application/json" \
		-d "{\"database\": \"projects/{{project_id}}/databases/\", \"export_directory\": \"$TMP_DIR\"}")

	if [ "$HTTP_CODE" -ne 200 ]; then
		echo "Error: Datastore export failed with HTTP $HTTP_CODE" >&2
		exit 1
	fi

	DS_EXPORT_DIR=$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d -name "datastore_export_*" | head -n 1)
	if [ -z "$DS_EXPORT_DIR" ] || [ ! -d "$DS_EXPORT_DIR" ]; then
		echo "Error: No export directory created in $TMP_DIR" >&2
		exit 1
	fi

	mkdir -p "{{ds_data_dir}}"
	rm -rf "{{ds_data_dir}}"/*
	mv "$DS_EXPORT_DIR"/* "{{ds_data_dir}}/"
	echo "Data saved to {{ds_data_dir}}"

# shut down the datastore emulator
ds-shutdown:
	@echo "Shutting down emulator..."
	@curl -s -f -X POST "http://{{ds_host}}:{{ds_port}}/shutdown"
	@echo "Server terminated."

# export current datastore state and shut down the emulator
ds-stop: ds-save ds-shutdown

# generate requirements.txt from pyproject.toml for deployment
export-reqs:
	uv pip compile pyproject.toml -o main/requirements.txt

# format code
fix:
	uv run ruff format .
	# fix-assets:
	node_modules/.bin/prettier --write "**/*.{js,json,scss,md,yml,yaml}"
	# fix-code:
	node_modules/.bin/eslint --fix .

# install dependencies
install:
	yarn install
	uv lock --upgrade
	uv sync --all-extras --no-install-project --frozen

# lint and check code
lint: _lint-assets _lint-code
	uv run ruff check .
	uv run ty check .

_lint-assets:
	node_modules/.bin/prettier --check "**/*.{js,json,scss,md,yml,yaml}"

_lint-code:
	node_modules/.bin/eslint .

# check for newer dependency versions
outdated:
	yarn outdated || true
	uv tree --outdated | grep -v '^[│ ]' | sed $'s/.*(latest:.*/\033[1;33m&\033[0m/' || true

# quick smoke test
test:
	uv run python -m unittest discover -s tests -p "*.py"

# sync node and JS dependencies 
yarn:
	yarn
