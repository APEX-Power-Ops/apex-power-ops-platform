#!/usr/bin/env node
/**
 * Import Estimator JSON data into Dataverse
 * Version 2.0 - Now includes ScopeLaborDetail creation
 * 
 * Usage: node import-estimator-v2.js <path-to-json>
 */

import 'dotenv/config';
import axios from 'axios';
import fs from 'fs';

const DATAVERSE_URL = process.env.DATAVERSE_URL;
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID;
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID;
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;

let accessToken = null;

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
  
  accessToken = response.data.access_token;
  return accessToken;
}

async function createRecord(entitySetName, data) {
  const url = `${DATAVERSE_URL}/api/data/v9.2/${entitySetName}`;
  
  const response = await axios.post(url, data, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      "Content-Type": "application/json",
      "Accept": "application/json",
      "Prefer": "return=representation"
    }
  });
  
  return response.data;
}

async function importEstimator(jsonPath) {
  console.log("🏗️ RESA Dataverse Import Tool v2.0\n");
  
  // Load JSON
  console.log(`📂 Loading: ${jsonPath}`);
  const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));
  console.log(`   Project: ${data.project.name}`);
  console.log(`   Scopes: ${data.scopes.length}`);
  console.log();
  
  // Get token
  console.log("🔐 Authenticating...");
  await getAccessToken();
  console.log("   ✅ Token acquired\n");
  
  // 1. Create Client
  console.log("🔧 Creating Client...");
  const client = await createRecord("cr950_clients", {
    cr950_name: data.client.name
  });
  console.log(`   ✅ Client: ${client.cr950_name} (${client.cr950_clientid})\n`);
  
  // 2. Create Site
  console.log("🔧 Creating Site...");
  const site = await createRecord("cr950_sites", {
    cr950_name: data.site.name,
    cr950_address: data.site.address,
    cr950_city: data.site.city,
    cr950_state: data.site.state,
    cr950_zip: data.site.zipCode,
    cr950_sitecontactemail: data.site.contactEmail,
    "cr950_client@odata.bind": `/cr950_clients(${client.cr950_clientid})`
  });
  console.log(`   ✅ Site: ${site.cr950_name} (${site.cr950_siteid})\n`);
  
  // 3. Create Project
  console.log("🔧 Creating Project...");
  const project = await createRecord("cr950_projectses", {
    cr950_project_name: data.project.name,
    cr950_job_number: data.project.projectNumber,
    "cr950_client@odata.bind": `/cr950_clients(${client.cr950_clientid})`,
    "cr950_site@odata.bind": `/cr950_sites(${site.cr950_siteid})`
  });
  console.log(`   ✅ Project: ${project.cr950_project_name} #${project.cr950_job_number} (${project.cr950_projectsid})\n`);
  
  // 4. Create Scopes with ScopeLaborDetail
  console.log("🔧 Creating Scopes + ScopeLaborDetails...");
  let totalApparatus = 0;
  
  for (const scopeData of data.scopes) {
    // Create Scope
    const scope = await createRecord("cr950_projectscopes", {
      cr950_scope_name: scopeData.name,
      cr950_testing_standard: scopeData.scopeType === 'ATS' ? 957080000 : 957080001, // ATS=957080000, MTS=957080001
      "cr950_Project@odata.bind": `/cr950_projectses(${project.cr950_projectsid})`
    });
    console.log(`   ✅ Scope: ${scope.cr950_scope_name}`);
    
    // Create ScopeLaborDetail for this scope
    // Calculate effective labor rate: Total Value / Total Hours
    const effectiveRate = scopeData.totalHours > 0 
      ? scopeData.quotedAmount / scopeData.totalHours 
      : 0;
    
    const scopeLaborDetail = await createRecord("cr950_scopelabordetailses", {
      cr950_name: `${scopeData.name} - Labor Details`,
      cr950_total_apparatus_hours: scopeData.totalHours,
      cr950_scope_total_value: scopeData.quotedAmount,
      cr950_scopemultiplier: scopeData.multiplier || 1.0,
      cr950_effectivelaborrate: effectiveRate,
      cr950_onsitelabortotal: scopeData.financials?.onsiteLaborTotal || 0,
      cr950_offsitelabortotal: scopeData.financials?.offsiteLaborTotal || 0,
      cr950_traveltotal: scopeData.financials?.travelTotal || 0,
      cr950_outsideservicestotal: scopeData.financials?.outsideServicesTotal || 0,
      cr950_iscurrentversion: true,
      "cr950_projectscope_id@odata.bind": `/cr950_projectscopes(${scope.cr950_projectscopeid})`
    });
    console.log(`      💰 ScopeLaborDetail: $${scopeData.quotedAmount.toLocaleString()} @ $${effectiveRate.toFixed(2)}/hr`);
    
    // Create Apparatus for each scope
    for (const appData of scopeData.apparatus) {
      // Create one apparatus record per quantity
      for (let i = 0; i < appData.quantity; i++) {
        await createRecord("cr950_apparatuses", {
          cr950_apparatus_designation: appData.equipmentType,
          cr950_labor_hours: appData.hoursPerUnit,
          cr950_notes: appData.section,
          "cr950_Scope@odata.bind": `/cr950_projectscopes(${scope.cr950_projectscopeid})`,
          "cr950_Project@odata.bind": `/cr950_projectses(${project.cr950_projectsid})`
        });
        totalApparatus++;
      }
    }
    console.log(`      📦 ${scopeData.apparatus.reduce((sum, a) => sum + a.quantity, 0)} apparatus records created`);
  }
  
  console.log();
  console.log("============================================================");
  console.log("✅ IMPORT COMPLETE!");
  console.log("============================================================");
  console.log(`   Client: ${data.client.name}`);
  console.log(`   Site: ${data.site.name}`);
  console.log(`   Project: ${data.project.projectNumber}`);
  console.log(`   Scopes: ${data.scopes.length}`);
  console.log(`   ScopeLaborDetails: ${data.scopes.length}`);
  console.log(`   Apparatus: ${totalApparatus}`);
  console.log(`   Grand Total: $${data.summary.grandTotal.toLocaleString()}`);
  console.log();
  console.log("📊 Financial Summary:");
  data.scopes.forEach(s => {
    const rate = s.totalHours > 0 ? (s.quotedAmount / s.totalHours).toFixed(2) : 0;
    console.log(`   ${s.name}: $${s.quotedAmount.toLocaleString()} (${s.totalHours} hrs @ $${rate}/hr)`);
  });
}

// Run
const jsonPath = process.argv[2] || "C:\\RESA_Power_Build\\Reference_Files\\Excel\\_DATAVERSE_IMPORT_20251127_114935.json";
importEstimator(jsonPath).catch(e => {
  console.error("❌ Import failed:", e.response?.data || e.message);
  process.exit(1);
});
