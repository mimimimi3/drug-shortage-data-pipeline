
resource "google_storage_bucket" "raw_data_bucket" {
  name          = "drug-shortage-raw-data-bucket"
  location      = var.location
  force_destroy = true


  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}


resource "google_bigquery_dataset" "raw" {
  dataset_id = "raw_dataset"
  project    = var.project_id
  location   = var.location
}

resource "google_bigquery_dataset" "staging" {
  dataset_id = "staging_dataset"
  project    = var.project_id
  location   = var.location
}

resource "google_bigquery_dataset" "intermediate" {
  dataset_id = "int_dataset"
  project    = var.project_id
  location   = var.location
}

resource "google_bigquery_dataset" "mart" {
  dataset_id = "mart_dataset"
  project    = var.project_id
  location   = var.location
}