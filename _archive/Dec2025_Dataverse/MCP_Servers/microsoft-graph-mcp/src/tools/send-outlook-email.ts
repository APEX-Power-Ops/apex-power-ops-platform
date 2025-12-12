import { getGraphClient, sendEmail } from "../utils/graph-client.js";

/**
 * Result interface for email sending
 */
export interface EmailResult {
  status: "sent";
  from: string;
  to: string[];
  subject: string;
  sentAt: string;
}

/**
 * Send email via Outlook
 */
export async function sendOutlookEmail(params: {
  from: string;
  to: string[];
  subject: string;
  body: string;
  bodyType?: "text" | "html";
  cc?: string[];
  bcc?: string[];
  importance?: "low" | "normal" | "high";
  attachments?: { name: string; contentBytes: string }[];
}): Promise<EmailResult> {
  const {
    from,
    to,
    subject,
    body,
    bodyType = "html",
    cc,
    bcc,
    importance = "normal",
    attachments,
  } = params;

  console.error(`Sending email from ${from}...`);
  console.error(`To: ${to.join(", ")}`);
  console.error(`Subject: ${subject}`);

  try {
    const client = getGraphClient();

    const message: any = {
      message: {
        subject,
        body: {
          contentType: bodyType === "html" ? "HTML" : "Text",
          content: body,
        },
        toRecipients: to.map((email) => ({
          emailAddress: { address: email },
        })),
        importance,
      },
    };

    // Add optional fields
    if (cc && cc.length > 0) {
      message.message.ccRecipients = cc.map((email) => ({
        emailAddress: { address: email },
      }));
    }

    if (bcc && bcc.length > 0) {
      message.message.bccRecipients = bcc.map((email) => ({
        emailAddress: { address: email },
      }));
    }

    if (attachments && attachments.length > 0) {
      message.message.attachments = attachments.map((att) => ({
        "@odata.type": "#microsoft.graph.fileAttachment",
        name: att.name,
        contentBytes: att.contentBytes,
      }));
    }

    await client.api(`/users/${from}/sendMail`).post(message);

    console.error(`✅ Email sent successfully`);

    return {
      status: "sent",
      from,
      to,
      subject,
      sentAt: new Date().toISOString(),
    };
  } catch (error: any) {
    console.error(`Error sending email: ${error.message}`);
    throw new Error(`Failed to send email: ${error.message}`);
  }
}

/**
 * Get email drafts
 */
export async function getDrafts(userEmail: string): Promise<any[]> {
  try {
    const client = getGraphClient();

    const drafts = await client
      .api(`/users/${userEmail}/mailFolders/drafts/messages`)
      .top(25)
      .get();

    return drafts.value;
  } catch (error: any) {
    console.error(`Error getting drafts: ${error.message}`);
    throw error;
  }
}

/**
 * Create email draft
 */
export async function createDraft(params: {
  userEmail: string;
  to: string[];
  subject: string;
  body: string;
  bodyType?: "text" | "html";
}): Promise<any> {
  const { userEmail, to, subject, body, bodyType = "html" } = params;

  try {
    const client = getGraphClient();

    const draft = await client
      .api(`/users/${userEmail}/messages`)
      .post({
        subject,
        body: {
          contentType: bodyType === "html" ? "HTML" : "Text",
          content: body,
        },
        toRecipients: to.map((email) => ({
          emailAddress: { address: email },
        })),
      });

    return draft;
  } catch (error: any) {
    console.error(`Error creating draft: ${error.message}`);
    throw error;
  }
}
