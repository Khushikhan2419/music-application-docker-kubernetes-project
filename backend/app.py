from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)

# ---------------- AWS CONFIG ----------------
AWS_ACCESS_KEY_ID = ""      
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION = "ap-southeast-2"
BUCKET_NAME = "khushiawssongs"

SONG_PREFIX = "song/"        # Folder for songs
IMAGE_PREFIX = "images/"     # Folder for images (album art)

# ---------------- BOTO3 CLIENT ----------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# ---------------- GET SONGS WITH IMAGE ----------------
@app.route("/songs", methods=["GET"])
def get_songs():
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=SONG_PREFIX)

        if "Contents" not in response:
            return jsonify({"message": "No songs found"}), 404

        songs = []

        for obj in response["Contents"]:
            key = obj["Key"]

            # only pick audio files
            if key.lower().endswith((".mp3", ".wav", ".aac", ".m4a", ".ogg")):

                # Song URL
                song_url = s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": BUCKET_NAME, "Key": key},
                    ExpiresIn=3600,
                )

                # Image key based on song name
                base_name = os.path.splitext(os.path.basename(key))[0]
                image_key = IMAGE_PREFIX + base_name + ".jpg"

                # Default image (if not found)
                image_url = None
                try:
                    # Generate image URL
                    image_url = s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": BUCKET_NAME, "Key": image_key},
                        ExpiresIn=3600,
                    )
                except:
                    image_url = None

                songs.append({
                    "file": key,
                    "url": song_url,
                    "image": image_url
                })

        return jsonify(songs), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- UPLOAD SONG + IMAGE ----------------
@app.route("/upload_song", methods=["POST"])
def upload_song():
    try:
        # Check song
        if "song" not in request.files:
            return jsonify({"error": "Song file missing"}), 400

        song_file = request.files["song"]

        if song_file.filename == "":
            return jsonify({"error": "No song selected"}), 400

        song_filename = secure_filename(song_file.filename)

        # validate audio
        if not song_filename.lower().endswith((".mp3", ".wav", ".aac", ".m4a", ".ogg")):
            return jsonify({"error": "Only audio files allowed"}), 400

        song_key = SONG_PREFIX + song_filename

        # Upload song
        s3.upload_fileobj(song_file, BUCKET_NAME, song_key)

        # ---------------- IMAGE (OPTIONAL) ----------------
        if "image" in request.files:
            image_file = request.files["image"]
            if image_file.filename != "":
                image_key = IMAGE_PREFIX + os.path.splitext(song_filename)[0] + ".jpg"
                s3.upload_fileobj(image_file, BUCKET_NAME, image_key)

        return jsonify({"message": f"Uploaded {song_filename} successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
