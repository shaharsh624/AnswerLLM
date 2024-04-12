import datetime
import os
import re
import pymongo
import streamlit as st
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
from langchain_helper import create_vector_db

import pandas as pd

load_dotenv()

client = pymongo.MongoClient(os.getenv("MONGO_URL"), server_api=ServerApi("1"))
db = client.get_database("main")["llmUsers"]


# AUTHENTICATION
def insert_user(email, username, password):
    date_joined = str(datetime.datetime.now())
    return db.insert_one(
        {
            "email": email,
            "username": username,
            "password": password,
            "date_joined": date_joined,
            "projects": {},
        }
    )


def fetch_users():
    users = [user for user in db.find()]
    return list(users)


def get_user_emails():
    emails = [user["email"] for user in db.find()]
    return emails


def get_usernames():
    usernames = [user["username"] for user in db.find()]
    return usernames


def validate_email(email):
    pattern = "^[a-zA-Z0-9-_]+@[a-zA-Z0-9]+.[a-z]{1,3}$"  # tesQQ12@gmail.com

    if re.match(pattern, email):
        return True
    return False


def validate_username(username):
    pattern = "^[a-zA-Z0-9_]*$"
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
                                        insert_user(
                                            email, username.lower(), hashed_password[0]
                                        )
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

        st.form_submit_button("Sign Up")


# PROJECTS


def get_projects(email):
    projects_db = [user["projects"] for user in db.find({"email": email})][0]
    projects = list(projects_db)
    return projects_db


def insert_project(email, project_name, project_description):
    prev_projects = [user["projects"] for user in db.find({"email": email})][0]
    new_project = {project_name: {"project_desc": project_description, "files": {}}}
    new_project.update(prev_projects)

    return db.update_one({"email": email}, {"$set": {"projects": new_project}})


def get_files(email, project_name):
    projects_db = [user["projects"] for user in db.find({"email": email})][0]
    if project_name in projects_db:
        files_db = projects_db[project_name]["files"]
        files = list(files_db.keys())
        return files_db
    else:
        return "Project not found"


def insert_file(email, project_name, file_name_original, file):
    file_name = file_name_original.replace(".", ",")
    if file is not None and file.name.endswith(".csv"):
        try:
            df = pd.read_csv(file, encoding="latin-1")
            data = df.to_dict("records")

            # Saving to MongoDB
            db.update_one(
                {"email": email},
                {
                    "$set": {
                        f"projects.{project_name}.files.{file_name}": data,
                        "date_modified": str(datetime.datetime.now()),
                    }
                },
            )

            # Saving locally
            directory = os.path.join("data", project_name)
            if not os.path.exists(directory):
                os.makedirs(directory)
            file_path = os.path.join(directory, file_name_original)
            df.to_csv(file_path, index=False)

            create_vector_db(project_name, file_name_original)
        except Exception as e:
            st.error(f"Error during upload: {str(e)}")
    else:
        st.error("File is either None or not a CSV file.")
