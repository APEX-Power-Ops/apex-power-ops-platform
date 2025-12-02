#!/usr/bin/env node
/**
 * Get lookup attribute details (schema names) for binding
 */

import 'dotenv/config';
import axios from 'axios';

const DATAVERSE_URL = process.env.DATAVERSE_URL;
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID;
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID;
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;

async function run() {
  const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
  const params = new URLSearchParams({
    client_id: AZURE_CLIENT_ID,
    scope: `${DATAVERSE_URL}/.default`,
    client_secret: AZURE_CLIENT_SECRET,
    grant_type: 'client_credentials'
  });
  
  const tokenRes = await axios.post(tokenUrl, params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  const token = tokenRes.data.access_token;
  console.log("✅ Token acquired\n");
  
  const tables = ['cr950_site', 'cr950_project', 'cr950_scope', 'cr950_scopelabordetail', 'cr950_apparatus'];
  
  for (const table of tables) {
    // Get lookup attributes with schema names
    const url = `${DATAVERSE_URL}/api/data/v9.2/EntityDefinitions(LogicalName='${table}')/Attributes/Microsoft.Dynamics.CRM.LookupAttributeMetadata?$select=LogicalName,SchemaName,DisplayName,Targets`;
    
    const response = await axios.get(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        Accept: 'application/json'
      }
    });
    
    console.log(`\n📋 ${table} - Lookup Attributes:`);
    console.log('─'.repeat(60));
    
    response.data.value
      .filter(a => a.LogicalName.startsWith('cr950_'))
      .forEach(a => {
        const display = a.DisplayName?.UserLocalizedLabel?.Label || '';
        const targets = a.Targets?.join(', ') || '';
        console.log(`  ${a.LogicalName.padEnd(35)} → ${targets}`);
        console.log(`    Bind with: "${a.SchemaName}@odata.bind"`);
      });
  }
}

run().catch(err => {
  console.error("❌ Error:", err.response?.data?.error?.message || err.message);
});
