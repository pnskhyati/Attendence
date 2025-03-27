import pandas as pd
import re

def run(path):
    xls = pd.ExcelFile("C:/Users/LENOVO/Downloads/Data Engineering/Data Engineering/data - sample.xlsx")
    
    attendance_df = pd.read_excel(xls, sheet_name="attendance")
    attendance_df['attendance_date'] = pd.to_datetime(attendance_df['attendance_date'])
    attendance_df = attendance_df.sort_values(by=['student_id', 'attendance_date'])

    absence_records = []
    
    for student_id, group in attendance_df.groupby('student_id'):
        group = group.reset_index(drop=True)
        group['absent_streak'] = (group['status'] == 'Absent').astype(int)
        group['streak_start'] = group['attendance_date'].diff().dt.days.ne(1).cumsum()

        streaks = group.groupby('streak_start').agg(
            start_date=('attendance_date', 'first'),
            end_date=('attendance_date', 'last'),
            total_absent_days=('absent_streak', 'sum')
        ).reset_index()

        streaks = streaks[streaks['total_absent_days'] > 3]
        
        if not streaks.empty:
            latest_streak = streaks.iloc[-1] 
            absence_records.append([
                student_id,
                latest_streak['start_date'],
                latest_streak['end_date'],
                latest_streak['total_absent_days']
            ])

   
    absence_df = pd.DataFrame(absence_records, columns=['student_id', 'absence_start_date', 'absence_end_date', 'total_absent_days'])

    final_df = absence_df.merge(students_df[['student_id', 'parent_email', 'student_name']], on='student_id', how='left')

    def is_valid_email(email):
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*@[a-zA-Z]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email)))

    final_df['email'] = final_df['parent_email'].apply(lambda x: x if is_valid_email(x) else None)

    def generate_message(row):
        if pd.notna(row['email']):
            return f"Dear Parent, your child {row['student_name']} was absent from {row['absence_start_date'].strftime('%Y-%m-%d')} to {row['absence_end_date'].strftime('%Y-%m-%d')} for {row['total_absent_days']} days. Please ensure their attendance improves."
        return None

    final_df['msg'] = final_df.apply(generate_message, axis=1)

    final_df = final_df[['student_id', 'absence_start_date', 'absence_end_date', 'total_absent_days', 'email', 'msg']]

    return final_df