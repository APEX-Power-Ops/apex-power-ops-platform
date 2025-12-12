import { queryMetadata } from "../utils/dataverse-client.js";

/**
 * API Documentation result interface
 */
export interface APIDocResult {
  format: string;
  version: string;
  spec: any;
  endpoints: number;
  generatedAt: string;
}

/**
 * Generate API documentation from Dataverse schema
 */
export async function generateAPIDocumentation(params: {
  format?: "openapi" | "markdown";
  includeExamples?: boolean;
}): Promise<APIDocResult> {
  const { format = "openapi", includeExamples = true } = params;

  console.error("Generating API documentation...");

  try {
    // Get all custom tables
    const tables = await getAllCustomTables();

    // Generate OpenAPI spec
    const spec = await generateOpenAPISpec(tables, includeExamples);

    // Count endpoints (CRUD operations per table)
    const endpoints = tables.length * 5; // GET, GET/:id, POST, PATCH, DELETE per table

    return {
      format,
      version: "3.0.0",
      spec,
      endpoints,
      generatedAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error("Error generating API docs:", error.message);
    throw new Error(`Failed to generate API docs: ${error.message}`);
  }
}

/**
 * Get all custom tables
 */
async function getAllCustomTables(): Promise<any[]> {
  try {
    const result = await queryMetadata(
      "EntityDefinitions?$select=LogicalName,DisplayName,PrimaryIdAttribute,Description&$filter=startswith(LogicalName, 'cr950_')"
    );

    return result.value || [];
  } catch (error: any) {
    console.error("Error getting custom tables:", error.message);
    return [];
  }
}

/**
 * Generate OpenAPI 3.0 specification
 */
async function generateOpenAPISpec(
  tables: any[],
  includeExamples: boolean
): Promise<any> {
  const spec: any = {
    openapi: "3.0.0",
    info: {
      title: "RESA Power Project Tracker API",
      description:
        "REST API for the RESA Power Project Tracker Dataverse solution. This API provides access to all project management entities including Projects, Scopes, Tasks, Apparatus, and Revenue tracking.",
      version: "1.0.0",
      contact: {
        name: "RESA Power Development Team",
        email: "dev@resapower.com",
      },
    },
    servers: [
      {
        url: "https://org99cd6c6e.crm.dynamics.com/api/data/v9.2",
        description: "Development Environment",
      },
    ],
    security: [
      {
        oauth2: [],
      },
    ],
    paths: {},
    components: {
      securitySchemes: {
        oauth2: {
          type: "oauth2",
          flows: {
            authorizationCode: {
              authorizationUrl:
                "https://login.microsoftonline.com/270d5723-4b30-4f3b-b9cb-6527be741b42/oauth2/v2.0/authorize",
              tokenUrl:
                "https://login.microsoftonline.com/270d5723-4b30-4f3b-b9cb-6527be741b42/oauth2/v2.0/token",
              scopes: {
                "https://org99cd6c6e.crm.dynamics.com/.default":
                  "Access Dataverse as user",
              },
            },
          },
        },
      },
      schemas: {},
    },
  };

  // Generate paths and schemas for each table
  for (const table of tables) {
    await addTableToSpec(spec, table, includeExamples);
  }

  return spec;
}

/**
 * Add table endpoints and schema to OpenAPI spec
 */
async function addTableToSpec(
  spec: any,
  table: any,
  includeExamples: boolean
): Promise<void> {
  const logicalName = table.LogicalName;
  const displayName =
    table.DisplayName?.UserLocalizedLabel?.Label || logicalName;
  const pluralName = `${logicalName}s`; // Simple pluralization
  const primaryKey = table.PrimaryIdAttribute || `${logicalName}id`;

  // Get field metadata for schema
  const fields = await getTableFields(logicalName);

  // Create schema definition
  spec.components.schemas[displayName] = createSchema(
    table,
    fields,
    includeExamples
  );

  // Add collection endpoint (GET /tables)
  spec.paths[`/${pluralName}`] = {
    get: {
      summary: `List ${displayName} records`,
      description: `Retrieve a list of ${displayName} records with optional filtering, sorting, and pagination.`,
      tags: [displayName],
      parameters: [
        {
          name: "$select",
          in: "query",
          description: "Comma-separated list of fields to include",
          schema: { type: "string" },
          example: `${logicalName}_name,${logicalName}_status`,
        },
        {
          name: "$filter",
          in: "query",
          description: "OData filter expression",
          schema: { type: "string" },
          example: "statecode eq 0",
        },
        {
          name: "$top",
          in: "query",
          description: "Maximum number of records to return",
          schema: { type: "integer", default: 50 },
        },
        {
          name: "$orderby",
          in: "query",
          description: "Sort expression",
          schema: { type: "string" },
          example: `${logicalName}_name asc`,
        },
      ],
      responses: {
        "200": {
          description: "Success",
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  value: {
                    type: "array",
                    items: {
                      $ref: `#/components/schemas/${displayName}`,
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    post: {
      summary: `Create ${displayName} record`,
      description: `Create a new ${displayName} record.`,
      tags: [displayName],
      requestBody: {
        required: true,
        content: {
          "application/json": {
            schema: {
              $ref: `#/components/schemas/${displayName}`,
            },
          },
        },
      },
      responses: {
        "201": {
          description: "Created",
          headers: {
            "OData-EntityId": {
              description: "URL of the created record",
              schema: { type: "string" },
            },
          },
        },
      },
    },
  };

  // Add single record endpoint (GET/PATCH/DELETE /tables/:id)
  spec.paths[`/${pluralName}({id})`] = {
    get: {
      summary: `Get ${displayName} record`,
      description: `Retrieve a single ${displayName} record by ID.`,
      tags: [displayName],
      parameters: [
        {
          name: "id",
          in: "path",
          required: true,
          description: "Record ID (GUID)",
          schema: { type: "string", format: "uuid" },
        },
        {
          name: "$select",
          in: "query",
          description: "Comma-separated list of fields to include",
          schema: { type: "string" },
        },
      ],
      responses: {
        "200": {
          description: "Success",
          content: {
            "application/json": {
              schema: {
                $ref: `#/components/schemas/${displayName}`,
              },
            },
          },
        },
        "404": {
          description: "Record not found",
        },
      },
    },
    patch: {
      summary: `Update ${displayName} record`,
      description: `Update an existing ${displayName} record.`,
      tags: [displayName],
      parameters: [
        {
          name: "id",
          in: "path",
          required: true,
          description: "Record ID (GUID)",
          schema: { type: "string", format: "uuid" },
        },
      ],
      requestBody: {
        required: true,
        content: {
          "application/json": {
            schema: {
              $ref: `#/components/schemas/${displayName}`,
            },
          },
        },
      },
      responses: {
        "204": {
          description: "No Content - Update successful",
        },
        "404": {
          description: "Record not found",
        },
      },
    },
    delete: {
      summary: `Delete ${displayName} record`,
      description: `Delete a ${displayName} record.`,
      tags: [displayName],
      parameters: [
        {
          name: "id",
          in: "path",
          required: true,
          description: "Record ID (GUID)",
          schema: { type: "string", format: "uuid" },
        },
      ],
      responses: {
        "204": {
          description: "No Content - Delete successful",
        },
        "404": {
          description: "Record not found",
        },
      },
    },
  };
}

/**
 * Get table fields for schema generation
 */
async function getTableFields(tableName: string): Promise<any[]> {
  try {
    const result = await queryMetadata(
      `EntityDefinitions(LogicalName='${tableName}')/Attributes?$select=LogicalName,DisplayName,AttributeType,RequiredLevel,MaxLength,Description`
    );

    return result.value || [];
  } catch (error: any) {
    console.error(`Error getting fields for ${tableName}:`, error.message);
    return [];
  }
}

/**
 * Create JSON schema for a table
 */
function createSchema(table: any, fields: any[], includeExamples: boolean): any {
  const schema: any = {
    type: "object",
    description:
      table.Description?.UserLocalizedLabel?.Label ||
      `${table.DisplayName?.UserLocalizedLabel?.Label || table.LogicalName} entity`,
    properties: {},
    required: [],
  };

  // Add fields to schema
  for (const field of fields) {
    const logicalName = field.LogicalName;
    const attributeType = field.AttributeType;
    const isRequired =
      field.RequiredLevel?.Value === "ApplicationRequired" ||
      field.RequiredLevel?.Value === "SystemRequired";

    // Map Dataverse type to JSON Schema type
    const fieldSchema = mapAttributeTypeToSchema(field);

    schema.properties[logicalName] = fieldSchema;

    if (isRequired && !logicalName.startsWith("_")) {
      schema.required.push(logicalName);
    }
  }

  // Add example if requested
  if (includeExamples) {
    schema.example = generateExample(table, fields);
  }

  return schema;
}

/**
 * Map Dataverse attribute type to JSON Schema type
 */
function mapAttributeTypeToSchema(field: any): any {
  const typeMap: { [key: string]: any } = {
    String: { type: "string", maxLength: field.MaxLength },
    Memo: { type: "string", maxLength: field.MaxLength },
    Integer: { type: "integer" },
    Decimal: { type: "number", format: "decimal" },
    Money: { type: "number", format: "currency" },
    DateTime: { type: "string", format: "date-time" },
    Boolean: { type: "boolean" },
    Lookup: { type: "string", format: "uuid", description: "Lookup (GUID)" },
    Picklist: { type: "integer", description: "Choice value" },
    MultiSelectPicklist: { type: "string", description: "Comma-separated choice values" },
    Owner: { type: "string", format: "uuid", description: "Owner (GUID)" },
    Customer: { type: "string", format: "uuid", description: "Customer (GUID)" },
    Uniqueidentifier: { type: "string", format: "uuid" },
  };

  const schema = typeMap[field.AttributeType] || { type: "string" };

  // Add description
  schema.description =
    field.Description?.UserLocalizedLabel?.Label ||
    field.DisplayName?.UserLocalizedLabel?.Label ||
    field.LogicalName;

  return schema;
}

/**
 * Generate example data for a schema
 */
function generateExample(table: any, fields: any[]): any {
  const example: any = {};

  for (const field of fields.slice(0, 5)) {
    // Limit to first 5 fields for cleaner examples
    const logicalName = field.LogicalName;
    const attributeType = field.AttributeType;

    // Generate example value based on type
    switch (attributeType) {
      case "String":
      case "Memo":
        example[logicalName] = `Example ${field.DisplayName?.UserLocalizedLabel?.Label || logicalName}`;
        break;
      case "Integer":
        example[logicalName] = 42;
        break;
      case "Decimal":
      case "Money":
        example[logicalName] = 99.99;
        break;
      case "DateTime":
        example[logicalName] = "2025-11-23T12:00:00Z";
        break;
      case "Boolean":
        example[logicalName] = true;
        break;
      case "Lookup":
      case "Owner":
      case "Customer":
      case "Uniqueidentifier":
        example[logicalName] = "00000000-0000-0000-0000-000000000000";
        break;
      case "Picklist":
        example[logicalName] = 1;
        break;
      default:
        example[logicalName] = "example_value";
    }
  }

  return example;
}
