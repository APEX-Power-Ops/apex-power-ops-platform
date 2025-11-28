import { getAccessToken, config } from "../utils/dataverse-client.js";
import axios from "axios";

/**
 * Component comparison interface
 */
export interface ComponentDiff {
  componentType: string;
  componentName: string;
  changeType: "added" | "removed" | "modified" | "unchanged";
  sourceVersion?: string;
  targetVersion?: string;
}

/**
 * Comparison result interface
 */
export interface ComparisonResult {
  sourceSolution: string;
  targetSolution: string;
  sourceVersion: string;
  targetVersion: string;
  added: number;
  modified: number;
  removed: number;
  unchanged: number;
  components: ComponentDiff[];
  comparedAt: string;
}

/**
 * Compare two solutions
 */
export async function compareSolutions(params: {
  sourceSolution: string;
  targetSolution: string;
  componentTypes?: string[];
}): Promise<ComparisonResult> {
  const { sourceSolution, targetSolution, componentTypes } = params;

  console.error(
    `Comparing solutions: ${sourceSolution} vs ${targetSolution}...`
  );

  try {
    // Get both solution infos
    const [sourceInfo, targetInfo] = await Promise.all([
      getSolutionInfo(sourceSolution),
      getSolutionInfo(targetSolution),
    ]);

    // Get components for both solutions
    const [sourceComponents, targetComponents] = await Promise.all([
      getSolutionComponents(sourceInfo.solutionid, componentTypes),
      getSolutionComponents(targetInfo.solutionid, componentTypes),
    ]);

    // Compare components
    const comparison = compareComponents(sourceComponents, targetComponents);

    const result: ComparisonResult = {
      sourceSolution: sourceInfo.uniquename,
      targetSolution: targetInfo.uniquename,
      sourceVersion: sourceInfo.version,
      targetVersion: targetInfo.version,
      added: comparison.added.length,
      modified: comparison.modified.length,
      removed: comparison.removed.length,
      unchanged: comparison.unchanged.length,
      components: [
        ...comparison.added.map((c) => ({
          componentType: getComponentTypeName(c.componenttype),
          componentName: c.objectid,
          changeType: "added" as const,
          targetVersion: targetInfo.version,
        })),
        ...comparison.modified.map((c) => ({
          componentType: getComponentTypeName(c.componenttype),
          componentName: c.objectid,
          changeType: "modified" as const,
          sourceVersion: sourceInfo.version,
          targetVersion: targetInfo.version,
        })),
        ...comparison.removed.map((c) => ({
          componentType: getComponentTypeName(c.componenttype),
          componentName: c.objectid,
          changeType: "removed" as const,
          sourceVersion: sourceInfo.version,
        })),
      ],
      comparedAt: new Date().toISOString(),
    };

    console.error(
      `✅ Comparison complete: ${result.added} added, ${result.modified} modified, ${result.removed} removed`
    );

    return result;
  } catch (error: any) {
    console.error(`Error comparing solutions: ${error.message}`);
    throw new Error(`Failed to compare solutions: ${error.message}`);
  }
}

/**
 * Get solution information
 */
async function getSolutionInfo(solutionName: string): Promise<any> {
  const token = await getAccessToken();
  const url = `${config.DATAVERSE_URL}/api/data/v9.2/solutions?$select=solutionid,friendlyname,version,uniquename&$filter=uniquename eq '${solutionName}'`;

  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });

  if (response.data.value.length === 0) {
    throw new Error(`Solution not found: ${solutionName}`);
  }

  return response.data.value[0];
}

/**
 * Get solution components
 */
async function getSolutionComponents(
  solutionId: string,
  componentTypes?: string[]
): Promise<any[]> {
  const token = await getAccessToken();

  let filter = `_solutionid_value eq ${solutionId}`;
  if (componentTypes && componentTypes.length > 0) {
    const typeFilter = componentTypes
      .map((t) => `componenttype eq ${t}`)
      .join(" or ");
    filter += ` and (${typeFilter})`;
  }

  const url = `${config.DATAVERSE_URL}/api/data/v9.2/solutioncomponents?$select=solutioncomponentid,objectid,componenttype&$filter=${filter}`;

  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });

  return response.data.value;
}

/**
 * Compare component lists
 */
function compareComponents(
  sourceComponents: any[],
  targetComponents: any[]
): {
  added: any[];
  modified: any[];
  removed: any[];
  unchanged: any[];
} {
  const sourceMap = new Map(
    sourceComponents.map((c) => [`${c.componenttype}:${c.objectid}`, c])
  );
  const targetMap = new Map(
    targetComponents.map((c) => [`${c.componenttype}:${c.objectid}`, c])
  );

  const added: any[] = [];
  const modified: any[] = [];
  const removed: any[] = [];
  const unchanged: any[] = [];

  // Find added and modified components
  for (const [key, targetComp] of targetMap) {
    const sourceComp = sourceMap.get(key);
    if (!sourceComp) {
      added.push(targetComp);
    } else {
      // In a full implementation, we would compare component details
      // For now, we consider matching components as unchanged
      unchanged.push(targetComp);
    }
  }

  // Find removed components
  for (const [key, sourceComp] of sourceMap) {
    if (!targetMap.has(key)) {
      removed.push(sourceComp);
    }
  }

  return { added, modified, removed, unchanged };
}

/**
 * Get component type name from type code
 */
function getComponentTypeName(typeCode: number): string {
  const typeMap: Record<number, string> = {
    1: "Entity",
    2: "Attribute",
    3: "Relationship",
    9: "Option Set",
    10: "Entity Relationship",
    11: "Entity Relationship Role",
    12: "Entity Relationship Relationships",
    13: "Managed Property",
    14: "Entity Key",
    16: "Privilege",
    17: "PrivilegeObjectTypeCode",
    20: "Role",
    21: "Role Privilege",
    22: "Display String",
    23: "Display String Map",
    24: "Form",
    25: "Organization",
    26: "Saved Query",
    29: "Workflow",
    31: "Report",
    32: "Report Entity",
    33: "Report Category",
    34: "Report Visibility",
    35: "Attachment",
    36: "Email Template",
    37: "Contract Template",
    38: "KB Article Template",
    39: "Mail Merge Template",
    44: "Duplicate Rule",
    45: "Duplicate Rule Condition",
    46: "Entity Map",
    47: "Attribute Map",
    48: "Ribbon Command",
    49: "Ribbon Context Group",
    50: "Ribbon Customization",
    52: "Ribbon Rule",
    53: "Ribbon Tab To Command Map",
    55: "Ribbon Diff",
    59: "Saved Query Visualization",
    60: "System Form",
    61: "Web Resource",
    62: "Site Map",
    63: "Connection Role",
    64: "Complex Control",
    65: "Hierarchy Rule",
    66: "Custom Control",
    68: "Custom Control Default Config",
    70: "Field Security Profile",
    71: "Field Permission",
    90: "Plugin Type",
    91: "Plugin Assembly",
    92: "SDK Message Processing Step",
    93: "SDK Message Processing Step Image",
    95: "Service Endpoint",
    150: "Routing Rule",
    151: "Routing Rule Item",
    152: "SLA",
    153: "SLA Item",
    154: "Convert Rule",
    155: "Convert Rule Item",
    161: "Mobile Offline Profile",
    162: "Mobile Offline Profile Item",
    165: "Similarity Rule",
    166: "Data Source Mapping",
    201: "SDKMessage",
    202: "SDKMessageFilter",
    203: "SdkMessagePair",
    204: "SdkMessageRequest",
    205: "SdkMessageRequestField",
    206: "SdkMessageResponse",
    207: "SdkMessageResponseField",
    208: "Import Map",
    210: "WebWizard",
    300: "Canvas App",
    371: "Connector",
    372: "Environment Variable Definition",
    373: "Environment Variable Value",
    380: "AI Project Type",
    381: "AI Project",
    400: "Entity Analytics Config",
    401: "Attribute Image Config",
    402: "Entity Image Config",
  };

  return typeMap[typeCode] || `Unknown (${typeCode})`;
}
