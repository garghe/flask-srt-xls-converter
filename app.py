import base64
import os
import shutil
import time

from flask import Flask, render_template, request
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
from subtitles import Subtitles

app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.secret_key = 'YOUR KEY'

ALLOWED_EXTENSIONS = {'srt'}
OUTPUT_FOLDER = 'output'
OUTPUT_FOLDER_ARCHIVE = 'archives'
UPLOAD_FOLDER = app.config.get("UPLOAD_FOLDER")
FROM_EMAIL = app.config.get("FROM_EMAIL")
TO_EMAIL = app.config.get("TO_EMAIL")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process', methods=('GET', 'POST'))
def process():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            app.logger.info('No file part')
            return render_template('error.html')

        if not os.path.exists(OUTPUT_FOLDER):
            os.mkdir(OUTPUT_FOLDER)

        if not os.path.exists(OUTPUT_FOLDER_ARCHIVE):
            os.mkdir(OUTPUT_FOLDER_ARCHIVE)

        for f in request.files.getlist('file'):
            if allowed_file(f.filename):
                f.save(os.path.join(UPLOAD_FOLDER, f.filename))
                subtitles = Subtitles(app)
                subtitles.convert(input_filename=UPLOAD_FOLDER + '/' + f.filename, output_filename='output/' + f.filename + '.xls')
            else:
                return render_template('error.html')

        zip_filename = 'output_' + str(int(time.time())) + '.zip'
        shutil.make_archive(zip_filename, 'zip', 'output')

        shutil.rmtree(OUTPUT_FOLDER)

        message = Mail(from_email=FROM_EMAIL,
                       to_emails=TO_EMAIL,
                       subject='Here is your information',
                       html_content='<strong>Please find information attached.</strong>')

        with open(zip_filename + '.zip', 'rb') as f:
            data = f.read()
            f.close()
        encoded_file = base64.b64encode(data).decode()

        attachedFile = Attachment(
            FileContent(encoded_file),
            FileName(zip_filename),
            FileType('application/zip'),
            Disposition('attachment')
        )
        message.attachment = attachedFile

        sendgrid_key = app.config.get("SENDGRID_SECRET")
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)

        return render_template('processed.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS