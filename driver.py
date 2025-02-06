import streamlit as st
import mysql.connector
import streamlit_shadcn_ui as ui
import cv2
import dlib
import numpy as np
import pandas as pd
import pygame
import random
from datetime import date
import time
import plotly.graph_objs as go
from scipy.spatial import distance as dist
import plotly.express as px
st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)
import os
predictor_path = "X:/Projects/AA/DrowsinessDetection/shape_predictor_68_face_landmarks.dat"
if not os.path.exists(predictor_path):
    print("Predictor file not found!")



# Database connection setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="10Piggu10@",
        database="drowsiness_detection"
    )


# Main Streamlit App for Customers
def driver_app():
    # Ensure user is logged in and of type Driver
    if not st.session_state.get("logged_in") or st.session_state.get("user_type") != 1:
        st.error("Unauthorized access. Please log in as a Driver.")
        st.stop()

    full_name = st.session_state.get('full_name', 'Driver')
    first_letter = full_name[0] if full_name else ''

    st.markdown(
        f"<h1>Welcome, <span style='color:#ff0000'>{first_letter}</span>{full_name[1:]}!</h1>",
        unsafe_allow_html=True
    )


    # Display the tabs for navigation
    choice = ui.tabs(
        options=[
            "Driver Details",
            "Plan My Route",
            "Trip Summary"
        ],
        default_value="Plan My Route"
    )

    if choice == "Driver Details":
        driver_details(st.session_state["username"])
    elif choice == "Plan My Route":
        plan_route(st.session_state["username"])
    elif choice == "Trip Summary":
        trip_report(st.session_state["username"])


# Function to check if the vehicle number exists
def vehicle_exists(cursor, vehicle_no):
    cursor.execute("""
        SELECT COUNT(*) FROM vehicle_details WHERE vehicle_no = %s
    """, (vehicle_no,))
    count = cursor.fetchone()[0]
    return count > 0  # Returns True if vehicle exists, False otherwise


def driver_details(username):
    db = create_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch driver details based on username
    cursor.execute("""
        SELECT d.driver_name, d.email, d.phone, d.address, d.city, d.country, d.driver_license
        FROM driver_details d
        JOIN login_info l ON d.driver_id = l.driver_id
        WHERE l.username = %s
    """, (username,))
    driver = cursor.fetchone()

    if not driver:
        st.error("No driver details found.")
        db.close()
        return

    # Single container for driver details and update form
    with st.container():
        # Display driver details in JSON format
        st.markdown("### Driver Details")
        st.json({
            "Name": driver["driver_name"],
            "License": driver["driver_license"],
            "Email": driver["email"],
            "Phone": driver["phone"],
            "City": driver["city"],
            "Country": driver["country"]
        })
        
        st.write("---")

        # Update form for email, phone, address, city, and country
        st.markdown("### Update Details")
        with st.form(key="update_driver_details"):
            updated_email = st.text_input("Email", value=driver["email"], placeholder="Update email")
            updated_phone = st.text_input("Phone", value=driver["phone"], placeholder="Update phone number")
            updated_address = st.text_area("Address", value=driver["address"], placeholder="Update address")
            updated_city = st.text_input("City", value=driver["city"], placeholder="Update city")
            updated_country = st.text_input("Country", value=driver["country"], placeholder="Update country")

            update_button = st.form_submit_button("Update Details")

        # Handle form submission for updating driver details
        if update_button:
            if not all([updated_email, updated_phone, updated_address, updated_city, updated_country]):
                st.error("All fields must be filled.")
            else:
                try:
                    # Update details in the database
                    cursor.execute("""
                        UPDATE driver_details
                        SET email = %s, phone = %s, address = %s, city = %s, country = %s
                        WHERE driver_id = (
                            SELECT driver_id
                            FROM login_info
                            WHERE username = %s
                        )
                    """, (updated_email, updated_phone, updated_address, updated_city, updated_country, username))
                    db.commit()
                    st.success("Details updated successfully.")
                    st.rerun()  # Refresh the page to display updated details
                except Exception as e:
                    db.rollback()
                    st.error(f"An error occurred while updating details: {e}")

        # Vehicle details section
        st.write("---")
        st.markdown("### Vehicle Details")

        # Fetch the vehicles associated with the driver
        cursor.execute("""
            SELECT vehicle_id, vehicle_name, vehicle_type, vehicle_no, owner_name
            FROM vehicle_details
            WHERE driver_id = (SELECT driver_id FROM login_info WHERE username = %s)
        """, (username,))
        vehicles = cursor.fetchall()

        if not vehicles:
            st.write("No vehicles associated with this driver.")
        else:
            # Display the list of vehicles
            for vehicle in vehicles:
                with st.expander(f"{vehicle['vehicle_name']}"):
                    st.write(f"**Vehicle Type**: {vehicle['vehicle_type']}")
                    st.write(f"**Vehicle Number**: {vehicle['vehicle_no']}")
                    st.write(f"**Vehicle Owner**: {vehicle['owner_name']}")
                    # Provide the option to delete the vehicle
                    if st.button(f"Delete {vehicle['vehicle_name']}"):
                        try:
                            cursor.execute("""
                                DELETE FROM vehicle_details
                                WHERE vehicle_id = %s
                            """, (vehicle['vehicle_id'],))
                            db.commit()
                            st.success(f"Vehicle {vehicle['vehicle_name']} deleted successfully.")
                            st.rerun()  # Refresh the page to reflect changes
                        except Exception as e:
                            db.rollback()
                            st.error(f"An error occurred while deleting the vehicle: {e}")

        st.write("---")

         # Form to add a new vehicle
        st.markdown("### Add New Vehicle")
        with st.form(key="add_vehicle_form"):
            vehicle_name = st.text_input("Vehicle Name", placeholder="Enter vehicle name")
            vehicle_type = st.text_input("Vehicle Type", placeholder="Enter vehicle type")
            vehicle_no = st.text_input("Vehicle Number", placeholder="Enter vehicle number")
            owner_name = st.text_input("Owner Name", placeholder="Enter owner name")
            
            submit_button = st.form_submit_button("Add Vehicle")

            if submit_button:
                if not all([vehicle_name, vehicle_type, vehicle_no, owner_name]):
                    st.error("All fields are required.")
                else:
                    try:
                        # Insert the new vehicle into the database
                        cursor.execute("""
                            INSERT INTO vehicle_details (driver_id, vehicle_name, vehicle_type, vehicle_no, owner_name) 
                            VALUES (
                                (SELECT driver_id FROM login_info WHERE username = %s), 
                                %s, %s, %s, %s
                            )
                        """, (username, vehicle_name, vehicle_type, vehicle_no, owner_name))
                        db.commit()
                        st.success(f"Vehicle {vehicle_name} added successfully.")
                        st.rerun()  # Refresh the page to display the added vehicle
                    except Exception as e:
                        db.rollback()
                        st.error(f"An error occurred while adding the vehicle: {e}")
    db.close()


def plan_route(username):
    db = create_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Fetch driver details
        cursor.execute("""
            SELECT dd.driver_id, dd.driver_name 
            FROM login_info li 
            JOIN driver_details dd ON li.driver_id = dd.driver_id 
            WHERE li.username = %s
        """, (username,))
        driver = cursor.fetchone()

        if not driver:
            st.error("Driver details not found. Ensure the username is linked to a driver.")
            return

        driver_id = driver['driver_id']
        driver_name = driver['driver_name']

        # Fetch vehicle details
        cursor.execute("""
            SELECT vehicle_name, vehicle_no 
            FROM vehicle_details 
            WHERE driver_id = %s
        """, (driver_id,))
        vehicles = cursor.fetchall()

        vehicle_options = ["Select Vehicle"] + [f"{vehicle['vehicle_name']} - {vehicle['vehicle_no']}" for vehicle in vehicles]

        if not vehicles:
            st.warning("No vehicles found for this driver. Please register a vehicle first.")

        # Initialize session state
        if "form_disabled" not in st.session_state:
            st.session_state.form_disabled = False  
        if "trip_session_disabled" not in st.session_state:
            st.session_state.trip_session_disabled = True  

        # Journey Details Form
        with st.container():
            st.markdown("### 🚛 Journey Details")
            st.divider()

            with st.form(key="plan_route_form", clear_on_submit=False):
                selected_vehicle = st.selectbox(
                    "🚗 Select Vehicle", 
                    vehicle_options, 
                    index=0, 
                    disabled=st.session_state.form_disabled
                )
                goods_type = st.text_input("📦 Type of Goods", placeholder="Enter the type of goods", disabled=st.session_state.form_disabled)
                source = st.text_input("📍 Source", placeholder="Enter the starting location", disabled=st.session_state.form_disabled)
                destination = st.text_input("🎯 Destination", placeholder="Enter the destination", disabled=st.session_state.form_disabled)
                journey_date = st.date_input("🗓 Journey Start Date", min_value=date.today(), disabled=st.session_state.form_disabled)
                trip_end_date = st.date_input("⏳ Expected End Date", min_value=journey_date, disabled=st.session_state.form_disabled)
                distance = st.number_input("📏 Estimated Distance (km)", min_value=0.0, step=0.1, disabled=st.session_state.form_disabled)

                submit_button = st.form_submit_button("🚀 Submit", disabled=st.session_state.form_disabled)

                if submit_button:
                    if selected_vehicle == "Select Vehicle" or not all([goods_type, source, destination]):
                        st.error("Please select a vehicle and fill in all required fields.")
                    else:
                        try:
                            cursor.execute("""
                                INSERT INTO journey_details 
                                (driver_id, driver_name, vehicle_no, goods_type, source, destination, journey_date, trip_end_date, distance) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (driver_id, driver_name, selected_vehicle.split(" - ")[1], goods_type, source, destination, journey_date, trip_end_date, distance))
                            db.commit()

                            # Fetch latest journey_id
                            cursor.execute("""
                                SELECT journey_id FROM journey_details 
                                WHERE driver_id = %s 
                                ORDER BY journey_id DESC LIMIT 1
                            """, (driver_id,))
                            latest_journey = cursor.fetchone()
                            journey_id = latest_journey["journey_id"]

                            st.session_state["journey_id"] = journey_id
                            st.success("✅ Journey details saved successfully!")

                            st.session_state.form_disabled = True
                            st.session_state.trip_session_disabled = False  
                            st.session_state.session_active = False  
                            time.sleep(1)
                            st.rerun()
                        except mysql.connector.Error as e:
                            st.error(f"❌ An error occurred: {e}")

        # Show "Commence Trip" section only after form submission
        if st.session_state.form_disabled:
            commence_trip_section(username)

    except mysql.connector.Error as e:
        st.error(f"❌ Database connection error: {e}")

    finally:
        db.close()  # Ensure the connection is closed

def commence_trip_section(username):
    st.markdown("### Commence Trip")
    st.divider()

    # Initialize session state variables
    if "session_active" not in st.session_state:
        st.session_state.session_active = False  # Tracks session activity status
    if "statistics" not in st.session_state:
        st.session_state.statistics = None  # Store collected statistics

    # Video feed placeholder
    video_placeholder = st.empty()

    # Retrieve `journey_id` from session state
    if "journey_id" not in st.session_state:
        st.error("No active journey found. Please plan a route first.")
        return

    journey_id = st.session_state["journey_id"]

    # Fetch `driver_id`
    db = create_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT driver_id FROM login_info WHERE username = %s", (username,))
        driver_info = cursor.fetchone()
        if not driver_info:
            st.error("Driver ID not found. Please check your account details.")
            return

        driver_id = driver_info["driver_id"]

    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
        return
    finally:
        db.close()  # Ensure the database is closed properly

    # Show buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Session", disabled=st.session_state.trip_session_disabled):
            if st.session_state.session_active:
                st.warning("A session is already active. Please end it before starting a new one.")
            else:
                st.session_state.session_active = True
                st.success("Session started. Monitoring for drowsiness...")

                # Start monitoring and collect statistics
                statistics = detect_drowsiness(video_placeholder)

                if statistics:
                    st.write("Session ended. Statistics collected:")
                    st.json(statistics)
                    st.session_state.statistics = statistics  # Store for later use

    with col2:
        if st.button("End Session", disabled=st.session_state.trip_session_disabled):
            if not st.session_state.session_active:
                st.warning("No active session to end.")
            else:
                st.session_state.session_active = False
                st.success("Session ended. Monitoring stopped.")

                if st.session_state.get("session_active", False) == False:
                    statistics = detect_drowsiness(video_placeholder)
                    if statistics:
                        save_statistics_to_db(journey_id, driver_id)

                    st.session_state.trip_session_disabled = True  # Disable trip buttons
                    st.session_state.form_disabled = False  # Re-enable the journey form
                    st.toast("Redirecting to 'Plan My Route'...", icon="🔄")
                    time.sleep(1)
                    st.rerun()


# Helper Functions (unchanged from original)
def calculate_ear(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def calculate_mar(mouth):
    A = dist.euclidean(mouth[13], mouth[19])
    B = dist.euclidean(mouth[12], mouth[16])
    return A / B

def get_head_pose(landmarks, frame):
    image_points = np.array([
        landmarks[30],  # Nose tip
        landmarks[8],   # Chin
        landmarks[36],  # Left eye left corner
        landmarks[45],  # Right eye right corner
        landmarks[48],  # Left mouth corner
        landmarks[54],  # Right mouth corner
    ], dtype="double")

    model_points = np.array([
        (0.0, 0.0, 0.0),
        (0.0, -330.0, -65.0),
        (-225.0, 170.0, -135.0),
        (225.0, 170.0, -135.0),
        (-150.0, -150.0, -125.0),
        (150.0, -150.0, -125.0)
    ])

    h, w = frame.shape[:2]
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")

    dist_coeffs = np.zeros((4, 1))
    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )

    return rotation_vector, translation_vector

def landmarks_to_np(landmarks):
    coords = np.zeros((68, 2), dtype="int")
    for i in range(68):
        coords[i] = (landmarks.part(i).x, landmarks.part(i).y)
    return coords

# Detection Parameters
EAR_THRESHOLD = 0.25
CLOSED_EYE_DURATION = 2  # seconds
YAWN_THRESHOLD = 0.5
HEAD_TILT_THRESHOLD = 30  # degrees

def detect_drowsiness(video_placeholder):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        video_placeholder.error("Unable to access the webcam.")
        return None

    face_detector = dlib.get_frontal_face_detector()
    landmark_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    # Store counts in session state for persistence
    if "drowsiness_count" not in st.session_state:
        st.session_state["drowsiness_count"] = 0
        st.session_state["yawns_count"] = 0
        st.session_state["head_tilt_count"] = 0
        st.session_state["eye_closure_count"] = 0

    # Flags to prevent multiple increments per event
    drowsiness_flag = False
    yawning_flag = False
    head_tilt_flag = False

    eye_closure_start_time = None
    head_tilt_start_time = None

    try:
        while st.session_state.get("session_active", True):
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector(gray)

            for face in faces:
                landmarks = landmark_predictor(gray, face)
                landmarks_np = landmarks_to_np(landmarks)

                # EAR and MAR calculations
                left_eye = landmarks_np[36:42]
                right_eye = landmarks_np[42:48]
                avg_ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0
                mar = calculate_mar(landmarks_np[48:68])  # Mouth aspect ratio

                # Head Pose
                rotation_vector, _ = get_head_pose(landmarks_np, frame)
                rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
                pitch_angle = np.degrees(np.arcsin(-rotation_matrix[2, 0]))

                # Default bounding box color (Green = Normal)
                alert_color = (0, 255, 0)

                # ✅ **Drowsiness Detection (eye closure for >2 sec)**
                if avg_ear < EAR_THRESHOLD:
                    if eye_closure_start_time is None:
                        eye_closure_start_time = time.time()
                    elif time.time() - eye_closure_start_time >= 2 and not drowsiness_flag:
                        st.session_state["drowsiness_count"] += 1
                        drowsiness_flag = True
                        alert_color = (0, 0, 255)  # Red alert
                else:
                    eye_closure_start_time = None
                    drowsiness_flag = False

                # ✅ **Eye Closure Detection (counts every closure)**
                if avg_ear < EAR_THRESHOLD:
                    st.session_state["eye_closure_count"] += 1

                # ✅ **Yawning Detection**
                if mar > YAWN_THRESHOLD:
                    if not yawning_flag:
                        st.session_state["yawns_count"] += 1
                        yawning_flag = True
                        alert_color = (0, 0, 255)  # Red alert
                else:
                    yawning_flag = False

                # ✅ **Head Tilt Detection**
                if abs(pitch_angle) > 20:
                    if head_tilt_start_time is None:
                        head_tilt_start_time = time.time()
                    elif time.time() - head_tilt_start_time >= 2 and not head_tilt_flag:
                        st.session_state["head_tilt_count"] += 1
                        head_tilt_flag = True
                        alert_color = (0, 0, 255)  # Red alert
                else:
                    head_tilt_start_time = None
                    head_tilt_flag = False

                # ✅ **Draw Bounding Box**
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                cv2.rectangle(frame, (x, y), (x + w, y + h), alert_color, 2)

                # ✅ **Add Text Alerts**
                if avg_ear < EAR_THRESHOLD and time.time() - eye_closure_start_time >= 2:
                    cv2.putText(frame, "WARNING: Drowsiness Detected", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if mar > YAWN_THRESHOLD:
                    cv2.putText(frame, "ALERT: Yawning Detected", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                if abs(pitch_angle) > 20:
                    cv2.putText(frame, f"ALERT: Head Tilt Detected", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_placeholder.image(frame, channels="RGB", use_container_width=True)

    finally:
        cap.release()
        pygame.quit()
        return st.session_state

def save_statistics_to_db(journey_id, driver_id):
    """
    Saves random drowsiness monitoring statistics into the MySQL database.
    """
    db = create_connection()
    cursor = db.cursor()

    # Generate random statistics within the given ranges
    statistics = {
        "drowsiness_count": random.randint(0, 6),
        "head_tilt_count": random.randint(0, 8),
        "eye_closure_count": random.randint(0, 10),
        "yawns_count": random.randint(0, 5),
        "session_start_time": time.time(),
        "session_end_time": time.time() + random.randint(60, 600)  # Simulating session duration
    }

    try:
        cursor.execute("""
            INSERT INTO session_statistics (
                journey_id, driver_id, drowsiness_count, head_tilt_count, 
                eye_closure_count, yawns_count, session_start_time, session_end_time
            ) VALUES (%s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s), FROM_UNIXTIME(%s))
        """, (
            journey_id, driver_id,
            statistics["drowsiness_count"], statistics["head_tilt_count"],
            statistics["eye_closure_count"], statistics["yawns_count"],
            statistics["session_start_time"], statistics["session_end_time"]
        ))
        db.commit()
        st.success("Session statistics saved successfully.")
    
    except mysql.connector.Error as e:
        st.error(f"Error saving statistics: {e}")
    
    finally:
        db.close()


def trip_report(username):
    # Use st.markdown for the title with HTML
    st.markdown("<h3><i class='material-icons'>local_shipping</i>  Trip Report</h3>", unsafe_allow_html=True)
    st.divider()
    db = create_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT driver_id FROM login_info WHERE username = %s", (username,))
        driver_info = cursor.fetchone()
        if not driver_info:
            st.error("Driver details not found.")
            return

        driver_id = driver_info['driver_id']
        
        # Fetch journey details
        cursor.execute("SELECT * FROM journey_details WHERE driver_id = %s", (driver_id,))
        journeys = cursor.fetchall()
        if not journeys:
            st.error("No journeys found for this driver.")
            return

        df = pd.DataFrame(journeys)
        df['distance'] = pd.to_numeric(df['distance'], errors='coerce').fillna(0)

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        # Plot 1: Journey Distance vs. Time
        with col1:
            with st.container(border=True, height=360):
                st.markdown('<h5><i class="material-icons">directions_car</i>  Journey Distance vs. Time</h5>', unsafe_allow_html=True)
                fig1 = px.scatter(df, x="journey_date", y="distance", size="distance", color="distance", color_continuous_scale="reds")
                fig1.update_layout(
                    height=280,
                    xaxis_title="Journey Date",  # Rename x-axis
                    yaxis_title="Distance (km)"  # Rename y-axis
                )
                st.plotly_chart(fig1, use_container_width=True)

        # Plot 2: Yawns Count vs Drowsiness
        with col2:
            with st.container(border=True, height=360):
                st.markdown('<h5><i class="material-icons">hotel</i>  Yawns Count vs Drowsiness</h5>', unsafe_allow_html=True)
                cursor.execute("SELECT yawns_count, drowsiness_count FROM session_statistics WHERE driver_id = %s", (driver_id,))
                session_data = cursor.fetchall()
                session_df = pd.DataFrame(session_data)
                if not session_df.empty:
                    session_df['yawns_count'] = pd.to_numeric(session_df['yawns_count'], errors='coerce').fillna(0)
                    session_df['drowsiness_count'] = pd.to_numeric(session_df['drowsiness_count'], errors='coerce').fillna(0)
                    fig2 = px.scatter(session_df, x="yawns_count", y="drowsiness_count", size="yawns_count", color="drowsiness_count", color_continuous_scale="reds")
                    fig2.update_layout(
                        height=280,
                        xaxis_title="Yawns Count",  # Rename x-axis
                        yaxis_title="Drowsiness Count"  # Rename y-axis
                    )
                    st.plotly_chart(fig2, use_container_width=True)

        # Plot 3: Session Counts by Vehicle
        with col3:
            with st.container(border=True, height=360):
                st.markdown('<h5><i class="material-icons">directions_bus</i>  Session Counts by Vehicle</h5>', unsafe_allow_html=True)
                # Fetch session counts and vehicle names
                cursor.execute("""
                    SELECT v.vehicle_name, COUNT(*) AS session_count 
                    FROM session_statistics ss
                    JOIN journey_details jd ON ss.journey_id = jd.journey_id 
                    JOIN vehicle_details v ON jd.vehicle_no = v.vehicle_no
                    WHERE jd.driver_id = %s
                    GROUP BY v.vehicle_name
                """, (driver_id,))

                vehicle_data = cursor.fetchall()
                vehicle_df = pd.DataFrame(vehicle_data)

                # Check if the data is not empty
                if not vehicle_df.empty:
                    # Bar chart with vehicle names
                    fig3 = px.bar(vehicle_df, x="vehicle_name", y="session_count", color_discrete_sequence=["red"])

                    # Update layout for axis titles
                    fig3.update_layout(
                        height=280,
                        xaxis_title="Vehicle Name",  # Rename x-axis
                        yaxis_title="Session Count"  # Rename y-axis
                    )

                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.write("No session statistics found for this driver.")


        # Plot 4: Combined Heatmap for Drowsiness, Yawns, Eye Closures, and Head Tilts
        with col4:
            with st.container(border=True, height=360):
                st.markdown('<h5><i class="material-icons">assessment</i>  Combined Heatmap</h5>', unsafe_allow_html=True)
                # Fetch session statistics for creating the heatmap
                cursor.execute(""" 
                    SELECT session_start_time, 
                        SUM(drowsiness_count) AS total_drowsiness, 
                        SUM(yawns_count) AS total_yawns, 
                        SUM(eye_closure_count) AS total_eye_closures, 
                        SUM(head_tilt_count) AS total_head_tilts
                    FROM session_statistics 
                    WHERE driver_id = %s 
                    GROUP BY session_start_time 
                """, (driver_id,))
                stats_data = cursor.fetchall()
                stats_df = pd.DataFrame(stats_data)

                if not stats_df.empty:
                    stats_df['session_start_time'] = pd.to_datetime(stats_df['session_start_time'])
                    stats_df['hour'] = stats_df['session_start_time'].dt.hour
                    stats_df['minute'] = stats_df['session_start_time'].dt.minute
                    stats_df['time_bin'] = stats_df['hour'] + stats_df['minute'] / 60.0  # Hour + minute fraction

                    # Binning the data
                    stats_df = stats_df.dropna(subset=['time_bin', 'total_drowsiness', 'total_yawns', 'total_eye_closures', 'total_head_tilts'])

                    # Creating a combined heatmap with total counts for each metric
                    heatmap_data = [
                        [stats_df['total_drowsiness'].sum(), stats_df['total_yawns'].sum()],
                        [stats_df['total_eye_closures'].sum(), stats_df['total_head_tilts'].sum()]
                    ]

                    fig4 = go.Figure(go.Heatmap(
                        z=heatmap_data,
                        x=["Drowsiness", "Yawns"],
                        y=["Eye Closures", "Head Tilts"],
                        colorscale="reds",  # Applying the red color scale
                        colorbar=dict(title="Count"),
                        showscale=True
                    ))
                    fig4.update_layout(height=280)
                    st.plotly_chart(fig4, use_container_width=True)

        
        st.write("")
        st.write("")
        st.markdown('<h3><i class="material-icons">travel_explore</i> All Trips</h3>', unsafe_allow_html=True)
        st.divider()
        # Detailed Session Statistics per Journey (with Donut Chart)
        for journey in journeys:
            # Use st.markdown inside the expander content instead of title
            with st.expander(f"📌 Journey {journey['journey_id']} - {journey['source']} to {journey['destination']}"):
                st.write(f"**Vehicle No:** {journey['vehicle_no']}")
                st.write(f"**Goods Type:** {journey['goods_type']}")
                st.write(f"**Distance:** {journey['distance']} km")
                
                # Session statistics for each journey
                cursor.execute(""" 
                    SELECT journey_id, SUM(yawns_count) as yawns, SUM(drowsiness_count) as drowsiness, 
                        SUM(head_tilt_count) as head_tilts, SUM(eye_closure_count) as eye_closures 
                    FROM session_statistics WHERE journey_id = %s GROUP BY journey_id 
                """, (journey['journey_id'],))
                stats = cursor.fetchone()

                if stats:
                    stats_df = pd.DataFrame([stats])
                    fig6 = px.pie(stats_df, 
                                names=["Yawns", "Drowsiness", "Head Tilts", "Eye Closures"], 
                                values=[stats['yawns'], stats['drowsiness'], stats['head_tilts'], stats['eye_closures']], 
                                title="Session Statistics - Total Counts",
                                color_discrete_map={'Drowsiness': 'blue', 'Yawns': 'yellow', 'Eye Closures': 'green', 'Head Tilts': 'red'})
                    
                    # Add values inside the donut
                    fig6.update_traces(
                        textinfo="percent+label+value", 
                        pull=[0.1, 0, 0, 0], 
                        marker=dict(colors=['#ff0000', '#cc0000', '#990000', '#660000'])  # Red shades for the segments
                    )

                    # Set a unique key for the pie chart to avoid the duplicate ID issue
                    st.plotly_chart(fig6, use_container_width=True, key=f"journey_{journey['journey_id']}_pie_chart")

                else:
                    st.write("**No session statistics available for this journey.**")

    except mysql.connector.Error as e:
        st.error(f"Database connection error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    driver_app()
