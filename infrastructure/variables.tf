variable "project_id"{
    description = "GCP Project ID"
    type = string

}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "livekit_api_key" {
  description = "LiveKit API Key"
  type        = string
  sensitive   = true
}

variable "livekit_api_secret" {
  description = "LiveKit API Secret"
  type        = string
  sensitive   = true
}

variable "deepgram_api_key" {
  description = "Deepgram API Key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}