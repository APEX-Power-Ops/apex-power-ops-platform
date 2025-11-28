import { queryMetadata } from "../utils/dataverse-client.js";

/**
 * User guide result interface
 */
export interface UserGuideResult {
  role: string;
  sections: number;
  pages: number;
  content: string;
  generatedAt: string;
}

/**
 * Role-specific workflows and permissions
 */
const ROLE_WORKFLOWS = {
  FieldTech: {
    displayName: "Field Technician",
    description: "Front-line technicians performing installation and testing work",
    primaryTables: ["cr950_apparatus", "cr950_tasks"],
    workflows: [
      {
        title: "Mark Apparatus Complete",
        steps: [
          "Navigate to the Apparatus record",
          "Update Status to 'Complete'",
          "Enter Completion Date",
          "Add any notes or photos",
          "Save the record",
        ],
      },
      {
        title: "Log Time on Tasks",
        steps: [
          "Open the Task record",
          "Update Actual Hours worked",
          "Add notes about work performed",
          "Save the record",
        ],
      },
    ],
    permissions: {
      read: ["cr950_projectses", "cr950_projectscopes", "cr950_tasks", "cr950_apparatus"],
      create: [],
      update: ["cr950_apparatus", "cr950_tasks"],
      delete: [],
    },
  },
  JobLead: {
    displayName: "Job Lead / Foreman",
    description: "Lead technicians managing field crews and coordinating work",
    primaryTables: ["cr950_projectscopes", "cr950_tasks", "cr950_apparatus"],
    workflows: [
      {
        title: "Create New Scope",
        steps: [
          "Navigate to the Project",
          "Click 'New Scope'",
          "Enter Scope Name and Description",
          "Link to Client Location",
          "Save the record",
        ],
      },
      {
        title: "Assign Tasks to Crew",
        steps: [
          "Open the Scope",
          "View Task list",
          "Assign tasks to team members",
          "Set target completion dates",
          "Monitor progress",
        ],
      },
      {
        title: "Review Scope Completion",
        steps: [
          "Check all apparatus are marked complete",
          "Verify all tasks have actual hours",
          "Review photos and documentation",
          "Mark scope ready for billing",
        ],
      },
    ],
    permissions: {
      read: ["cr950_projectses", "cr950_projectscopes", "cr950_tasks", "cr950_apparatus", "cr950_clients", "cr950_locations"],
      create: ["cr950_projectscopes", "cr950_tasks", "cr950_apparatus"],
      update: ["cr950_projectscopes", "cr950_tasks", "cr950_apparatus"],
      delete: ["cr950_tasks", "cr950_apparatus"],
    },
  },
  PM: {
    displayName: "Project Manager",
    description: "Managers overseeing entire projects from planning to completion",
    primaryTables: ["cr950_projectses", "cr950_projectscopes", "cr950_clients", "cr950_locations"],
    workflows: [
      {
        title: "Create New Project",
        steps: [
          "Navigate to Projects",
          "Click 'New Project'",
          "Enter Project Name and Number",
          "Select Client and Primary Location",
          "Set Project Manager (yourself)",
          "Enter estimated hours and budget",
          "Save the project",
        ],
      },
      {
        title: "Monitor Project Progress",
        steps: [
          "Open Project Dashboard",
          "Review completion percentage",
          "Check actual vs estimated hours",
          "Review scope statuses",
          "Address any blockers or issues",
        ],
      },
      {
        title: "Generate Project Reports",
        steps: [
          "Navigate to Reports",
          "Select 'Project Status Report'",
          "Choose date range and filters",
          "Export to Excel or PDF",
          "Share with stakeholders",
        ],
      },
    ],
    permissions: {
      read: ["ALL"],
      create: ["cr950_projectses", "cr950_projectscopes", "cr950_tasks", "cr950_apparatus", "cr950_clients", "cr950_locations"],
      update: ["cr950_projectses", "cr950_projectscopes", "cr950_tasks", "cr950_apparatus"],
      delete: ["cr950_projectscopes", "cr950_tasks"],
    },
  },
  Billing: {
    displayName: "Billing / Accounting",
    description: "Staff managing invoicing, revenue recognition, and financial tracking",
    primaryTables: ["cr950_apparatusrevenues", "cr950_projectses", "cr950_clients"],
    workflows: [
      {
        title: "Generate Invoice from Completed Apparatus",
        steps: [
          "Navigate to Apparatus Revenue",
          "Filter for completed, unbilled apparatus",
          "Select apparatus for invoicing",
          "Generate invoice in QuickBooks",
          "Mark apparatus as billed",
          "Record invoice number and date",
        ],
      },
      {
        title: "Track Project Revenue",
        steps: [
          "Open Project record",
          "Review Total Revenue field",
          "Check revenue by scope",
          "Compare actual vs estimated revenue",
          "Export revenue report",
        ],
      },
      {
        title: "Month-End Revenue Recognition",
        steps: [
          "Run revenue report for month",
          "Reconcile with QuickBooks",
          "Identify discrepancies",
          "Update apparatus revenue records",
          "Generate financial statements",
        ],
      },
    ],
    permissions: {
      read: ["cr950_projectses", "cr950_projectscopes", "cr950_apparatus", "cr950_apparatusrevenues", "cr950_clients"],
      create: ["cr950_apparatusrevenues"],
      update: ["cr950_apparatusrevenues"],
      delete: [],
    },
  },
  Executive: {
    displayName: "Executive / Leadership",
    description: "Senior leadership viewing high-level metrics and dashboards",
    primaryTables: ["cr950_projectses", "cr950_clients"],
    workflows: [
      {
        title: "View Executive Dashboard",
        steps: [
          "Navigate to Dashboards",
          "Select 'Executive Overview'",
          "Review key metrics (revenue, active projects, completion rates)",
          "Drill down into specific projects or clients",
          "Export reports as needed",
        ],
      },
      {
        title: "Review Client Portfolio",
        steps: [
          "Navigate to Clients",
          "Sort by total revenue or project count",
          "Review client health indicators",
          "Identify top clients and growth opportunities",
        ],
      },
      {
        title: "Analyze Performance Trends",
        steps: [
          "Open Power BI reports",
          "Review month-over-month trends",
          "Compare actual vs budget",
          "Identify areas for improvement",
          "Share insights with management team",
        ],
      },
    ],
    permissions: {
      read: ["ALL"],
      create: [],
      update: [],
      delete: [],
    },
  },
};

/**
 * Generate role-specific user guide
 */
export async function generateUserGuide(params: {
  role: "FieldTech" | "JobLead" | "PM" | "Billing" | "Executive";
  includeScreenshots?: boolean;
  outputFormat?: "markdown" | "docx" | "pdf";
}): Promise<UserGuideResult> {
  const {
    role,
    includeScreenshots = false,
    outputFormat = "markdown",
  } = params;

  console.error(`Generating user guide for role: ${role}...`);

  try {
    const roleConfig = ROLE_WORKFLOWS[role];

    if (!roleConfig) {
      throw new Error(`Unknown role: ${role}`);
    }

    // Generate user guide content
    const content = generateUserGuideMarkdown(roleConfig, includeScreenshots);

    // Count sections and estimate pages
    const sections = roleConfig.workflows.length + 5; // workflows + intro + login + troubleshooting + faq + conclusion
    const pages = Math.ceil(content.length / 3000); // Rough estimate: 3000 chars per page

    return {
      role: roleConfig.displayName,
      sections,
      pages,
      content,
      generatedAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error(`Error generating user guide for ${role}:`, error.message);
    throw new Error(`Failed to generate user guide: ${error.message}`);
  }
}

/**
 * Generate user guide markdown content
 */
function generateUserGuideMarkdown(
  roleConfig: any,
  includeScreenshots: boolean
): string {
  let md = `# ${roleConfig.displayName} User Guide\n\n`;
  md += `**RESA Power Project Tracker**\n\n`;
  md += `---\n\n`;

  // Introduction
  md += `## Introduction\n\n`;
  md += `Welcome to the RESA Power Project Tracker! This guide is designed specifically for **${roleConfig.displayName}** users.\n\n`;
  md += `**Role Description:** ${roleConfig.description}\n\n`;
  md += `**Primary Tables You'll Work With:**\n`;
  for (const table of roleConfig.primaryTables) {
    md += `- ${formatTableName(table)}\n`;
  }
  md += `\n---\n\n`;

  // Getting Started
  md += `## Getting Started\n\n`;
  md += `### How to Log In\n\n`;
  md += `1. Navigate to the Dataverse environment URL\n`;
  md += `2. Sign in with your Microsoft 365 credentials\n`;
  md += `3. Select "RESA Power Project Tracker" from the app list\n`;
  md += `4. You'll see your personalized homepage based on your role\n\n`;

  if (includeScreenshots) {
    md += `![Login Screen](./images/login-screen.png)\n\n`;
  }

  md += `### Navigation\n\n`;
  md += `- **Left Sidebar:** Access to all tables and views\n`;
  md += `- **Top Bar:** Search, notifications, and profile menu\n`;
  md += `- **Main Area:** Records list or forms\n`;
  md += `- **Quick Create:** Use the + button to quickly create new records\n\n`;
  md += `---\n\n`;

  // Common Workflows
  md += `## Common Workflows\n\n`;
  md += `This section covers the most common tasks you'll perform as a ${roleConfig.displayName}.\n\n`;

  for (let i = 0; i < roleConfig.workflows.length; i++) {
    const workflow = roleConfig.workflows[i];
    md += `### ${i + 1}. ${workflow.title}\n\n`;

    md += `**Steps:**\n\n`;
    for (let j = 0; j < workflow.steps.length; j++) {
      md += `${j + 1}. ${workflow.steps[j]}\n`;
    }
    md += `\n`;

    if (includeScreenshots) {
      md += `![${workflow.title}](./images/${workflow.title.toLowerCase().replace(/\s+/g, "-")}.png)\n\n`;
    }

    md += `**Tips:**\n`;
    md += `- Save your work frequently\n`;
    md += `- Use the refresh button if data seems out of date\n`;
    md += `- Contact your supervisor if you encounter errors\n\n`;
    md += `---\n\n`;
  }

  // Permissions
  md += `## Your Permissions\n\n`;
  md += `As a ${roleConfig.displayName}, you have the following access levels:\n\n`;

  md += `### Read Access\n`;
  if (roleConfig.permissions.read.includes("ALL")) {
    md += `✅ **All Tables** - You can view all records in the system\n\n`;
  } else {
    for (const table of roleConfig.permissions.read) {
      md += `✅ ${formatTableName(table)}\n`;
    }
    md += `\n`;
  }

  md += `### Create Access\n`;
  if (roleConfig.permissions.create.length === 0) {
    md += `⬜ No create permissions\n\n`;
  } else {
    for (const table of roleConfig.permissions.create) {
      md += `✅ ${formatTableName(table)}\n`;
    }
    md += `\n`;
  }

  md += `### Update Access\n`;
  if (roleConfig.permissions.update.length === 0) {
    md += `⬜ No update permissions\n\n`;
  } else {
    for (const table of roleConfig.permissions.update) {
      md += `✅ ${formatTableName(table)}\n`;
    }
    md += `\n`;
  }

  md += `### Delete Access\n`;
  if (roleConfig.permissions.delete.length === 0) {
    md += `⬜ No delete permissions\n\n`;
  } else {
    for (const table of roleConfig.permissions.delete) {
      md += `✅ ${formatTableName(table)}\n`;
    }
    md += `\n`;
  }

  md += `---\n\n`;

  // Troubleshooting
  md += `## Troubleshooting\n\n`;
  md += `### Common Issues\n\n`;
  md += `#### "You don't have permission to access this record"\n`;
  md += `**Solution:** Contact your Project Manager or system administrator to request access.\n\n`;

  md += `#### "Record was modified by another user"\n`;
  md += `**Solution:** Refresh the page and retry your changes. Your local copy was out of date.\n\n`;

  md += `#### "Required field is missing"\n`;
  md += `**Solution:** Check that all fields marked with a red asterisk (*) are filled in before saving.\n\n`;

  md += `#### Data Not Appearing\n`;
  md += `**Solution:** Try refreshing the page. If the problem persists, check your filters and views.\n\n`;

  md += `---\n\n`;

  // FAQ
  md += `## Frequently Asked Questions\n\n`;
  md += `### How do I export data to Excel?\n`;
  md += `Click the Excel icon in the command bar, then choose "Download" or "Open in Excel Online".\n\n`;

  md += `### Can I customize my views?\n`;
  md += `Yes! You can create personal views by clicking "Create View" and setting your own filters and columns.\n\n`;

  md += `### How do I get reports?\n`;
  md += `Navigate to the "Reports" section in the left sidebar, or ask your Project Manager about Power BI dashboards.\n\n`;

  md += `### Who do I contact for help?\n`;
  md += `- **Technical Issues:** IT Support\n`;
  md += `- **Process Questions:** Your Project Manager\n`;
  md += `- **Access Requests:** System Administrator\n\n`;

  md += `---\n\n`;

  // Conclusion
  md += `## Additional Resources\n\n`;
  md += `- **Full Documentation:** [RESA Power Documentation Portal](docs-url)\n`;
  md += `- **Video Tutorials:** [RESA Power Training Videos](videos-url)\n`;
  md += `- **Support Email:** support@resapower.com\n`;
  md += `- **Support Phone:** (555) 123-4567\n\n`;

  md += `---\n\n`;
  md += `**Document Version:** 1.0\n`;
  md += `**Last Updated:** ${new Date().toLocaleDateString()}\n`;
  md += `**Generated By:** resa-docs-mcp\n`;

  return md;
}

/**
 * Format table name for display
 */
function formatTableName(logicalName: string): string {
  return logicalName
    .replace(/^cr950_/, "")
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
