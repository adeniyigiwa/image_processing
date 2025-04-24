# Image Processing with Amazon Rekognition and PhotoPrism
This project processes images in a folder before moving them to PhotoPrism. It uses Amazon Rekognition to label the images, translates the labels into German, and optionally identifies faces in the images. If a person is recognized, their name is included in the image description. This solution is designed to enhance image metadata before uploading to PhotoPrism.

## Table of Contents
1. Overview
2. Installation
3. Configuration
4. How It Works
5. Folder Structure
6. Usage




### Overview
This tool automates the following image processing tasks:
Resizing images that exceed 4.5 MB to make them compatible with Amazon Rekognition's 5MB size limit.
Labeling images using Amazon Rekognition (e.g., identifying objects like "car", "dog", "person").
Translating Rekognition labels into German for localized descriptions.
Face detection: If a person is detected, the script identifies faces using Rekognition's face recognition API, adding the person’s name to the description.
Face collection management: Adds new faces to Rekognition's face collection for future identification.
Saving metadata to text files for easy tracking and reuse.

### Installation
1. Install Dependencies:
  #### Python 3.x
  #### boto3 (Amazon Web Services SDK for Python)
  #### Pillow (for image handling)
  #### googletrans (for label translation)

2. Install with pip:
  ### pip install boto3 Pillow googletrans

3. Set Up AWS Credentials:
   #### Make sure you have valid AWS credentials (Access Key ID and Secret Access Key) configured using AWS CLI or through environment variables:
   aws configure
   
5. Create Rekognition Face Collection:
   ##### In the AWS console, create a Rekognition face collection for storing identified faces.

### Configuration
Before using the script, ensure the following configurations are set:
AWS Region: Make sure your AWS services (Rekognition, Translate, etc.) are set to the appropriate region.
Face Collection Name: Specify the name of the Rekognition face collection where known faces will be stored.
Folder Paths: Define the folder where images will be processed and the folder for unknown faces.
Modify these settings in the configuration section of the script:

# Configuration
folder_path = 'path_to_images/'  # Folder with images
face_collection_name = 'your_face_collection_name'
unknown_faces_folder = 'path_to_unknown_faces/'
How It Works
1. Image Size Check & Resizing:
The script checks if the image size exceeds 4.5 MB and resizes it if needed.
2. Image Labeling:
Amazon Rekognition is called to label the image (e.g., detecting "car", "tree", "person").
3. Translation of Labels to German:
The labels from Rekognition are translated into German using Amazon Translate.
4. Face Recognition:
If a person is detected in the image, Rekognition's face recognition API is used to match known faces in the collection.
The names of recognized individuals are added to the description.
5. Face Collection Management:
The script supports adding new faces to Rekognition's face collection by placing known people’s images in a specific folder.
6. Data Saving:
Translated labels and face recognition data are saved for future reference, ensuring that the script does not need to repeat the same operations.

### Folder Structure
The following folder structure is used for organizing the images and metadata:
project/
│
├── pics/                     # Folder for image files to be processed
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
│
├── translate.txt             # Stores previously translated labels
├── unknown_faces/            # Folder for storing images of unidentified faces
│   ├── face1.jpg
│   └── ...
│
└── face_collection/          # Folder for adding new known faces
    ├── Anna/
    │   └── anna1.jpg
    ├── John/
    │   └── john1.jpg
    └── ...
### Usage
1. Place the images to be processed in the pics/ folder.
2. Run the script, and it will:
      Process each image.
      Detect objects and people using Rekognition.
      Translate the labels into German.
      Identify faces and add their names to the image descriptions.
      Save unknown faces in the unknown_faces/ folder.
python process_images.py

