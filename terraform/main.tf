terraform {
  required_version = ">= 1.15.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "kind-sre-lab"
}

resource "kubernetes_namespace_v1" "sre_lab" {
  metadata {
    name = "sre-lab"

    labels = {
      name = "sre-lab"
    }
  }
}
