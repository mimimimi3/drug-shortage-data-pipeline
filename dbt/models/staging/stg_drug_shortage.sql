{{ config(materialized='view') }}

SELECT 
  -- identifier
  package_ndc as package_national_drug_code,

  -- drug info
  generic_name,
  presentation as drug_presentation,
  dosage_form,
  therapeutic_category,

  -- company info
  company_name,
  contact_info,

  -- shortage info
  update_date,
  update_type,
  availability,
  status,
  initial_posting_date,
  related_info,
  related_info_link,
  shortage_reason,
  discontinued_date,
  resolved_note,
  change_date,
  
  -- openfda fields
  openfda,

  -- metadata
  extracted_at


FROM {{ source('fda_drug_shortage_raw', 'drug_shortage_data') }}