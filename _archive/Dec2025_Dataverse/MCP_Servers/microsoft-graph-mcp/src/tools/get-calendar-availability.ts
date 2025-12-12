import { getGraphClient } from "../utils/graph-client.js";

/**
 * Availability result interface
 */
export interface AvailabilityResult {
  userEmail: string;
  startTime: string;
  endTime: string;
  availabilityView: string;
  busySlots: TimeSlot[];
  freeSlots: TimeSlot[];
}

export interface TimeSlot {
  start: string;
  end: string;
  status: "free" | "tentative" | "busy" | "oof" | "workingElsewhere";
}

/**
 * Get calendar availability for a user
 */
export async function getCalendarAvailability(params: {
  userEmail: string;
  startTime: string;
  endTime: string;
  timeZone?: string;
  intervalMinutes?: number;
}): Promise<AvailabilityResult> {
  const {
    userEmail,
    startTime,
    endTime,
    timeZone = "Pacific Standard Time",
    intervalMinutes = 30,
  } = params;

  console.error(`Getting calendar availability for: ${userEmail}`);
  console.error(`Time range: ${startTime} to ${endTime}`);

  try {
    const client = getGraphClient();

    const scheduleRequest = {
      schedules: [userEmail],
      startTime: {
        dateTime: startTime,
        timeZone,
      },
      endTime: {
        dateTime: endTime,
        timeZone,
      },
      availabilityViewInterval: intervalMinutes,
    };

    const response = await client
      .api("/users/${userEmail}/calendar/getSchedule")
      .post(scheduleRequest);

    const schedule = response.value[0];

    // Parse availability view
    const busySlots: TimeSlot[] = [];
    const freeSlots: TimeSlot[] = [];

    // Availability view is a string where each character represents a time slot
    // 0 = free, 1 = tentative, 2 = busy, 3 = out of office, 4 = working elsewhere
    const availabilityView = schedule.availabilityView || "";

    // Convert schedule items to slots
    if (schedule.scheduleItems) {
      for (const item of schedule.scheduleItems) {
        const slot: TimeSlot = {
          start: item.start.dateTime,
          end: item.end.dateTime,
          status: item.status,
        };

        if (item.status === "free") {
          freeSlots.push(slot);
        } else {
          busySlots.push(slot);
        }
      }
    }

    console.error(`✅ Availability retrieved`);
    console.error(`Busy slots: ${busySlots.length}`);
    console.error(`Free slots: ${freeSlots.length}`);

    return {
      userEmail,
      startTime,
      endTime,
      availabilityView,
      busySlots,
      freeSlots,
    };
  } catch (error: any) {
    console.error(`Error getting calendar availability: ${error.message}`);
    throw new Error(`Failed to get calendar availability: ${error.message}`);
  }
}

/**
 * Find common free time for multiple users
 */
export async function findMeetingTime(params: {
  attendees: string[];
  duration: number;
  startTime: string;
  endTime: string;
  timeZone?: string;
}): Promise<any> {
  const { attendees, duration, startTime, endTime, timeZone = "Pacific Standard Time" } = params;

  console.error(`Finding meeting time for ${attendees.length} attendees...`);
  console.error(`Duration: ${duration} minutes`);

  try {
    const client = getGraphClient();

    const meetingTimeRequest = {
      attendees: attendees.map((email) => ({
        emailAddress: {
          address: email,
        },
        type: "required",
      })),
      timeConstraint: {
        timeslots: [
          {
            start: {
              dateTime: startTime,
              timeZone,
            },
            end: {
              dateTime: endTime,
              timeZone,
            },
          },
        ],
      },
      meetingDuration: `PT${duration}M`,
      returnSuggestionReasons: true,
      minimumAttendeePercentage: 100,
    };

    // Use the organizer's email (first attendee) for the API call
    const organizerEmail = attendees[0];

    const suggestions = await client
      .api(`/users/${organizerEmail}/findMeetingTimes`)
      .post(meetingTimeRequest);

    console.error(`✅ Found ${suggestions.meetingTimeSuggestions?.length || 0} possible meeting times`);

    return suggestions;
  } catch (error: any) {
    console.error(`Error finding meeting time: ${error.message}`);
    throw error;
  }
}

/**
 * Get user's calendar events
 */
export async function getCalendarEvents(params: {
  userEmail: string;
  startTime: string;
  endTime: string;
}): Promise<any[]> {
  const { userEmail, startTime, endTime } = params;

  try {
    const client = getGraphClient();

    const events = await client
      .api(`/users/${userEmail}/calendar/calendarView`)
      .query({
        startDateTime: startTime,
        endDateTime: endTime,
      })
      .top(50)
      .get();

    return events.value;
  } catch (error: any) {
    console.error(`Error getting calendar events: ${error.message}`);
    throw error;
  }
}
