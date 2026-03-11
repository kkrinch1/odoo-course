# -*- coding: utf-8 -*-
{
    "name": "Hospital",
    "version": "1.0.0",
    "summary": "Hospital management (patients, doctors, visits, diagnoses)",
    "description": "Training module hr_hospital: patients, doctors, visits, diagnoses, wizards, demo data.",
    "category": "Human Resources",
    "author": "Oleksii",
    "license": "LGPL-3",
    "depends": ["base", "hr", "mail"],
    "data": [
        # Security
        "security/ir.model.access.csv",

        # Base/reference models first
        "views/doctor_speciality_views.xml",
        "views/contact_person_views.xml",
        "views/disease_views.xml",

        # Wizards/actions that are referenced from core views
        "wizard/hr_hospital_reschedule_visit_wizard_view.xml",
        "wizard/hr_hospital_patient_card_export_wizard_view.xml",

        # Core models
        "views/doctor_views.xml",
        "views/patient_views.xml",
        "views/doctor_schedule_views.xml",
        "views/patient_visit_views.xml",
        "views/diagnosis_views.xml",
        "views/history_views.xml",

        # Reports
        "report/hr_hospital_doctor_report.xml",

        # Other wizards (views/actions)
        "wizard/hr_hospital_doctor_schedule_wizard_view.xml",
        "wizard/hr_hospital_mass_reassign_doctor_wizard_view.xml",
        "wizard/hr_hospital_disease_report_wizard_view.xml",

        # Menu last (references actions/views above)
        "views/hr_hospital_menu.xml",
    ],
    "demo": [
        # Reference data first
        "demo/doctor_speciality_demo.xml",
        "demo/hr_hospital_disease_demo.xml",

        # Master data
        "demo/hr_hospital_doctor_demo.xml",
        "demo/hr_hospital_contact_person_demo.xml",
        "demo/hr_hospital_patient_demo.xml",

        # Operational data
        "demo/hr_hospital_doctor_schedule_demo.xml",
        "demo/hr_hospital_patient_visit_demo.xml",
        "demo/hr_hospital_medical_diagnosis_demo.xml",

    ],

    "application": True,
    "installable": True,
}
