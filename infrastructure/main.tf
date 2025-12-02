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

# Data source for project
data "google_project" "project" {
  project_id = var.project_id
}

# Enable required APIs
resource "google_project_service" "compute" {
  service = "compute.googleapis.com"
}

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

# Grant Cloud Run default service account access to secrets (for API)
resource "google_secret_manager_secret_iam_member" "livekit_api_key_access_cloudrun" {
  secret_id = google_secret_manager_secret.livekit_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "livekit_api_secret_access_cloudrun" {
  secret_id = google_secret_manager_secret.livekit_api_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Service account for agent VM
resource "google_service_account" "agent_sa" {
  account_id   = "gymmando-agent"
  display_name = "Gymmando Agent Service Account"
}

# Grant agent service account access to all secrets
resource "google_secret_manager_secret_iam_member" "livekit_api_key_access_agent" {
  secret_id = google_secret_manager_secret.livekit_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "livekit_api_secret_access_agent" {
  secret_id = google_secret_manager_secret.livekit_api_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "deepgram_api_key_access_agent" {
  secret_id = google_secret_manager_secret.deepgram_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key_access_agent" {
  secret_id = google_secret_manager_secret.openai_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant agent SA permission to pull from Artifact Registry
resource "google_project_iam_member" "agent_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
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

# Allow public access to API
resource "google_cloud_run_service_iam_member" "api_public" {
  service  = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Compute Engine VM for Agent
resource "google_compute_instance" "agent" {
  name         = "gymmando-agent"
  machine_type = "e2-small"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"  # Container-Optimized OS
      size  = 20
    }
  }

  network_interface {
    network = "default"
    access_config {
      # Ephemeral public IP
    }
  }

  service_account {
    email  = google_service_account.agent_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    gce-container-declaration = <<-EOF
      spec:
        containers:
        - name: agent
          image: ${var.region}-docker.pkg.dev/${var.project_id}/gymmando-repo/gymmando-agent:latest
          env:
          - name: LIVEKIT_URL
            value: "wss://gymbo-li7l0in9.livekit.cloud"
          - name: LIVEKIT_API_KEY
            value: "${var.livekit_api_key}"
          - name: LIVEKIT_API_SECRET
            value: "${var.livekit_api_secret}"
          - name: DEEPGRAM_API_KEY
            value: "${var.deepgram_api_key}"
          - name: OPENAI_API_KEY
            value: "${var.openai_api_key}"
          stdin: false
          tty: false
        restartPolicy: Always
    EOF
  }

  allow_stopping_for_update = true

  depends_on = [
    google_project_service.compute,
    google_artifact_registry_repository.docker_repo,
    google_service_account.agent_sa
  ]
}

# Firewall rule to allow health checks (optional, for monitoring)
resource "google_compute_firewall" "allow_health_check" {
  name    = "allow-health-check"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gymmando-agent"]
}

# Service Account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions Service Account"
}

# Grant Editor role to GitHub Actions service account
resource "google_project_iam_member" "github_actions_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Create JSON key for GitHub Actions
resource "google_service_account_key" "github_actions_key" {
  service_account_id = google_service_account.github_actions.name
}