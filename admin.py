import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import streamlit_shadcn_ui as ui
import plotly.express as px
import plotly.graph_objects as go

# Database connection setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="10Piggu10@",
        database="drowsiness_detection"
    )

# Main Streamlit App
def main():
    st.markdown('<h1><span style="color:#ff0000">A</span>dmin Panel</h1>', unsafe_allow_html=True)
    choice = ui.tabs(options=[
        "Dashboard",
        "Drivers Info"
    ],
    default_value="Dashboard"
    )

    # Dashboard Overview
    if choice == "Dashboard":
        dashboard()

    # Manage Drivers
    elif choice == "Drivers Info":
        driver_management()

def dashboard():
    db = create_connection()
    cursor = db.cursor(dictionary=True)

    # 1. Total Drowsiness Count (Overall)
    cursor.execute("SELECT SUM(drowsiness_count) AS total_drowsiness FROM session_statistics")
    total_drowsiness = cursor.fetchone()["total_drowsiness"]

    # 2. Average Drowsiness Detected per Driver
    cursor.execute("""
        SELECT driver_id, AVG(drowsiness_count) AS avg_drowsiness
        FROM session_statistics
        GROUP BY driver_id
    """)
    avg_drowsiness_data = cursor.fetchall()
    avg_drowsiness_df = pd.DataFrame(avg_drowsiness_data)

    # 3. Total Sessions Per Vehicle
    cursor.execute("""
        SELECT v.vehicle_name, COUNT(*) AS session_count 
        FROM session_statistics ss
        JOIN journey_details jd ON ss.journey_id = jd.journey_id 
        JOIN vehicle_details v ON jd.vehicle_no = v.vehicle_no
        GROUP BY v.vehicle_name
    """)
    vehicle_data = cursor.fetchall()
    vehicle_df = pd.DataFrame(vehicle_data)

    # 4. Top 5 Drivers with Highest Drowsiness Count
    cursor.execute("""
        SELECT d.driver_name, SUM(ss.drowsiness_count) AS total_drowsiness
        FROM session_statistics ss
        JOIN driver_details d ON ss.driver_id = d.driver_id
        GROUP BY d.driver_name
        ORDER BY total_drowsiness DESC
        LIMIT 5
    """)
    top_drivers_data = cursor.fetchall()
    top_drivers_df = pd.DataFrame(top_drivers_data)

    # 5. Average Journey Distance over Time
    cursor.execute("""
        SELECT DATE(journey_date) AS journey_date, AVG(distance) AS avg_distance
        FROM journey_details
        GROUP BY DATE(journey_date)
    """)
    avg_distance_data = cursor.fetchall()
    avg_distance_df = pd.DataFrame(avg_distance_data)

    # 6. Drowsiness Trend Over Time
    cursor.execute("""
        SELECT DATE(session_start_time) AS session_date, SUM(drowsiness_count) AS total_drowsiness
        FROM session_statistics
        GROUP BY DATE(session_start_time)
    """)
    drowsiness_trend_data = cursor.fetchall()
    drowsiness_trend_df = pd.DataFrame(drowsiness_trend_data)

    # Create session_df for drowsiness vs yawns graph
    cursor.execute("SELECT yawns_count, drowsiness_count FROM session_statistics")
    session_data = cursor.fetchall()
    session_df = pd.DataFrame(session_data)

    # Fetch driver names from the driver_details table
    cursor.execute("SELECT driver_id, driver_name FROM driver_details")
    drivers = cursor.fetchall()

    # Create a dictionary mapping driver_id to driver_name
    driver_name_dict = {driver["driver_id"]: driver["driver_name"] for driver in drivers}

    # Add driver_name to the avg_drowsiness_df dataframe
    avg_drowsiness_df["driver_name"] = avg_drowsiness_df["driver_id"].map(driver_name_dict)

    # --- Metrics Section (2x2 Layout) ---
    st.markdown('<h3><span style="color:#ff0000">D</span>rowsiness Detection Stats</h3>', unsafe_allow_html=True)

    # 2x2 Layout for Metrics Cards
    col1, col2 = st.columns(2)
    with col1:
        # Metric 1: Average Drowsiness Detected per Driver
        avg_drowsiness_value = avg_drowsiness_df["avg_drowsiness"].mean() if not avg_drowsiness_df.empty else 0
        with st.container():
            st.metric(label="Avg Drowsiness Detected per Driver", value=f"{avg_drowsiness_value:.2f}",border=True)
    with col2:
        # Metric 2: Total Number of Active Drivers
        cursor.execute("SELECT COUNT(DISTINCT driver_id) AS active_drivers FROM driver_details")
        active_drivers = cursor.fetchone()["active_drivers"]
        with st.container():
            st.metric(label="Active Drivers", value=f"{active_drivers}",border=True)
    
    col3, col4 = st.columns(2)
    with col3:
        # Metric 3: Total Number of Vehicles
        cursor.execute("SELECT COUNT(DISTINCT vehicle_no) AS total_vehicles FROM vehicle_details")
        total_vehicles = cursor.fetchone()["total_vehicles"]
        with st.container():
            st.metric(label="Total Vehicles", value=f"{total_vehicles}",border=True)
    with col4:
        # Metric 4: Average Journey Distance
        avg_distance_value = avg_distance_df["avg_distance"].mean() if not avg_distance_df.empty else 0
        with st.container():
            st.metric(label="Avg Journey Distance (km)", value=f"{avg_distance_value:.2f}",border=True)

    # --- Visuals Section (3x2 Layout) ---
    # 3x2 Layout for Graphs
    col1, col2 = st.columns(2)

    # 1. Drowsiness vs Yawns (Scatter Plot)
    with col1:
        if not session_df.empty:
            fig1 = px.scatter(session_df, x="yawns_count", y="drowsiness_count", size="yawns_count", 
                              title="Drowsiness vs Yawns", color="drowsiness_count", color_continuous_scale="reds")
            fig1.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#000000"),
                xaxis_title="Yawns Count",
                yaxis_title="Drowsiness Count"
            )
            st.plotly_chart(fig1, use_container_width=True)

    # 2. Vehicle-wise Session Count (Bar Chart)
    with col2:
        if not vehicle_df.empty:
            fig2 = px.bar(vehicle_df, x="vehicle_name", y="session_count", title="Vehicle-wise Session Count", 
                          color="session_count", color_continuous_scale="reds")
            fig2.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#000000"),
                xaxis_title="Vehicle Name", 
                yaxis_title="Session Count"
            )
            st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    # 3. Top 5 Drivers with Highest Drowsiness (Bar Chart)
    with col3:
        if not top_drivers_df.empty:
            fig3 = px.bar(top_drivers_df, x="driver_name", y="total_drowsiness", title="Top 5 Drivers with Highest Drowsiness",
                          labels={"driver_name": "Driver Name", "total_drowsiness": "Total Drowsiness"},
                          color="total_drowsiness", color_discrete_sequence=["red"])
            fig3.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#000000"),
                xaxis_title="Driver Name", 
                yaxis_title="Drowsiness Count"
            )
            st.plotly_chart(fig3, use_container_width=True)

    # 4. Drowsiness Trend Over Time (Line Chart)
    with col4:
        if not drowsiness_trend_df.empty:
            fig4 = px.line(drowsiness_trend_df, x="session_date", y="total_drowsiness", 
                           title="Drowsiness Trend Over Time", 
                           labels={"session_date": "Date", "total_drowsiness": "Drowsiness Count"},
                           color_discrete_sequence=["red"])
            fig4.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#000000")
            )
            st.plotly_chart(fig4, use_container_width=True)

    col5, col6 = st.columns(2)

    # 5. Average Drowsiness Detected per Driver (Bar Chart)
    with col5:
        if not avg_drowsiness_df.empty:
            # Modify to use 'driver_name' on the x-axis and red bars
            fig5 = px.bar(avg_drowsiness_df, x="driver_name", y="avg_drowsiness", 
                        labels={"driver_name": "Driver Name", "avg_drowsiness": "Average Drowsiness"},
                        title="Avg Drowsiness Detected per Driver", 
                        color="avg_drowsiness", color_discrete_sequence=["red"])
            
            # Update layout to apply better red shading and make sure everything looks clean
            fig5.update_layout(
                xaxis_title="Driver Name", 
                yaxis_title="Average Drowsiness",
                xaxis_tickangle=-45,  # Rotate x-axis labels to avoid overlap
                coloraxis_colorbar=dict(title="Drowsiness Level", tickvals=[0, 0.5, 1], ticktext=["Low", "Medium", "High"])  # Add color bar for reference
            )
            
            # Display the plot
            st.plotly_chart(fig5, use_container_width=True)



    # 6. Average Journey Distance over Time (Line Chart)
    with col6:
        if not avg_distance_df.empty:
            fig6 = px.line(avg_distance_df, x="journey_date", y="avg_distance", 
                           title="Avg Journey Distance over Time", 
                           labels={"journey_date": "Date", "avg_distance": "Average Distance"},
                           color_discrete_sequence=["red"])
            fig6.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color="#000000")
            )
            st.plotly_chart(fig6, use_container_width=True)
    
    db.close()


def driver_management():
    db = create_connection()
    cursor = db.cursor(dictionary=True)

    st.markdown('<h3><span style="color:#ff0000">D</span>river Info</h3>', unsafe_allow_html=True)

    # Fetch all drivers info
    cursor.execute("SELECT driver_id, driver_name FROM driver_details")
    drivers = cursor.fetchall()

    if not drivers:
        st.write("No drivers found in the database.")
        db.close()
        return

    # Dropdown to select driver
    driver_names = [driver['driver_name'] for driver in drivers]
    selected_driver_name = st.selectbox("Select a Driver", driver_names)

    if selected_driver_name:
        # Fetch the driver information
        cursor.execute("SELECT * FROM driver_details WHERE driver_name = %s", (selected_driver_name,))
        driver = cursor.fetchone()

        # Display driver info with enhanced formatting
        st.write(f"**Name**: {driver['driver_name']}")
        st.write(f"**Email**: {driver['email']}")
        st.write(f"**Phone**: {driver['phone']}")
        st.write(f"**Address**: {driver['address']}")
        st.write(f"**Gender**: {driver['gender']}")
        st.write(f"**DOB**: {driver['dob']}")
        st.write(f"**City**: {driver['city']}")
        st.write(f"**Country**: {driver['country']}")
        st.write(f"**Driver License**: {driver['driver_license']}")
        st.write(f"**Date of Registration**: {driver['date_of_registration']}")

        # Use divider for better sectioning
        st.divider()

        # Fetch vehicles owned by the driver
        cursor.execute("SELECT vehicle_no, vehicle_name FROM vehicle_details WHERE owner_name = %s", (driver['driver_name'],))
        vehicles = cursor.fetchall()

        if vehicles:
            st.markdown("### **Vehicles Owned by the Driver**")
            vehicles_df = pd.DataFrame(vehicles)

            # Check if 'driver_id' exists before trying to drop it
            if 'driver_id' in vehicles_df.columns:
                vehicles_df = vehicles_df.drop(columns=['driver_id'])

            # Rename columns for better readability
            vehicles_df.columns = ['Vehicle No', 'Vehicle Name']

            # Display vehicles as a table with better styling
            st.dataframe(vehicles_df.style.set_properties(**{
                'background-color': 'white',
                'color': 'black',
                'border': '1px solid black'
            }).set_table_styles([{
                'selector': 'thead th', 'props': [('background-color', '#f4f4f4'), ('font-weight', 'bold')]
            }]))
        else:
            st.write("No vehicles owned by this driver.")

        # Use divider again before journey data
        st.divider()

        # Fetch journey and session statistics data
        query = """
        SELECT 
            j.vehicle_no, j.goods_type, j.source, j.destination, j.journey_date, j.trip_end_date, j.distance,
            ss.drowsiness_count, ss.head_tilt_count, ss.eye_closure_count, ss.yawns_count
        FROM journey_details j
        JOIN session_statistics ss ON j.journey_id = ss.journey_id
        WHERE j.driver_name = %s
        """
        cursor.execute(query, (selected_driver_name,))
        journey_data = cursor.fetchall()

        if journey_data:
            st.markdown("### **Journey Details and Session Statistics**")
            journey_df = pd.DataFrame(journey_data)

            # Rename columns for better readability
            journey_df.columns = ['Vehicle No', 'Goods Type', 'Source', 'Destination', 'Journey Start Date', 'Journey End Date', 'Distance (km)', 'Drowsiness Count', 'Head Tilt Count', 'Eye Closure Count', 'Yawns Count']

            # Add table with enhanced styling
            st.dataframe(journey_df.style.set_properties(**{
                'background-color': 'white',
                'color': 'black',
                'border': '1px solid black'
            }).set_table_styles([{
                'selector': 'thead th', 'props': [('background-color', '#f4f4f4'), ('font-weight', 'bold')]
            }]))
        else:
            st.write("No journey details found for this driver.")

    db.close()



if __name__ == "__main__":
    main()
