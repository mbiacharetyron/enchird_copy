# Backend Setup with Django

This are instructions for setting up the backend on your local environment.


## Database Setup

1. Download and install pdAdmin 4 or an version you are comfortable working with.
    - Download link MAC OS
    https://www.postgresql.org/ftp/pgadmin/pgadmin4/v7.8/macos/

    - Download link Windows
    https://www.postgresql.org/ftp/pgadmin/pgadmin4/v7.8/windows/

2. Run pgAdmin4 and enter your master password when setting up your pgAdmin (Take default settings during installation)

3. On the left panel, Click the dropdown on servers, then the dropdown on PostgreSQL.

4. Right click on databases and click create, then databases and name the database, (enchird_database), then click on save.


***


## Getting Started

1. You should have installed python, prefereabley 3.8 and above.

2. Navigate to the backend folder where you will find this README file and another folder named "enchird_backend".

3. Create a virtual envirnonment with:

    ```bash
   python -m venv venv
   ```

4. Start your virtual environment by 

    ```
    venv\scripts\activate
    ```

5. cd into the (enchird_backend) folder

6. Install the requirement of the backend by running 

    ```
    pip install -r requirements.txt
    ```

7. Run migrations

    ```
    python manage.py migrate
    ```

8. Populate the database

    ```
    psql -U postgres -d <database_name> -f backup.sql

    ```
    NOTE: For this to work (psql command):

        Add PostgreSQL bin Directory to PATH:

        Find the path to the PostgreSQL bin directory. This directory typically contains the PostgreSQL command-line utilities.

        Add this directory to your system's PATH. Follow these steps to do it on Windows:

        Open the Windows Start menu and search for "Environment Variables" or "Edit the system environment variables."

        Click the "Environment Variables" button.

        In the "System Variables" section, find the "Path" variable and click "Edit."

        Click "New" and add the path to the PostgreSQL bin directory.

        Click "OK" to save your changes.

        Close and reopen your command prompt to apply the changes.

9. Start the backend server by running 

    ```
    python manage.py runserver
    ```

***
## Postman Setup

1. If you have postman already setup, you can import the json collection (Enchird LMS.postman_collection.json) from the backend folder. This collect contains few startup requests like login, create student

***
## Authentication System

1. We are currently using JWT for authentication.
   
2. Upon login with correct email and password an "access_token" and "refresh_token" are sent as JSON response.

3. The access_token is used for make requests that require authentication and is different for each user. 

4. The access_token expires after 30 minutes and there is a request in the postman collection which allows you to get a new access token using the refresh_token.

5. The access_token is passed in the header of the request as (Authorization: Bearer <access_token_value>)





