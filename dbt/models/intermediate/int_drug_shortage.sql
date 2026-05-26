{{config(
  materialized='incremental',
  unique_key='package_national_drug_code',
  incremental_strategy='merge',
  on_schema_change='sync_all_columns')}}

with sorted_data as (
    select *,
    row_number() over (partition by package_national_drug_code order by update_date desc) as row_number
    from {{ ref('stg_drug_shortage')}} 
    {% if is_incremental() %}
        where date(extracted_at) = current_date()
    {% endif %}
)

select 
  package_national_drug_code,
  generic_name,
  drug_presentation,
  dosage_form,
  therapeutic_category,
  company_name,
  contact_info,
  update_date,
  update_type,
  case
    when availability is null then null
    when trim(availability) = 'Limited Availability' then 'Limited Availability'
    when trim(availability) = 'Limited Availabiltiy' then 'Limited Availability'
    when trim(availability) = 'Limited availability' then 'Limited Availability'
    else 'other'
  end as availability,
  status,
  initial_posting_date,
  related_info,
  related_info_link,
  shortage_reason,
  discontinued_date,
  resolved_note,
  change_date,
  openfda.package_ndc as all_package_national_drug_code,
  openfda.brand_name[safe_offset(0)] as brand_name,
  openfda.manufacturer_name[safe_offset(0)] as manufacturer_name,
  extracted_at

from sorted_data
where row_number = 1

