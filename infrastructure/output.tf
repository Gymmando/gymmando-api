output "api_url" {
  description = "URL of the API service"
  value       = google_cloud_run_v2_service.api.uri
}

output "agent_url" {
  description = "URL of the agent service"
  value       = google_cloud_run_v2_service.agent.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/gymmando-repo"
}