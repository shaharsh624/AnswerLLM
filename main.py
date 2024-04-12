import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from dependencies import (
    sign_up,
    fetch_users,
    insert_project,
    get_projects,
    get_files,
    insert_file,
)
import traceback
from langchain_helper import get_qa_chain

st.set_page_config(page_title="Streamlit Auth", page_icon=":lock:", layout="wide")

try:
    users = fetch_users()
    emails = []
    usernames = []
    passwords = []

    for user in users:
        emails.append(user["email"])
        usernames.append(user["username"])
        passwords.append(user["password"])

    credentials = {"usernames": {}}

    for i in range(len(emails)):
        credentials["usernames"][usernames[i]] = {
            "name": emails[i],
            "password": passwords[i],
        }

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="streamlit-auth",
        key="abcdef",
        cookie_expiry_days=4,
    )

    email, authentication_status, username = authenticator.login(
        ":green[Login]", "main"
    )

    info, info1 = st.columns(2)

    if not authentication_status:
        sign_up()

    if username:
        if username in usernames:
            if authentication_status:
                username = username[0].upper() + username[1:]
                # MAIN APP
                st.sidebar.subheader(f"Welcome {username.upper()}")
                authenticator.logout("Log Out", "sidebar")

                # Actions
                projects_name = sorted(list(get_projects(email)))
                projects_desc = get_projects(email)
                pages = ["Home", "Create Project"] + projects_name
                page = st.sidebar.selectbox("Choose a page", pages)

                if page == "Home":
                    st.subheader("This is the home page")
                    st.markdown(
                        """
                        ---
                        Created with ❤️ by Harsh

                        """
                    )
                elif page == "Create Project":
                    st.title("Create new Project")
                    with st.form(key="add_project", clear_on_submit=True):
                        project_name = st.text_input(
                            ":blue[Project Name]", placeholder="Enter Project Name"
                        )
                        project_desc = st.text_input(
                            ":blue[Description]",
                            placeholder="Enter Project Description",
                        )

                        if st.form_submit_button("Create Project"):
                            insert_project(email, project_name, project_desc)
                            st.write("Project created successfully!")
                else:
                    st.title(page)
                    st.subheader(projects_desc[page]["project_desc"])

                    # Upload Files
                    with st.form(key="add_file", clear_on_submit=True):
                        st.subheader("Upload new File")
                        file_name = st.text_input(
                            ":blue[Give your file a name]",
                            placeholder="Enter File Name",
                        )
                        file = st.file_uploader(
                            ":blue[Choose a file to upload]",
                            type=["csv", "json", "txt"],
                        )

                        if st.form_submit_button("Add File"):
                            insert_file(email, page, file_name, file)

                    # View Files
                    files = get_files(email, page)
                    if files:
                        file_names = [x.replace(",", ".") for x in list(files.keys())]
                        for file in file_names:
                            with st.expander(label=file):
                                col1, col2 = st.columns([2, 1], gap="medium")
                                with col1:
                                    df = pd.DataFrame(files[file.replace(".", ",")])
                                    st.write(df)
                                with col2:
                                    st.subheader("Questionnaires")
                                    question = st.text_input(
                                        "Question: ", key=page + "-" + file
                                    )

                                    if question:
                                        chain = get_qa_chain(page, file_name)
                                        response = chain(question)

                                        st.subheader("Answer")
                                        st.write(response["result"])

            elif not authentication_status:
                with info:
                    st.error("Incorrect Password or username")
            else:
                with info:
                    st.warning("Please feed in your credentials")
        else:
            with info:
                st.warning("Username does not exist, Please Sign up")

except Exception as e:
    st.error("Refresh Page")
    st.error(traceback.format_exc())
