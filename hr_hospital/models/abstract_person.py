# -*- coding: utf-8 -*-
import re
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


_PHONE_RE = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AbstractPerson(models.AbstractModel):
    _name = "abstract.person"
    _description = "Abstract Person"
    _inherit = ["image.mixin"]
    _rec_name = "full_name"

    last_name = fields.Char(string="Last Name", required=True)
    first_name = fields.Char(string="First Name", required=True)
    middle_name = fields.Char(string="Middle Name")

    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    sex = fields.Selection(
        selection=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        string="Gender",
    )

    birth_date = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute="_compute_age", store=True)

    full_name = fields.Char(string="Full Name", compute="_compute_full_name", store=True)

    citizenship_country_id = fields.Many2one("res.country", string="Citizenship Country")
    lang_id = fields.Many2one("res.lang", string="Communication Language")

    # -------------------------
    # COMPUTE
    # -------------------------
    @api.depends("last_name", "first_name", "middle_name")
    def _compute_full_name(self):
        for rec in self:
            parts = [rec.last_name, rec.first_name, rec.middle_name]
            rec.full_name = " ".join([p.strip() for p in parts if p and p.strip()]) or "No Name"

    @api.depends("birth_date")
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.birth_date:
                delta = relativedelta(today, rec.birth_date)
                rec.age = max(delta.years, 0)
            else:
                rec.age = 0

    # -------------------------
    # HELPERS
    # -------------------------
    def _get_default_lang_code_by_country(self, country_code):
        """
        Map citizenship country code -> res.lang code
        """
        country_code = (country_code or "").upper()
        mapping = {
            "UA": "uk_UA",
            "IT": "it_IT",
            "DE": "de_DE",
            # US / default:
            "US": "en_US",
        }
        return mapping.get(country_code, "en_US")

    # ✅ ТЗ 6.3: при смене страны гражданства — предложить язык общения
    @api.onchange("citizenship_country_id")
    def _onchange_citizenship_country_id_set_lang(self):
        """
        Логика "пропонувати" (и чтобы реально работало):
        - если lang_id пустой -> подставляем по стране
        - если lang_id уже стоит, но это был "дефолт старой страны" -> обновляем на дефолт новой страны
        - если lang_id пользовательский -> не перетираем
        """
        Lang = self.env["res.lang"]

        for rec in self:
            if not rec.citizenship_country_id:
                continue

            new_country_code = rec.citizenship_country_id.code or ""
            new_lang_code = rec._get_default_lang_code_by_country(new_country_code)

            # Что было раньше (до onchange)
            old_country_code = rec._origin.citizenship_country_id.code if rec._origin and rec._origin.citizenship_country_id else ""
            old_default_lang_code = rec._get_default_lang_code_by_country(old_country_code)

            current_lang_code = rec.lang_id.code if rec.lang_id else False

            # 1) Язык пустой -> ставим
            should_set = not rec.lang_id

            # 2) Язык был дефолтом старой страны -> можно обновить
            if rec.lang_id and current_lang_code == old_default_lang_code:
                should_set = True

            if not should_set:
                continue

            lang = Lang.search([("code", "=", new_lang_code)], limit=1)
            if not lang and new_lang_code != "en_US":
                lang = Lang.search([("code", "=", "en_US")], limit=1)

            if lang:
                rec.lang_id = lang
            else:
                return {
                    "warning": {
                        "title": _("Language not found"),
                        "message": _(
                            "Cannot find language '%s' in res.lang. "
                            "Install it in Settings -> Translations -> Languages."
                        )
                        % new_lang_code,
                    }
                }

    # -------------------------
    # CONSTRAINS
    # -------------------------
    @api.constrains("phone")
    def _check_phone_format(self):
        for rec in self:
            if rec.phone and not _PHONE_RE.match(rec.phone.strip()):
                raise ValidationError("Invalid phone format.")

    @api.constrains("email")
    def _check_email_format(self):
        for rec in self:
            if rec.email and not _EMAIL_RE.match(rec.email.strip()):
                raise ValidationError("Invalid email format.")

    @api.constrains("birth_date")
    def _check_birth_date(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.birth_date and rec.birth_date >= today:
                # requirement: age > 0
                raise ValidationError("Date of birth must be in the past (age > 0).")
