
from pathlib import Path
import pandas as pd


# STEP 1: Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# STEP 2: Define the Excel file path
EXCEL_FILE = PROJECT_ROOT / "data" / "meetflow_schedule.xlsx"


# STEP 3: Create a function to read meetings
def load_meetings():

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_FILE}"
        )

    meetings_df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Meetings"
    )

    return meetings_df


# STEP 4: Create a function to read tasks
def load_tasks():

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_FILE}"
        )

    tasks_df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Tasks"
    )

    return tasks_df


# STEP 5: Display the data
def main():

    print("\n========== MEETFLOW AI ==========")

    print("\n--- MEETING SCHEDULE ---")

    meetings = load_meetings()

    print(meetings.to_string(index=False))

    print("\n--- TASK SCHEDULE ---")

    tasks = load_tasks()

    print(tasks.to_string(index=False))

    print("\nExcel data loaded successfully!")


# STEP 6: Run the program
if __name__ == "__main__":
    main()
