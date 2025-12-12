import { getGraphClient } from "../utils/graph-client.js";
import axios from "axios";

// Simple Dataverse query function for contacts
async function getDataverseContacts(): Promise<any[]> {
  // This is a simplified version - in production, use proper Dataverse client
  const dataverseUrl = process.env.DATAVERSE_URL || "";
  
  if (!dataverseUrl) {
    console.error("DATAVERSE_URL not configured, skipping Dataverse sync");
    return [];
  }

  try {
    // Note: This requires DATAVERSE_URL to be set and proper authentication
    // For now, return empty array as this is optional functionality
    console.error("Dataverse integration requires resa-dataverse-mcp to be configured");
    return [];
  } catch (error) {
    console.error("Could not fetch Dataverse contacts");
    return [];
  }
}

/**
 * Sync result interface
 */
export interface SyncResult {
  totalContacts: number;
  syncedContacts: number;
  errors: number;
  duration: number;
  syncedAt: string;
}

/**
 * Sync Dataverse contacts to Outlook
 */
export async function syncContacts(params: {
  userEmail: string;
  syncDirection?: "dataverse-to-outlook" | "outlook-to-dataverse" | "bidirectional";
  folderName?: string;
}): Promise<SyncResult> {
  const {
    userEmail,
    syncDirection = "dataverse-to-outlook",
    folderName = "RESA Contacts",
  } = params;

  console.error(`Syncing contacts for: ${userEmail}`);
  console.error(`Direction: ${syncDirection}`);

  const startTime = Date.now();
  let syncedCount = 0;
  let errorCount = 0;

  try {
    const graphClient = getGraphClient();

    if (syncDirection === "dataverse-to-outlook" || syncDirection === "bidirectional") {
      // Get contacts from Dataverse
      console.error("Fetching contacts from Dataverse...");
      
      const dataverseContacts = await getDataverseContacts();

      if (dataverseContacts.length === 0) {
        console.error("No contacts found in Dataverse or Dataverse not configured");
        return {
          totalContacts: 0,
          syncedContacts: 0,
          errors: 0,
          duration: Date.now() - startTime,
          syncedAt: new Date().toISOString(),
        };
      }

      console.error(`Found ${dataverseContacts.length} contacts in Dataverse`);

      // Get or create contact folder in Outlook
      let contactFolder;
      try {
        const folders = await graphClient
          .api(`/users/${userEmail}/contactFolders`)
          .filter(`displayName eq '${folderName}'`)
          .get();

        if (folders.value && folders.value.length > 0) {
          contactFolder = folders.value[0];
        } else {
          contactFolder = await graphClient
            .api(`/users/${userEmail}/contactFolders`)
            .post({
              displayName: folderName,
            });
        }
      } catch (error: any) {
        console.error(`Error with contact folder: ${error.message}`);
        contactFolder = { id: "contacts" }; // Use default contacts folder
      }

      // Sync each contact
      for (const contact of dataverseContacts) {
        try {
          // Check if contact already exists in Outlook
          const existingContacts = await graphClient
            .api(`/users/${userEmail}/contactFolders/${contactFolder.id}/contacts`)
            .filter(`emailAddresses/any(e:e/address eq '${contact.emailaddress1}')`)
            .get();

          const outlookContact = {
            givenName: contact.firstname || "",
            surname: contact.lastname || "",
            emailAddresses: contact.emailaddress1
              ? [
                  {
                    address: contact.emailaddress1,
                    name: `${contact.firstname || ""} ${contact.lastname || ""}`.trim(),
                  },
                ]
              : [],
            businessPhones: contact.telephone1 ? [contact.telephone1] : [],
            mobilePhone: contact.mobilephone || "",
            jobTitle: contact.jobtitle || "",
            companyName: contact["cr950_client@OData.Community.Display.V1.FormattedValue"] || "",
          };

          if (existingContacts.value && existingContacts.value.length > 0) {
            // Update existing contact
            await graphClient
              .api(`/users/${userEmail}/contacts/${existingContacts.value[0].id}`)
              .patch(outlookContact);
          } else {
            // Create new contact
            await graphClient
              .api(`/users/${userEmail}/contactFolders/${contactFolder.id}/contacts`)
              .post(outlookContact);
          }

          syncedCount++;
        } catch (error: any) {
          console.error(`Error syncing contact ${contact.firstname} ${contact.lastname}: ${error.message}`);
          errorCount++;
        }
      }

      console.error(`✅ Synced ${syncedCount} contacts to Outlook`);
    }

    if (syncDirection === "outlook-to-dataverse" || syncDirection === "bidirectional") {
      console.error("Outlook to Dataverse sync not yet implemented");
      // This would require querying Outlook contacts and creating/updating in Dataverse
    }

    const duration = Date.now() - startTime;

    return {
      totalContacts: syncedCount + errorCount,
      syncedContacts: syncedCount,
      errors: errorCount,
      duration,
      syncedAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error(`Error syncing contacts: ${error.message}`);
    throw new Error(`Failed to sync contacts: ${error.message}`);
  }
}

/**
 * Get Outlook contacts
 */
export async function getOutlookContacts(params: {
  userEmail: string;
  folderName?: string;
  top?: number;
}): Promise<any[]> {
  const { userEmail, folderName, top = 50 } = params;

  try {
    const client = getGraphClient();

    let query = client.api(`/users/${userEmail}/contacts`).top(top);

    if (folderName) {
      const folders = await client
        .api(`/users/${userEmail}/contactFolders`)
        .filter(`displayName eq '${folderName}'`)
        .get();

      if (folders.value && folders.value.length > 0) {
        query = client
          .api(`/users/${userEmail}/contactFolders/${folders.value[0].id}/contacts`)
          .top(top);
      }
    }

    const contacts = await query.get();

    return contacts.value;
  } catch (error: any) {
    console.error(`Error getting Outlook contacts: ${error.message}`);
    throw error;
  }
}
