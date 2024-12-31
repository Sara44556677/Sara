from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, auth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('website.env')  

# Firebase initialization
try:
    cred = credentials.Certificate("firebase_website.json")  # Path to Firebase credentials
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    raise SystemExit("Failed to initialize Firebase Admin SDK")

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure random secret key

# Email Configuration
RECIPIENT_EMAIL = "alguindisara@gmail.com"  

def send_email(user_email, user_name, verification_link=None, message_body=None):
    """Send email via SMTP with verification link or contact message."""
    try:
        if verification_link:
            subject = f"Verify your email address"
            body = f"Hello {user_name},\n\nPlease verify your email by clicking the following link:\n{verification_link}"
        else:
            subject = f"New Message from {user_name}"
            body = f"Hello,\n\nYou have received a new message from {user_name} ({user_email}):\n\n{message_body}"

        msg = MIMEMultipart()
        msg['From'] = "alguindisara@gmail.com"
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('alguindisara@gmail.com', os.getenv('EMAIL_PASSWORD'))  # Use App Password from .env
            server.sendmail("alguindisara@gmail.com", RECIPIENT_EMAIL, msg.as_string())

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/')
def home():
    # Pass the username to the home page for displaying avatar
    return render_template('home.html', user_name=session.get('user_name')) 

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error_message = ""
    success_message = ""

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:
            error_message = "All fields are required!"
        elif len(password) < 6:
            error_message = "Password must be at least 6 characters!"
        else:
            try:
                # Create user in Firebase
                user = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )

                # Generate email verification link
                verification_link = auth.generate_email_verification_link(email)

                # Send the verification email to the user
                email_sent = send_email(email, name, verification_link=verification_link)

                if email_sent:
                    success_message = f"User {user.display_name} created successfully! Please check your email to verify your account."
                else:
                    error_message = "There was an error sending the verification email. Please try again later."
            except Exception as e:
                print(f"Error during signup: {e}")
                error_message = "An error occurred. Please try again."

    return render_template('signup.html', error_message=error_message, success_message=success_message)

@app.route('/verify_email/<uid>', methods=['GET'])
def verify_email(uid):
    try:
        user = auth.get_user(uid)
        if user.email_verified:
            return render_template('verify_email.html', message="Your email has already been verified.")
        else:
            return render_template('verify_email.html', message="Please click the link in your email to verify your email address.")
    except Exception as e:
        print(f"Error verifying email: {e}")
        return render_template('verify_email.html', message="Error during email verification.")

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = ""

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            error_message = "All fields are required!"
        else:
            try:
                user = auth.get_user_by_email(email)

                if not user.email_verified:
                    error_message = "Please verify your email before logging in."
                else:
                    session['user_name'] = user.display_name  
                    return redirect(url_for('home'))

            except Exception as e:
                print(f"Error during login: {e}")
                error_message = "Invalid email or user does not exist."

    return render_template('login.html', error_message=error_message)

@app.route('/contact', methods=['GET', 'POST'])  
def contact():
    error_message = ""
    success_message = ""

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        if not name or not email or not message:
            error_message = "All fields are required!"
        else:
            email_sent = send_email(email, name, message_body=message)

            if email_sent:
                success_message = "Your message has been sent successfully! Thank you for contacting us."
            else:
                error_message = "There was an error sending your message. Please try again later."

    return render_template('contact.html', error_message=error_message, success_message=success_message)

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/turtle_gallery')
def turtle_gallery():
    return render_template('photo_gallery.html')

if __name__ == '__main__':
    app.run(debug=True)
