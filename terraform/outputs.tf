# Terraform Outputs for Azure Infrastructure

output "kube_config" {
  description = "Kubernetes configuration for AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.name
}

output "acr_login_server" {
  description = "Login server URL for Azure Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "resource_group_name" {
  description = "Name of the Azure Resource Group"
  value       = azurerm_resource_group.main.name
}

output "cluster_endpoint" {
  description = "API server endpoint for AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].host
}

output "cluster_certificate_authority_data" {
  description = "Certificate authority data for AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].cluster_ca_certificate
  sensitive   = true
}

output "client_certificate" {
  description = "Client certificate for AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].client_certificate
  sensitive   = true
}

output "client_key" {
  description = "Client key for AKS cluster"
  value       = azurerm_kubernetes_cluster.main.kube_config[0].client_key
  sensitive   = true
}

output "acr_id" {
  description = "Azure Container Registry ID"
  value       = azurerm_container_registry.acr.id
}

output "acr_name" {
  description = "Azure Container Registry name"
  value       = azurerm_container_registry.acr.name
}

output "acr_admin_username" {
  description = "Azure Container Registry admin username"
  value       = azurerm_container_registry.acr.admin_username
  sensitive   = true
}

output "acr_admin_password" {
  description = "Azure Container Registry admin password"
  value       = azurerm_container_registry.acr.admin_password
  sensitive   = true
}

output "key_vault_id" {
  description = "Azure Key Vault ID"
  value       = azurerm_key_vault.main.id
}

output "key_vault_name" {
  description = "Azure Key Vault name"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "Azure Key Vault URI"
  value       = azurerm_key_vault.main.vault_uri
}

output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  value       = azurerm_log_analytics_workspace.main.workspace_id
}

output "log_analytics_workspace_name" {
  description = "Log Analytics Workspace name"
  value       = azurerm_log_analytics_workspace.main.name
}

output "log_analytics_primary_shared_key" {
  description = "Log Analytics Workspace primary shared key"
  value       = azurerm_log_analytics_workspace.primary_shared_key
  sensitive   = true
}

output "vnet_id" {
  description = "Virtual Network ID"
  value       = azurerm_virtual_network.main.id
}

output "vnet_name" {
  description = "Virtual Network name"
  value       = azurerm_virtual_network.main.name
}

output "subnet_id" {
  description = "AKS Subnet ID"
  value       = azurerm_subnet.aks.id
}

output "subnet_name" {
  description = "AKS Subnet name"
  value       = azurerm_subnet.aks.name
}

output "node_resource_group_name" {
  description = "Resource group name for AKS nodes"
  value       = azurerm_kubernetes_cluster.main.node_resource_group
}

output "identity_principal_id" {
  description = "Principal ID of AKS managed identity"
  value       = azurerm_kubernetes_cluster.main.identity[0].principal_id
}

output "identity_tenant_id" {
  description = "Tenant ID of AKS managed identity"
  value       = azurerm_kubernetes_cluster.main.identity[0].tenant_id
}

output "system_node_pool_name" {
  description = "Name of the system node pool"
  value       = azurerm_kubernetes_cluster.main.default_node_pool[0].name
}

output "ml_node_pool_name" {
  description = "Name of the ML workloads node pool"
  value       = azurerm_kubernetes_cluster_node_pool.ml_workloads.name
}

output "prometheus_grafana_url" {
  description = "URL for Grafana dashboard"
  value       = var.enable_monitoring ? "http://prometheus-operator-grafana.monitoring.svc.cluster.local" : null
}

output "argocd_url" {
  description = "URL for ArgoCD server"
  value       = var.enable_argocd ? "https://argocd.${var.cluster_name}.${azurerm_resource_group.main.location}.cloudapp.azure.com" : null
}

output "ingress_controller_url" {
  description = "URL for ingress controller"
  value       = var.enable_ingress_controller ? "http://nginx-ingress-controller.ingress-nginx.svc.cluster.local" : null
}

output "location" {
  description = "Azure region where resources are deployed"
  value       = azurerm_resource_group.main.location
}

output "tags" {
  description = "Tags applied to resources"
  value       = azurerm_resource_group.main.tags
}
