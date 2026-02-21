# -*- coding: utf-8 -*-
{
    "name": "Hospital",
    "version": "1.0.0",
    "summary": "Hospital management (patients, doctors, visits, diagnoses)",
    "description": "Training module hr_hospital: patients, doctors, visits, diagnoses, wizards, demo data.",
    "category": "Human Resources",
    "author": "Nikolai",
    "license": "LGPL-3",
    "depends": ["base", "hr", "mail"],
    'data': [
    'security/ir.model.access.csv',
    'views/doctor_speciality_views.xml',
    'views/doctor_views.xml',

    'wizard/hr_hospital_mass_reassign_doctor_wizard_view.xml',
    'wizard/hr_hospital_disease_report_wizard_view.xml',
    'wizard/hr_hospital_reschedule_visit_wizard_view.xml',
    'wizard/hr_hospital_doctor_schedule_wizard_view.xml',
    'wizard/hr_hospital_patient_card_export_wizard_view.xml',


    'views/patient_views.xml',
    'views/contact_person_views.xml',
    'views/patient_visit_views.xml',
    'views/disease_views.xml',
    'views/doctor_schedule_views.xml',
    'views/diagnosis_views.xml',
    'views/history_views.xml',
    'views/hr_hospital_menu.xml',
],

    "demo": [
    "demo/doctor_speciality_demo.xml",
    "demo/hr_hospital_doctor_demo.xml",
    "demo/hr_hospital_contact_person_demo.xml",
    "demo/hr_hospital_patient_demo.xml",
    "demo/hr_hospital_disease_demo.xml",
    "demo/hr_hospital_doctor_schedule_demo.xml",
    "demo/hr_hospital_patient_visit_demo.xml",
    "demo/hr_hospital_medical_diagnosis_demo.xml",
],


    "application": True,
    "installable": True,
}
