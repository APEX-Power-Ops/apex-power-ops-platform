import {
  queryDataverse,
  queryMetadata,
  config,
} from "../utils/dataverse-client.js";
import Handlebars from "handlebars";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Documentation result interface
 */
export interface DocumentationResult {
  tableName: string;
  displayName: string;
  documentation: string;
  fields: number;
  relationships: number;
  format: string;
  generatedAt: string;
}

/**
 * Field metadata interface
 */
interface FieldMetadata {
  displayName: string;
  logicalName: string;
  type: string;
  isRequired: boolean;
  maxLength?: number;
  description: string;
}

/**
 * Relationship metadata interface
 */
interface RelationshipMetadata {
  displayName: string;
  logicalName: string;
  relatedTable: string;
  relatedField: string;
  type: "ManyToOne" | "OneToMany";
}

/**
 * Generate comprehensive table documentation from Dataverse metadata
 */
export async function generateTableDocumentation(params: {
  tableName: string;
  includeFields?: boolean;
  includeRelationships?: boolean;
  includeBusinessRules?: boolean;
  outputFormat?: "markdown" | "html";
}): Promise<DocumentationResult> {
  const {
    tableName,
    includeFields = true,
    includeRelationships = true,
    includeBusinessRules = true,
    outputFormat = "markdown",
  } = params;

  console.error(
    `Generating documentation for table: ${tableName}...`
  );

  try {
    // 1. Get entity metadata
    const entityMetadata = await getEntityMetadata(tableName);

    // 2. Get field definitions
    const fields = includeFields
      ? await getFieldMetadata(tableName)
      : [];

    // 3. Get relationships
    const relationships = includeRelationships
      ? await getRelationshipMetadata(tableName)
      : { manyToOne: [], oneToMany: [] };

    // 4. Get calculated and rollup fields
    const calculatedFields = fields.filter(
      (f: any) => f.type?.includes("Calculated")
    );
    const rollupFields = fields.filter((f: any) =>
      f.type?.includes("Rollup")
    );

    // 5. Prepare template data
    const templateData = {
      displayName: entityMetadata.DisplayName || tableName,
      logicalName: entityMetadata.LogicalName || tableName,
      schemaName: entityMetadata.SchemaName || tableName,
      primaryKey:
        entityMetadata.PrimaryIdAttribute || `${tableName}id`,
      createdOn: entityMetadata.CreatedOn
        ? new Date(entityMetadata.CreatedOn).toLocaleDateString()
        : "Unknown",
      modifiedOn: entityMetadata.ModifiedOn
        ? new Date(entityMetadata.ModifiedOn).toLocaleDateString()
        : "Unknown",
      description:
        entityMetadata.Description ||
        `Table for managing ${entityMetadata.DisplayName || tableName} records.`,
      fieldCount: fields.length,
      fields: fields,
      relationshipCount:
        relationships.manyToOne.length +
        relationships.oneToMany.length,
      manyToOneRelationships: relationships.manyToOne,
      oneToManyRelationships: relationships.oneToMany,
      calculatedFields:
        calculatedFields.length > 0 ? calculatedFields : null,
      rollupFields: rollupFields.length > 0 ? rollupFields : null,
      businessRules: includeBusinessRules
        ? await getBusinessRules(tableName)
        : null,
      sampleFields: fields.slice(0, 5),
      requiredFields: fields.filter((f: any) => f.isRequired).slice(0, 3),
      updateableFields: fields.filter((f: any) => !f.isRequired).slice(0, 3),
      generatedDate: new Date().toISOString(),
    };

    // 6. Generate documentation using template
    const documentation = await renderTemplate(templateData, outputFormat);

    return {
      tableName,
      displayName: entityMetadata.DisplayName || tableName,
      documentation,
      fields: fields.length,
      relationships:
        relationships.manyToOne.length +
        relationships.oneToMany.length,
      format: outputFormat,
      generatedAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error(
      `Error generating documentation for ${tableName}:`,
      error.message
    );
    throw new Error(
      `Failed to generate documentation: ${error.message}`
    );
  }
}

/**
 * Get entity metadata from Dataverse
 */
async function getEntityMetadata(tableName: string): Promise<any> {
  try {
    const result = await queryMetadata(
      `EntityDefinitions?$select=LogicalName,DisplayName,SchemaName,PrimaryIdAttribute,Description,CreatedOn,ModifiedOn&$filter=LogicalName eq '${tableName}'`
    );

    if (!result.value || result.value.length === 0) {
      throw new Error(`Table ${tableName} not found`);
    }

    return result.value[0];
  } catch (error: any) {
    throw new Error(`Failed to get entity metadata: ${error.message}`);
  }
}

/**
 * Get field metadata for a table
 */
async function getFieldMetadata(
  tableName: string
): Promise<FieldMetadata[]> {
  try {
    const result = await queryMetadata(
      `EntityDefinitions(LogicalName='${tableName}')/Attributes?$select=LogicalName,DisplayName,AttributeType,RequiredLevel,MaxLength,Description`
    );

    if (!result.value) {
      return [];
    }

    return result.value.map((attr: any) => ({
      displayName: attr.DisplayName?.UserLocalizedLabel?.Label || attr.LogicalName,
      logicalName: attr.LogicalName,
      type: getFieldTypeDisplay(attr.AttributeType),
      isRequired:
        attr.RequiredLevel?.Value === "ApplicationRequired" ||
        attr.RequiredLevel?.Value === "SystemRequired",
      maxLength: attr.MaxLength || undefined,
      description:
        attr.Description?.UserLocalizedLabel?.Label ||
        `Field for ${attr.DisplayName?.UserLocalizedLabel?.Label || attr.LogicalName}`,
    }));
  } catch (error: any) {
    console.error(`Error getting field metadata: ${error.message}`);
    return [];
  }
}

/**
 * Get relationship metadata for a table
 */
async function getRelationshipMetadata(tableName: string): Promise<{
  manyToOne: RelationshipMetadata[];
  oneToMany: RelationshipMetadata[];
}> {
  try {
    // Get Many-to-One relationships
    const manyToOneResult = await queryMetadata(
      `EntityDefinitions(LogicalName='${tableName}')/ManyToOneRelationships?$select=SchemaName,ReferencedEntity,ReferencedAttribute,ReferencingAttribute`
    );

    // Get One-to-Many relationships
    const oneToManyResult = await queryMetadata(
      `EntityDefinitions(LogicalName='${tableName}')/OneToManyRelationships?$select=SchemaName,ReferencedEntity,ReferencedAttribute,ReferencingEntity,ReferencingAttribute`
    );

    const manyToOne = manyToOneResult.value
      ? manyToOneResult.value.map((rel: any) => ({
          displayName: formatRelationshipName(rel.SchemaName),
          logicalName: rel.SchemaName,
          relatedTable: rel.ReferencedEntity,
          relatedField: rel.ReferencedAttribute,
          type: "ManyToOne" as const,
        }))
      : [];

    const oneToMany = oneToManyResult.value
      ? oneToManyResult.value.map((rel: any) => ({
          displayName: formatRelationshipName(rel.SchemaName),
          logicalName: rel.SchemaName,
          relatedTable: rel.ReferencingEntity,
          relatedField: rel.ReferencingAttribute,
          type: "OneToMany" as const,
        }))
      : [];

    return { manyToOne, oneToMany };
  } catch (error: any) {
    console.error(`Error getting relationship metadata: ${error.message}`);
    return { manyToOne: [], oneToMany: [] };
  }
}

/**
 * Get business rules for a table (placeholder - would need Workflow/BusinessRule API)
 */
async function getBusinessRules(tableName: string): Promise<any[] | null> {
  // Note: Business rules are stored in workflows
  // This would require querying the Workflow entity
  // For now, return null to indicate not implemented
  return null;
}

/**
 * Render template with data
 */
async function renderTemplate(
  data: any,
  format: string
): Promise<string> {
  try {
    const templatePath = join(
      __dirname,
      "../templates/table-documentation.hbs"
    );
    const templateSource = readFileSync(templatePath, "utf-8");
    const template = Handlebars.compile(templateSource);

    return template(data);
  } catch (error: any) {
    throw new Error(`Template rendering failed: ${error.message}`);
  }
}

/**
 * Format field type for display
 */
function getFieldTypeDisplay(attributeType: string): string {
  const typeMap: { [key: string]: string } = {
    String: "Text",
    Memo: "Multiline Text",
    Integer: "Whole Number",
    Decimal: "Decimal Number",
    Money: "Currency",
    DateTime: "Date and Time",
    Boolean: "Yes/No",
    Lookup: "Lookup",
    Picklist: "Choice",
    MultiSelectPicklist: "Multi-Select Choice",
    Owner: "Owner",
    Customer: "Customer",
    Uniqueidentifier: "Unique Identifier",
  };

  return typeMap[attributeType] || attributeType;
}

/**
 * Format relationship name for display
 */
function formatRelationshipName(schemaName: string): string {
  // Convert schema name to display name
  // e.g., "cr950_cr950_projects_cr950_projectscope" -> "Projects to Project Scopes"
  return schemaName
    .split("_")
    .filter((part) => part !== "cr950")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
