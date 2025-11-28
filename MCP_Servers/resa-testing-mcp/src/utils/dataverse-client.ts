import axios from "axios";

// Environment configuration
const DATAVERSE_URL = process.env.DATAVERSE_URL || "https://org99cd6c6e.crm.dynamics.com";
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || "270d5723-4b30-4f3b-b9cb-6527be741b42";
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || "9df3350f-b3b4-47c4-97b5-499a8b02acc7";
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || "";

// Safety check - development environment only
if (process.env.ENVIRONMENT === "PRODUCTION") {
  console.error("WARNING: resa-testing-mcp should only run in DEVELOPMENT environment");
}

// Token management
let accessToken: string | null = null;
let tokenExpiry: number = 0;

/**
 * Get Azure AD access token for Dataverse API
 * Caches token and reuses if still valid (with 5 minute buffer)
 */
export async function getAccessToken(): Promise<string> {
  const now = Date.now();
  
  // Reuse token if still valid (with 5 minute buffer)
  if (accessToken && tokenExpiry > now + 300000) {
    return accessToken;
  }
  
  const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
  const params = new URLSearchParams({
    client_id: AZURE_CLIENT_ID,
    scope: `${DATAVERSE_URL}/.default`,
    client_secret: AZURE_CLIENT_SECRET,
    grant_type: "client_credentials",
  });
  
  try {
    const response = await axios.post(tokenUrl, params.toString(), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    
    accessToken = response.data.access_token;
    tokenExpiry = now + (response.data.expires_in * 1000);
    
    return accessToken!;
  } catch (error: any) {
    throw new Error(`Authentication failed: ${error.response?.data?.error_description || error.message}`);
  }
}

/**
 * Query records from a Dataverse table
 * @param entityName - Logical name of the table (e.g., 'cr950_projectses', 'cr950_apparatus')
 * @param select - Comma-separated list of fields to retrieve
 * @param filter - OData filter expression
 * @param top - Maximum number of records to return
 * @param expand - Related entities to expand (with $select)
 */
export async function queryDataverse(
  entityName: string,
  select?: string,
  filter?: string,
  top?: number,
  expand?: string
): Promise<any[]> {
  const token = await getAccessToken();
  
  let url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}`;
  const params: string[] = [];
  
  if (select) params.push(`$select=${select}`);
  if (filter) params.push(`$filter=${filter}`);
  if (top) params.push(`$top=${top}`);
  if (expand) params.push(`$expand=${expand}`);
  
  if (params.length > 0) {
    url += `?${params.join("&")}`;
  }
  
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
 * Get a single record by ID
 * @param entityName - Logical name of the table
 * @param recordId - GUID of the record
 * @param select - Comma-separated list of fields to retrieve
 */
export async function getRecord(
  entityName: string,
  recordId: string,
  select?: string
): Promise<any> {
  const token = await getAccessToken();
  
  let url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}(${recordId})`;
  if (select) {
    url += `?$select=${select}`;
  }
  
  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });
  
  return response.data;
}

/**
 * Create a new record in Dataverse
 * @param entityName - Logical name of the table
 * @param data - Record data to create
 * @returns The ID of the created record
 */
export async function createRecord(entityName: string, data: any): Promise<string> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}`;
  
  const response = await axios.post(url, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json; charset=utf-8",
      Accept: "application/json",
      Prefer: "return=representation",
    },
  });
  
  // Extract GUID from OData-EntityId header or response
  const entityId = response.headers["odata-entityid"] || response.data["@odata.id"];
  if (entityId) {
    const match = entityId.match(/\(([a-f0-9-]+)\)/i);
    if (match) return match[1];
  }
  
  return "created";
}

/**
 * Update an existing record in Dataverse
 * @param entityName - Logical name of the table
 * @param recordId - GUID of the record to update
 * @param data - Fields to update
 */
export async function updateRecord(
  entityName: string,
  recordId: string,
  data: any
): Promise<void> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}(${recordId})`;
  
  await axios.patch(url, data, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json; charset=utf-8",
    },
  });
}

/**
 * Delete a record from Dataverse
 * @param entityName - Logical name of the table
 * @param recordId - GUID of the record to delete
 */
export async function deleteRecord(entityName: string, recordId: string): Promise<void> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}(${recordId})`;
  
  await axios.delete(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
    },
  });
}

/**
 * Query metadata from Dataverse
 * Used for getting entity and attribute definitions
 * @param path - Metadata path (e.g., 'EntityDefinitions', 'EntityDefinitions(LogicalName='cr950_projects')')
 */
export async function queryMetadata(path: string): Promise<any> {
  const token = await getAccessToken();
  const url = `${DATAVERSE_URL}/api/data/v9.2/${path}`;
  
  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    },
  });
  
  return response.data;
}

/**
 * Execute a batch request (multiple operations in one HTTP call)
 * @param requests - Array of Dataverse operations
 */
export async function executeBatch(requests: any[]): Promise<any[]> {
  const token = await getAccessToken();
  const batchId = `batch_${Date.now()}`;
  const changesetId = `changeset_${Date.now()}`;
  
  // Build batch request body
  let batchBody = `--${batchId}\r\n`;
  batchBody += `Content-Type: multipart/mixed; boundary=${changesetId}\r\n\r\n`;
  
  requests.forEach((req, index) => {
    batchBody += `--${changesetId}\r\n`;
    batchBody += `Content-Type: application/http\r\n`;
    batchBody += `Content-Transfer-Encoding: binary\r\n`;
    batchBody += `Content-ID: ${index + 1}\r\n\r\n`;
    batchBody += `${req.method} ${req.url} HTTP/1.1\r\n`;
    batchBody += `Content-Type: application/json\r\n\r\n`;
    if (req.body) {
      batchBody += JSON.stringify(req.body) + "\r\n";
    }
    batchBody += `\r\n`;
  });
  
  batchBody += `--${changesetId}--\r\n`;
  batchBody += `--${batchId}--\r\n`;
  
  const response = await axios.post(`${DATAVERSE_URL}/api/data/v9.2/$batch`, batchBody, {
    headers: {
      Authorization: `Bearer ${token}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": `multipart/mixed; boundary=${batchId}`,
    },
  });
  
  return response.data;
}

// Export configuration for tools to use
export const config = {
  DATAVERSE_URL,
  AZURE_TENANT_ID,
  AZURE_CLIENT_ID,
  ENVIRONMENT: process.env.ENVIRONMENT || "DEVELOPMENT",
};
