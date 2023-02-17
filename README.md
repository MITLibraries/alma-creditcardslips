# alma-creditcardslips

A CLI application to generate and email credit card slips for Alma invoices via the Alma API.

## Development

- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`
- To run the app: `pipenv run ccslips --help`

## ENV Variables

- `LOG_LEVEL` = Optional, set to a valid Python logging level (e.g. `DEBUG`, case-insensitive) if desired. Can also be passed as an option directly to the ccslips command. Defaults to `INFO` if not set or passed to the command.
- `SENTRY_DSN` = If set to a valid Sentry DSN, enables Sentry exception monitoring. This is not needed for local development.
- `WORKSPACE` = Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.
