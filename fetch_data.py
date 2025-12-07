import pandas as pd
from jira import JIRA
from jira.exceptions import JIRAError
import warnings

# نادیده گرفتن هشدارهای مربوط به Regex
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- تنظیمات ---
JIRA_SERVER = 'https://issues.apache.org/jira'
PROJECT_KEY = 'DUBBO' 

def connect_to_jira():
    print("Connecting to Apache Jira...")
    return JIRA(server=JIRA_SERVER)

def find_field_id(jira, field_names):
    print(f"Searching for field ID matching: {field_names}...")
    all_fields = jira.fields()
    for field in all_fields:
        if field['name'].lower() in [name.lower() for name in field_names]:
            print(f"Found field: '{field['name']}' -> ID: {field['id']}")
            return field['id']
    return None

def get_issues_safe(jira, project_key, sprint_field_id, sp_field_id):
    """
    تلاش هوشمند برای دریافت داده‌ها.
    اگر کوئری با پوینت نتیجه نداد، بدون پوینت می‌گیرد.
    """
    # --- تلاش اول: با Story Point ---
    if sp_field_id:
        try:
            print(f"Attempting to fetch with Story Points ({sp_field_id})...")
            # شرط پوینت را نگه می‌داریم تا ببینیم آیا دیتایی می‌دهد یا خیر
            jql = f'project = {project_key} AND sprint is not EMPTY AND "{sp_field_id}" is not EMPTY'
            fields = ['summary', 'status', 'created', 'resolutiondate', sprint_field_id, sp_field_id]
            
            issues = jira.search_issues(jql, maxResults=1000, fields=fields)
            
            # نکته کلیدی اصلاح شده: اگر لیست خالی بود، یعنی دسترسی نداریم یا دیتایی نیست
            if len(issues) > 0:
                return issues, sp_field_id
            else:
                print(">> Zero issues found with Story Points (Likely permission restriction).")
                print(">> Switching to Fallback Mode (Counting Issues)...")
                
        except JIRAError as e:
            print(f">> API Error with Story Points: {e}")
            print(">> Switching to Fallback Mode...")
    
    # --- تلاش دوم (Fallback): بدون Story Point ---
    # در این حالت فقط تعداد تسک‌ها را می‌شماریم
    print("Fetching issues WITHOUT Story Point filter...")
    jql = f'project = {project_key} AND sprint is not EMPTY'
    fields = ['summary', 'status', 'created', 'resolutiondate', sprint_field_id]
    
    # اینجا فقط ۱۰۰۰ تا می‌گیریم. برای پروژه واقعی شاید نیاز باشد maxResults را بیشتر کنید
    return jira.search_issues(jql, maxResults=1000, fields=fields), None

def get_sprint_data(jira):
    # 1. پیدا کردن ID ها
    sp_field_id = find_field_id(jira, ['Story Points', 'Story Point', 'Story Points Estimate'])
    sprint_field_id = find_field_id(jira, ['Sprint', 'Sprint/s'])
    
    if not sprint_field_id:
        print("Error: Could not find 'Sprint' field. Cannot proceed.")
        return None

    # 2. دریافت ایشوها (با استراتژی جدید)
    issues, valid_sp_id = get_issues_safe(jira, PROJECT_KEY, sprint_field_id, sp_field_id)
    
    if not issues:
        print("No issues found even in fallback mode.")
        return None

    sprint_metrics = {}
    print(f"Processing {len(issues)} issues...")

    for issue in issues:
        # استخراج اسپرینت
        sprints = getattr(issue.fields, sprint_field_id)
        if not sprints:
            continue
            
        try:
            # تلاش برای گرفتن نام آخرین اسپرینت
            last_sprint = sprints[-1]
            sprint_name = last_sprint.split('name=')[1].split(',')[0]
        except:
            sprint_name = str(sprints[-1])

        # استخراج مقدار (یا پوینت یا عدد ۱)
        val = 0
        if valid_sp_id:
            try:
                raw_val = getattr(issue.fields, valid_sp_id)
                if raw_val:
                    val = float(raw_val)
            except:
                val = 0
        
        # اگر پوینت نداشتیم (حالت Fallback)، هر تسک را ۱ امتیاز فرض می‌کنیم
        if val == 0 and not valid_sp_id:
            val = 1

        # بررسی وضعیت
        status = str(issue.fields.status.name)
        is_completed = status.lower() in ['resolved', 'closed', 'done']

        if sprint_name not in sprint_metrics:
            sprint_metrics[sprint_name] = {'PV': 0, 'EV': 0, 'Issue_Count': 0}
        
        sprint_metrics[sprint_name]['Issue_Count'] += 1
        sprint_metrics[sprint_name]['PV'] += val
        if is_completed:
            sprint_metrics[sprint_name]['EV'] += val

    return sprint_metrics

def save_to_excel(data):
    if not data:
        print("No data to save.")
        return

    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'Sprint_Name'
    df.reset_index(inplace=True)
    
    df['TD_SonarQube_Hours'] = '' 
    df['Sprint_End_Date'] = '' 
    
    # تلاش برای مرتب‌سازی عددی اسپرینت‌ها
    try:
        df['sort_key'] = df['Sprint_Name'].str.extract(r'(\d+)').astype(float)
        df = df.sort_values(by='sort_key').drop(columns=['sort_key'])
    except:
        df = df.sort_values(by='Sprint_Name')
    
    filename = f'{PROJECT_KEY}_EVM_Data_Auto.xlsx'
    df.to_excel(filename, index=False)
    print(f"Done! Data saved to {filename}")

# --- اجرای برنامه ---
if __name__ == "__main__":
    try:
        jira_conn = connect_to_jira()
        metrics = get_sprint_data(jira_conn)
        save_to_excel(metrics)
    except Exception as e:
        print(f"Critical Error: {e}")