#!/usr/bin/env node
/**
 * Discover schema for all RESA custom tables
 * Shows actual field names from new environment
 */

import 'dotenv/config';
import axios from 'axios';

const DATAVERSE_URL = process.env.DATAVERSE_URL;
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID;
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID;
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;

async function getToken() {
  const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
  const params = new URLSearchParams({
    client_id: AZURE_CLIENT_ID,
    scope: `${DATAVERSE_URL}/.default`,
    client_secret: AZURE_CLIENT_SECRET,
    grant_type: 'client_credentials'
  });
  
  const res = await axios.post(tokenUrl, params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  return res.data.access_token;
}

async function getTableAttributes(token, logicalName) {
  // Get entity metadata with attributes
  const url = `${DATAVERSE_URL}/api/data/v9.2/EntityDefinitions(LogicalName='${logicalName}')?$expand=Attributes($select=LogicalName,AttributeType,DisplayName,RequiredLevel,IsPrimaryId,IsPrimaryName)`;
  
  const response = await axios.get(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      'OData-MaxVersion': '4.0',
      'OData-Version': '4.0',
      Accept: 'application/json'
    }
  });
  
  return response.data;
}

async function run() {
  console.log("🔍 RESA Dataverse Schema Discovery\n");
  console.log(`Environment: ${DATAVERSE_URL}\n`);
  
  const token = await getToken();
  console.log("✅ Token acquired\n");
  
  const tables = [
    'cr950_client',
    'cr950_site', 
    'cr950_project',
    'cr950_scope',
    'cr950_scopelabordetail',
    'cr950_apparatus',
    'cr950_estimator'
  ];
  
  for (const table of tables) {
    try {
      const entity = await getTableAttributes(token, table);
      
      console.log(`\n${'═'.repeat(70)}`);
      console.log(`📋 ${table} → ${entity.EntitySetName}`);
      console.log(`${'═'.repeat(70)}`);
      console.log(`Primary Key: ${entity.PrimaryIdAttribute}`);
      console.log(`Primary Name: ${entity.PrimaryNameAttribute}`);
      console.log(`\nCustom Attributes (cr950_):`);
      
      // Filter to custom attributes
      const customAttrs = entity.Attributes
        .filter(a => a.LogicalName.startsWith('cr950_') && !a.LogicalName.includes('@'))
        .sort((a, b) => a.LogicalName.localeCompare(b.LogicalName));
      
      for (const attr of customAttrs) {
        const required = attr.RequiredLevel?.Value === 'ApplicationRequired' || 
                        attr.RequiredLevel?.Value === 'SystemRequired' ? '⚠️ REQUIRED' : '';
        const primary = attr.IsPrimaryId ? '🔑 PK' : (attr.IsPrimaryName ? '📛 Name' : '');
        const display = attr.DisplayName?.UserLocalizedLabel?.Label || '';
        
        console.log(`  ${attr.LogicalName.padEnd(45)} ${attr.AttributeType.padEnd(15)} ${primary} ${required} ${display ? `(${display})` : ''}`);
      }
      
      // Show lookup attributes (relationships)
      const lookups = entity.Attributes
        .filter(a => a.AttributeType === 'Lookup' && a.LogicalName.startsWith('cr950_'))
        .sort((a, b) => a.LogicalName.localeCompare(b.LogicalName));
      
      if (lookups.length > 0) {
        console.log(`\nLookup Fields (Relationships):`);
        for (const lookup of lookups) {
          console.log(`  ${lookup.LogicalName} → (bind with @odata.bind)`);
        }
      }
      
    } catch (err) {
      console.error(`❌ Error getting ${table}: ${err.response?.data?.error?.message || err.message}`);
    }
  }
}

run().catch(err => {
  console.error("❌ Fatal:", err.message);
  process.exit(1);
});
