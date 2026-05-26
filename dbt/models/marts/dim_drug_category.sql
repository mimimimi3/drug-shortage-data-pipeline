SELECT DISTINCT
    package_national_drug_code,
    generic_name,
    category AS therapeutic_category,
    status
FROM {{ ref('int_drug_shortage') }},
UNNEST(therapeutic_category) AS category