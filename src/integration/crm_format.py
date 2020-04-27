#key- field from CRM, value- field from user model.
CRM_FORMAT  = {
    'Contacts': {
        'Email': 'email',
        'First_Name': 'first_name',
        'Last_Name': 'last_name',
        'Full_Name': 'full_name',
        'Other_Country': 'country',
        'Other_State': 'state',
        'Date_Of_Birth': 'date_of_birth',
        'Other_City': 'city',
        'Other_Zip': 'zip_code',
        'Phone': 'phone'
    },
    'Vendors': {
        'db_id': 'db_id',
        'Vendor_Name': 'farm_name',
        "Vendor_Type": 'vendor_type_parse',
        'Phone': 'company_phone',
        'Email': 'company_email',
        'Layout': '',
        'Website': 'website',
        'County': 'primary_county',
        'Region': 'region',
        'Appellations': 'appellation',
        # 'Special_Certifications': 'ethics_and_certifications_parse',
        # 'Transportation_Methods': 'transportation',
        'LinkedIn': 'linkedin_url',
        'Instagram': 'instagram_url',
        'Facebook': 'facebook_url',
        'Twitter': 'twitter_url',
        'Canopy_Sqf_Outdoor': 'outdoor_sqf',
        'Indoor_Mixed_Lighting_Type': 'lighting_type',
        'Type_of_Nutrients_Used': 'type_of_nutrie   nts',
        'Canopy_Sqf_Indoor': 'indoor_sqf',
        'Yield_Per_Cycle_Mixed_Light': 'plants_cultivate_per_cycle',
        'Flower': 'flower_yield_percentage',
        'Smalls': 'small_yield_percentage',
        'Trim': 'trim_yield_percentage',
        'Annual_Harvests': 'no_of_harvest_per_year',
        'Harvest_1': 'cultivars_1_parse',
        'Harvest_2': 'cultivars_2_parse',
        'Harvest_3': 'cultivars_3_parse',
        'Contact_1': 'employees_parse', # Cultivation Manager
        'Contact_2': 'employees_parse', # Logistics Manager
        'Contact_3': 'employees_parse', # Quality Assurance Manager
        'Owner1': 'employees_parse', # Owner
        'Yearly_Revenue': 'annual_revenue_2019',
        #'Flower_Target_Price_Lb': 'avg_target_price',
        'Yearly_Budget': 'yearly_budget',
        #'Smalls_Target_Price_Lb': 'small_target_price',
        'Know_your_Cost_per_LB': 'know_cost_per_lbs',
        #'Trim_Target_Price_Lb': 'trim_target_price',
        'Cost_per_LB': 'cost_per_lbs',
        'Bucked_Untrimmed_Target_Price_Lb': 'bucked_target_price',
        'Know_your_Cost_per_Sqf': 'know_cost_per_sqf',
        'Cost_per_Sqf': 'cost_per_sqf',
        'Which_third_party_lab_do_you_use': '',
        'Number_of_Employees': 'no_of_employees',
        'Licenses_List': 'licenses',
        'Sellers_Permit_Box_Link': 'Sellers_Permit',
        'Do_you_work_with_other_Distributors': 'other_distributors',
        'Would_you_grow_genetics_suggested_by_Thrive': 'interested_in_growing_genetics',
        'Can_you_Process_on_Site': 'process_on_site',
        'How_many_clones_total_will_you_need_for_the_year': '',
        'Packaged_Flower_Line': 'packaged_flower_line',
        'Issues_with_Failed_Lab_Tests': 'lab_test_issues',
        'Farm_Co_Branding_Interest': 'interested_in_co_branding',
        'Have_you_ever_had_issues_with_failed_Lab_tests': 'issues_with_failed_lab_tests',
        'Marketing_material': 'marketing_material',
        'Featured_on_our_website_and_social_media': 'featured_on_our_site',
        'cultivars': 'cultivars'
    },
    'Licenses':{
        'id': 'license_id',
        'Name': 'license_number',
        'Legal_Business_Name': 'legal_business_name',
        'License_Type': 'license_type',
        'Expiration_Date': 'expiration_date',
        'Business_DBA': '',
        'Issue_Date': 'issue_date',
        'License_Box_Link': 'uploaded_license_to',
        'Premises_Address': 'premises_address',
        'Premises_City': 'premises_city',
        'Premises_Zipcode': 'zip_code',
        'Premises_State': 'premises_state',
        'Premises_County': 'premises_county',
        'Premises_APN_Number': 'premises_apn',
        'Owner': 'Owner',
    },
    'Vendors_X_Licenses': {
        'Licenses_Module': 'Licenses_Module',
        'Licenses': 'Licenses'
    },
    'Vendors_X_Cultivars': {
        'Cultivar_Associations': 'Cultivar_Associations',
        'Cultivars': 'Cultivars'
    },
    'Vendors_To_DB' : {
        "profile_contact_details": 
            {
            "farm_name": "Vendor_Name",
            "primary_county": "County",
            "region": "Region",
            "appellation": "Appellations",
            "ethics_and_certifications": "Special_Certifications",
            "other_distributors": "Do_you_work_with_other_Distributors",
            "transportation": "Transportation_Methods",
            "packaged_flower_line": "Packaged_Flower_Line",
            "interested_in_co_branding": "Farm_Co_Branding_Interest",
            "marketing_material": "Marketing_material",
            "featured_on_our_site": "Featured_on_our_website_and_social_media",
            "company_email": "Email",
            "company_phone": "Phone",
            "website": "Website",
            "instagram": "Instagram",
            "facebook": "Facebook",
            "linkedin": "Linkedin",
            "twitter": "Twitter",
            "no_of_employees": "Number_of_Employees",
            "employees": "Contacts_parse"
            },
        "profile_overview": {
            "lighting_type": "Indoor_Mixed_Lighting_Type", 
            "type_of_nutrients": "Type_of_Nutrients_Used",
            "interested_in_growing_genetics": "Would_you_grow_genetics_suggested_by_Thrive",
            "issues_with_failed_lab_tests": "Have_you_ever_had_issues_with_failed_Lab_tests",
            "lab_test_issues": "Issues_with_Failed_Lab_Tests",
            "plants_cultivate_per_cycle": "Yield_Per_Cycle_Mixed_Light",
            "annual_untrimmed_yield": "",
            "no_of_harvest": "Annual_Harvests",
            "indoor_sqf": "Canopy_Sqf_Indoor",
            "outdoor_sqf": "Canopy_Sqf_Outdoor",
            "no_of_harvest_per_year": "Annual_Harvests",
            "mixed_light_sqf": ""
            },
        "processing_config":{
            "flower_yield_percentage": "Flower",
            "small_yield_percentage": "Smalls",
            "trim_yield_percentage": "Trim",
            "know_yield_per_plant":"",
            "yield_per_plant":"",
            "know_yield_per_sq_ft":"",
            "avg_yield_pr_sq_ft":"",
            "process_on_site":"Can_you_Process_on_Site",
            "cultivars": "cultivars"
            },
        "financial_details": {
            "annual_revenue_2019": "Yearly_Revenue",
            "projected_2020_revenue": "",
            "target_profit_margin": "",
            "yearly_budget": "Yearly_Budget",
            "know_cost_per_lbs": "Know_your_Cost_per_LB",
            "cost_per_lbs": "Cost_per_LB",
            "know_cost_per_sqf": "Know_your_Cost_per_Sqf",
            "cost_per_sqf": "Cost_per_Sqf",
            "avg_target_price": "Flower_Target_Price_Lb",
            "small_target_price": "Smalls_Target_Price_Lb",
            "trim_target_price": "Trim_Target_Price_Lb",
            "bucked_target_price": "Bucked_Untrimmed_Target_Price_Lb"
            },
    }
}

VENDOR_TYPES = {
    'cultivator':'Cultivator',
}