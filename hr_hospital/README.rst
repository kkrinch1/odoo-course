hr_hospital
===========

Overview
--------

``hr_hospital`` is a custom Odoo 19 training module for basic hospital workflow management.

The module covers:

- doctors
- patients
- visits
- diagnoses
- diseases
- doctor schedules
- primary doctor history
- wizards
- printable doctor report

Main Features
-------------

- Shared abstract person model for doctors and patients
- Doctor specialties, mentor/intern logic, license validation
- Patient visits with statuses, costs, recommendations, and diagnoses
- Disease classifier with hierarchy and ICD-10 code support
- Doctor schedule management and availability checks
- Wizards for rescheduling, schedule filling, exports, and reports
- PDF doctor report with visit history and patient table
- Role-based access for patient, intern, doctor, manager, and administrator
- Ukrainian translation file
- Automated model tests

Security
--------

The module defines the following Hospital roles:

- Patient
- Intern
- Doctor
- Manager
- Administrator

Visit access is restricted by access rights and record rules:

- patients can read only their own visits
- interns can read and edit only their own visits
- doctors can read and edit their own visits and visits of their interns
- managers can read all visits
- administrators have full access, including deletion

Installation
------------

1. Copy the module to a custom addons path.
2. Make sure the addons path is included in ``odoo.conf``.
3. Update the apps list.
4. Install or upgrade ``hr_hospital``.

Example update command:

.. code-block:: bash

   python odoo-bin -c odoo.conf -d odoo_db1 -u hr_hospital --dev=all

Tests
-----

The module contains automated tests for model methods.

Run tests with:

.. code-block:: bash

   python odoo-bin -c odoo.conf -d odoo_db1 -u hr_hospital --test-enable --stop-after-init

Demo Data
---------

When demo data is enabled, the module creates:

- doctor specialties
- doctors and interns
- patients and contact persons
- diseases
- doctor schedules
- visits
- diagnoses

Structure
---------

Main directories:

- ``models/``
- ``views/``
- ``wizard/``
- ``report/``
- ``security/``
- ``demo/``
- ``i18n/``
- ``tests/``
- ``static/description/``

Author
------

Oleksii
