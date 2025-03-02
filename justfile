export COMPOSE_FILE := "docker-compose.local.yml"
# Note that if you are running these commands without just, you will need to run the above command
# in your terminal before running any of the commands below, or add "-f docker-compose.local.yml" to
# the docker compose commands after the word "compose".

# List all available commands
default:
    @just --list

# Build python image
[group("compose")]
build:
    @echo "Building python image..."
    @docker compose build

# Start up containers
[group("compose")]
up:
    @echo "Starting up containers..."
    @docker compose up -d --remove-orphans

# Stop containers
[group("compose")]
down:
    @echo "Stopping containers..."
    @docker compose down

# Remove containers and their volumes
[group("compose")]
prune *args:
    @echo "Killing containers and removing volumes..."
    @docker compose down -v {{ args }}

# View container logs
[group("compose"), group("docker")]
logs *args:
    @docker compose logs -f {{ args }}

# Lint staged changes
[group("docker"), group("testing")]
lint *args:
    @docker compose exec django pre-commit run {{ args }}

# Run a command in the Django container
[group("docker")]
run +cmd:
    @docker compose exec django {{ cmd }}

# Open a shell in the Django container
[group("docker")]
shell:
    @docker compose run --rm django bash

# Executes `manage.py` command
[group("management")]
manage +args:
    @docker compose run --rm django python ./manage.py {{ args }}

# Make and apply database migrations
[group("management")]
migrate: (manage "makemigrations") (manage "migrate")

# Load initial data into the database
[group("management")]
loaddata +filename="initial.json": (manage "loaddata" filename)

# Create a superuser account
[group("management")]
createsuperuser: (manage "createsuperuser")

# Open a Python shell in the Django container
[group("management")]
pyshell: (manage "shell_plus")

# Run tests.
[group("testing")]
test:
    @docker compose run --rm django pytest

# Run tests and open coverage report
[group("testing")]
coverage:
    -docker compose run --rm django coverage run -m pytest
    @docker compose exec django coverage html
    @open ./htmlcov/index.html

# Run type checks
[group("testing")]
typecheck:
    @docker compose exec django mypy democrasite
