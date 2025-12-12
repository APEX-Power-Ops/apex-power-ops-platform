import { getGraphClient, createCalendarEvent, CalendarEvent } from "../utils/graph-client.js";

/**
 * Result interface for meeting creation
 */
export interface MeetingResult {
  meetingId: string;
  subject: string;
  startTime: string;
  endTime: string;
  joinUrl?: string;
  webLink: string;
  organizerEmail: string;
  attendees: string[];
}

/**
 * Create a Teams meeting
 */
export async function createTeamsMeeting(params: {
  organizerEmail: string;
  subject: string;
  startTime: string;
  endTime: string;
  attendees: string[];
  body?: string;
  location?: string;
  timeZone?: string;
}): Promise<MeetingResult> {
  const {
    organizerEmail,
    subject,
    startTime,
    endTime,
    attendees,
    body,
    location,
    timeZone = "Pacific Standard Time",
  } = params;

  console.error(`Creating Teams meeting: ${subject}...`);
  console.error(`Organizer: ${organizerEmail}`);
  console.error(`Time: ${startTime} to ${endTime}`);
  console.error(`Attendees: ${attendees.join(", ")}`);

  try {
    const client = getGraphClient();

    // Create calendar event with Teams meeting
    const event: CalendarEvent = {
      subject,
      start: {
        dateTime: startTime,
        timeZone,
      },
      end: {
        dateTime: endTime,
        timeZone,
      },
      attendees: attendees.map((email) => ({
        emailAddress: {
          address: email,
        },
        type: "required",
      })),
      isOnlineMeeting: true,
      onlineMeetingProvider: "teamsForBusiness",
    };

    // Add optional fields
    if (body) {
      event.body = {
        contentType: "HTML",
        content: body,
      };
    }

    if (location) {
      event.location = {
        displayName: location,
      };
    }

    const createdEvent = await client
      .api(`/users/${organizerEmail}/calendar/events`)
      .post(event);

    console.error(`✅ Teams meeting created successfully`);
    console.error(`Join URL: ${createdEvent.onlineMeeting?.joinUrl || "N/A"}`);

    return {
      meetingId: createdEvent.id,
      subject: createdEvent.subject,
      startTime: createdEvent.start.dateTime,
      endTime: createdEvent.end.dateTime,
      joinUrl: createdEvent.onlineMeeting?.joinUrl,
      webLink: createdEvent.webLink,
      organizerEmail: createdEvent.organizer.emailAddress.address,
      attendees: createdEvent.attendees.map((a: any) => a.emailAddress.address),
    };
  } catch (error: any) {
    console.error(`Error creating Teams meeting: ${error.message}`);
    throw new Error(`Failed to create Teams meeting: ${error.message}`);
  }
}

/**
 * Get meeting details
 */
export async function getMeetingDetails(params: {
  userEmail: string;
  meetingId: string;
}): Promise<any> {
  const { userEmail, meetingId } = params;

  try {
    const client = getGraphClient();

    const event = await client
      .api(`/users/${userEmail}/calendar/events/${meetingId}`)
      .get();

    return event;
  } catch (error: any) {
    console.error(`Error getting meeting details: ${error.message}`);
    throw error;
  }
}

/**
 * Cancel a meeting
 */
export async function cancelMeeting(params: {
  userEmail: string;
  meetingId: string;
  comment?: string;
}): Promise<void> {
  const { userEmail, meetingId, comment } = params;

  try {
    const client = getGraphClient();

    await client
      .api(`/users/${userEmail}/calendar/events/${meetingId}/cancel`)
      .post({
        comment: comment || "Meeting cancelled",
      });

    console.error(`✅ Meeting cancelled successfully`);
  } catch (error: any) {
    console.error(`Error cancelling meeting: ${error.message}`);
    throw error;
  }
}
