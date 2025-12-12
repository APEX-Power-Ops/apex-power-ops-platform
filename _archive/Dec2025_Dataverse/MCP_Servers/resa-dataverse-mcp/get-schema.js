#!/usr/bin/env node
/**
 * Get existing estimator record to see field schema
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
  
  // Get existing estimator record
  const url = `${DATAVERSE_URL}/api/data/v9.2/cr950_estimators?$top=1`;
  
  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0',
      Accept: 'application/json'
    }
  });
  
  if (response.data.value.length > 0) {
    console.log('📋 Existing Estimator Record Fields:');
    const record = response.data.value[0];
    
    // Show only cr950_ fields (custom fields)
    const customFields = Object.keys(record)
      .filter(k => k.startsWith('cr950_') || k.startsWith('_cr950_'))
      .sort();
    
    console.log('\nCustom Fields (cr950_):');
    customFields.forEach(f => {
      const val = record[f];
      const display = val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val).substring(0, 60);
      console.log(`  ${f}: ${display}`);
    });
  } else {
    console.log('No estimator records found');
  }
  
  // Also get Client record
  const clientUrl = `${DATAVERSE_URL}/api/data/v9.2/cr950_clients?$top=1`;
  const clientRes = await axios.get(clientUrl, {
    headers: {
      Authorization: `Bearer ${token}`,
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0',
      Accept: 'application/json'
    }
  });
  
  if (clientRes.data.value.length > 0) {
    console.log('\n📋 Existing Client Record Fields:');
    const record = clientRes.data.value[0];
    const customFields = Object.keys(record)
      .filter(k => k.startsWith('cr950_') || k.startsWith('_cr950_'))
      .sort();
    
    console.log('\nCustom Fields (cr950_):');
    customFields.forEach(f => {
      const val = record[f];
      const display = val === null ? 'null' : typeof val === 'object' ? JSON.stringify(val) : String(val).substring(0, 60);
      console.log(`  ${f}: ${display}`);
    });
  }
}

run().catch(err => {
  console.error("❌ Error:", err.response?.data?.error?.message || err.message);
});
