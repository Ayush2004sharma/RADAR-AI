from datetime import datetime

# project_id -> { files, updated_at }
FILE_STRUCTURE_CACHE = {}

# project_id -> { path, status }
FILE_REQUEST_CACHE = {}

# project_id -> { path, content }
FILE_CONTENT_CACHE = {}
