python manage.py spectacular --format openapi-json --file schema.json
cd democrasite-frontend
rm -r lib/auto
openapi-generator-cli generate -g typescript-fetch -i ../schema.json -o lib/auto
pre-commit run --all-files
