select 
  package_national_drug_code,
  generic_name,
  coalesce(dosage_form, 'unknown') as dosage_form,
  company_name,
  contact_info,
  update_date,
  update_type,
  coalesce(availability, 'unknown') as availability,
  status,
  coalesce(shortage_reason, 'unknown') as shortage_reason,
  initial_posting_date,
  discontinued_date,
  resolved_note,
  change_date,
  extracted_at,
  case 
    when status = 'Resolved' then date_diff(update_date,initial_posting_date, day)
    else null
  end as resolution_time

from {{ ref('int_drug_shortage') }}