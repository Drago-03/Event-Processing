import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import extra_streamlit_components as stx
from streamlit_option_menu import option_menu
import json

# Set page configuration
st.set_page_config(
    page_title="Event Manager",
    page_icon="📅",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Custom fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Main container */
    .main {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Custom button styling */
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        border-radius: 8px;
        border: none;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Custom header styling */
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: #2C3E50;
    }
    
    /* Custom input fields */
    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    
    /* Custom card styling */
    .event-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('events.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         title TEXT NOT NULL,
         description TEXT,
         date TEXT NOT NULL,
         category TEXT,
         status TEXT,
         created_at TEXT)
    ''')
    conn.commit()
    conn.close()

# Database operations
class EventDatabase:
    @staticmethod
    def add_event(title, description, date, category, status):
        conn = sqlite3.connect('events.db')
        c = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            INSERT INTO events (title, description, date, category, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, date, category, status, created_at))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all_events():
        conn = sqlite3.connect('events.db')
        df = pd.read_sql_query("SELECT * FROM events", conn)
        conn.close()
        return df
    
    @staticmethod
    def update_event_status(event_id, new_status):
        conn = sqlite3.connect('events.db')
        c = conn.cursor()
        c.execute("UPDATE events SET status = ? WHERE id = ?", (new_status, event_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete_event(event_id):
        conn = sqlite3.connect('events.db')
        c = conn.cursor()
        c.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()

# Initialize the database
init_db()

# App header
st.title("📅 Event Manager")
st.markdown("---")

# Navigation menu
selected = option_menu(
    menu_title=None,
    options=["Create Event", "View Events", "Analytics"],
    icons=["calendar-plus", "list-check", "graph-up"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "#4CAF50", "font-size": "20px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "--hover-color": "#eee",
        },
        "nav-link-selected": {"background-color": "#4CAF50", "color": "white"},
    }
)

# Create Event Section
if selected == "Create Event":
    st.header("Create New Event")
    
    with st.form("event_form"):
        title = st.text_input("Event Title")
        description = st.text_area("Event Description")
        date = st.date_input("Event Date")
        category = st.selectbox("Category", ["Meeting", "Conference", "Workshop", "Social", "Other"])
        status = st.selectbox("Status", ["Planned", "In Progress", "Completed", "Cancelled"])
        
        submit_button = st.form_submit_button("Create Event")
        
        if submit_button:
            if title and date:
                EventDatabase.add_event(title, description, str(date), category, status)
                st.success("Event created successfully!")
            else:
                st.error("Please fill in all required fields.")

# View Events Section
elif selected == "View Events":
    st.header("Event List")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect("Filter by Status", 
            ["Planned", "In Progress", "Completed", "Cancelled"])
    with col2:
        category_filter = st.multiselect("Filter by Category",
            ["Meeting", "Conference", "Workshop", "Social", "Other"])
    
    # Get and display events
    events_df = EventDatabase.get_all_events()
    
    if not events_df.empty:
        # Apply filters
        if status_filter:
            events_df = events_df[events_df['status'].isin(status_filter)]
        if category_filter:
            events_df = events_df[events_df['category'].isin(category_filter)]
        
        # Display events
        for _, event in events_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    <div class="event-card">
                        <h3>{event['title']}</h3>
                        <p>{event['description']}</p>
                        <p><strong>Date:</strong> {event['date']}</p>
                        <p><strong>Category:</strong> {event['category']}</p>
                        <p><strong>Status:</strong> {event['status']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button(f"Delete Event {event['id']}"):
                        EventDatabase.delete_event(event['id'])
                        st.experimental_rerun()
                with col3:
                    new_status = st.selectbox(
                        "Update Status",
                        ["Planned", "In Progress", "Completed", "Cancelled"],
                        key=f"status_{event['id']}"
                    )
                    if new_status != event['status']:
                        EventDatabase.update_event_status(event['id'], new_status)
                        st.experimental_rerun()
    else:
        st.info("No events found. Create some events to see them here!")

# Analytics Section
elif selected == "Analytics":
    st.header("Event Analytics")
    
    events_df = EventDatabase.get_all_events()
    
    if not events_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Events by Category")
            category_counts = events_df['category'].value_counts()
            st.bar_chart(category_counts)
        
        with col2:
            st.subheader("Events by Status")
            status_counts = events_df['status'].value_counts()
            st.bar_chart(status_counts)
        
        # Timeline of events
        st.subheader("Event Timeline")
        events_df['date'] = pd.to_datetime(events_df['date'])
        events_timeline = events_df.set_index('date').sort_index()
        st.line_chart(events_timeline.groupby('date').size())
        
        # Recent activity
        st.subheader("Recent Activity")
        recent_events = events_df.sort_values('created_at', ascending=False).head(5)
        st.dataframe(recent_events[['title', 'date', 'status', 'created_at']])
    else:
        st.info("No events data available for analysis.")

# Add footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Created by Drago using Streamlit</p>
</div>
""", unsafe_allow_html=True)