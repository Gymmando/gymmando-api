terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
}

# Artifact Registry repository
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "gymmando-repo"
  format        = "DOCKER"
  
  depends_on = [google_project_service.artifactregistry]
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "livekit_api_key" {
  secret_id = "livekit-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "livekit_api_key" {
  secret      = google_secret_manager_secret.livekit_api_key.id
  secret_data = var.livekit_api_key
}

resource "google_secret_manager_secret" "livekit_api_secret" {
  secret_id = "livekit-api-secret"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "livekit_api_secret" {
  secret      = google_secret_manager_secret.livekit_api_secret.id
  secret_data = var.livekit_api_secret
}

resource "google_secret_manager_secret" "deepgram_api_key" {
  secret_id = "deepgram-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "deepgram_api_key" {
  secret      = google_secret_manager_secret.deepgram_api_key.id
  secret_data = var.deepgram_api_key
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# Cloud Run - API Service
resource "google_cloud_run_v2_service" "api" {
  name     = "gymmando-api"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/gymmando-repo/gymmando-api:latest"
      
      ports {
        container_port = 8000
      }
      
      env {
        name = "LIVEKIT_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.livekit_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "LIVEKIT_API_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.livekit_api_secret.secret_id
            version = "latest"
          }
        }
      }
    }
  }
  
  depends_on = [
    google_project_service.run,
    google_artifact_registry_repository.docker_repo
  ]
}

# Cloud Run - Agent Service
resource "google_cloud_run_v2_service" "agent" {
  name     = "gymmando-agent"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/gymmando-repo/gymmando-agent:latest"
      
      env {
        name  = "LIVEKIT_URL"
        value = "wss://gymbo-li7l0in9.livekit.cloud"
      }
      
      env {
        name = "LIVEKIT_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.livekit_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "LIVEKIT_API_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.livekit_api_secret.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "DEEPGRAM_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.deepgram_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
  
  depends_on = [
    google_project_service.run,
    google_artifact_registry_repository.docker_repo
  ]
}

# Allow public access to API
resource "google_cloud_run_service_iam_member" "api_public" {
  service  = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions Service Account"
}

# Grant permissions
resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/artifactregistry.admin",
    "roles/secretmanager.admin",
    "roles/iam.serviceAccountUser"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Create JSON key
resource "google_service_account_key" "github_actions_key" {
  service_account_id = google_service_account.github_actions.name
}

# Output the key (base64 encoded)
output "github_actions_key" {
  value     = google_service_account_key.github_actions_key.private_key
  sensitive = true
}

resource "google_project_iam_member" "github_actions_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Grant Cloud Run service accounts access to secrets
resource "google_secret_manager_secret_iam_member" "livekit_api_key_access" {
  secret_id = google_secret_manager_secret.livekit_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "livekit_api_secret_access" {
  secret_id = google_secret_manager_secret.livekit_api_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "deepgram_api_key_access" {
  secret_id = google_secret_manager_secret.deepgram_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key_access" {
  secret_id = google_secret_manager_secret.openai_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Add this data source at the top
data "google_project" "project" {
  project_id = var.project_id
}