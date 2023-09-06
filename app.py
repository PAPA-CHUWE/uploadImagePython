from flask import Flask, request, render_template, flash
import os
import psycopg2
from psycopg2 import OperationalError
from PIL import Image

app = Flask(__name__)
secret_key = os.urandom(24)
app.secret_key = secret_key  # Change this to a random secret key

# Define allowed image file types and dimensions for a profile picture
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_IMAGE_DIMENSION = (300, 300)  # You can adjust the maximum dimensions as needed

# Database configuration
try:
    db = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='wkpProg219!',
        database='pyImagedb'
    )

    cursor = db.cursor()

    # SQL statement to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS imagestbl (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255),
        filetype VARCHAR(100),
        filesize INT
    );
    """

    cursor.execute(create_table_sql)
    db.commit()

    cursor.close()
except OperationalError as e:
    app.logger.error(e)
    flash('Database connection error.', 'error')
    db = None

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to check if the image dimensions are suitable for a profile picture
def is_profile_picture(image):
    try:
        img = Image.open(image)
        img.thumbnail(MAX_IMAGE_DIMENSION)
        return img.size == MAX_IMAGE_DIMENSION
    except Exception as e:
        app.logger.error(e)
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if db is None:
        return 'Database connection error. Please check the logs.'

    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '' and allowed_file(image.filename) and is_profile_picture(image):
            # Save the image to a temporary folder
            image_path = os.path.join('uploads', image.filename)
            image.save(image_path)

            # Insert image details into the database
            cursor = db.cursor()
            try:
                cursor.execute("""
                    INSERT INTO imagestbl (filename, filetype, filesize)
                    VALUES (%s, %s, %s)
                """, (image.filename, image.content_type, os.path.getsize(image_path)))
                db.commit()
                cursor.close()
                return 'Image uploaded successfully!'
            except Exception as e:
                app.logger.error(e)
                flash('Image upload failed.', 'error')
                db.rollback()
                cursor.close()
        else:
            return 'Invalid image file or dimensions are not suitable for a profile picture.'

    return 'No image uploaded.'

if __name__ == '__main__':
    app.run(debug=True)
