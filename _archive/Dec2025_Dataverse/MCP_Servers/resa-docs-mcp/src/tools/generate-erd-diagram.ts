import { queryMetadata } from "../utils/dataverse-client.js";

/**
 * ERD Diagram result interface
 */
export interface ERDiagramResult {
  format: string;
  code: string;
  tables: number;
  relationships: number;
  generatedAt: string;
}

/**
 * Table info for ERD
 */
interface TableInfo {
  logicalName: string;
  displayName: string;
  primaryKey: string;
  fields: Array<{
    logicalName: string;
    displayName: string;
    type: string;
    isRequired: boolean;
    isPrimaryKey: boolean;
  }>;
}

/**
 * Relationship info for ERD
 */
interface RelationshipInfo {
  schemaName: string;
  fromTable: string;
  toTable: string;
  type: "one-to-many" | "many-to-one" | "many-to-many";
  fromField: string;
  toField: string;
}

/**
 * Generate Entity Relationship Diagram (ERD) from Dataverse schema
 */
export async function generateERDiagram(params: {
  tables?: string[];
  includeAllRelationships?: boolean;
  format?: "mermaid" | "plantuml";
}): Promise<ERDiagramResult> {
  const {
    tables,
    includeAllRelationships = true,
    format = "mermaid",
  } = params;

  console.error("Generating ERD diagram...");

  try {
    // 1. Get all tables or specific tables
    const tablesToInclude = tables || (await getAllCustomTables());

    // 2. Get table metadata
    const tableInfos: TableInfo[] = [];
    for (const tableName of tablesToInclude) {
      const tableInfo = await getTableInfo(tableName);
      if (tableInfo) {
        tableInfos.push(tableInfo);
      }
    }

    // 3. Get relationships
    const relationships = await getRelationshipsForTables(
      tablesToInclude,
      includeAllRelationships
    );

    // 4. Generate diagram code
    const diagramCode =
      format === "mermaid"
        ? generateMermaidERD(tableInfos, relationships)
        : generatePlantUMLERD(tableInfos, relationships);

    return {
      format,
      code: diagramCode,
      tables: tableInfos.length,
      relationships: relationships.length,
      generatedAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error("Error generating ERD:", error.message);
    throw new Error(`Failed to generate ERD: ${error.message}`);
  }
}

/**
 * Get all custom tables (cr950_ prefix)
 */
async function getAllCustomTables(): Promise<string[]> {
  try {
    const result = await queryMetadata(
      "EntityDefinitions?$select=LogicalName&$filter=startswith(LogicalName, 'cr950_')"
    );

    return result.value
      ? result.value.map((e: any) => e.LogicalName)
      : [];
  } catch (error: any) {
    console.error("Error getting custom tables:", error.message);
    return [];
  }
}

/**
 * Get detailed table information
 */
async function getTableInfo(tableName: string): Promise<TableInfo | null> {
  try {
    // Get entity metadata
    const entityResult = await queryMetadata(
      `EntityDefinitions?$select=LogicalName,DisplayName,PrimaryIdAttribute&$filter=LogicalName eq '${tableName}'`
    );

    if (!entityResult.value || entityResult.value.length === 0) {
      return null;
    }

    const entity = entityResult.value[0];

    // Get fields (limit to key fields for cleaner ERD)
    const fieldsResult = await queryMetadata(
      `EntityDefinitions(LogicalName='${tableName}')/Attributes?$select=LogicalName,DisplayName,AttributeType,RequiredLevel,IsPrimaryId`
    );

    const fields = fieldsResult.value
      ? fieldsResult.value
          .filter(
            (attr: any) =>
              attr.IsPrimaryId ||
              attr.RequiredLevel?.Value === "ApplicationRequired" ||
              attr.RequiredLevel?.Value === "SystemRequired" ||
              attr.AttributeType === "Lookup"
          )
          .map((attr: any) => ({
            logicalName: attr.LogicalName,
            displayName:
              attr.DisplayName?.UserLocalizedLabel?.Label ||
              attr.LogicalName,
            type: getFieldTypeDisplay(attr.AttributeType),
            isRequired:
              attr.RequiredLevel?.Value === "ApplicationRequired" ||
              attr.RequiredLevel?.Value === "SystemRequired",
            isPrimaryKey: attr.IsPrimaryId || false,
          }))
      : [];

    return {
      logicalName: entity.LogicalName,
      displayName:
        entity.DisplayName?.UserLocalizedLabel?.Label ||
        entity.LogicalName,
      primaryKey: entity.PrimaryIdAttribute,
      fields,
    };
  } catch (error: any) {
    console.error(
      `Error getting table info for ${tableName}:`,
      error.message
    );
    return null;
  }
}

/**
 * Get relationships between tables
 */
async function getRelationshipsForTables(
  tables: string[],
  includeAll: boolean
): Promise<RelationshipInfo[]> {
  const relationships: RelationshipInfo[] = [];

  for (const tableName of tables) {
    try {
      // Get Many-to-One relationships
      const manyToOneResult = await queryMetadata(
        `EntityDefinitions(LogicalName='${tableName}')/ManyToOneRelationships?$select=SchemaName,ReferencedEntity,ReferencedAttribute,ReferencingAttribute`
      );

      if (manyToOneResult.value) {
        for (const rel of manyToOneResult.value) {
          // Only include if target table is in our list or includeAll is true
          if (includeAll || tables.includes(rel.ReferencedEntity)) {
            relationships.push({
              schemaName: rel.SchemaName,
              fromTable: tableName,
              toTable: rel.ReferencedEntity,
              type: "many-to-one",
              fromField: rel.ReferencingAttribute,
              toField: rel.ReferencedAttribute,
            });
          }
        }
      }
    } catch (error: any) {
      console.error(
        `Error getting relationships for ${tableName}:`,
        error.message
      );
    }
  }

  return relationships;
}

/**
 * Generate Mermaid ERD syntax
 */
function generateMermaidERD(
  tables: TableInfo[],
  relationships: RelationshipInfo[]
): string {
  let mermaid = "erDiagram\n\n";

  // Add tables with fields
  for (const table of tables) {
    const displayName = formatTableName(table.displayName);
    mermaid += `  ${displayName} {\n`;

    for (const field of table.fields) {
      const fieldType = field.type.replace(" ", "_");
      const constraint = field.isPrimaryKey
        ? "PK"
        : field.isRequired
        ? "NOT_NULL"
        : "";
      mermaid += `    ${fieldType} ${field.logicalName} ${constraint}\n`;
    }

    mermaid += `  }\n\n`;
  }

  // Add relationships
  for (const rel of relationships) {
    const fromTable = formatTableName(
      tables.find((t) => t.logicalName === rel.fromTable)?.displayName ||
        rel.fromTable
    );
    const toTable = formatTableName(
      tables.find((t) => t.logicalName === rel.toTable)?.displayName ||
        rel.toTable
    );

    // Many-to-one: from table has FK to to table
    // In ERD: toTable ||--o{ fromTable
    mermaid += `  ${toTable} ||--o{ ${fromTable} : "${rel.schemaName}"\n`;
  }

  return mermaid;
}

/**
 * Generate PlantUML ERD syntax
 */
function generatePlantUMLERD(
  tables: TableInfo[],
  relationships: RelationshipInfo[]
): string {
  let plantuml = "@startuml\n\n";
  plantuml += "!define Table(name,desc) class name as \"desc\" << (T,#FFAAAA) >>\n";
  plantuml += "!define primary_key(x) <b>x</b>\n";
  plantuml += "!define foreign_key(x) <i>x</i>\n\n";
  plantuml += "hide methods\n";
  plantuml += "hide stereotypes\n\n";

  // Add tables
  for (const table of tables) {
    const displayName = formatTableName(table.displayName);
    plantuml += `class ${displayName} {\n`;

    for (const field of table.fields) {
      const prefix = field.isPrimaryKey ? "+ " : "  ";
      const suffix = field.isPrimaryKey ? " <<PK>>" : "";
      plantuml += `${prefix}${field.logicalName}: ${field.type}${suffix}\n`;
    }

    plantuml += `}\n\n`;
  }

  // Add relationships
  for (const rel of relationships) {
    const fromTable = formatTableName(
      tables.find((t) => t.logicalName === rel.fromTable)?.displayName ||
        rel.fromTable
    );
    const toTable = formatTableName(
      tables.find((t) => t.logicalName === rel.toTable)?.displayName ||
        rel.toTable
    );

    // Many-to-one relationship
    plantuml += `${toTable} "1" -- "0..*" ${fromTable}\n`;
  }

  plantuml += "\n@enduml";

  return plantuml;
}

/**
 * Format table name for diagram
 */
function formatTableName(name: string): string {
  // Remove cr950_ prefix and format
  return name
    .replace(/^cr950_/, "")
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

/**
 * Format field type for display
 */
function getFieldTypeDisplay(attributeType: string): string {
  const typeMap: { [key: string]: string } = {
    String: "string",
    Memo: "text",
    Integer: "int",
    Decimal: "decimal",
    Money: "currency",
    DateTime: "datetime",
    Boolean: "boolean",
    Lookup: "lookup",
    Picklist: "choice",
    MultiSelectPicklist: "choices",
    Owner: "owner",
    Customer: "customer",
    Uniqueidentifier: "guid",
  };

  return typeMap[attributeType] || attributeType.toLowerCase();
}
