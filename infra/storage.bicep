param location string = resourceGroup().location
param storageAccountName string = 'stcamptest003'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowSharedKeyAccess: false
  }
}

resource blob 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  parent: storage
  name: 'default'
}

resource artifacts 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blob
  name: 'artifacts'
  properties: { publicAccess: 'None' }
}

resource tables 'Microsoft.Storage/storageAccounts/tableServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

var tableNames = ['contacts', 'stepoutput', 'events', 'inbox', 'auditlog', 'bounces', 'optout', 'conversions', 'campaignstate', 'prospects']
resource runtimeTables 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-05-01' = [for tableName in tableNames: {
  parent: tables
  name: tableName
}]

output storageAccountId string = storage.id
