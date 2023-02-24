# alma-creditcardslips

A CLI application to generate and email credit card slips for Alma invoices via the Alma API.

## Development

- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`
- To run the app: `pipenv run ccslips --help`

## Required ENV Variables

- `ALMA_API_URL`: Base URL for the Alma API.
- `ALMA_API_READ_KEY`: Read-only key for the appropriate Alma instance (sandbox or prod) Acquisitions API.
- `WORKSPACE`: Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.

## Optional ENV Variables

- `ALMA_API_TIMEOUT`: Request timeout for Alma API calls. Defaults to 30 seconds if not set.
- `LOG_LEVEL`: Set to a valid Python logging level (e.g. `DEBUG`, case-insensitive) if desired. Can also be passed as an option directly to the ccslips command. Defaults to `INFO` if not set or passed to the command.
- `SENTRY_DSN`: If set to a valid Sentry DSN enables Sentry exception monitoring. This is not needed for local development.
