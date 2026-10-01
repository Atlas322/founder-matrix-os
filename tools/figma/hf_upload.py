"""Higgsfield media_upload-оос авсан presigned URL руу файл PUT хийх туслах.
  python hf_upload.py <file> <upload_url> <content_type>"""
import sys, urllib.request
f, url, ct = sys.argv[1], sys.argv[2], sys.argv[3]
req = urllib.request.Request(url, data=open(f, "rb").read(), method="PUT", headers={"Content-Type": ct})
print(urllib.request.urlopen(req).status)
