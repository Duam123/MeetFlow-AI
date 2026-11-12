from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo


# STEP 1: Define the Excel file location
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_FOLDER = PROJECT_ROOT / "data"

DATA_FOLDER.mkdir(parents=True, exist_ok=True)

EXCEL_FILE = DATA_FOLDER / "meetflow_schedule.xlsx"


# STEP 2: Create a new Excel workbook
workbook = Workbook()


# STEP 3: Create Meetings sheet
meetings_sheet = workbook.active
meetings_sheet.title = "Meetings"

meeting_headers = [
    "Meeting_ID",
    "Meeting_Title",
    "Meeting_Date",
    "Start_Time",
    "End_Time",
    "Participants",
    "Participant_Emails",
    "Meeting_Link",
    "Agenda",
    "Status",
    "Reminder_Minutes",
]

meetings_sheet.append(meeting_headers)


# STEP 4: Add sample meeting records
meeting_data = [
    [
        "M001",
        "Project Review",
        "2026-11-17",
        "10:00",
        "11:00",
        "Ali, Sara",
        "ali@example.com, sara@example.com",
        "https://meet.google.com/example",
        "Discuss project progress",
        "Scheduled",
        15,
    ],
    [
        "M002",
        "Team Planning",
        "2026-11-18",
        "14:00",
        "15:00",
        "Ahmed, Dua",
        "ahmed@example.com, dua@example.com",
        "https://meet.google.com/example",
        "Plan upcoming tasks",
        "Scheduled",
        30,
    ],
]

for meeting in meeting_data:
    meetings_sheet.append(meeting)


# STEP 5: Create Tasks sheet
tasks_sheet = workbook.create_sheet("Tasks")

task_headers = [
    "Task_ID",
    "Task_Title",
    "Assigned_To",
    "Assigned_Email",
    "Due_Date",
    "Due_Time",
    "Priority",
    "Status",
    "Reminder_Minutes",
    "Related_Meeting_ID",
]

tasks_sheet.append(task_headers)


# STEP 6: Add sample task records
task_data = [
    [
        "T001",
        "Complete frontend development",
        "Ali",
        "ali@example.com",
        "2026-11-17",
        "17:00",
        "High",
        "Pending",
        60,
        "M001",
    ],
    [
        "T002",
        "Prepare testing report",
        "Sara",
        "sara@example.com",
        "2026-11-18",
        "12:00",
        "Medium",
        "Pending",
        30,
        "M001",
    ],
]

for task in task_data:
    tasks_sheet.append(task)


# STEP 7: Apply professional styling
header_fill = PatternFill(
    fill_type="solid",
    fgColor="243B64"
)

header_font = Font(
    bold=True,
    color="FFFFFF",
    size=11
)

for sheet in [meetings_sheet, tasks_sheet]:
    sheet.freeze_panes = "A2"

    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    sheet.auto_filter.ref = sheet.dimensions

    for column_cells in sheet.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:
            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        sheet.column_dimensions[column_letter].width = min(
            max_length + 4,
            35
        )


# STEP 8: Add Excel tables
meetings_table = Table(
    displayName="MeetingsTable",
    ref=meetings_sheet.dimensions
)

meetings_table_style = TableStyleInfo(
    name="TableStyleMedium2",
    showFirstColumn=False,
    showLastColumn=False,
    showRowStripes=True,
    showColumnStripes=False,
)

meetings_table.tableStyleInfo = meetings_table_style
meetings_sheet.add_table(meetings_table)


tasks_table = Table(
    displayName="TasksTable",
    ref=tasks_sheet.dimensions
)

tasks_table_style = TableStyleInfo(
    name="TableStyleMedium4",
    showFirstColumn=False,
    showLastColumn=False,
    showRowStripes=True,
    showColumnStripes=False,
)

tasks_table.tableStyleInfo = tasks_table_style
tasks_sheet.add_table(tasks_table)


# STEP 9: Save the Excel workbook
workbook.save(EXCEL_FILE)

print("\nMeetFlow AI Excel file created successfully!")
print(f"File location: {EXCEL_FILE}")
print("Sheets created: Meetings, Tasks")