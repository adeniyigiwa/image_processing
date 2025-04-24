import boto3
from PIL import Image
import os
import io
import uuid
import shutil
import mimetypes

# Define constants and file paths
collection_id = 'Faces4Photoprism'
collection_filename = "./collection.txt"
translation_filename = "./translate.txt"
path_to_temp = "./temp/"
path_to_faces = "./pics/"
path_to_unknown_faces = "./_unknown/"
path_to_pictures = "/mnt/Dropbox/Camera Uploads/"

# Initialize clients
client = boto3.client('rekognition')
translate = boto3.client('translate', region_name='eu-west-1', use_ssl=True)
mimetypes.init()


def limit_img_size(img_filename, img_target_filename, target_filesize, tolerance=5):
    img = img_orig = Image.open(img_filename)
    aspect = img.size[0] / img.size[1]

    while True:
        with io.BytesIO() as buffer:
            img.save(buffer, format="JPEG")
            data = buffer.getvalue()
        filesize = len(data)
        size_deviation = filesize / target_filesize
        if size_deviation <= (100 + tolerance) / 100:
            with open(img_target_filename, "wb") as f:
                f.write(data)
            break
        else:
            new_width = img.size[0] / size_deviation**0.5
            new_height = new_width / aspect
            img = img_orig.resize((int(new_width), int(new_height)))


def resize_image(photo, maxsize, overwrite=False):
    size = os.path.getsize(photo)
    if size > maxsize:
        if not overwrite:
            new_filename = path_to_temp + uuid.uuid4().hex + ".jpg"
        else:
            new_filename = photo
        limit_img_size(photo, new_filename, maxsize)
        return new_filename
    return photo


def save_collection(collected_faces):
    with open(collection_filename, "w") as f:
        for face in collected_faces:
            f.write(face + "\n")


def load_collection():
    if not os.path.exists(collection_filename):
        return []
    with open(collection_filename) as f:
        return [line.strip() for line in f]


def save_translate(wortliste):
    with open(translation_filename, "w") as f:
        for key in wortliste:
            f.write(f"{key};{wortliste[key]}\n")


def load_translate():
    wortliste = {}
    if not os.path.exists(translation_filename):
        return wortliste
    with open(translation_filename) as f:
        for line in f:
            en, de = line.strip().split(";")
            wortliste[en] = de
    return wortliste


def read_filelist(pfad):
    return [f for f in os.listdir(pfad) if os.path.isfile(os.path.join(pfad, f))]


def list_faces_in_collection(collection_id):
    faces_count = 0
    response = client.list_faces(CollectionId=collection_id, MaxResults=10)
    while True:
        for face in response['Faces']:
            print(face)
            faces_count += 1
        if 'NextToken' in response:
            response = client.list_faces(CollectionId=collection_id,
                                         NextToken=response['NextToken'], MaxResults=10)
        else:
            break
    return faces_count


def search_face(photo, collection_id):
    threshold = 50
    photo = resize_image(photo, 4500000, overwrite=True)
    with open(photo, 'rb') as imageSource:
        response = client.search_faces_by_image(CollectionId=collection_id,
                                                Image={'Bytes': imageSource.read()},
                                                FaceMatchThreshold=threshold,
                                                MaxFaces=1)
    found_faces = []
    for match in response.get('FaceMatches', []):
        found_faces.append(match['Face']['ExternalImageId'])

    if not found_faces:
        shutil.move(photo, os.path.join(path_to_unknown_faces, os.path.basename(photo)))

    return set(found_faces)


def search_faces(photo, collection_id):
    img = Image.open(photo)
    photo_work = resize_image(photo, 4500000)
    with open(photo_work, 'rb') as imageSource:
        response = client.detect_faces(Image={'Bytes': imageSource.read()}, Attributes=['ALL'])

    found_persons = []

    for face in response['FaceDetails']:
        box = face['BoundingBox']
        left = img.width * box['Left']
        top = img.height * box['Top']
        width = img.width * box['Width']
        height = img.height * box['Height']
        cropped = img.crop((left, top, left + width, top + height))
        temp_filename = path_to_temp + uuid.uuid4().hex + ".jpg"
        cropped.save(temp_filename)
        temp_filename = resize_image(temp_filename, 4500000, overwrite=True)
        results = search_face(temp_filename, collection_id)
        found_persons.extend(results)

    return found_persons


def add_faces_to_collection(photo, photo_id, collection_id):
    with open(photo, 'rb') as imageSource:
        response = client.index_faces(CollectionId=collection_id,
                                      Image={'Bytes': imageSource.read()},
                                      ExternalImageId=photo_id,
                                      MaxFaces=1,
                                      QualityFilter="AUTO",
                                      DetectionAttributes=['ALL'])

    return len(response['FaceRecords'])


def update_collection(collected_faces):
    for root, _, files in os.walk(path_to_faces):
        person_name = os.path.relpath(root, path_to_faces)
        if person_name == ".":
            continue
        for onefile in files:
            filename = os.path.join(root, onefile)
            if filename not in collected_faces:
                filename = resize_image(filename, 4500000, overwrite=True)
                if add_faces_to_collection(filename, person_name, collection_id) > 0:
                    collected_faces.append(filename)
    return collected_faces


# Main execution block

# Try creating a new collection
try:
    client.create_collection(CollectionId=collection_id)
    print(f"Collection '{collection_id}' created.")
except client.exceptions.ResourceAlreadyExistsException:
    print(f"Collection '{collection_id}' already exists.")

# Load previous data
collected_faces = load_collection()
translated = load_translate()

# Update face collection
collected_faces = update_collection(collected_faces)
save_collection(collected_faces)

# Process all pictures
for datei in read_filelist(path_to_pictures):
    photo = os.path.join(path_to_pictures, datei)
    mime_type = mimetypes.guess_type(photo)[0]

    if mime_type and mime_type.startswith('image'):
        photo_work = resize_image(photo, 4500000)

        with open(photo_work, 'rb') as image:
            response = client.detect_labels(Image={'Bytes': image.read()}, MaxLabels=50)

        label_lst = [label['Name'] for label in response['Labels']]
        label_lst += [parent['Name'] for label in response['Labels'] for parent in label['Parents']]
        labels_en = set(label_lst)

        labels_de = []
        for label_en in labels_en:
            if label_en in translated:
                labels_de.append(translated[label_en])
            else:
                result = translate.translate_text(Text=label_en, SourceLanguageCode="en", TargetLanguageCode="de")
                translated[label_en] = result['TranslatedText']
                labels_de.append(result['TranslatedText'])

        save_translate(translated)
        print(f"Labels for {photo}: {labels_de}")

