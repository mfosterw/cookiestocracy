python manage.py spectacular --format openapi-json --file schema.json
cd democrasite-frontend
rm -r lib/auto
openapi-generator-cli generate -i ../schema.json -g typescript-fetch -o lib/auto
pre-commit run --all-files
