#!/usr/bin/env node
/**
 * Import Estimator JSON data into Dataverse
 * Version 3.0 - Updated for org7bdbc942 schema
 * 
 * Usage: node import-estimator.js <path-to-json>
 * 
 * Environment: org7bdbc942.crm.dynamics.com (Developer)
 * Last Updated: December 2, 2025
 */

import 'dotenv/config';
import axios from 'axios';
import fs from 'fs';

const DATAVERSE_URL = process.env.DATAVERSE_URL;
const AZURE_TENANT_ID = process.env.AZURE_TENANT_ID;
const AZURE_CLIENT_ID = process.env.AZURE_CLIENT_ID;
const AZURE_CLIENT_SECRET = process.env.AZURE_CLIENT_SECRET;

let accessToken = null;

// ============================================================
// Table Schema Reference (org7bdbc942)
// ============================================================
// cr950_clients       PK: cr950_clientid      Name: cr950_clientname
// cr950_sites         PK: cr950_siteid        Name: cr950_sitename
// cr950_projects      PK: cr950_projectid     Name: cr950_projectname
// cr950_scopes        PK: cr950_scopeid       Name: cr950_scopename
// cr950_scopelabordetails  PK: cr950_scopelabordetailid  Name: cr950_scopelaborname
// cr950_apparatuses   PK: cr950_apparatusid   Name: cr950_apparatusname
// cr950_estimators    PK: cr950_estimatorid   Name: cr950_estimator_name
// ============================================================

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

async function findOrCreateClient(clientName) {
  // Check if client exists
  const checkUrl = `${DATAVERSE_URL}/api/data/v9.2/cr950_clients?$filter=cr950_clientname eq '${encodeURIComponent(clientName)}'&$top=1`;
  
  const checkRes = await axios.get(checkUrl, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "OData-MaxVersion": "4.0",
      "OData-Version": "4.0",
      Accept: "application/json",
    }
  });
  
  if (checkRes.data.value.length > 0) {
    const existing = checkRes.data.value[0];
    console.log(`   ↩️  Client exists: ${existing.cr950_clientname} (${existing.cr950_clientid})`);
    return existing;
  }
  
  // Create new
  const client = await createRecord("cr950_clients", {
    cr950_clientname: clientName,
    cr950_clientactive: true
  });
  console.log(`   ✅ Created: ${client.cr950_clientname} (${client.cr950_clientid})`);
  return client;
}

async function importEstimator(jsonPath) {
  console.log("🏗️ RESA Dataverse Import Tool v3.0\n");
  console.log(`📍 Environment: ${DATAVERSE_URL}\n`);
  
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
  
  // 1. Find or Create Client
  console.log("🔧 Processing Client...");
  const client = await findOrCreateClient(data.client.name);
  console.log();
  
  // 2. Create Site
  console.log("🔧 Creating Site...");
  const site = await createRecord("cr950_sites", {
    cr950_sitename: data.site.name,
    cr950_siteaddress: data.site.address,
    cr950_sitecity: data.site.city,
    cr950_sitestate: data.site.state,
    cr950_sitezip: data.site.zipCode,
    cr950_sitecontactemail: data.site.contactEmail || null,
    cr950_sitecontactname: data.site.contactName || null,
    cr950_sitecontactphone: data.site.contactPhone || null,
    cr950_siteactive: true,
    "cr950_SiteClient@odata.bind": `/cr950_clients(${client.cr950_clientid})`
  });
  console.log(`   ✅ Site: ${site.cr950_sitename} (${site.cr950_siteid})\n`);
  
  // 3. Create Project
  console.log("🔧 Creating Project...");
  const project = await createRecord("cr950_projects", {
    cr950_projectname: data.project.name,
    cr950_projectnumber: data.project.projectNumber,
    cr950_project_lead: data.project.projectLead || null,
    cr950_project_business_unit: data.project.businessUnit || null,
    cr950_projectstartdate: data.project.startDate || null,
    cr950_projectactive: true,
    "cr950_ProjectClient@odata.bind": `/cr950_clients(${client.cr950_clientid})`,
    "cr950_ProjectSite@odata.bind": `/cr950_sites(${site.cr950_siteid})`
  });
  console.log(`   ✅ Project: ${project.cr950_projectname} #${project.cr950_projectnumber} (${project.cr950_projectid})\n`);
  
  // 4. Create Scopes with ScopeLaborDetail
  console.log("🔧 Creating Scopes + ScopeLaborDetails...");
  let totalApparatus = 0;
  
  for (const scopeData of data.scopes) {
    // Create Scope
    const scope = await createRecord("cr950_scopes", {
      cr950_scopename: scopeData.name,
      cr950_scopetype: scopeData.scopeType, // "ATS" or "MTS" as string
      cr950_scopenumber: `${scopeData.scopeIndex}`,
      cr950_scopeactive: true,
      "cr950_ScopeProject@odata.bind": `/cr950_projects(${project.cr950_projectid})`,
      "cr950_scope_clientid@odata.bind": `/cr950_clients(${client.cr950_clientid})`,
      "cr950_scope_siteid@odata.bind": `/cr950_sites(${site.cr950_siteid})`
    });
    console.log(`   ✅ Scope: ${scope.cr950_scopename}`);
    
    // Create ScopeLaborDetail for this scope
    const effectiveRate = scopeData.totalHours > 0 
      ? scopeData.quotedAmount / scopeData.totalHours 
      : 0;
    
    const scopeLaborDetail = await createRecord("cr950_scopelabordetails", {
      cr950_scopelaborname: `${scopeData.name} - Labor Details`,
      cr950_scopelabortotalhours: scopeData.totalHours,
      cr950_scopelaborquotedamount: scopeData.quotedAmount,
      cr950_scopelabormultiplier: scopeData.multiplier || 1.0,
      cr950_scopelaboreffectiverate: effectiveRate,
      cr950_scopelaboronsitetotal: scopeData.financials?.onsiteLaborTotal || 0,
      cr950_scopelaboroffsitetotal: scopeData.financials?.offsiteLaborTotal || 0,
      cr950_scopelabortraveltotal: scopeData.financials?.travelTotal || 0,
      cr950_scopelaboroutsidetotal: scopeData.financials?.outsideServicesTotal || 0,
      cr950_scopelaboractive: true,
      "cr950_ScopeLaborScope@odata.bind": `/cr950_scopes(${scope.cr950_scopeid})`
    });
    console.log(`      💰 ScopeLaborDetail: $${scopeData.quotedAmount.toLocaleString()} @ $${effectiveRate.toFixed(2)}/hr`);
    
    // Create Apparatus for each scope
    // Note: cr950_apparatustask is REQUIRED but we don't have tasks yet
    // For now, skip apparatus creation or create tasks first
    console.log(`      📦 Apparatus: ${scopeData.apparatus.reduce((sum, a) => sum + a.quantity, 0)} items (skipped - requires Task)`);
    
    /*
    // TODO: Create Task first, then apparatus
    for (const appData of scopeData.apparatus) {
      for (let i = 0; i < appData.quantity; i++) {
        await createRecord("cr950_apparatuses", {
          cr950_apparatusname: `${appData.equipmentType} ${i+1}`,
          cr950_apparatustype: appData.equipmentType,
          cr950_apparatushoursperunit: appData.hoursPerUnit,
          cr950_apparatussection: appData.section,
          cr950_apparatusrow: appData.row,
          cr950_apparatusquantity: 1,
          cr950_apparatustotalhours: appData.hoursPerUnit,
          cr950_apparatusactive: true,
          "cr950_apparatus_scopeid@odata.bind": `/cr950_scopes(${scope.cr950_scopeid})`,
          "cr950_apparatus_projectid@odata.bind": `/cr950_projects(${project.cr950_projectid})`,
          "cr950_apparatus_clientid@odata.bind": `/cr950_clients(${client.cr950_clientid})`,
          "cr950_apparatustask@odata.bind": `/cr950_tasks(${taskId})` // REQUIRED
        });
        totalApparatus++;
      }
    }
    */
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
  console.log(`   Apparatus: ${totalApparatus} (skipped - Task required)`);
  console.log(`   Grand Total: $${data.summary?.grandTotal?.toLocaleString() || 'N/A'}`);
  console.log();
  console.log("📊 Financial Summary:");
  data.scopes.forEach(s => {
    const rate = s.totalHours > 0 ? (s.quotedAmount / s.totalHours).toFixed(2) : 0;
    console.log(`   ${s.name}: $${s.quotedAmount.toLocaleString()} (${s.totalHours} hrs @ $${rate}/hr)`);
  });
  
  // Return created record IDs for reference
  return {
    clientId: client.cr950_clientid,
    siteId: site.cr950_siteid,
    projectId: project.cr950_projectid
  };
}

// Run
const jsonPath = process.argv[2] || "C:\\RESA_Power_Build\\Reference_Files\\Excel\\_DATAVERSE_IMPORT_20251129_202330.json";
importEstimator(jsonPath).catch(e => {
  console.error("❌ Import failed:", e.response?.data?.error?.message || e.response?.data || e.message);
  if (e.response?.data?.error?.innererror) {
    console.error("Inner error:", e.response.data.error.innererror.message);
  }
  process.exit(1);
});
