param location string = 'francecentral'
param containerAppName string = 'orbit-campaign-test003'
param environmentName string = 'cae-orbit-platform'
param environmentResourceGroup string = 'rg-orbit-platform'
param acrName string = 'crorbitplatform'
param imageName string
param userAssignedIdentityName string = 'id-orbit-campaign-test003'
param keyVaultName string = 'kv-orbit-camp-test003'
param storageAccountName string = 'stcamptest003'

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: userAssignedIdentityName
}

resource env 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: environmentName
  scope: resourceGroup(environmentResourceGroup)
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
  scope: resourceGroup(environmentResourceGroup)
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: identity.id
        }
      ]
      secrets: [
        { name: 'acs-email-connection-string', keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/acs-email-connection-string', identity: identity.id }
        { name: 'acs-sms-connection-string', keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/acs-sms-connection-string', identity: identity.id }
        { name: 'compeak-token', keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/compeak-token', identity: identity.id }
        { name: 'tracking-hmac-key', keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/tracking-hmac-key', identity: identity.id }
        { name: 'foundry-endpoint', keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/foundry-endpoint', identity: identity.id }
        { name: 'foundry-api-key', keyVaultUrl: 'https://${keyVaultName}.vault.azure.net/secrets/foundry-api-key', identity: identity.id }
      ]
    }
    template: {
      containers: [
        {
          name: 'runtime'
          image: imageName
          env: [
            { name: 'ENVIRONMENT', value: 'production' }
            { name: 'CAMPAIGN_ID', value: '4451dffd-e063-4cec-9105-d9ba3efde49b' }
            { name: 'PUBLIC_BASE_URL', value: 'https://${containerAppName}.orangepond-00000000.francecentral.azurecontainerapps.io' }
          ]
          probes: [
            { type: 'Liveness', httpGet: { path: '/health', port: 8000 }, initialDelaySeconds: 30, periodSeconds: 30 }
            { type: 'Readiness', httpGet: { path: '/health', port: 8000 }, initialDelaySeconds: 10, periodSeconds: 10 }
          ]
          resources: { cpu: json('0.5'), memory: '1Gi' }
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output containerAppUrl string = app.properties.configuration.ingress.fqdn
