I need a cli utility which can be used to extract metadata from photo files. The supported file types must include: ARW, JPG, PNG. Please use Python with the Typer package. The cli should include the following methods: 

1. get_photo_metadata - takes as input (input_path,  output_path). 

Input path is a file path which leads to a file or directory. If the path leads to a file then read the file metadata and write it to json. Capture all metadata offered in the file. If the path leads to a directory then walk through the directory and every sub directory looking for valid photo  file types. For each photo found capture all provided metadata and write it to json. 

Output path is the directory where metadata json files are written to. 

For each photo file found the name of the metadata json file is FILE_NAME.json, where FILE_NAME is the name of the photo file.

2. create_metadata_markdown - takes input (input_path, output_path).

Input path is a file path which leads to a file or directory. If the path leads to a file then read the metadata json file. Identify the following fields in the metadata: date, image, location, collection, width, heigt. Write those fields to an md file of the form (this is an example metadata markdown file):

---
date: 2025:08:27 21:37:45-07:00
image: https://served-photos-556758165742-us-west-2-an.s3.us-west-2.amazonaws.com/gallery/DSC00037.jpg
location: Portland, OR
collection: Bridges
width: 9214
height: 6143
---

If any of the above fields can not be found in the metadata then leave that field blank. If the path leads to a directory then walk through the directory and every sub directory looking for valid photo metadata json files. For each photo metadata json file found create a metadata markdown file as described above. 

Output path is the directory where metadata markdown files are written to. 

For each photo metadata json file found the name of the markdown file should be FILE_NAME.md.


Please add a test suite to riggorously test each method. Look for edge cases and possible failure states.

Let me know if you have any questions.
