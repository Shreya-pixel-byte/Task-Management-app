import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# ---------- Setup ----------
st.set_page_config(page_title="🧠 Project Dashboard", layout="wide")

# ---------- Add corkboard background ----------
st.markdown(
    """
    <style>
    .main {
        background-image: url('https://i.imgur.com/Ot5DWAW.png');
        background-size: cover;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Helper Functions ----------
def load_tasks():
    if os.path.exists("tasks.json"):
        with open("tasks.json", "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open("tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(name, description, deadline, priority, attachment_path=""):
    task = {
        "id": datetime.now().timestamp(),
        "name": name,
        "description": description,
        "deadline": str(deadline),
        "created": str(datetime.now().date()),
        "status": "To Do",
        "priority": priority,
        "attachment": attachment_path
    }
    tasks.append(task)
    save_tasks(tasks)

def color_by_priority(priority):
    return {"High": "#ff4b4b", "Medium": "#ffa500", "Low": "#4bb543"}.get(priority, "#d3d3d3")

# ---------- Load Tasks ----------
tasks = load_tasks()

# ---------- Sidebar: Add Task ----------
st.sidebar.header("➕ Create New Task")
with st.sidebar.form("task_form"):
    name = st.text_input("📝 Task Title")
    desc = st.text_area("📌 Description")
    deadline = st.date_input("📅 Deadline", min_value=datetime.now().date())
    priority = st.selectbox("🚦 Priority", ["Low", "Medium", "High"])
    file = st.file_uploader("📁 Attachment", type=["pdf", "png", "jpg", "docx"])
    submitted = st.form_submit_button("Create Task")

    if submitted and name:
        filepath = ""
        if file:
            os.makedirs("assets", exist_ok=True)
            filepath = f"assets/{file.name}"
            with open(filepath, "wb") as f:
                f.write(file.read())
        add_task(name, desc, deadline, priority, filepath)
        st.success("✅ Task added!")
        st.rerun()
    elif submitted:
        st.warning("⚠️ Task name required.")

# ---------- Dashboard Header ----------
st.title("📋 StickIt")
st.markdown("Organize tasks, manage deadlines, and collaborate visually.")

# ---------- Calendar View ----------
st.subheader("📆 Calendar Overview")
calendar_events = [
    {"title": t["name"], "start": t["deadline"], "end": t["deadline"], "color": color_by_priority(t["priority"])}
    for t in tasks
]
calendar(events=calendar_events, options={"initialView": "dayGridMonth", "height": 500})

# ---------- Task Metrics ----------
st.subheader("📊 Progress Overview")
df = pd.DataFrame(tasks)
if not df.empty:
    status_counts = df["status"].value_counts()
    st.markdown("### 🧩 Tasks by Status")
    st.bar_chart(status_counts)
else:
    st.info("No tasks available yet. Add one from the sidebar.")

# ---------- Task Board with Edit & Delete ----------
st.subheader("🗂️ Task Board")
columns = st.columns(3)
status_names = ["To Do", "In Progress", "Done"]

for i, status in enumerate(status_names):
    with columns[i]:
        st.markdown(f"### {status}")
        for t in tasks:
            if t["status"] == status:
                color = color_by_priority(t["priority"])

                with st.container():
                    st.markdown(f"""
                    <div style="
                        background-color: {color};
                        padding: 15px;
                        border-radius: 12px;
                        margin-bottom: 6px;
                        box-shadow: 3px 3px 8px rgba(0,0,0,0.2);
                        color: white;
                        font-weight: 600;
                    ">
                        <div style="font-size: 18px;">📝 {t['name']}</div>
                        <div style="font-size: 14px; margin-top: 6px;">{t['description']}</div>
                        <div style="font-size: 12px; margin-top: 8px;">
                            📅 Due: {t['deadline']} | 🏷️ Priority: {t['priority']}
                        </div>
                        {f'<div style="margin-top: 5px;">📎 <a href="{t["attachment"]}" style="color: white;">Attachment</a></div>' if t["attachment"] else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    key_prefix = f"{t['id']}"

                    edit_mode = st.checkbox("✏️ Edit Task", key=f"edit_{key_prefix}")

                    if edit_mode:
                        new_name = st.text_input("Task Title", value=t["name"], key=f"name_{key_prefix}")
                        new_desc = st.text_area("Description", value=t["description"], key=f"desc_{key_prefix}")
                        new_deadline = st.date_input("Deadline", value=pd.to_datetime(t["deadline"]).date(), key=f"deadline_{key_prefix}")
                        new_priority = st.selectbox("Priority", ["Low", "Medium", "High"], index=["Low","Medium","High"].index(t["priority"]), key=f"priority_{key_prefix}")
                        
                        if st.button("💾 Save Changes", key=f"save_{key_prefix}"):
                            t["name"] = new_name
                            t["description"] = new_desc
                            t["deadline"] = str(new_deadline)
                            t["priority"] = new_priority
                            save_tasks(tasks)
                            st.success("✅ Task updated!")
                            st.rerun()

                    new_status = st.selectbox("🔁 Update Status", status_names, index=status_names.index(status), key=f"status_{key_prefix}")
                    if new_status != status:
                        t["status"] = new_status
                        save_tasks(tasks)
                        st.rerun()

                    if st.button("🗑️ Delete Task", key=f"delete_{key_prefix}"):
                        tasks.remove(t)
                        save_tasks(tasks)
                        st.success("🗑️ Task deleted!")
                        st.rerun()

# ---------- Deadline Warnings ----------
st.subheader("⚠️ Deadlines")
if not df.empty:
    df['deadline'] = pd.to_datetime(df['deadline'])
    upcoming = df[(df['deadline'] > datetime.now()) & (df['deadline'] <= datetime.now() + timedelta(days=3))]
    overdue = df[df['deadline'] < datetime.now()]

    if not upcoming.empty:
        st.warning("⏳ Tasks due soon")
        st.dataframe(upcoming[['name', 'deadline', 'status']])

    if not overdue.empty:
        st.error("❌ Overdue Tasks")
        st.dataframe(overdue[['name', 'deadline', 'status']])

# ---------- Footer ----------
st.markdown("---")
st.markdown("🚀 Built with ❤️ by Shreya | Your lightweight Monday.com alternative.")
