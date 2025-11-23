**API formatting for Column Creation**



**Calculated Columns**



To add calculated columns to Dataverse tables using the API or CLI, you can follow these steps:



1\. Using the Dataverse Web API

You can create a calculated column by defining its properties and formula through the Web API. Here's a high-level overview:





Define the Column:



Use the POST method to create a new column in the desired table.

Specify the column type as Calculated in the request payload.







Set the Formula:



Include the calculated property in the payload, where you define the formula using Power FX expressions.



Example Request:

JsonPOST \[DataverseInstanceURL]/api/data/v9.2/EntityDefinitions(LogicalName='your\_table')/Attributes

{

&nbsp;   "AttributeType": "Calculated",

&nbsp;   "LogicalName": "new\_calculatedcolumn",

&nbsp;   "DisplayName": {

&nbsp;       "LocalizedLabels": \[

&nbsp;           {

&nbsp;               "Label": "Calculated Column",

&nbsp;               "LanguageCode": 1033

&nbsp;           }

&nbsp;       ]

&nbsp;   },

&nbsp;   "Description": {

&nbsp;       "LocalizedLabels": \[

&nbsp;           {

&nbsp;               "Label": "This is a calculated column",

&nbsp;               "LanguageCode": 1033

&nbsp;           }

&nbsp;       ]

&nbsp;   },

&nbsp;   "FormulaDefinition": "your\_formula\_here"

}



Replace your\_formula\_here with the Power FX formula you want to use.





Publish Changes:



After creating the column, publish the table to make the changes live.





**Rollup Columns**





Copilot Search Branding



To add rollup columns to Dataverse tables via API or CLI, you can use the Dataverse Web API or Power Platform CLI. Here's a concise guide for both approaches:



1\. Using Dataverse Web API

You can create rollup columns by sending a POST request to the Dataverse Web API. Here's how:



Steps:

Authenticate: Obtain an access token using Azure AD for your Dataverse environment.

Define the Rollup Column:

Use the EntityMetadata and AttributeMetadata endpoints.

Specify the rollup column's properties, such as SourceEntity, SourceAttribute, AggregationType (e.g., Sum, Avg, Min, Max), and FilterCriteria.

Example Request:

Json



Copy code

POST https://<your-environment>.api.crm.dynamics.com/api/data/v9.2/EntityDefinitions(LogicalName='your\_table')/Attributes

Content-Type: application/json

Authorization: Bearer <access\_token>



{

&nbsp; "@odata.type": "Microsoft.Dynamics.CRM.RollupAttributeMetadata",

&nbsp; "LogicalName": "new\_rollupcolumn",

&nbsp; "DisplayName": {

&nbsp;   "LocalizedLabels": \[

&nbsp;     {

&nbsp;       "Label": "Total Sales",

&nbsp;       "LanguageCode": 1033

&nbsp;     }

&nbsp;   ]

&nbsp; },

&nbsp; "SourceEntity": "sales",

&nbsp; "SourceAttribute": "amount",

&nbsp; "AggregationType": "Sum",

&nbsp; "FilterCriteria": "<filter XML here>"

}

Publish Customizations: After creating the column, publish the changes using the PublishAllXml endpoint.





