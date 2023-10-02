# alma-creditcardslips

A CLI application to generate and email credit card slips for Alma invoices via the Alma API.

## Description
Credit card slips are generated for items purchased with a credit card (e.g. from vendors like Amazon), which means we prepay rather than receive an invoice after shipment, which is our workflow with most vendors. The credit card slip is in lieu of a vendor-generated invoice, and is used for processing by Acquisition staff.

 The application runs daily and retrieves PO lines with:
* `status=ACTIVE`
* `acquisition_method=PURCHASE_NOLETTER` (`Credit card` in the Alma UI)
* A note that begins with `CC-`

The application is scheduled to run each day as an Elastic Container Service (ECS) task. By default, it retrieves PO lines from 2 days before the date the application is run. Originally, it was set for 1 day before the application is run but a bug was discovered in August 2023 that required a change to 2 days before in order to get the expected output. 

The application fills in a template with the PO line data and the resulting file is emailed as an attachment to the necessary stakeholders. Acquisitions staff print out the attachment, mark it up, and complete recording the payment in Alma. 

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
- `SES_RECIPIENT_EMAIL`: Email address(es) for recipient(s) who should receive the credit card slips email. Multiple email addresses should be separated by a space, e.g. `SES_RECIPIENT_EMAIL=recipient1@example.com recipient2@example.com`. This value can either be set in ENV or passed directly to the command line as an option.
- `SES_SEND_FROM_EMAIL`: Verified email address for sending emails via SES. This value can either be set in ENV or passed directly to the command as an option.
