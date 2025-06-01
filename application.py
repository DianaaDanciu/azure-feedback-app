import os
from flask import Flask, request, render_template, redirect, url_for
from azure.data.tables import TableServiceClient, TableEntity
from azure.storage.blob import BlobServiceClient
from datetime import datetime
import uuid

app = Flask(__name__)

# Azure settings
STORAGE_CONNECTION_STRING = os.environ.get("STORAGE_CONNECTION_STRING")
if not STORAGE_CONNECTION_STRING:
    raise RuntimeError("STORAGE_CONNECTION_STRING environment variable is not set.")
blob_service = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
table_service = TableServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
table_client = table_service.get_table_client("feedback")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form["feedback"]
        file = request.files.get("image")
        row_key = str(uuid.uuid4())

        image_url = ""
        if file:
            blob_client = blob_service.get_blob_client(container="images", blob=row_key + "-" + file.filename)
            blob_client.upload_blob(file)
            image_url = blob_client.url

        entity = {
            "PartitionKey": "feedback",
            "RowKey": row_key,
            "text": text,
            "image_url": image_url,
            "date": datetime.utcnow().isoformat()
        }
        table_client.create_entity(entity)

        return redirect(url_for("index"))

    feedbacks = table_client.query_entities("PartitionKey eq 'feedback'")
    sorted_feedbacks = sorted(feedbacks, key=lambda x: x["date"], reverse=True)
    return render_template("index.html", feedbacks=sorted_feedbacks)
