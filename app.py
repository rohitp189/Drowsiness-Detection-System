import streamlit as st
import mysql.connector
import bcrypt
from datetime import datetime
from admin import main
from driver import driver_app
import time
# Initialize session state

st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)

# MySQL Connection Setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="10Piggu10@",
        database="drowsiness_detection"
    )

# Hash the password
def hash_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')  # Convert bytes to string

# Check password
def check_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))  # Convert stored_hash to bytes

# Validate password

# Function to validate password based on given requirements
def validate_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char in "!@#$%^&*()" for char in password):
        return False
    return True

# Forgot Driver Username
def forgot_username(email):
    db = create_connection()
    cursor = db.cursor(dictionary=True)
    
    # First, get the driver_id from driver_details using the email
    cursor.execute("SELECT driver_id FROM driver_details WHERE email = %s", (email,))
    driver = cursor.fetchone()
    
    if driver:
        driver_id = driver['driver_id']
        
        # Now, use the driver_id to fetch the username from login_info
        cursor.execute("SELECT username FROM login_info WHERE driver_id = %s", (driver_id,))
        user = cursor.fetchone()
        db.close()
        
        if user:
            return user['username']
    
    db.close()
    return None


# Function to check if the driver_id already exists in the database
def driver_id_exists(driver_id):
    db = create_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT driver_id FROM driver_details WHERE driver_id = %s", (driver_id,))
    driver = cursor.fetchone()
    db.close()
    return driver is not None

# Login Page Updates
def login_page():
    st.markdown('<h1><span style="color:#ff0000">L</span>ogin Page</h1>', unsafe_allow_html=True)
    with st.form(key="login_form"):
        username = st.text_input("Username", placeholder="Enter your Driver Username")  # Use username instead of driver_id
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit_button = st.form_submit_button("Login")

    if submit_button:
        if not username or not password:
            st.error("Please fill in both username and password.")
            return

        db = create_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM login_info WHERE username = %s", (username,))  # Use username in query
        user = cursor.fetchone()
        db.close()

        if user and check_password(user['password'], password):
            st.session_state.logged_in = True
            st.session_state.username = username  # Store username in session state
            st.session_state.user_type = user['user_type']
            
            if user['user_type'] == 1:  # Driver
                db = create_connection()
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT driver_name FROM driver_details WHERE driver_id = %s", (user['driver_id'],))  # Fetch driver_name using driver_id
                driver = cursor.fetchone()
                db.close()
                st.session_state.full_name = driver['driver_name'] if driver else "Driver"
            else:
                st.session_state.full_name = "Admin"

            st.success(f"Welcome, {st.session_state.full_name}!")
            with st.spinner("Redirecting to dashboard..."):
                time.sleep(3)
            st.rerun()
        else:
            st.error("Invalid login credentials. Please try again.")

def register_driver(username, driver_name, email, phone, address, gender, dob, city, country, driver_license, password):
    db = create_connection()
    cursor = db.cursor()

    try:
        # Insert into driver_details (driver_id is auto-incremented)
        cursor.execute("""
            INSERT INTO driver_details (driver_name, email, phone, address, gender, dob, city, country, driver_license)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (driver_name, email, phone, address, gender, dob, city, country, driver_license))

        # Get the last inserted driver_id (auto-incremented)
        cursor.execute("SELECT LAST_INSERT_ID()")
        driver_id = cursor.fetchone()[0]

        # Commit changes
        db.commit()

        # Hash the password
        password_hash = hash_password(password)

        # Insert into login_info with the auto-generated driver_id
        cursor.execute("""
            INSERT INTO login_info (driver_id, username, password, user_type)
            VALUES (%s, %s, %s, 1)
        """, (driver_id, username, password_hash))

        # Commit changes
        db.commit()

    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise e
    finally:
        db.close()  # Ensure the connection is closed

# Registration process (auto-increment driver_id)

def registration_page():
    st.markdown('<h1>New Driver <span style="color:#ff0000">R</span>egistration</h1>', unsafe_allow_html=True)

    # Initialize session state if not already set
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False

    # Only show form if not submitted
    if not st.session_state.form_submitted:
        with st.form(key="registration_form"):
            username = st.text_input("Driver ID", placeholder="Enter your new username", max_chars=30, key="username")
            driver_name = st.text_input("Driver Name", placeholder="Enter your Full Name", max_chars=30, key="driver_name")
            email = st.text_input("Email", placeholder="Enter your Email", max_chars=30, key="email")
            phone = st.text_input("Phone", placeholder="Enter your Phone Number", max_chars=10, key="phone")
            address = st.text_area("Address", placeholder="Enter your Address", max_chars=150, key="address")
            gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"], key="gender")
            dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1), max_value=datetime.today(), key="dob")
            city = st.text_input("City", placeholder="Enter your City", max_chars=15, key="city")
            country = st.text_input("Country", placeholder="Enter your Country", max_chars=15, key="country")
            driver_license = st.text_input("Driver License", placeholder="Enter your License Number", max_chars=12, key="driver_license")
            password = st.text_input("Password", type="password", placeholder="Enter your new Password", max_chars=25, key="password")

            st.info("Password must be at least 8 characters long, include at least 1 uppercase letter, 1 special character, and 1 number.")

            submit_button = st.form_submit_button("Register")

        # Process form submission
        if submit_button:
            if not all([username, driver_name, email, phone, address, gender != "Select", dob, city, country, driver_license, password]):
                st.error("All fields are required.")
            elif not validate_password(password):
                st.error("Password must meet the requirements.")
            else:
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Simulating registration steps
                    progress_bar.progress(20)
                    status_text.text("Validating inputs...")
                    time.sleep(1)

                    progress_bar.progress(50)
                    status_text.text("Checking database for conflicts...")
                    time.sleep(1)

                    progress_bar.progress(80)
                    status_text.text("Updating database with new registration...")
                    time.sleep(2)

                    # Call function to register the driver in DB
                    register_driver(username, driver_name, email, phone, address, gender, dob, city, country, driver_license, password)

                    progress_bar.progress(100)
                    status_text.text("Registration Successful!")
                    st.success("Registration successful! Redirecting to new registration...")


                    # Automatically reset form and allow new registration
                    reset_form()

                except Exception as e:
                    st.error(f"An error occurred during registration: {e}")

def reset_form():
    """Refresh the page to reset the form."""
    time.sleep(2)  # Wait for 3 seconds before refreshing
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)




# Define the function that will show the dialog with the UserID
@st.dialog("Your Driver Username")
def show_userid():
    if 'driver_id' in st.session_state:
        st.success(f"Found your Driver Username: {st.session_state.driver_id}")
    else:
        st.write("UserID not found.")
    
    # Clear session state to reset the dialog and close it
    if st.button("OK"):
        # This will clear the session state and close the dialog
        st.session_state.driver_id = None
        st.session_state.email_verified = False
        st.session_state.code_verified = False
        st.rerun()  # This will rerun the app and refresh the page
        reset_form()

def forgot_driver_page():
    st.markdown('<h1>Forgot Driver <span style="color:#ff0000">U</span>sername</h1>', unsafe_allow_html=True)
    
    # Initialize session state for driver_id if not already initialized
    if 'driver_id' not in st.session_state:
        st.session_state.driver_id = None  # Default initialization

    # Create the form for forgot Driver Id page
    with st.form(key="forgot_userid_form"):
        # Step 1: Input for Email (Only shown initially)
        if 'email_verified' not in st.session_state:
            email = st.text_input("Enter your email")
            submit_button = st.form_submit_button("Send Code")

            # If submit button is clicked, send the code to the user's email
            if submit_button:
                if email:
                    driver_id = forgot_username(email)  # Pass email to the function to get the driver_id
                    if driver_id:
                        st.session_state.email_verified = True
                        st.session_state.driver_id = driver_id  # Set driver_id in session state
                        st.session_state.code_verified = False  # Reset code_verified flag
                        st.info("Code sent to your email.")
                    else:
                        st.error("No Driver Id found for this email.")
                else:
                    st.error("Please enter a valid email.")

        # Step 2: Code Verification (Only shown after email is verified)
        if 'email_verified' in st.session_state and not st.session_state.code_verified:
            code = st.text_input("Enter Code")
            verify_button = st.form_submit_button("Verify Code")

            # Perform code verification when the button is clicked
            if verify_button:
                if code == "1010":  # Always mock code "1010"
                    st.session_state.code_verified = True
                    # Display the UserID dialog after successful code verification
                    show_userid()
                else:
                    st.error("Incorrect code entered.")


# Function to validate if the username exists in the database
def validate_username(username):
    db = create_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT ld.username, dd.email
        FROM login_info ld
        JOIN driver_details dd ON ld.driver_id = dd.driver_id
        WHERE ld.username = %s
    """, (username,))
    
    user = cursor.fetchone()
    db.close()
    
    if user:
        return user['email']  # Return the email associated with the username
    else:
        return None  # Return None if the username does not exist

# Function to get the current password hash from the database
def get_current_password(username):
    db = create_connection()
    cursor = db.cursor()
    cursor.execute("SELECT password FROM login_info WHERE username = %s", (username,))
    result = cursor.fetchone()
    db.close()
    
    if result:
        return result[0]  # Return the current password hash
    else:
        return None  # Return None if no user found

# Function to update the password in the database
def forgot_password(username, new_password):
    db = create_connection()
    cursor = db.cursor()
    new_password_hash = hash_password(new_password)
    cursor.execute("UPDATE login_info SET password = %s WHERE username = %s", (new_password_hash, username))
    db.commit()
    db.close()

# Function to validate password based on given requirements
def validate_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char in "!@#$%^&*()" for char in password):
        return False
    return True

# Function to reset the password
@st.dialog("Reset Password")
def reset_password_dialog():
    # Check if the username is initialized
    if 'username' not in st.session_state:
        st.error("Username not found. Please log in first.")
        return

    # Fetch the current hashed password from the database
    current_password_hash = get_current_password(st.session_state.username)

    if current_password_hash is None:
        st.error("User not found in the system. Please try again.")
        return

    # Create a form for password reset
    with st.form(key="reset_password_form"):
        new_password = st.text_input("New Password", type="password", placeholder="Enter a strong password")
        confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter the new password")
        submit_button = st.form_submit_button("Submit")

        if submit_button:
            # Check if new password and confirm password match
            if new_password == confirm_password:
                # Fetch the current password hash from the database
                db = create_connection()
                cursor = db.cursor()
                cursor.execute("SELECT password FROM login_info WHERE username = %s", (st.session_state.username,))
                result = cursor.fetchone()
                db.close()

                if result:
                    # Compare the plain text new password with the old password
                    old_password_hash = result[0]
                    if check_password(old_password_hash, new_password):
                        st.error("New password cannot be the same as the current password.")
                    elif not validate_password(new_password):  # Validate the new password
                        st.error("Password does not meet the required criteria. Ensure it is at least 8 characters long, contains digits, uppercase letters, and special characters.")
                    else:
                        # Proceed to update the password
                        forgot_password(st.session_state.username, new_password)
                        st.success("Password reset successful.")
                        time.sleep(3)
                        st.session_state.clear()  # Clear session state after reset
                        st.rerun()  # Rerun the app
                        reset_form()
                else:
                    st.error("User not found in the system.")
            else:
                st.error("Passwords do not match. Please try again.")

# Main function for Forgot Password page
def forgot_password_page():
    st.markdown('<h1>Forgot <span style="color:#ff0000">P</span>assword</h1>', unsafe_allow_html=True)

    # Initialize session state for username, email, and verification flags
    if 'username' not in st.session_state:
        st.session_state.username = None  # Initialize username to None if not set
    if 'email_verified' not in st.session_state:
        st.session_state.email_verified = False  # Initialize email_verified flag
    if 'code_verified' not in st.session_state:
        st.session_state.code_verified = False  # Initialize code_verified flag
    if 'show_code_input' not in st.session_state:
        st.session_state.show_code_input = False  # Initialize flag for showing code input

    # Step 1: Username input and verification
    with st.container():  # Use container for both username and code input sections
        if not st.session_state.email_verified:
            with st.form(key="forgot_password_form"):
                username = st.text_input("Enter your Driver Username")
                submit_button = st.form_submit_button("Send Code")

                if submit_button:
                    if username:
                        # Retrieve the email associated with the username from the database
                        email = validate_username(username)  # Ensure this function is implemented

                        if email:
                            # Store email and username in session state
                            st.session_state.username = username
                            st.session_state.email = email
                            st.session_state.code_verified = False  # Reset code_verified flag
                            st.session_state.email_verified = True  # Mark email as verified
                            st.info(f"Code has been sent to your registered email: {email}")
                            st.session_state.show_code_input = True  # Show code input section
                        else:
                            st.error("No Driver found with this username.")
                    else:
                        st.error("Please enter a valid username.")

        # Step 2: Code Verification input (Only shown after username is verified)
        if st.session_state.show_code_input:
            with st.form(key="code_verification_form"):
                code = st.text_input("Enter Verification Code")
                verify_button = st.form_submit_button("Verify Code")

                if verify_button:
                    if code == "1010":  # Replace with actual verification logic
                        st.session_state.code_verified = True
                        # Show the Reset Password dialog after successful code verification
                        reset_password_dialog()  # Show the reset password form
                    else:
                        st.error("Incorrect code entered.")

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.full_name = None

# Define Home Page
def home_page():
    # Stylish Title
    st.markdown("""
    <h1>Welcome to the <span style="color:#FF4500;">D</span>rowsiness <span style="color:#FF4500;">D</span>etection & <span style="color:#FF4500;">D</span>river Management System</h1>
    """, unsafe_allow_html=True)
    st.write("")

    # Introduction Section
    st.markdown("""
    <div style="background-color:#f7f7f7; padding: 20px; border-radius: 8px;">
    <h3>Why Choose Our System?</h3>
    Our AI-powered system ensures road safety by detecting driver drowsiness in real-time**. Key benefits include:
    <ul>
        <li><b>Accurate AI Detection:</b> Monitors eye closure, yawning, and head movements.</li>
        <li><b>Real-Time Alerts:</b> Immediate warnings to prevent accidents.</li>
        <li><b>Driver Management:</b> Keep track of driver activity and ensure compliance.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Key Features Section
    st.markdown("<h3 style='color:#FF4500;'>Key Features:</h3>", unsafe_allow_html=True)
    features = [
        ("Real-Time Face & Eye Tracking", "Detects drowsiness using facial landmark detection."),
        ("Instant Alerts & Notifications", "Audio-visual alarms to wake up drivers."),
        ("Trip Monitoring", "Logs trip data and driver behavior."),
        ("Advanced AI Models", "Utilizes deep learning for enhanced accuracy."),
        ("Secure Data Management", "Encrypted data storage for safety compliance."),
    ]
    
    cols = st.columns(3)
    for i, feature in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"<h4><b> {feature[0]}</b></h4>", unsafe_allow_html=True)
            st.write(feature[1])
    
    # How It Works Section
    st.markdown("<h3 style='color:#FF4500;'>How It Works:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <ol>
        <li><b>Face Detection:</b> Uses OpenCV and Dlib to identify driver’s facial landmarks.</li>
        <li><b>Drowsiness Calculation:</b> Eye Aspect Ratio (EAR) and Yawn detection analyze fatigue.</li>
        <li><b>Alert System:</b> Triggers alarms and notifies managers in real-time.</li>
        <li><b>Data Logging:</b> Stores driver behavior for safety audits and analytics.</li>
    </ol>
    """, unsafe_allow_html=True)

    # Benefits Section
    st.markdown("<h3 style='color:#FF4500;'>Benefits:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <ul>
        <li>Prevents road accidents caused by drowsy driving.</li>
        <li>Enhances driver accountability and performance.</li>
        <li>Improves fleet management and regulatory compliance.</li>
    </ul>
    """, unsafe_allow_html=True)
    
    # Call to Action Section
    st.markdown(""" 
    <div style="text-align:center; background-color:#FF4500; color:white; padding: 20px; border-radius: 8px;">
        <h2>Take the Next Step Towards Safer Roads!</h2>
        <p>Empower drivers with AI-driven fatigue monitoring and real-time alerts.</p>
        <a href="#get-started" style="background-color:#f8f8f8; color:#FF4500; padding: 10px 20px; border-radius: 5px; text-decoration:none; font-weight:bold;">Start Now</a>
    </div>
    """, unsafe_allow_html=True)
    st.write("")  


    # Testimonials Section
    st.markdown("<h3 style='color:#FF4500;'>Testimonials:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <blockquote>
        <p><i>"This system significantly improved our fleet safety. Highly recommended!"</i> – <b>Michael R.</b> (Fleet Manager)</p>
        <p><i>"Real-time alerts helped me avoid accidents during long hauls."</i> – <b>David K.</b> (Truck Driver)</p>
    </blockquote>
    """, unsafe_allow_html=True)

    # Contact Us Section
    st.markdown("<h3 style='color:#FF4500;'>Contact Us:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color:#f7f7f7; padding: 20px; border-radius: 8px;">
        <p>For inquiries and support, contact us:</p>
        <ul>
            <li><b>Email:</b> <a href="mailto:rohitpawra189@gmail.com">rohitpawra189@gmail.com</a></li>
            <li><b>GitHub:</b> <a href="https://github.com/rohitp189">rohitp189</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer Section
    st.markdown("""
    <footer style="display: flex; justify-content: space-between; padding: 10px; background-color: #f7f7f7;">
        <span style="color:#FF4500;">© Rohit Pawra 2024</span>
        <span style="color:#FF4500;">v1.5</span>
    </footer>
    """, unsafe_allow_html=True)

    
# Define Logout Page
def logout_page():
    st.markdown(f"## Account: {st.session_state.get('full_name', 'User')}")
    if st.session_state.logged_in:
        if st.button("Log out"):
            # Clear the session state for login
            st.session_state.logged_in = False
            st.session_state.full_name = None
            st.session_state.user_type = None
            st.session_state.driver_id = None
            st.success("Logged out successfully.")
            st.rerun()

# Main function for logged-in users
def loggedin():
    if st.session_state.user_type == 0:  # Admin
        main()  # Run Admin's main page
    else:  # Customer
        driver_app()  # Run Customer's main page

# Placeholder for "Manage" tab when not logged in
def loggedout():
    st.markdown(
    "<h1 style='text-align: center;'> <span style='color:#ff0000'>P</span>lease log in to access this page!</h1>",
    unsafe_allow_html=True)


# Pages Configuration
home = st.Page(home_page, title="Home", icon=":material/home:")
login = st.Page(login_page, title="Login", icon=":material/login:")
logout = st.Page(logout_page, title=f"Account: {st.session_state.get('full_name', 'User')}", icon=":material/account_circle:")
mlogout = st.Page(loggedout, title="Manage", icon=":material/manage_accounts:")
mlogin = st.Page(loggedin, title="Manage", icon=":material/manage_accounts:")
regist = st.Page(registration_page, title="New Registration", icon=":material/person_add:")
forgotp = st.Page(forgot_password_page, title="Forgot Password", icon=":material/password:")
forgotid = st.Page(forgot_driver_page, title="Forgot Driver ID", icon=":material/question_mark:")

# Navigation Setup
if st.session_state.get("logged_in", False):
    if st.session_state.user_type == 0:  # Admin
        pg = st.navigation(
            {
                "Home": [home],
                "Account": [logout],
                "Manage Drivers": [mlogin],  # Admin can manage customers
            }
        )
    else:  # Customer
        pg = st.navigation(
            {
                "Home": [home],
                "Account": [logout],
                "Session": [mlogin],  # Customer manages their own account
            }
        )
else:
    pg = st.navigation(
        {
            "Home": [home],
            "Account": [login, regist, forgotp, forgotid],
            "Session": [mlogout],
        }
    )

# Run Selected Page
pg.run()
