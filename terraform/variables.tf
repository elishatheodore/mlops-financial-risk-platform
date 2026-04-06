# Terraform Variables for Azure Infrastructure

variable "location" {
  description = "Azure region where resources will be deployed"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "aks-risk-platform"
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-mlops-risk-platform"
}

variable "kubernetes_version" {
  description = "Kubernetes version for AKS cluster"
  type        = string
  default     = "1.28.0"
}

variable "vnet_address_space" {
  description = "Address space for the virtual network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "aks_subnet_address_prefix" {
  description = "Address prefix for AKS subnet"
  type        = list(string)
  default     = ["10.0.0.0/22"]
}

variable "system_node_pool" {
  description = "Configuration for system node pool"
  type = object({
    node_count       = number
    vm_size         = string
    os_disk_size_gb = number
    min_count       = number
    max_count       = number
  })
  default = {
    node_count       = 2
    vm_size         = "Standard_D2s_v3"
    os_disk_size_gb = 30
    min_count       = 2
    max_count       = 3
  }
}

variable "ml_node_pool" {
  description = "Configuration for ML workloads node pool"
  type = object({
    node_count       = number
    vm_size         = string
    os_disk_size_gb = number
    min_count       = number
    max_count       = number
  })
  default = {
    node_count       = 1
    vm_size         = "Standard_D4s_v3"
    os_disk_size_gb = 100
    min_count       = 1
    max_count       = 5
  }
}

variable "acr_sku" {
  description = "SKU tier for Azure Container Registry"
  type        = string
  default     = "Standard"
}

variable "log_analytics_workspace_sku" {
  description = "SKU for Log Analytics Workspace"
  type        = string
  default     = "PerGB2018"
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

variable "key_vault_sku" {
  description = "SKU for Azure Key Vault"
  type        = string
  default     = "standard"
}

variable "key_vault_soft_delete_retention_days" {
  description = "Number of days to retain soft-deleted secrets"
  type        = number
  default     = 7
}

variable "prometheus_storage_size" {
  description = "Storage size for Prometheus"
  type        = string
  default     = "50Gi"
}

variable "grafana_admin_password" {
  description = "Admin password for Grafana"
  type        = string
  default     = "admin123"
  sensitive   = true
}

variable "argocd_server_type" {
  description = "Service type for ArgoCD server"
  type        = string
  default     = "LoadBalancer"
}

variable "ingress_controller_replicas" {
  description = "Number of replicas for ingress controller"
  type        = number
  default     = 2
}

variable "tags" {
  description = "Tags to apply to all resources"
  type = map(string)
  default = {
    Project     = "mlops-financial-risk-platform"
    ManagedBy   = "terraform"
  }
}

variable "enable_monitoring" {
  description = "Enable monitoring stack (Prometheus, Grafana, etc.)"
  type        = bool
  default     = true
}

variable "enable_argocd" {
  description = "Enable ArgoCD deployment"
  type        = bool
  default     = true
}

variable "enable_ingress_controller" {
  description = "Enable ingress controller deployment"
  type        = bool
  default     = true
}

variable "network_profile" {
  description = "Network profile configuration for AKS"
  type = object({
    network_plugin     = string
    network_policy     = string
    service_cidr       = string
    dns_service_ip     = string
    docker_bridge_cidr = string
  })
  default = {
    network_plugin     = "azure"
    network_policy     = "calico"
    service_cidr       = "10.1.0.0/16"
    dns_service_ip     = "10.1.0.10"
    docker_bridge_cidr = "172.17.0.1/16"
  }
}

variable "rbac_aad" {
  description = "Azure AD RBAC configuration"
  type = object({
    managed            = bool
    azure_rbac_enabled = bool
  })
  default = {
    managed            = true
    azure_rbac_enabled = true
  }
}

variable "addon_profile" {
  description = "AKS addon profile configuration"
  type = object({
    oms_agent = object({
      enabled                    = bool
      log_analytics_workspace_id = string
    })
    azure_policy = object({
      enabled = bool
    })
    ingress_application_gateway = object({
      enabled = bool
    })
  })
  default = {
    oms_agent = {
      enabled                    = true
      log_analytics_workspace_id = ""
    }
    azure_policy = {
      enabled = true
    }
    ingress_application_gateway = {
      enabled = false
    }
  }
}

variable "node_labels" {
  description = "Default labels to apply to all nodes"
  type        = map(string)
  default     = {}
}

variable "node_taints" {
  description = "Default taints to apply to all nodes"
  type        = list(string)
  default     = []
}
