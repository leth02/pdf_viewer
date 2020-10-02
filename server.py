import os
from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.utils import secure_filename
import csv

UPLOAD_FOLDER = 'L:\\flask_app\\upload_files'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'2/5dh81`sewr'
app.config['TESTING'] = True


# Check file extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Serve Upload Page at localhost:5000/
@app.route('/', methods = ['GET', 'POST'])
def upload():
  if request.method == "GET":
    return render_template('upload.html')

  else:
    if request.form.get('upload'):

      # Check if POST request has the file part
      if 'file' not in request.files:
        flash('No file part detected')
        return redirect(url_for('/'))

      file = request.files['file']

      # if user does not select file and hit upload, browser also
      # submit an empty part without filename
      if file.filename == '':
        flash("No selected file")
        return redirect(request.url)
      
      if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Refresh the page to allow users to upload more file(s)
        return render_template('upload.html')

# Serve all files view at localhost:5000/view
@app.route('/view', methods = ["GET", "POST"])
def view():
  remote_addr = request.headers.environ.get('REMOTE_ADDR', "")
  user_agent = request.headers.environ.get('HTTP_USER_AGENT', "")

  if request.method == "GET":
    file_list = generate_file_list()
    print(file_list)
    return render_template('view.html', file_list = file_list)
  
  else:
    if request.form.get('view_the_file'):
      filename = request.form.get('checkbox')
      
      # Render the viewer template with filename so that it can use the filename to fetch the real PDF file
      return render_template("viewer.html", filename = filename, remote_addr = remote_addr, user_agent = user_agent)
    
    else:
      return render_template('greeting.html')
  
# API endpoint serving requests for PDF files
@app.route('/storage/<filename>', methods = ["GET"])
def storage(filename):
  if request.method == "GET":
    # we send the file from the directory whose name matches filename param
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
  else:
    file_list = generate_file_list()
    return render_template("view.html", file_list = file_list)

# Receive the logging information and save it to csv file
@app.route('/log', methods = ["POST"])
def log():
  if request.is_json:
    content = request.get_json()
    client_addr = content["Client_Addr"]
    client_agent = content["Client_Agent"][0:11]
    time_recorded = content["Time_Recorded"]
    filename = content["Filename"]
    page_viewed = content["Page_Viewed"]
    time_spent_on_page = content["Time_Spent_On_Page"]

    # Write to csv logging file
    with open('log.csv', 'a+', newline='') as csvfile:
      fieldnames = ['Client_Addr', 'Client_Agent', 'Time_Recorded', 'Filename', 'Page_Viewed', 'Time_Spent_On_Page(Seconds)']
      writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
      writer.writerow({
        'Client_Addr': client_addr,
        'Client_Agent': client_agent,
        'Time_Recorded': time_recorded,
        'Filename': filename,
        'Page_Viewed': page_viewed,
        'Time_Spent_On_Page(Seconds)': time_spent_on_page
      })

    return 'LOG DATA POSTED'

# Create file list for localhost:5000/view      
def generate_file_list():
  response = []

  # file_list for view.html
  with os.scandir(UPLOAD_FOLDER) as entries:
    count = 1
    for entry in entries:
      if entry.is_file():  
        name = entry.name
        size = size_conversion(entry.stat().st_size)
        response.append((count, name, size)) # one record contains (count, file name, file size)

        count += 1

  return response

# Calculate size of pdf files
def size_conversion(size):
  if size < 1024:
    return str(size) + "bytes"
  elif size >= 1024 and size < 1048576:
    return str(round(size / 1024)) + "KB"
  elif size > 1048576:
    return str(round(size / 1048576)) + "MB"

if __name__ == "__main__":
  app.run()