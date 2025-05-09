from google.cloud import bigquery

def get_bigquery_schema():
    """Define the BigQuery schema based on the API data structure."""
    
    return [
        # Date fields
        bigquery.SchemaField("Vuosi", "INTEGER", description="Year"),
        bigquery.SchemaField("Kk", "INTEGER", description="Month"),
        # YearMonth field for partitioning
        bigquery.SchemaField("YearMonth", "DATE", description="Year and month as DATE for partitioning"),
        
        # Administrative structure
        bigquery.SchemaField("Ha_Tunnus", "STRING", description="Administrative branch code"),
        bigquery.SchemaField("Hallinnonala", "STRING", description="Administrative branch name"),
        bigquery.SchemaField("Tv_Tunnus", "STRING", description="Accounting unit code"),
        bigquery.SchemaField("Kirjanpitoyksikkö", "STRING", description="Accounting unit name"),
        
        # Budget structure
        bigquery.SchemaField("PaaluokkaOsasto_TunnusP", "STRING", description="Main class/section code"),
        bigquery.SchemaField("PaaluokkaOsasto_sNimi", "STRING", description="Main class/section name"),
        bigquery.SchemaField("Luku_TunnusP", "STRING", description="Chapter code"),
        bigquery.SchemaField("Luku_sNimi", "STRING", description="Chapter name"),
        bigquery.SchemaField("Momentti_TunnusP", "STRING", description="Moment code"),
        bigquery.SchemaField("Momentti_sNimi", "STRING", description="Moment name"),
        bigquery.SchemaField("TakpT_TunnusP", "STRING", description="Budget account code"),
        bigquery.SchemaField("TakpT_sNimi", "STRING", description="Budget account name"),
        bigquery.SchemaField("TakpTr_sNimi", "STRING", description="Budget account group name"),
        
        # Accounting structure
        bigquery.SchemaField("Tililuokka_Tunnus", "STRING", description="Account class code"),
        bigquery.SchemaField("Tililuokka_sNimi", "STRING", description="Account class name"),
        bigquery.SchemaField("Ylatiliryhma_Tunnus", "STRING", description="Parent account group code"),
        bigquery.SchemaField("Ylatiliryhma_sNimi", "STRING", description="Parent account group name"),
        bigquery.SchemaField("Tiliryhma_Tunnus", "STRING", description="Account group code"),
        bigquery.SchemaField("Tiliryhma_sNimi", "STRING", description="Account group name"),
        bigquery.SchemaField("Tililaji_Tunnus", "STRING", description="Account type code"),
        bigquery.SchemaField("Tililaji_sNimi", "STRING", description="Account type name"),
        bigquery.SchemaField("LkpT_Tunnus", "STRING", description="Business accounting code"),
        bigquery.SchemaField("LkpT_sNimi", "STRING", description="Business accounting name"),
        
        # Financial values
        bigquery.SchemaField("Alkuperäinen_talousarvio", "FLOAT", description="Original budget"),
        bigquery.SchemaField("Lisätalousarvio", "FLOAT", description="Supplementary budget"),
        bigquery.SchemaField("Voimassaoleva_talousarvio", "FLOAT", description="Current budget"),
        bigquery.SchemaField("Käytettävissä", "FLOAT", description="Available"),
        bigquery.SchemaField("Alkusaldo", "FLOAT", description="Opening balance"),
        bigquery.SchemaField("Nettokertymä_ko_vuodelta", "FLOAT", description="Net accumulation for the year"),
        bigquery.SchemaField("NettoKertymaAikVuosSiirrt", "FLOAT", description="Net accumulation from previous years"),
        bigquery.SchemaField("Nettokertymä", "FLOAT", description="Net accumulation total"),
        bigquery.SchemaField("Loppusaldo", "FLOAT", description="Closing balance")
    ]