#!/usr/bin/env node
/**
 * Test $select parameter issue
 */

import axios from 'axios';

const DATAVERSE_URL = "https://org99cd6c6e.crm.dynamics.com";
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID || "";
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID || "";
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET || "";

async function getAccessToken() {
  const tokenUrl = `https://login.microsoftonline.com/${AZURE_TENANT_ID}/oauth2/v2.0/token`;
  const params = new URLSearchParams({
    client_id: AZURE_CLIENT_ID,
    scope: `${DATAVERSE_URL}/.default`,
    client_secret: AZURE_CLIENT_SECRET,
    grant_type: "client_credentials",
  });
  
  const response = await axios.post(tokenUrl, params.toString(), {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  
  return response.data.access_token;
}

async function testQuery(token, url, description) {
  console.log(`\n📝 ${description}`);
  console.log(`   URL: ${url}`);
  
  try {
    const response = await axios.get(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        Accept: "application/json",
      },
    });
    
    console.log(`   ✅ Success! Found ${response.data.value.length} records`);
    if (response.data.value.length > 0) {
      console.log(`   Fields returned: ${Object.keys(response.data.value[0]).slice(0, 8).join(', ')}...`);
    }
    return true;
  } catch (error) {
    console.log(`   ❌ Failed (${error.response?.status}): ${error.response?.data?.error?.message || error.message}`);
    return false;
  }
}

async function main() {
  console.log("🧪 Testing $select Parameter Formats\n");
  
  const token = await getAccessToken();
  
  const tests = [
    {
      url: `${DATAVERSE_URL}/api/data/v9.2/systemusers?$top=1`,
      desc: "Test 1: No $select (all fields)"
    },
    {
      url: `${DATAVERSE_URL}/api/data/v9.2/systemusers?$select=systemuserid,fullname&$top=1`,
      desc: "Test 2: With $select (proper format)"
    },
    {
      url: `${DATAVERSE_URL}/api/data/v9.2/systemusers?$select=$select=systemuserid,fullname&$top=1`,
      desc: "Test 3: Double $select= (BUG - what code might be doing)"
    },
    {
      url: `${DATAVERSE_URL}/api/data/v9.2/systemusers?$select=systemuserid&$select=fullname&$top=1`,
      desc: "Test 4: Multiple $select parameters"
    },
  ];
  
  for (const test of tests) {
    await testQuery(token, test.url, test.desc);
  }
  
  console.log("\n" + "=".repeat(70));
  console.log("💡 Recommendation:");
  console.log("If Test 2 works but Test 3 fails, the issue is double $select= prefix");
  console.log("Check if caller is passing '$select=field1,field2' instead of 'field1,field2'");
}

main().catch(error => {
  console.error("\n❌ Fatal error:", error.message);
  process.exit(1);
});
