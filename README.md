### AIGIS
AIGIS is a web application that allows users to create, edit, and delete geospacial posts.
The platform provides a user-friendly interface for users to interact with geospatial data and provides AI powered analysis and insight .
### Features

- Create, edit, and delete geospacial posts
- AI powered analysis and prediction
- User authentication and authorization
- Geospatial data visualization
- Responsive design
- User-friendly interface
- 
### Installation
Assuming you have access to an Ubuntu server, you can install AIGIS using the following steps:
Clone the repository:
>     git clone https://github.com/jamescndubuisi/AIGIS.git
>     cd AIGIS

#### Execute the following commands:

>     sudo apt update
>     sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl

### Create Postgresql database and user:

>     postgres=# sudo -u postgres psql
>     postgres=# CREATE DATABASE dbname;
>     postgres=# CREATE USER dbuser WITH PASSWORD 'db_password';
>     postgres=# GRANT ALL PRIVILEGES ON DATABASE dbname TO dbuser;
>     postgres=# ALTER ROLE dbuser SET client_encoding TO 'utf8';
>     postgres=# ALTER ROLE dbuser SET default_transaction_isolation TO 'read committed';
>     postgres=# ALTER ROLE dbuser SET timezone TO 'UTC';
>     postgres=# ALTER DATABASE dbname OWNER TO dbuser;
>     postgres=# \q

### Grant your local user access to static files
>      $ sudo usermod -a -G your_user www-data

### Create a virtual environment and activate it:

>     $ python3 -m venv venv
>     $ source venv/bin/activate

### Install the required packages:
>     (venv) $ pip install -r requirements.txt
>     (venv)$ nano AIGIS/settings.py

ALLOWED_HOSTS = ['your_server_domain_or_IP', 'second_domain_or_IP', . . ., 'localhost']

#### Create .env file

>     (venv)$ nano AIGIS/.env
>     SECRET_KEY=your_secret_key
>     SECRET_KEY=django-insecure-_by_i4hlef_hsun$2uaog&_8cg+_n+_dag*90s+t%ezowg4&jq
>     DB_NAME=aigis_db
>     DB_USER=aigis_db_user
>     DB_PASSWORD=0112345567890@aigis
>     SERVER_IP=129.159.139.126
>     DEFAULT_FROM_EMAIL="your_email@domain"
>     GOOGLE_API= your_google_api_key

### Run the following commands to setup database migrations and collect static files:
>     (venv)$ python manage.py makemigrations
>     (venv)$ python manage.py migrate
>     (venv)$ python manage.py createsuperuser
>     (venv)$ python manage.py collectstatic
#### Run the following commands to test the gunicorn server:

>     (venv)$gunicorn --bind 0.0.0.0:8000 AIGIS.wsgi
>     (venv)$deactivate
>     $
### Create a cronjob for your celery worker

>     $crontab -e
>     @reboot /home/ubuntu/AIGIS/venv/bin/celery -A AIGIS.celery worker -l info -P eventlet
### This is where the peculiarities end
### The rest is just a standard django project deployment
Checkout the following link for more details:
https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu
#### Do not forget to open port 80 and 443 on your server and turn debug to false
