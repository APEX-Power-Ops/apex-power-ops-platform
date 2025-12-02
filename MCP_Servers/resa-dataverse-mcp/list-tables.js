#!/usr/bin/env node
/**
 * List all custom tables in new Dataverse environment
 * Shows both LogicalName and EntitySetName (API name)
 */

import 'dotenv/config';
import axios from 'axios';

const DATAVERSE_URL = process.env.DATAVERSE_URL;
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID;
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID;
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;

async function run() {
  console.log("🔍 Listing RESA Tables in New Environment\n");
  console.log(`Environment: ${DATAVERSE_URL}\n`);
  
  // Get token
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
  
  // Query all entity definitions, filter locally for cr950_ tables
  const url = `${DATAVERSE_URL}/api/data/v9.2/EntityDefinitions?$select=LogicalName,EntitySetName,DisplayName`;
  
  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0',
      Accept: 'application/json'
    }
  });
  
  console.log('📋 Custom Tables (cr950_ prefix):\n');
  console.log('LogicalName'.padEnd(30) + 'EntitySetName (API)'.padEnd(30) + 'Display Name');
  console.log('─'.repeat(90));
  
  response.data.value
    .filter(e => e.LogicalName.startsWith('cr950_'))
    .sort((a, b) => a.LogicalName.localeCompare(b.LogicalName))
    .forEach(e => {
      const displayName = e.DisplayName?.UserLocalizedLabel?.Label || '';
      console.log(e.LogicalName.padEnd(30) + e.EntitySetName.padEnd(30) + displayName);
    });
    
  console.log('\n✅ Use EntitySetName values for API queries');
}

run().catch(err => {
  console.error("❌ Error:", err.response?.data?.error?.message || err.message);
  process.exit(1);
});
