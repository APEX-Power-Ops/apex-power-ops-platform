import { Client } from "@microsoft/microsoft-graph-client";
import { ClientSecretCredential } from "@azure/identity";
import { TokenCredentialAuthenticationProvider } from "@microsoft/microsoft-graph-client/authProviders/azureTokenCredentials/index.js";
import "isomorphic-fetch";

/**
 * Configuration from environment variables
 */
export const config = {
  AZURE_TENANT_ID: process.env.AZURE_TENANT_ID || "",
  AZURE_CLIENT_ID: process.env.AZURE_CLIENT_ID || "",
  AZURE_CLIENT_SECRET: process.env.AZURE_CLIENT_SECRET || "",
  ENVIRONMENT: process.env.ENVIRONMENT || "DEVELOPMENT",
};

// Validate configuration
if (!config.AZURE_TENANT_ID || !config.AZURE_CLIENT_ID || !config.AZURE_CLIENT_SECRET) {
  throw new Error("Missing required environment variables: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET");
}

// Safety check
if (config.ENVIRONMENT !== "DEVELOPMENT") {
  throw new Error("This server is configured for DEVELOPMENT environment only. Do not run in production.");
}

/**
 * Graph API client singleton
 */
let graphClient: Client | null = null;

/**
 * Get authenticated Microsoft Graph client
 */
export function getGraphClient(): Client {
  if (!graphClient) {
    // Create credential
    const credential = new ClientSecretCredential(
      config.AZURE_TENANT_ID,
      config.AZURE_CLIENT_ID,
      config.AZURE_CLIENT_SECRET
    );

    // Create authentication provider
    const authProvider = new TokenCredentialAuthenticationProvider(credential, {
      scopes: ["https://graph.microsoft.com/.default"],
    });

    // Create Graph client
    graphClient = Client.initWithMiddleware({
      authProvider,
    });
  }

  return graphClient;
}

/**
 * SharePoint site utility functions
 */
export interface SharePointSite {
  id: string;
  displayName: string;
  webUrl: string;
}

/**
 * Get SharePoint site by name or URL
 */
export async function getSharePointSite(siteNameOrUrl: string): Promise<SharePointSite> {
  const client = getGraphClient();

  try {
    // If it looks like a URL, use it directly
    if (siteNameOrUrl.startsWith("http")) {
      const url = new URL(siteNameOrUrl);
      const hostname = url.hostname;
      const sitePath = url.pathname;
      
      const site = await client
        .api(`/sites/${hostname}:${sitePath}`)
        .get();
      
      return {
        id: site.id,
        displayName: site.displayName,
        webUrl: site.webUrl,
      };
    }

    // Otherwise, search for site by name
    const sites = await client
      .api("/sites")
      .filter(`displayName eq '${siteNameOrUrl}'`)
      .get();

    if (sites.value && sites.value.length > 0) {
      return {
        id: sites.value[0].id,
        displayName: sites.value[0].displayName,
        webUrl: sites.value[0].webUrl,
      };
    }

    throw new Error(`SharePoint site not found: ${siteNameOrUrl}`);
  } catch (error: any) {
    console.error(`Error getting SharePoint site: ${error.message}`);
    throw error;
  }
}

/**
 * Get default document library for a site
 */
export async function getDefaultDocumentLibrary(siteId: string): Promise<any> {
  const client = getGraphClient();

  try {
    const drives = await client
      .api(`/sites/${siteId}/drives`)
      .get();

    // Find the default Documents library
    const defaultDrive = drives.value.find((drive: any) => 
      drive.name === "Documents" || drive.driveType === "documentLibrary"
    );

    if (!defaultDrive) {
      throw new Error("Default document library not found");
    }

    return defaultDrive;
  } catch (error: any) {
    console.error(`Error getting document library: ${error.message}`);
    throw error;
  }
}

/**
 * Outlook/Calendar utility functions
 */
export interface CalendarEvent {
  subject: string;
  start: { dateTime: string; timeZone: string };
  end: { dateTime: string; timeZone: string };
  attendees?: { emailAddress: { address: string; name?: string } }[];
  body?: { contentType: string; content: string };
  location?: { displayName: string };
  isOnlineMeeting?: boolean;
  onlineMeetingProvider?: string;
}

/**
 * Create calendar event
 */
export async function createCalendarEvent(userId: string, event: CalendarEvent): Promise<any> {
  const client = getGraphClient();

  try {
    const createdEvent = await client
      .api(`/users/${userId}/calendar/events`)
      .post(event);

    return createdEvent;
  } catch (error: any) {
    console.error(`Error creating calendar event: ${error.message}`);
    throw error;
  }
}

/**
 * Get user's calendar availability
 */
export async function getCalendarAvailability(
  userId: string,
  startTime: string,
  endTime: string
): Promise<any> {
  const client = getGraphClient();

  try {
    const schedules = await client
      .api(`/users/${userId}/calendar/getSchedule`)
      .post({
        schedules: [userId],
        startTime: { dateTime: startTime, timeZone: "UTC" },
        endTime: { dateTime: endTime, timeZone: "UTC" },
      });

    return schedules;
  } catch (error: any) {
    console.error(`Error getting calendar availability: ${error.message}`);
    throw error;
  }
}

/**
 * Send email via Outlook
 */
export async function sendEmail(params: {
  from: string;
  to: string[];
  subject: string;
  body: string;
  bodyType?: "text" | "html";
  cc?: string[];
  bcc?: string[];
}): Promise<void> {
  const client = getGraphClient();

  try {
    const message = {
      message: {
        subject: params.subject,
        body: {
          contentType: params.bodyType === "html" ? "HTML" : "Text",
          content: params.body,
        },
        toRecipients: params.to.map((email) => ({
          emailAddress: { address: email },
        })),
        ccRecipients: params.cc?.map((email) => ({
          emailAddress: { address: email },
        })),
        bccRecipients: params.bcc?.map((email) => ({
          emailAddress: { address: email },
        })),
      },
    };

    await client
      .api(`/users/${params.from}/sendMail`)
      .post(message);
  } catch (error: any) {
    console.error(`Error sending email: ${error.message}`);
    throw error;
  }
}

console.error("Microsoft Graph client initialized");
console.error(`Environment: ${config.ENVIRONMENT}`);
console.error(`Tenant ID: ${config.AZURE_TENANT_ID}`);
