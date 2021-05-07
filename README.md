# SRT to Excel Subtitles converter

## Project Description
A simple Flask web application that:
1. Accept multiple SRT Subtitles files for upload
2. Convert them into Excel files
3. Compress them
4. Send them via email, using Sendgrid

##How to Run
1. Clone the repo
2. Copy .env_template to .env and set:
   1. SENDGRID_SECRET (You'll need to get a Sendgrid account first and create an API KEY)
   2. UPLOAD_FOLDER, local folder where the files will be uploaded
3. Execute `flask run` - webapp will start on http://127.0.0.1:8080


