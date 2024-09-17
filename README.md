# alma-creditcardslips

A CLI application to generate and email credit card slips for Alma invoices via the Alma API.

Credit card slips are generated for items purchased with a credit card (e.g. from vendors like Amazon), which means we prepay rather than receive an invoice after shipment, which is our workflow with most vendors. The credit card slip is in lieu of a vendor-generated invoice and is used for processing by Acquisition staff.

The app retrieves purchase order (PO) lines from the Alma REST API with the following criteria:
* `status=ACTIVE`
* `acquisition_method=PURCHASE_NOLETTER` (`Credit card` in the Alma UI)
* A note that begins with `CC-`

**Note:** By default, it retrieves PO lines from two (2) days before the date the application is run. Originally, it was set for one (1) day before the application is run, but a bug was discovered in August 2023 that required the change in order to get the expected output. 

Data is extracted from the PO lines and used to fill in a template, and the resulting file is emailed as an attachment to the necessary stakeholders. Acquisitions staff print out the attachment, mark it up, and complete recording the payment in Alma. 

This Python CLI application is run on a schedule as an Elastic Container Service (ECS) task in AWS via EventBridge rules. 

## Development

- To preview a list of available Makefile commands: `make help`
- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`
- To run the app: `pipenv run ccslips --help`

## Environment Variables

### Required

```shell
ALMA_API_URL=### Base URL for the Alma API.
ALMA_API_READ_KEY=### Read-only key for the appropriate Alma instance (sandbox or prod) Acquisitions API.
SENTRY_DSN=### If set to a valid Sentry DSN enables Sentry exception monitoring. This is not needed for local development.
WORKSPACE=### Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.
```

### Optional

```shell
ALMA_API_TIMEOUT=### Request timeout for Alma API calls. Defaults to 30 seconds.
SES_RECIPIENT_EMAIL=### Email addresses for recipients of the the credit card slips email. Multiple email addresses should be separated by a space, e.g. 'recipient1@example.com recipient2@example.com'. This value can also be passed directly to the CLI command via the -r/--recipient-email option.
SES_SEND_FROM_EMAIL=### Verified email address for sending emails via SES. This value can also be passed directly to the CLI command via the -s/--source-email option.
```
