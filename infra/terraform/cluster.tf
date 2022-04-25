# Adapted from https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/container_cluster

resource "google_container_cluster" "primary" {
  name     = "primary"
  location = "europe-west1-b"

  initial_node_count = 3
  workload_identity_config {
    identity_namespace = "${data.google_project.project.project_id}.svc.id.goog"
  }
  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = "/14"
    services_ipv4_cidr_block = "/20"
  }
  node_config {
    preemptible  = true
    machine_type = "e2-small"
  }
}

output "cluster_id" {
    description = "GKE cluster id; pass to `gcloud cluster get-credentials`"
    value = google_container_cluster.primary.id
}
