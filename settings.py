from os import environ

SENDGRID_SECRET = environ.get('SENDGRID_SECRET')
UPLOAD_FOLDER = environ.get('UPLOAD_FOLDER')
FROM_EMAIL = environ.get('FROM_EMAIL')
TO_EMAIL = environ.get('TO_EMAIL')