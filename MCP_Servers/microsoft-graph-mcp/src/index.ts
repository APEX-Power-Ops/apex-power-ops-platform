#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

// Import Microsoft Graph tools
import { createSharePointFolder, listSharePointFolders } from "./tools/create-sharepoint-folder.js";
import { uploadToSharePoint } from "./tools/upload-to-sharepoint.js";
import { createTeamsMeeting, getMeetingDetails, cancelMeeting } from "./tools/create-teams-meeting.js";
import { sendOutlookEmail, getDrafts, createDraft } from "./tools/send-outlook-email.js";
import { getCalendarAvailability, findMeetingTime, getCalendarEvents } from "./tools/get-calendar-availability.js";
import { syncContacts, getOutlookContacts } from "./tools/sync-contacts.js";

// Create server instance
const server = new Server(
  {
    name: "microsoft-graph-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definitions
const TOOLS = [
  {
    name: "create_sharepoint_folder",
    description:
      "Create a folder in SharePoint document library. Supports nested folder creation. Useful for organizing project documents.",
    inputSchema: {
      type: "object",
      properties: {
        siteName: {
          type: "string",
          description: "SharePoint site name or URL",
        },
        folderPath: {
          type: "string",
          description: "Folder path to create (e.g., 'Projects/2025/LASNAP16'). Supports nested folders.",
        },
        description: {
          type: "string",
          description: "Optional description for the folder",
        },
      },
      required: ["siteName", "folderPath"],
    },
  },
  {
    name: "upload_to_sharepoint",
    description:
      "Upload a file to SharePoint document library. Supports both small (<4MB) and large files with resumable upload.",
    inputSchema: {
      type: "object",
      properties: {
        siteName: {
          type: "string",
          description: "SharePoint site name or URL",
        },
        folderPath: {
          type: "string",
          description: "Destination folder path in SharePoint",
        },
        filePath: {
          type: "string",
          description: "Local file path to upload",
        },
        fileName: {
          type: "string",
          description: "Optional: custom filename (defaults to original filename)",
        },
        overwrite: {
          type: "boolean",
          description: "Overwrite existing file. Default: false",
          default: false,
        },
      },
      required: ["siteName", "folderPath", "filePath"],
    },
  },
  {
    name: "create_teams_meeting",
    description:
      "Create a Microsoft Teams online meeting with calendar event. Automatically generates Teams join link.",
    inputSchema: {
      type: "object",
      properties: {
        organizerEmail: {
          type: "string",
          description: "Email address of meeting organizer",
        },
        subject: {
          type: "string",
          description: "Meeting subject/title",
        },
        startTime: {
          type: "string",
          description: "Start time in ISO 8601 format (e.g., '2025-11-25T10:00:00')",
        },
        endTime: {
          type: "string",
          description: "End time in ISO 8601 format",
        },
        attendees: {
          type: "array",
          items: { type: "string" },
          description: "Array of attendee email addresses",
        },
        body: {
          type: "string",
          description: "Optional meeting description/agenda (HTML supported)",
        },
        location: {
          type: "string",
          description: "Optional physical location",
        },
        timeZone: {
          type: "string",
          description: "Time zone (default: 'Pacific Standard Time')",
          default: "Pacific Standard Time",
        },
      },
      required: ["organizerEmail", "subject", "startTime", "endTime", "attendees"],
    },
  },
  {
    name: "send_outlook_email",
    description:
      "Send an email via Outlook. Supports HTML content, CC/BCC, importance levels, and attachments.",
    inputSchema: {
      type: "object",
      properties: {
        from: {
          type: "string",
          description: "Sender email address",
        },
        to: {
          type: "array",
          items: { type: "string" },
          description: "Array of recipient email addresses",
        },
        subject: {
          type: "string",
          description: "Email subject",
        },
        body: {
          type: "string",
          description: "Email body content",
        },
        bodyType: {
          type: "string",
          enum: ["text", "html"],
          description: "Body content type. Default: 'html'",
          default: "html",
        },
        cc: {
          type: "array",
          items: { type: "string" },
          description: "Optional CC recipients",
        },
        bcc: {
          type: "array",
          items: { type: "string" },
          description: "Optional BCC recipients",
        },
        importance: {
          type: "string",
          enum: ["low", "normal", "high"],
          description: "Email importance. Default: 'normal'",
          default: "normal",
        },
      },
      required: ["from", "to", "subject", "body"],
    },
  },
  {
    name: "get_calendar_availability",
    description:
      "Check a user's calendar availability for a given time range. Returns busy/free slots and availability view.",
    inputSchema: {
      type: "object",
      properties: {
        userEmail: {
          type: "string",
          description: "User email address to check availability",
        },
        startTime: {
          type: "string",
          description: "Start time in ISO 8601 format",
        },
        endTime: {
          type: "string",
          description: "End time in ISO 8601 format",
        },
        timeZone: {
          type: "string",
          description: "Time zone (default: 'Pacific Standard Time')",
          default: "Pacific Standard Time",
        },
        intervalMinutes: {
          type: "number",
          description: "Time slot interval in minutes. Default: 30",
          default: 30,
        },
      },
      required: ["userEmail", "startTime", "endTime"],
    },
  },
  {
    name: "sync_contacts",
    description:
      "Sync contacts between Dataverse and Outlook. Creates/updates contacts in specified Outlook folder.",
    inputSchema: {
      type: "object",
      properties: {
        userEmail: {
          type: "string",
          description: "User email address for Outlook contacts",
        },
        syncDirection: {
          type: "string",
          enum: ["dataverse-to-outlook", "outlook-to-dataverse", "bidirectional"],
          description: "Sync direction. Default: 'dataverse-to-outlook'",
          default: "dataverse-to-outlook",
        },
        folderName: {
          type: "string",
          description: "Outlook contact folder name. Default: 'RESA Contacts'",
          default: "RESA Contacts",
        },
      },
      required: ["userEmail"],
    },
  },
  {
    name: "find_meeting_time",
    description:
      "Find common available time slots for multiple attendees. Useful for scheduling meetings.",
    inputSchema: {
      type: "object",
      properties: {
        attendees: {
          type: "array",
          items: { type: "string" },
          description: "Array of attendee email addresses",
        },
        duration: {
          type: "number",
          description: "Meeting duration in minutes",
        },
        startTime: {
          type: "string",
          description: "Search start time in ISO 8601 format",
        },
        endTime: {
          type: "string",
          description: "Search end time in ISO 8601 format",
        },
        timeZone: {
          type: "string",
          description: "Time zone (default: 'Pacific Standard Time')",
          default: "Pacific Standard Time",
        },
      },
      required: ["attendees", "duration", "startTime", "endTime"],
    },
  },
  {
    name: "list_sharepoint_folders",
    description:
      "List folders in a SharePoint document library location.",
    inputSchema: {
      type: "object",
      properties: {
        siteName: {
          type: "string",
          description: "SharePoint site name or URL",
        },
        folderPath: {
          type: "string",
          description: "Folder path to list (default: root '/')",
          default: "/",
        },
      },
      required: ["siteName"],
    },
  },
];

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    if (!args) {
      throw new McpError(ErrorCode.InvalidParams, "Missing arguments");
    }

    switch (name) {
      case "create_sharepoint_folder": {
        const result = await createSharePointFolder({
          siteName: args.siteName as string,
          folderPath: args.folderPath as string,
          description: args.description as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "upload_to_sharepoint": {
        const result = await uploadToSharePoint({
          siteName: args.siteName as string,
          folderPath: args.folderPath as string,
          filePath: args.filePath as string,
          fileName: args.fileName as string | undefined,
          overwrite: args.overwrite as boolean | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "create_teams_meeting": {
        const result = await createTeamsMeeting({
          organizerEmail: args.organizerEmail as string,
          subject: args.subject as string,
          startTime: args.startTime as string,
          endTime: args.endTime as string,
          attendees: args.attendees as string[],
          body: args.body as string | undefined,
          location: args.location as string | undefined,
          timeZone: args.timeZone as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "send_outlook_email": {
        const result = await sendOutlookEmail({
          from: args.from as string,
          to: args.to as string[],
          subject: args.subject as string,
          body: args.body as string,
          bodyType: args.bodyType as "text" | "html" | undefined,
          cc: args.cc as string[] | undefined,
          bcc: args.bcc as string[] | undefined,
          importance: args.importance as "low" | "normal" | "high" | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "get_calendar_availability": {
        const result = await getCalendarAvailability({
          userEmail: args.userEmail as string,
          startTime: args.startTime as string,
          endTime: args.endTime as string,
          timeZone: args.timeZone as string | undefined,
          intervalMinutes: args.intervalMinutes as number | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "sync_contacts": {
        const result = await syncContacts({
          userEmail: args.userEmail as string,
          syncDirection: args.syncDirection as any,
          folderName: args.folderName as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "find_meeting_time": {
        const result = await findMeetingTime({
          attendees: args.attendees as string[],
          duration: args.duration as number,
          startTime: args.startTime as string,
          endTime: args.endTime as string,
          timeZone: args.timeZone as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "list_sharepoint_folders": {
        const result = await listSharePointFolders({
          siteName: args.siteName as string,
          folderPath: args.folderPath as string | undefined,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`
        );
    }
  } catch (error: any) {
    console.error(`Error executing tool: ${error.message}`);
    throw new McpError(
      ErrorCode.InternalError,
      `Tool execution failed: ${error.message}`
    );
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("microsoft-graph-mcp server started");
  console.error("Available tools:");
  console.error("  - create_sharepoint_folder: Create folders in SharePoint");
  console.error("  - upload_to_sharepoint: Upload files to SharePoint");
  console.error("  - create_teams_meeting: Schedule Teams meetings");
  console.error("  - send_outlook_email: Send emails via Outlook");
  console.error("  - get_calendar_availability: Check calendar availability");
  console.error("  - sync_contacts: Sync Dataverse contacts to Outlook");
  console.error("  - find_meeting_time: Find common meeting times");
  console.error("  - list_sharepoint_folders: List SharePoint folders");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
