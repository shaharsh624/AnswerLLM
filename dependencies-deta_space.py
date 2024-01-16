import streamlit as st
import streamlit_authenticator as stauth
from deta import Deta
import datetime
import re
import os
from dotenv import load_dotenv

load_dotenv()

deta = Deta(os.getenv("DETA_KEY"))

# Deta Base
db = deta.Base("streamlit-auth")
drive = deta.Drive("streamlit-drive")

response = drive.get_url("codebasics_faqs.csv")
print("Files", response)


# AUTHENTICATION
def insert_user(email, username, password):
    date_joined = str(datetime.datetime.now())
    return db.put(
        {
            "key": email,
            "username": username,
            "password": password,
            "date_joined": date_joined,
            "projects": {},
        }
    )


def fetch_users():
    users = db.fetch()
    return users.items


def get_user_emails():
    users = db.fetch()
    emails = []
    for user in users.items:
        emails.append(user["key"])
    return emails


def get_usernames():
    users = db.fetch()
    usernames = []
    for user in users.items:
        usernames.append(user["key"])
    return usernames


def validate_email(email):
    pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+.[a-z]{1,3}$"  # tesQQ12@gmail.com

    if re.match(pattern, email):
        return True
    return False


def validate_username(username):
    pattern = "^[a-zA-Z0-9]*$"
    if re.match(pattern, username):
        return True
    return False


def sign_up():
    with st.form(key="signup", clear_on_submit=True):
        st.subheader(":green[Sign Up]")
        email = st.text_input(":blue[Email]", placeholder="Enter Your Email")
        username = st.text_input(":blue[Username]", placeholder="Enter Your Username")
        password1 = st.text_input(
            ":blue[Password]", placeholder="Enter Your Password", type="password"
        )
        password2 = st.text_input(
            ":blue[Confirm Password]",
            placeholder="Confirm Your Password",
            type="password",
        )

        if email:
            if validate_email(email):
                if email not in get_user_emails():
                    if validate_username(username):
                        if username not in get_usernames():
                            if len(username) >= 2:
                                if len(password1) >= 6:
                                    if password1 == password2:
                                        # Add User to DB
                                        hashed_password = stauth.Hasher(
                                            [password2]
                                        ).generate()
                                        insert_user(email, username, hashed_password[0])
                                        st.success("Account created successfully!!")
                                        st.balloons()
                                    else:
                                        st.warning("Passwords Do Not Match")
                                else:
                                    st.warning("Password is too Short")
                            else:
                                st.warning("Username Too short")
                        else:
                            st.warning("Username Already Exists")
                    else:
                        st.warning("Invalid Username")
                else:
                    st.warning("Email Already exists!!")
            else:
                st.warning("Invalid Email")

        btn1, btn2, btn3, btn4, btn5 = st.columns(5)

        with btn3:
            st.form_submit_button("Sign Up")


# PROJECTS


def get_projects(email):
    projects_db = db.get(email)["projects"]
    projects = list(projects_db.keys())
    return projects


def insert_project(email, project_name, project_description):
    prev_projects = db.get(email)["projects"]
    new_project = {project_name: {"project_desc": project_description, "files": {}}}
    new_project.update(prev_projects)
    return db.update({"projects": new_project}, email)


def get_files(email, project_name):
    files_db = db.get(email)["projects"][project_name]["files"]
    files = list(files_db.keys())
    return files_db
