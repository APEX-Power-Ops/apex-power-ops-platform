#!/usr/bin/env node
/**
 * Test script to diagnose resa-dataverse-mcp connection issues
 * Run with: node test-connection.js
 */

import 'dotenv/config';
import axios from 'axios';

// Load environment from .env if exists
const DATAVERSE_URL = process.env.DATAVERSE_URL || "https://org7bdbc942.crm.dynamics.com";
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || "";
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || "";
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || "";

console.log("🔍 Testing RESA Dataverse MCP Connection\n");
console.log("Configuration:");
console.log(`  Dataverse URL: ${DATAVERSE_URL}`);
console.log(`  Tenant ID: ${AZURE_TENANT_ID ? '✅ Set' : '❌ Missing'}`);
console.log(`  Client ID: ${AZURE_CLIENT_ID ? '✅ Set' : '❌ Missing'}`);
console.log(`  Client Secret: ${AZURE_CLIENT_SECRET ? '✅ Set' : '❌ Missing'}`);
console.log();

async function getAccessToken() {
  console.log("📝 Step 1: Getting access token...");
  
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
    
    console.log("✅ Token acquired successfully\n");
    return response.data.access_token;
  } catch (error) {
    console.error("❌ Token acquisition failed:");
    console.error(error.response?.data || error.message);
    process.exit(1);
  }
}

async function testQuery(token, entityName) {
  console.log(`📝 Testing query: ${entityName}`);
  
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entityName}?$top=1`;
  console.log(`  URL: ${url}`);
  
  try {
    const response = await axios.get(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        Accept: "application/json",
      },
    });
    
    console.log(`✅ Success! Found ${response.data.value.length} record(s)`);
    if (response.data.value.length > 0) {
      console.log(`  Sample keys: ${Object.keys(response.data.value[0]).slice(0, 5).join(', ')}...`);
    }
    console.log();
    return true;
  } catch (error) {
    console.error(`❌ Query failed (${error.response?.status}):`);
    console.error(`  ${error.response?.data?.error?.message || error.message}`);
    console.log();
    return false;
  }
}

async function main() {
  // Check environment
  if (!AZURE_TENANT_ID || !AZURE_CLIENT_ID || !AZURE_CLIENT_SECRET) {
    console.error("❌ Missing required environment variables!");
    console.error("\nSet these before running:");
    console.error("  $env:AZURE_TENANT_ID = 'your-tenant-id'");
    console.error("  $env:AZURE_CLIENT_ID = 'your-client-id'");
    console.error("  $env:AZURE_CLIENT_SECRET = 'your-client-secret'");
    process.exit(1);
  }
  
  // Get token
  const token = await getAccessToken();
  
  // Test various table name formats
  console.log("🧪 Testing different table name formats:\n");
  
  const testCases = [
    { name: "systemusers", desc: "System table (known good)" },
    { name: "cr950_clients", desc: "Clients" },
    { name: "cr950_sites", desc: "Sites" },
    { name: "cr950_projects", desc: "Projects" },
    { name: "cr950_scopes", desc: "Scopes" },
    { name: "cr950_scopelabordetails", desc: "Scope Labor Details" },
    { name: "cr950_apparatuses", desc: "Apparatus" },
    { name: "cr950_tasks", desc: "Tasks" },
    { name: "cr950_estimators", desc: "Estimators" },
    { name: "cr950_locations", desc: "Locations" },
  ];
  
  const results = [];
  for (const test of testCases) {
    console.log(`Testing: ${test.desc}`);
    const success = await testQuery(token, test.name);
    results.push({ ...test, success });
  }
  
  // Summary
  console.log("\n" + "=".repeat(60));
  console.log("📊 TEST RESULTS SUMMARY");
  console.log("=".repeat(60));
  
  results.forEach(r => {
    const status = r.success ? "✅ WORKS" : "❌ FAILS";
    console.log(`${status} - ${r.name} (${r.desc})`);
  });
  
  console.log("\n💡 Recommendation:");
  const workingTables = results.filter(r => r.success);
  if (workingTables.length > 0) {
    console.log(`Use these table names in queries: ${workingTables.map(t => t.name).join(', ')}`);
  } else {
    console.log("❌ No table queries worked. Check permissions and configuration.");
  }
}

main().catch(error => {
  console.error("\n❌ Fatal error:", error.message);
  process.exit(1);
});
