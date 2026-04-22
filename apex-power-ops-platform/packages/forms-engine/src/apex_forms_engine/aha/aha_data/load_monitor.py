"""
AHA Activity Data: Load Monitor Installation
Source: C&W BDC AHA - Load Monitor Installation (DOCX)
"""

ACTIVITY = {
    "aha_form_id": "AHA",
    "activity_name": "Load Monitor Installation",
    "crew_rows": 4,
    "filename_parts": {
        "client": "CW",              # Cushman & Wakefield
        "project": "BDC",            # Baton Rouge Data Center
        "location": "Mech_A_SWBD",   # Mechanical Room A, Switchboard
    },
    "qualification": {
        "crew_leader": "Crew leader must be certified Level 2 for Load Monitor Installation.",
        "crew_member": "Crew member/assistant can be a certified Level 1 Load Monitor Installation.",
        "note": (
            "If a crew member is assigned that has not completed certification of "
            "Level 1 for this activity, the Crew Leader must provide direct supervision "
            "and on-the-job training for the crew member."
        ),
    },
    "task_steps": [
        {
            "step": "Traveling to and from your work areas",
            "hazards": "Slips/Trips/Falls\nStruck by",
            "mitigations": (
                "Eyes on path. Watch out for mobile equipment. "
                "Clean work area and maintain good housekeeping. "
                "Report all hazards to the crew leader."
            ),
            "rac_normal": "L",
        },
        {
            "step": "Perform Electric Shock Risk Assessment per NFPA 70E 130.4",
            "hazards": "N/A",
            "mitigations": (
                "Establish Limited Approach Boundary by use of danger tape or barriers. "
                "Determine required PPE per NFPA 70E Table 130.4(E)(a) or 130.4(E)(b)."
            ),
            "rac_normal": "L",
        },
        {
            "step": "Analyze each individual panel to determine available arc flash energy",
            "hazards": "N/A",
            "mitigations": (
                "Arc Flash Hazard Assessment. Analyze each individual panel for "
                "arc flash energy. Compare available incident energy against "
                "PPE arc rating. Do not exceed PPE rating."
            ),
            "rac_normal": "L",
        },
        {
            "step": "Opening/Closing Bolted Covers or Panel board covers",
            "hazards": "Shock/Arc Flash\nInadvertent Trip",
            "mitigations": (
                "Open doors slowly without rapid movement. Some relays can trip from "
                "door vibration. Do not rest tools or equipment on energized busbars."
            ),
            "rac_normal": "L",
        },
        {
            "step": "Removal of Bolted Covers or Panel board covers",
            "hazards": "Shock/Arc Flash",
            "mitigations": (
                "Panel covers will be removed by two technicians. If opening a bolted "
                "cover that may expose energized parts, don appropriate PPE before "
                "removing the last bolt. Stand to the side when removing the cover."
            ),
            "rac_normal": "L",
        },
        {
            "step": "Install voltage leads and CT leads for load monitoring",
            "hazards": "Shock/Arc Flash",
            "mitigations": (
                "Ensure all voltage and current leads are installed away from moving "
                "parts and not in contact with energized busbars. Secure leads to "
                "prevent contact with energized components. Verify CT polarity."
            ),
            "rac_normal": "M",
        },
        {
            "step": (
                "Verify meter readings & begin monitoring using laptop and Bluetooth connection"
            ),
            "hazards": "Exposed Fixed Circuit Part",
            "mitigations": (
                "Maintain Restricted Approach Boundary while confirming meter readings. "
                "Use insulated tools. Verify Bluetooth connection is stable before "
                "leaving the area unattended."
            ),
            "rac_normal": "M",
        },
        {
            "step": "Installation of Bolted Covers or Panel board covers",
            "hazards": "Pinch wire",
            "mitigations": (
                "When panel board covers are placed back on, wires can be pinched. "
                "Route all wires and leads clear of cover edges. "
                "Use two technicians for cover installation."
            ),
            "rac_normal": "M",
        },
        {
            "step": "Installation of Bolted Covers or Panel board covers",
            "hazards": "Inadvertent Trip\nShock/Arc Flash",
            "mitigations": (
                "When placing panel board covers on, it is easy to accidentally come "
                "in contact with energized components. Use caution and appropriate PPE. "
                "Do not force covers into place."
            ),
            "rac_normal": "M",
        },
        {
            "step": "Housekeeping and Final Cleanup",
            "hazards": "Slips/Trips/Falls",
            "mitigations": (
                "Clean work area and remove barriers from Limited Approach Boundary. "
                "Collect all tools and equipment. Verify no items left inside panels."
            ),
            "rac_normal": "L",
        },
    ],
}
