#!/bin/bash
# Script to set up BigQuery infrastructure using the bq command-line tool

echo "Setting up BigQuery infrastructure..."

# Configuration
PROJECT_ID="massi-financial-analysis"
DATASET_ID="finnish_finance_data"
TABLE_ID="budget_transactions"
LOCATION="EU"  # Set to EU for Finnish data

# Create dataset
echo "Creating dataset ${DATASET_ID} in project ${PROJECT_ID}..."
bq --location=${LOCATION} mk \
    --dataset \
    --description "Finnish government financial data" \
    ${PROJECT_ID}:${DATASET_ID}

# Check if dataset was created successfully
if [ $? -eq 0 ]; then
    echo "Dataset created successfully!"
else
    echo "Dataset creation failed or dataset already exists."
fi

# Create table with schema
echo "Creating table ${TABLE_ID} in dataset ${DATASET_ID}..."
bq mk \
    --table \
    --description "Finnish government budget transaction data" \
    --time_partitioning_field Vuosi \
    --clustering_fields Ha_Tunnus,Momentti_TunnusP \
    ${PROJECT_ID}:${DATASET_ID}.${TABLE_ID} \
    Vuosi:INTEGER,Kk:INTEGER,Ha_Tunnus:INTEGER,Hallinnonala:STRING,Tv_Tunnus:INTEGER,Kirjanpitoyksikkö:STRING,PaaluokkaOsasto_TunnusP:STRING,PaaluokkaOsasto_sNimi:STRING,Luku_TunnusP:STRING,Luku_sNimi:STRING,Momentti_TunnusP:STRING,Momentti_sNimi:STRING,TakpT_TunnusP:STRING,TakpT_sNimi:STRING,TakpTr_sNimi:STRING,Tililuokka_Tunnus:STRING,Tililuokka_sNimi:STRING,Ylatiliryhma_Tunnus:STRING,Ylatiliryhma_sNimi:STRING,Tiliryhma_Tunnus:STRING,Tiliryhma_sNimi:STRING,Tililaji_Tunnus:STRING,Tililaji_sNimi:STRING,LkpT_Tunnus:STRING,LkpT_sNimi:STRING,Alkuperäinen_talousarvio:FLOAT,Lisätalousarvio:FLOAT,Voimassaoleva_talousarvio:FLOAT,Käytettävissä:FLOAT,Alkusaldo:FLOAT,Nettokertymä_ko_vuodelta:FLOAT,NettoKertymaAikVuosSiirrt:FLOAT,Nettokertymä:FLOAT,Loppusaldo:FLOAT

# Check if table was created successfully
if [ $? -eq 0 ]; then
    echo "Table created successfully!"
else
    echo "Table creation failed or table already exists."
fi

# Create or update .env file with the correct values
echo "Updating .env file with correct configuration..."
cat > .env << EOL
# Google Cloud project info
PROJECT_ID=${PROJECT_ID}
DATASET_ID=${DATASET_ID}
TABLE_ID=${TABLE_ID}

# Vertex AI settings
REGION=europe-west4
MODEL_NAME=gemini-1.5-pro

# Application settings
DEBUG_MODE=True
LOG_LEVEL=INFO
EOL

echo "BigQuery setup complete!"
echo "Project: ${PROJECT_ID}"
echo "Dataset: ${DATASET_ID}"
echo "Table: ${TABLE_ID}"