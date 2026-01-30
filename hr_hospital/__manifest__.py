{
    "name": "HR Hospital",
    "version": "1.0.0",
    "category": "Human Resources",
    "summary": "Hospital module: doctors, patients, diseases, visits",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/hr_hospital_disease_data.xml",
        "views/hr_hospital_menu.xml",
        "views/doctor_views.xml",
        "views/patient_views.xml",
        "views/disease_views.xml",
        "views/visit_views.xml",
    ],
    "demo": [
        "demo/hr_hospital_doctor_demo.xml",
        "demo/hr_hospital_patient_demo.xml",
    ],
    "application": True,
    "installable": True,
    "license": "LGPL-3",
}
