## Setting Scopes

In creating the first Xero access token, provide the following [scopes](https://developer.xero.com/documentation/guides/oauth2/scopes/):

* offline_access
* accounting.transactions.read
* accounting.contacts.read
* accounting.reports.read

Make sure to use the `offline_access` scope, as it is required for the `refresh_token` to be valid for 60 days.