output "api_url" {
  description = "URL of the API service"
  value       = google_cloud_run_v2_service.api.uri
}

output "agent_vm_name" {
  description = "Name of the agent VM"
  value       = google_compute_instance.agent.name
}

output "agent_vm_ip" {
  description = "External IP of the agent VM"
  value       = google_compute_instance.agent.network_interface[0].access_config[0].nat_ip
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/gymmando-repo"
}

output "github_actions_key" {
  value     = google_service_account_key.github_actions_key.private_key
  sensitive = true
}