# -*- coding: utf-8 -*-
import base64
import csv
import io
import json
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PatientCardExportWizard(models.TransientModel):
    _name = "patient.card.export.wizard"
    _description = "Patient Card Export Wizard"

    patient_id = fields.Many2one("hr.hospital.patient", string="Patient", required=True)

    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    include_diagnoses = fields.Boolean(string="Include diagnoses", default=True)
    include_recommendations = fields.Boolean(string="Include recommendations", default=True)

    # ✅ ТЗ: default = мова пацієнта
    lang_id = fields.Many2one(
        "res.lang",
        string="Report Language",
        default=lambda self: self._default_lang_id(),
    )

    export_format = fields.Selection(
        selection=[("json", "JSON"), ("csv", "CSV")],
        string="Export format",
        default="json",
        required=True,
    )

    file_name = fields.Char(string="Filename", readonly=True)
    file_data = fields.Binary(string="File", readonly=True)

    @api.model
    def default_get(self, fields_list):
        """
        Ключевой момент: когда ты жмешь кнопку type=action,
        Odoo передает active_id/active_model в context.
        Мы подставляем patient_id = active_id.
        """
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")

        if active_model == "hr.hospital.patient" and active_id and "patient_id" in fields_list:
            res["patient_id"] = active_id

        return res

    @api.model
    def _default_lang_id(self):
        # сначала пытаемся через default_patient_id, если кто-то будет открывать action вручную
        patient_id = self.env.context.get("default_patient_id")

        # а если открыто кнопкой type=action — используем active_id
        if not patient_id and self.env.context.get("active_model") == "hr.hospital.patient":
            patient_id = self.env.context.get("active_id")

        if not patient_id:
            return False

        patient = self.env["hr.hospital.patient"].browse(patient_id)
        return patient.lang_id.id if patient.lang_id else False

    def _get_visits_domain(self):
        self.ensure_one()
        domain = [("patient_id", "=", self.patient_id.id)]

        if self.date_from:
            dt_from = datetime.combine(self.date_from, time.min)
            domain.append(("planned_date", ">=", dt_from))

        if self.date_to:
            dt_to = datetime.combine(self.date_to, time.max)
            domain.append(("planned_date", "<=", dt_to))

        return domain

    def _build_payload(self):
        self.ensure_one()

        Visit = self.env["hr.hospital.patient.visit"]
        visits = Visit.search(self._get_visits_domain(), order="planned_date desc")

        def visit_to_dict(v):
            data = {
                "id": v.id,
                "name": v.name,
                "state": v.state,
                "planned_date": v.planned_date and v.planned_date.isoformat(),
                "action_date": v.action_date and v.action_date.isoformat(),
                "doctor": v.doctor_id.display_name if v.doctor_id else None,
                "visit_type": v.visit_type,
                "cost": v.cost,
                "currency": v.currency_id.name if v.currency_id else None,
            }

            if self.include_recommendations:
                data["recommendation"] = v.recommendation or ""

            if self.include_diagnoses:
                diags = []
                for d in v.diagnoses_ids:
                    diags.append(
                        {
                            "id": d.id,
                            "disease": d.disease_id.display_name if hasattr(d, "disease_id") and d.disease_id else None,
                            "severity": getattr(d, "severity", False),
                            "approved": getattr(d, "approved", False),
                            "approved_by": d.approved_by_doctor_id.display_name
                            if hasattr(d, "approved_by_doctor_id") and d.approved_by_doctor_id
                            else None,
                            "approved_date": d.approved_date.isoformat()
                            if hasattr(d, "approved_date") and d.approved_date
                            else None,
                            "description": getattr(d, "description", "") or "",
                            "treatment": getattr(d, "treatment", "") or "",
                        }
                    )
                data["diagnoses"] = diags

            return data

        payload = {
            "patient": {
                "id": self.patient_id.id,
                "full_name": self.patient_id.full_name,
                "birth_date": self.patient_id.birth_date and self.patient_id.birth_date.isoformat(),
                "age": self.patient_id.age,
                "sex": self.patient_id.sex,
                "phone": self.patient_id.phone,
                "email": self.patient_id.email,
                "citizenship_country": self.patient_id.citizenship_country_id.name if self.patient_id.citizenship_country_id else None,
                "language": self.patient_id.lang_id.code if self.patient_id.lang_id else None,
            },
            "filters": {
                "date_from": self.date_from and self.date_from.isoformat(),
                "date_to": self.date_to and self.date_to.isoformat(),
                "include_diagnoses": self.include_diagnoses,
                "include_recommendations": self.include_recommendations,
            },
            "visits": [visit_to_dict(v) for v in visits],
        }
        return payload

    def action_export(self):
        self.ensure_one()

        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_("Date From cannot be later than Date To."))

        # Чтобы данные/названия могли быть на языке wizard-а (если потом расширишь переводы)
        ctx = dict(self.env.context)
        if self.lang_id:
            ctx["lang"] = self.lang_id.code

        wiz = self.with_context(ctx)
        payload = wiz._build_payload()

        if self.export_format == "json":
            content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            filename = f"patient_card_{self.patient_id.id}.json"
        else:
            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(
                [
                    "visit_id",
                    "visit_name",
                    "state",
                    "planned_date",
                    "doctor",
                    "visit_type",
                    "cost",
                    "currency",
                    "recommendation",
                    "diagnoses",
                ]
            )

            for v in payload["visits"]:
                diagnoses_text = ""
                if self.include_diagnoses:
                    diagnoses_text = "; ".join(
                        [f"{d.get('disease') or ''} ({d.get('severity') or ''})" for d in v.get("diagnoses", [])]
                    )

                writer.writerow(
                    [
                        v.get("id"),
                        v.get("name"),
                        v.get("state"),
                        v.get("planned_date"),
                        v.get("doctor"),
                        v.get("visit_type"),
                        v.get("cost"),
                        v.get("currency"),
                        v.get("recommendation") if self.include_recommendations else "",
                        diagnoses_text,
                    ]
                )

            content = output.getvalue().encode("utf-8")
            filename = f"patient_card_{self.patient_id.id}.csv"

        self.file_name = filename
        self.file_data = base64.b64encode(content)

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }
