# SRT to Excel Subtitles converter

## Project Description
A simple Flask web application that:
1. Accept multiple SRT Subtitles files for upload
2. Convert them into Excel files
3. Compress them
4. Send them via email, using Sendgrid

## How to Run
1. Clone the repo
2. Copy .env_template to .env and set:
   1. SENDGRID_SECRET (You'll need to get a Sendgrid account first and create an API KEY)
   2. UPLOAD_FOLDER, local folder where the files will be uploaded
   3. FROM_EMAIL, the email  originator
   4. TO_EMAIL, the email address destination
3. Execute `flask run` - webapp will start on http://127.0.0.1:8080

## Source 

#### SRT Subtitles example:

1
00:00:22,200 --> 00:00:27,080
Sub1 - Line 1
Sub1 - Line 2

2
00:00:27,160 --> 00:00:29,640
Sub 2 - Line 1


#### Excel output 

| Index | Cue-in --> Cue-out            |   Subtitle      |
|   1   | 00:00:22,200 --> 00:00:27,080 | Sub1 - Line 1   |
|       |                               | Sub1 - Line 2   | 
|   2   | 00:00:27,160 --> 00:00:29,640 | Sub2 - Line 1   | 

