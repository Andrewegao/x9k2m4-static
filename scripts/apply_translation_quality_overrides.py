#!/usr/bin/env python3
"""Apply human-reviewed corrections that must survive feed regeneration."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRANSLATED_FIELDS = (
    "title", "totalAmount", "individualPayout", "eligibility", "eligibilityBullets",
    "proofDetails", "summary", "scope", "estimatedClaimTime",
)
PROTECTED_FIELDS = (
    "id", "company", "imageURL", "logoURL", "deadline", "category",
    "proofRequired", "claimURL", "sourceURL", "dateAdded", "status",
    "claimCount", "payoutDisplayType", "caseInfo",
)
JOINED_SENTENCE_STARTS = {
    "es": "Si|Los|Las|El|La",
    "vi": "Nếu|Các|Người|Những|Một|Bạn",
    "fil": "Kung|Ang|Mga|Ito|Maaari|Kasama|Buksan",
}


def localize_total_amount(value: str, language: str) -> str:
    """Localize the small, structured total-amount vocabulary without touching facts."""
    exact = {
        "es": {
            "Undisclosed": "No divulgado",
            "Not disclosed": "No divulgado",
            "Claims-made": "Basado en reclamaciones",
            "Trust fund (through ~2034)": "Fondo fiduciario (hasta aproximadamente 2034)",
            "Varies": "Varía",
            "Non-cash settlement": "Acuerdo no monetario",
            "$50,000 alternative-cash fund": "$50,000 de fondo de pago alternativo en efectivo",
            "Not publicly stated": "No divulgado públicamente",
        },
        "zh-Hans": {
            "Undisclosed": "未披露",
            "Not disclosed": "未披露",
            "Claims-made": "按索赔额计算",
            "Trust fund (through ~2034)": "信托基金（截至约 2034 年）",
            "Varies": "视情况而定",
            "Non-cash settlement": "非现金和解",
            "$50,000 alternative-cash fund": "50,000 美元替代现金基金",
            "Not publicly stated": "未公开披露",
        },
        "vi": {
            "Undisclosed": "Chưa công bố",
            "Not disclosed": "Chưa công bố",
            "Claims-made": "Tính theo số yêu cầu bồi thường",
            "Trust fund (through ~2034)": "Quỹ tín thác (đến khoảng năm 2034)",
            "Varies": "Thay đổi",
            "Non-cash settlement": "Thỏa thuận phi tiền mặt",
            "$50,000 alternative-cash fund": "Quỹ tiền mặt thay thế $50,000",
            "Not publicly stated": "Chưa công bố công khai",
        },
        "fil": {
            "Undisclosed": "Hindi isiniwalat",
            "Not disclosed": "Hindi isiniwalat",
            "Claims-made": "Batay sa mga claim",
            "Trust fund (through ~2034)": "Trust fund (hanggang humigit-kumulang 2034)",
            "Varies": "Nag-iiba",
            "Non-cash settlement": "Settlement na hindi cash",
            "$50,000 alternative-cash fund": "$50,000 na pondong alternatibong cash",
            "Not publicly stated": "Hindi isinapubliko",
        },
    }
    if value in exact[language]:
        return exact[language][value]

    replacements = {
        "es": (
            ("Claims-made", "Basado en reclamaciones"), ("Up to ", "Hasta "),
            (" billion", " mil millones"), (" million", " millones"),
            (" cash pool", " de fondo en efectivo"), (" cap", " de límite"),
            ("(total ", "(total "), ("(cash)", "(efectivo)"), ("(crypto)", "(cripto)"),
        ),
        "zh-Hans": (
            ("Claims-made", "按索赔额计算"), ("Up to ", "最高 "),
            (" billion", " 十亿"), (" million", " 百万"),
            (" cash pool", " 现金池"), (" cap", " 上限"),
            ("(total ", "（总计 "), ("(cash)", "（现金）"), ("(crypto)", "（加密货币）"),
        ),
        "vi": (
            ("Claims-made", "Tính theo số yêu cầu bồi thường"), ("Up to ", "Lên đến "),
            (" billion", " tỷ"), (" million", " triệu"),
            (" cash pool", " quỹ tiền mặt"), (" cap", " giới hạn"),
            ("(total ", "(tổng "), ("(cash)", "(tiền mặt)"), ("(crypto)", "(tiền mã hóa)"),
        ),
        "fil": (
            ("Claims-made", "Batay sa mga claim"), ("Up to ", "Hanggang "),
            (" billion", " bilyon"), (" million", " milyon"),
            (" cash pool", " pondong cash"), (" cap", " limitasyon"),
            ("(total ", "(kabuuang "), ("(cash)", "(cash)"), ("(crypto)", "(crypto)"),
        ),
    }
    result = value
    for source, target in replacements[language]:
        result = result.replace(source, target)
    return result


def localize_untranslated_payout(value: str, language: str) -> str:
    """Repair payout labels that an earlier manifest incorrectly treated as translated."""
    exact = {
        "vi": {"TBD": "Chưa xác định"},
        "fil": {"TBD": "Hindi pa matukoy", "$8 (cash)": "$8 (cash na bayad)"},
        "zh-Hans": {},
        "es": {
            "TBD": "Por determinar",
            "Auto-credit to PSN wallet": "Crédito automático en la cartera de PSN",
            "Cash (amount set by claims volume)": "Efectivo (monto determinado por el volumen de reclamaciones)",
            "Cost reimbursement + extended warranty": "Reembolso de costos + garantía extendida",
            "Equal share of net settlement fund": "Parte igual del fondo neto del acuerdo",
            "Pro rata share (depends on claims filed)": "Parte prorrateada (depende de las reclamaciones presentadas)",
            "Refund for up to 3 products": "Reembolso de hasta 3 productos",
            "Repair reimbursement + warranty extension": "Reembolso de reparación + extensión de garantía",
            "Repayment of verified fraud loss": "Reembolso de pérdidas por fraude verificadas",
            "Replacement panels or prorated cash refund": "Paneles de reemplazo o reembolso en efectivo prorrateado",
            "Two $5-off vouchers": "Dos cupones de $5 de descuento",
            "30-50% of purchase price or free replacement door + labor":
                "30-50 % del precio de compra o puerta de reemplazo y mano de obra gratis",
            "$70 automatic, more with claim form":
                "$70 automáticos; más si se presenta un formulario de reclamación",
            "$150 (unrecalled) to $350 (recalled vehicles)":
                "$150 (sin retiro) a $350 (vehículos retirados)",
            "See notice (reported up to ~$1,000)": "Consulte el aviso (se informa hasta aproximadamente $1,000)",
            "See notice (reported up to ~$10,000)": "Consulte el aviso (se informa hasta aproximadamente $10,000)",
            "Varies (29% premium refund)": "Varía (reembolso del 29 % de la prima)",
            "Varies (equal share of $14M fund)": "Varía (parte igual del fondo de $14M)",
            "Up to $7,642 (paid at ~55% of allowed value)":
                "Hasta $7,642 (pagado a aproximadamente el 55 % del valor aprobado)",
            "Four day passes": "Cuatro pases de un día",
            "Pro rata securities payment": "Pago prorrateado por valores",
            "Pro rata restitution payment": "Pago de restitución prorrateado",
            "Property-specific surplus payment": "Pago del excedente específico de la propiedad",
            "Pro rata share based on approved class-member loss":
                "Parte prorrateada basada en la pérdida aprobada del miembro de la clase",
            "Pro rata share based on qualifying prescription spending":
                "Parte prorrateada basada en gastos de medicamentos recetados elegibles",
        },
    }
    if value in exact[language]:
        return exact[language][value]
    if language != "es":
        return value

    replacements = (
        ("Varies by membership fees paid", "Varía según las cuotas de membresía pagadas"),
        ("Varies by late fees charged", "Varía según los cargos por mora cobrados"),
        ("Varies by lease payments", "Varía según los pagos de arrendamiento"),
        ("Varies by merchant volume", "Varía según el volumen del comerciante"),
        ("Varies by valid claims", "Varía según las reclamaciones válidas"),
        ("Varies by claims filed", "Varía según las reclamaciones presentadas"),
        ("equal share of", "parte igual de"),
        ("equal share", "parte igual"),
        ("documented losses only", "solo pérdidas documentadas"),
        ("documented losses", "pérdidas documentadas"),
        ("for losses", "por pérdidas"),
        ("undocumented cash", "pago en efectivo sin documentación"),
        ("alternative cash", "pago alternativo en efectivo"),
        ("flat cash", "pago fijo en efectivo"),
        ("cash payment", "pago en efectivo"),
        ("cash needs ID", "el efectivo requiere identificación"),
        ("cash or store credit", "efectivo o crédito de tienda"),
        ("cash or credit", "efectivo o crédito"),
        ("pro rata based on purchases", "prorrateado según las compras"),
        ("pro rata by rent paid", "prorrateado según el alquiler pagado"),
        ("pro rata share", "parte prorrateada"),
        ("pro rata cash", "efectivo prorrateado"),
        ("pro-rata cash", "efectivo prorrateado"),
        ("pro-rata", "prorrateado"),
        ("pro rata", "prorrateado"),
        ("credit monitoring", "monitoreo de crédito"),
        ("yrs monitoring", "años de monitoreo"),
        ("yr monitoring", "año de monitoreo"),
        ("yrs ", "años de "),
        ("yr ", "año de "),
        ("Monitoring", "monitoreo"),
        ("monitoring", "monitoreo"),
        ("warranty", "garantía"),
        ("reimbursement", "reembolso"),
        ("with claim form", "con formulario de reclamación"),
        ("claims filed", "reclamaciones presentadas"),
        ("claim form", "formulario de reclamación"),
        ("with proof", "con comprobante"),
        ("without proof", "sin comprobante"),
        ("no docs", "sin documentos"),
        ("documented", "con documentación"),
        ("paid users", "usuarios de pago"),
        ("statutory", "legales"),
        ("recalled vehicles", "vehículos retirados"),
        ("unrecalled", "sin retiro"),
        ("allowed value", "valor aprobado"),
        ("paid at", "pagado al"),
        ("lost-time tier", "nivel por tiempo perdido"),
        ("premium refund", "reembolso de la prima"),
        ("capped at spend", "limitado al gasto"),
        ("voucher is auto", "el cupón es automático"),
        ("EEOC allocates", "asignado por la EEOC"),
        ("modification + compensation", "modificación + compensación"),
        ("see your notice", "consulte su aviso"),
        ("per forklift", "por montacargas"),
        ("per mattress", "por colchón"),
        ("per product", "por producto"),
        ("per loan", "por préstamo"),
        ("purchase price", "precio de compra"),
        ("% of", "% de"),
        ("free replacement door + labor", "puerta de reemplazo y mano de obra gratis"),
        ("store credit", "crédito de tienda"),
        ("Ubisoft credit", "crédito de Ubisoft"),
        ("Credit", "crédito"),
        ("credit", "crédito"),
        ("vouchers", "cupones"),
        ("voucher", "cupón"),
        ("Coupon", "cupón"),
        ("cash", "efectivo"),
        ("amount set by claims volume", "monto determinado por el volumen de reclamaciones"),
        ("min ", "mín. "),
        ("max ", "máx. "),
        ("or up to", "o hasta"),
        (" or ", " o "),
        ("Up to", "Hasta"),
        ("up to", "hasta"),
        ("Varies", "Varía"),
        ("Est.", "Aprox."),
        ("automatic", "automáticos"),
        ("more", "más"),
        ("losses", "pérdidas"),
        ("fund", "fondo"),
        ("discount", "descuento"),
        ("minimum", "mínimo"),
        ("flat", "fijo"),
    )
    result = re.sub(r"(?: in)? CA\b", " en CA", value)
    for source, target in replacements:
        result = result.replace(source, target)
    return result


def repair_spacing(value, language: str):
    if isinstance(value, list):
        return [repair_spacing(item, language) for item in value]
    if not isinstance(value, str):
        return value
    starts = JOINED_SENTENCE_STARTS.get(language)
    if starts:
        value = re.sub(rf"([.!?])(?=(?:{starts})\b)", r"\1 ", value)
    if language in {"es", "vi", "fil"}:
        value = re.sub(r"\s+([,.;:!?])", r"\1", value)
        # Translation engines sometimes drop whitespace at an inline protected-fact
        # boundary. Semicolons always separate clauses here. For sentence punctuation,
        # require an uppercase sentence start while preserving abbreviations such as
        # U.S./D.C. and the one www.* domain mentioned in eligibility prose.
        value = re.sub(r";(?=\S)", "; ", value)
        value = re.sub(r"(?<!www)(?<!\b[A-Z])([.!?])(?=[A-ZÀ-ỸĐ])", r"\1 ", value)
        value = re.sub(r"\(\s+", "(", value)
        value = re.sub(r"\s+\)", ")", value)
    value = value.replace("Est.$", "Est. $")
    # Keep settlement and company names intact when a translation engine has
    # treated parts of a brand as ordinary words.
    for source, target in (
        ("Back Checked", "BackChecked"),
        ("Sports Ed TV", "SportsEdTV"),
        ("Chemo Centryx", "ChemoCentryx"),
        ("AIS Info Source", "AIS InfoSource"),
    ):
        value = value.replace(source, target)
    value = value.replace("m aximum", "maximum").replace("b ase", "base")
    if language == "zh-Hans":
        value = value.replace("结算", "和解").replace("定居点", "和解")
    return value

OVERRIDES = {
    "es": {
        "suntrust-overdraft-ga-2026": {
            "summary": (
                "SunTrust resolvió reclamaciones de larga data que alegaban que ciertos cargos "
                "por sobregiro constituían usura según la ley de Georgia. Los pagos se calculan "
                "usando los propios registros del banco, más un 7 % de interés, con un mínimo de $5."
            ),
        },
        "fiton-vppa-2026": {
            "eligibilityBullets": [
                "Tenía una cuenta de FitOn",
                "Vio un video pregrabado de FitOn entre el 22 de octubre de 2022 y el 29 de mayo de 2026",
                "Máximo de $10, reducido prorrateadamente si las reclamaciones superan el límite",
            ],
        },
        "pacific-bag-wa-jobs-2026": {
            "individualPayout": "Mínimo estimado de $1,666.28",
        },
        "mercedes-emissions-warranty-2026": {
            "eligibility": (
                "Personas que pagaron de su bolsillo para diagnosticar, reparar o reemplazar "
                "piezas cubiertas de un vehículo Mercedes-Benz modelo 2015 o posterior, cuando "
                "la reparación se realizó entre los 4 años/50,000 millas y los 7 años/70,000 millas."
            ),
            "summary": (
                "Mercedes-Benz acordó resolver reclamaciones relacionadas con la cobertura de la "
                "garantía de emisiones. Los propietarios que pagaron de su bolsillo reparaciones "
                "cubiertas después de la garantía estándar, pero dentro del período de la garantía "
                "de emisiones, pueden solicitar un reembolso."
            ),
        },
    },
    "zh-Hans": {
        "pacific-bag-wa-jobs-2026": {
            "individualPayout": "预计至少 1,666.28 美元",
        },
        "farmers-heckathorn-tcpa-2026": {
            "title": "125 万美元 Farmers Insurance 代理 TCPA 自动电话和解",
            "eligibility": (
                "在 2020 年 4 月 19 日至 2026 年 6 月 15 日期间，接到指定 Farmers Insurance "
                "代理人或其代理机构两次以上电话营销电话或短信，且号码出现在诉讼名单上的人员。"
            ),
            "eligibilityBullets": [
                "收到指定代理商的 Farmers Insurance 电话营销电话或短信 2 次以上",
                "时间为 4/19/2020 至 6/15/2026",
                "您的号码出现在诉讼产生的名单上",
            ],
            "summary": (
                "这项 125 万美元的 TCPA 和解解决了某些 Farmers Insurance 代理人向“谢绝来电”"
                "登记号码拨打电话或发送短信的索赔。符合资格的接收者最多可以申请 160 美元。"
            ),
        },
        "mercedes-emissions-warranty-2026": {
            "eligibility": (
                "为 2015 年款或更新的梅赛德斯-奔驰车辆自费诊断、维修或更换承保零件，且维修发生在"
                "车龄 4 年/50,000 英里至 7 年/70,000 英里之间的个人。"
            ),
        },
    },
    "vi": {
        "pacific-bag-wa-jobs-2026": {
            "individualPayout": "Ước tính tối thiểu $1,666.28",
        },
        "centrelake-data-breach-ca-2026": {
            "summary": (
                "Centrelake Medical Group đã đồng ý dàn xếp các khiếu nại liên quan đến vụ vi "
                "phạm dữ liệu làm lộ thông tin bệnh nhân. Những bệnh nhân ở California đã nhận "
                "được thông báo có thể nhận từ $20 đến $3,500 dựa trên tổn thất có tài liệu chứng minh."
            ),
        },
        "team-group-dram-2026": {
            "title": "Thỏa thuận ấn định giá DRAM của Team Group / T-Force – không cần bằng chứng",
            "summary": (
                "Team Group đã dàn xếp các khiếu nại liên quan đến việc ấn định giá bộ nhớ DRAM. "
                "Nếu bạn đã mua RAM, máy tính, điện thoại hoặc thiết bị khác có DRAM trong thời "
                "gian đủ điều kiện, bạn có thể yêu cầu bồi thường cho tối đa 5 sản phẩm mà không "
                "cần bằng chứng mua hàng."
            ),
        },
        "mercedes-emissions-warranty-2026": {
            "eligibility": (
                "Những người đã tự trả chi phí để chẩn đoán, sửa chữa hoặc thay thế các bộ phận "
                "được bảo hành của xe Mercedes-Benz đời 2015 trở về sau, khi việc sửa chữa diễn ra "
                "trong khoảng từ 4 năm/50.000 dặm đến 7 năm/70.000 dặm."
            ),
            "summary": (
                "Mercedes-Benz đã đồng ý dàn xếp các khiếu nại liên quan đến phạm vi bảo hành khí "
                "thải. Chủ xe đã tự trả chi phí cho các sửa chữa được bảo hành sau thời hạn bảo "
                "hành tiêu chuẩn nhưng vẫn trong thời hạn bảo hành khí thải có thể yêu cầu hoàn tiền."
            ),
        },
    },
    "fil": {
        "mclaren-health-data-breach-2026": {
            "summary": (
                "Sumang-ayon ang McLaren Health Care na ayusin ang mga claim tungkol sa mga paglabag "
                "sa data noong 2023 at 2024 na nagkompromiso sa impormasyon ng pasyente. Maaaring "
                "makatanggap ang mga apektadong indibidwal ng hanggang $5,000 batay sa mga "
                "dokumentadong pagkalugi."
            ),
        },
        "centrelake-data-breach-ca-2026": {
            "summary": (
                "Sumang-ayon ang Centrelake Medical Group na ayusin ang mga claim tungkol sa paglabag "
                "sa data na naglantad ng impormasyon ng pasyente. Ang mga pasyente sa California na "
                "nakatanggap ng abiso ay maaaring makatanggap ng $20 hanggang $3,500 batay sa mga "
                "dokumentadong pagkalugi."
            ),
        },
        "red-robin-wa-jobs-2026": {
            "individualPayout": "Tinatayang $573.43, hanggang $5,000",
        },
        "pacific-bag-wa-jobs-2026": {
            "individualPayout": "Tinatayang hindi bababa sa $1,666.28",
        },
        "xactus-creditplus-fcra-2026": {
            "individualPayout": "Tinatayang $500",
        },
        "mercedes-emissions-warranty-2026": {
            "eligibility": (
                "Mga taong nagbayad mula sa sariling bulsa upang ma-diagnose, maipaayos, o mapalitan "
                "ang mga sakop na piyesa ng isang model year 2015 o mas bagong Mercedes-Benz, kung "
                "ang pagkukumpuni ay ginawa sa pagitan ng 4 na taon/50,000 milya at 7 taon/70,000 milya."
            ),
            "summary": (
                "Sumang-ayon ang Mercedes-Benz na ayusin ang mga claim tungkol sa saklaw ng emissions "
                "warranty. Maaaring humiling ng reimbursement ang mga may-aring nagbayad mula sa sariling "
                "bulsa para sa mga sakop na pagkukumpuni matapos ang karaniwang warranty ngunit habang "
                "sakop pa ng emissions warranty."
            ),
        },
    },
}

# Human-reviewed display copy for settlements added on 2026-08-19. Short display fields
# need explicit translations because inline fact protection can otherwise leave fragments
# such as "cash-benefit cap" in English or split company names into ordinary words.
NEW_SETTLEMENT_DISPLAY_OVERRIDES = {
    "es": {
        "advanced-recovery-equipment-data-breach-2026": {
            "title": "Acuerdo por violación de datos de Advanced Recovery Equipment & Supplies",
            "totalAmount": "Pagos en efectivo limitados a $325,000",
            "individualPayout": "Hasta $4,250 por pérdidas documentadas, hasta $50 en efectivo y monitoreo",
        },
        "aidvantage-tcpa-settlement-2026": {
            "title": "Acuerdo por llamadas pregrabadas de Aidvantage",
            "totalAmount": "$3 millones",
            "individualPayout": "Pago en efectivo prorrateado",
            "proofDetails": (
                "Los destinatarios de la tarjeta postal pueden presentar la reclamación utilizando "
                "el formulario personalizado enviado con el aviso. Quien no haya recibido una tarjeta "
                "postal debe solicitar por escrito un formulario de reclamación y presentar prueba de "
                "que una llamada o mensaje de voz artificial o pregrabado de Aidvantage llegó a su "
                "teléfono celular durante el período de la clase."
            ),
        },
        "backchecked-data-breach-2026": {
            "title": "Acuerdo por violación de datos de BackChecked",
            "totalAmount": "$535,000",
            "individualPayout": "$50 en efectivo o hasta $2,500, más monitoreo",
        },
        "king-county-jail-booking-settlement-2026": {
            "title": "Acuerdo por detención en la cárcel del condado de King",
            "totalAmount": "$1.6 millones",
            "individualPayout": "$150 o al menos $1,500, según las órdenes pendientes y la detención",
        },
        "zoll-heart-device-data-breach-2026": {
            "title": "Acuerdo por violación de datos de dispositivos cardíacos ZOLL",
            "totalAmount": "$3.5 millones",
            "individualPayout": "Efectivo prorrateado o hasta $5,000",
        },
        "vertical-hold-climbing-gender-settlement-2026": {
            "title": "Acuerdo de pases diarios de escalada Vertical Hold",
            "totalAmount": "Acuerdo no monetario",
            "individualPayout": "Cuatro pases diarios",
        },
        "sportsedtv-video-privacy-settlement-2026": {
            "title": "Acuerdo de privacidad de video de SportsEdTV",
            "totalAmount": "$500,000",
            "individualPayout": "Pago en efectivo prorrateado; las reclamaciones de California reciben dos partes",
        },
        "acmq-unsolicited-fax-settlement-2026": {
            "title": "Acuerdo por faxes no solicitados de ACMQ",
            "totalAmount": "Hasta $175,000 para reclamaciones de la clase",
            "individualPayout": "Hasta $500 por número de fax elegible",
            "summary": (
                "ACMQ y otros demandados resolvieron alegaciones de que se enviaron por fax "
                "anuncios de conferencias sin permiso. Las reclamaciones válidas pueden recibir "
                "hasta $500 por cada número de fax elegible verificado, sujeto al límite máximo "
                "de recuperación de la clase de $175,000 y a cualquier ajuste prorrateado."
            ),
        },
        "naper-grove-vision-care-data-breach-2026": {
            "title": "Acuerdo por violación de datos de Naper Grove Vision Care",
            "totalAmount": "Fondo de $50,000 para pagos alternativos en efectivo",
            "individualPayout": "Efectivo prorrateado o hasta $1,000, más monitoreo",
        },
        "moodswings-ticket-fee-settlement-2026": {
            "title": "Acuerdo por cargos de entradas de Moodswings",
            "totalAmount": "No divulgado públicamente",
            "individualPayout": "Efectivo por entrada o un código de descuento del 25%",
            "proofDetails": (
                "La presentación en línea requiere el ID de miembro de la clase del aviso del acuerdo. "
                "El pago en efectivo se calcula a partir de las compras de entradas elegibles que constan "
                "en los registros del acuerdo y requiere una reclamación válida; no hacer nada proporciona "
                "únicamente el código de descuento del 25 %."
            ),
        },
        "community-realty-management-data-breach-2026": {
            "title": "Acuerdo por violación de datos de Community Realty Management",
            "totalAmount": "Beneficios en efectivo limitados a $200,000",
            "individualPayout": "$20 en efectivo o hasta $2,000, más monitoreo",
        },
        "pierce-county-library-data-breach-2026": {
            "title": "Acuerdo por violación de datos de Pierce County Library",
            "totalAmount": "Beneficios en efectivo limitados a $385,000",
            "individualPayout": "Efectivo, pago por tiempo perdido o hasta $4,000, más monitoreo",
        },
        "chemocentryx-securities-settlement-2026": {
            "title": "Acuerdo de valores de ChemoCentryx",
            "totalAmount": "$69 millones",
            "individualPayout": "Pago prorrateado por valores",
        },
        "credit-suisse-rmbs-restitution-2026": {
            "title": "Fondo de restitución de RMBS de Credit Suisse",
            "totalAmount": "$300 millones",
            "individualPayout": "Pago de restitución prorrateado",
        },
        "automotive-information-systems-data-breach-2026": {
            "title": "Acuerdo por violación de datos de AIS InfoSource",
            "totalAmount": "No divulgado públicamente",
            "individualPayout": "Hasta $5,000, más monitoreo",
        },
        "dairy-farmers-america-data-breach-2026": {
            "title": "Acuerdo por violación de datos de Dairy Farmers of America",
            "totalAmount": "Pagos en efectivo limitados a $475,000",
            "individualPayout": "Efectivo estimado de $55 o hasta $4,500, más monitoreo",
        },
        "anixter-center-data-breach-2026": {
            "title": "Acuerdo por violación de datos de Anixter Center",
            "totalAmount": "No divulgado públicamente",
            "individualPayout": "$50 en efectivo o hasta $5,000, más monitoreo",
            "eligibility": "Personas a quienes se notificó que su información privada fue comprometida en el incidente de datos de Anixter Center de julio de 2023.",
            "eligibilityBullets": [
                "Su información privada estuvo involucrada en el incidente de julio de 2023",
                "Anixter Center le envió un aviso",
                "Envíe un reclamo válido antes del 19 de octubre de 2026",
            ],
        },
        "washington-county-oregon-tax-foreclosure-2026": {
            "title": "Acuerdo por ejecuciones fiscales del condado de Washington",
            "totalAmount": "$1.5 millones",
            "individualPayout": "Pago de excedente específico de la propiedad",
        },
        "hwwc-medical-data-breach-2026": {
            "title": "Acuerdo por violación de datos médicos de HWWC",
            "totalAmount": "No divulgado públicamente",
            "individualPayout": "Monitoreo y hasta $2,500 por pérdidas documentadas, más tiempo perdido elegible",
        },
        "mary-black-health-system-settlement-2026": {
            "title": "Acuerdo de Mary Black Health System",
            "totalAmount": "$2.25 millones",
            "individualPayout": "Parte prorrateada según la pérdida aprobada del miembro de la clase",
        },
        "bestway-above-ground-pool-settlement-2026": {
            "title": "Acuerdo por piscinas elevadas Bestway",
            "totalAmount": "$15 millones",
            "individualPayout": "$40 o el 10% del precio de compra elegible",
        },
        "kroger-prescription-savings-club-settlement-2026": {
            "title": "Acuerdo del club de ahorro para recetas de Kroger",
            "totalAmount": "$17 millones",
            "individualPayout": "Parte prorrateada según el gasto elegible en medicamentos recetados",
        },
    },
    "zh-Hans": {
        "advanced-recovery-equipment-data-breach-2026": {
            "title": "Advanced Recovery Equipment & Supplies 数据泄露和解",
            "totalAmount": "现金支付总额上限为 325,000 美元",
            "individualPayout": "记录损失最高 4,250 美元、现金最高 50 美元，另加监控服务",
        },
        "aidvantage-tcpa-settlement-2026": {
            "title": "Aidvantage 预录电话和解",
            "totalAmount": "3 百万美元",
            "individualPayout": "按比例现金支付",
            "proofDetails": (
                "收到明信片通知的人可使用通知随附的个性化索赔表提交索赔。未收到明信片通知的人必须书面"
                "申请索赔表，并提交证据，证明在集体诉讼期间，其手机收到过 Aidvantage 的人工语音或预录"
                "语音电话或留言。"
            ),
        },
        "backchecked-data-breach-2026": {
            "title": "BackChecked 数据泄露和解",
            "totalAmount": "535,000 美元",
            "individualPayout": "50 美元现金或最高 2,500 美元，另加监控服务",
        },
        "king-county-jail-booking-settlement-2026": {
            "title": "金县监狱拘留和解",
            "totalAmount": "1.6 百万美元",
            "individualPayout": "150 美元或至少 1,500 美元，视未执行逮捕令和拘留情况而定",
        },
        "zoll-heart-device-data-breach-2026": {
            "title": "ZOLL 心脏设备数据泄露和解",
            "totalAmount": "3.5 百万美元",
            "individualPayout": "按比例现金支付或最高 5,000 美元",
        },
        "vertical-hold-climbing-gender-settlement-2026": {
            "title": "Vertical Hold 攀岩日票和解",
            "totalAmount": "非现金和解",
            "individualPayout": "四张日票",
        },
        "sportsedtv-video-privacy-settlement-2026": {
            "title": "SportsEdTV 视频隐私和解",
            "totalAmount": "500,000 美元",
            "individualPayout": "按比例现金支付；加州索赔获得两份份额",
        },
        "acmq-unsolicited-fax-settlement-2026": {
            "title": "ACMQ 未经请求传真和解",
            "totalAmount": "集体索赔最高 175,000 美元",
            "individualPayout": "每个合格传真号码最高 500 美元",
            "summary": (
                "ACMQ 和其他被告就未经许可通过传真发送会议广告的指控达成和解。"
                "每个经核实的合格传真号码最多可获 500 美元；集体赔付总额上限为 "
                "175,000 美元，并可能按比例调整。"
            ),
        },
        "naper-grove-vision-care-data-breach-2026": {
            "title": "Naper Grove Vision Care 数据泄露和解",
            "totalAmount": "50,000 美元替代现金基金",
            "individualPayout": "按比例现金支付或最高 1,000 美元，另加监控服务",
        },
        "moodswings-ticket-fee-settlement-2026": {
            "title": "Moodswings 票务费和解",
            "totalAmount": "未公开披露",
            "individualPayout": "每张票现金支付或 25% 折扣码",
            "proofDetails": (
                "在线提交需要和解通知中的集体成员 ID。现金金额根据和解记录中的合格购票记录计算，且必须"
                "提交有效索赔；不采取任何行动只能获得 25% 折扣码。"
            ),
        },
        "community-realty-management-data-breach-2026": {
            "title": "Community Realty Management 数据泄露和解",
            "totalAmount": "现金福利总额上限为 200,000 美元",
            "individualPayout": "20 美元现金或最高 2,000 美元，另加监控服务",
            "eligibility": "Community Realty Management 确认私人信息可能因 2024 年 9 月 10 日至 10 月 22 日期间未经授权访问电子邮件账户而受到影响的人员，包括所有收到事件通知的人。",
            "eligibilityBullets": [
                "您的私人信息可能涉及遭到访问的电子邮件账户",
                "未经授权的访问发生于 2024 年 9 月 10 日至 10 月 22 日",
                "Community Realty Management 已将您确认为受影响人员，包括向您发送事件通知的情形",
                "在 2026 年 9 月 25 日之前提交有效索赔",
            ],
        },
        "pierce-county-library-data-breach-2026": {
            "title": "Pierce County Library 数据泄露和解",
            "totalAmount": "现金福利总额上限为 385,000 美元",
            "individualPayout": "现金、误工补偿或最高 4,000 美元，另加监控服务",
        },
        "chemocentryx-securities-settlement-2026": {
            "title": "ChemoCentryx 证券和解",
            "totalAmount": "69 百万美元",
            "individualPayout": "按比例证券赔付",
        },
        "credit-suisse-rmbs-restitution-2026": {
            "title": "Credit Suisse RMBS 赔偿基金",
            "totalAmount": "300 百万美元",
            "individualPayout": "按比例赔偿支付",
        },
        "automotive-information-systems-data-breach-2026": {
            "title": "AIS InfoSource 数据泄露和解",
            "totalAmount": "未公开披露",
            "individualPayout": "最高 5,000 美元，另加监控服务",
            "proofDetails": "纸质表格仅在已知登录 ID 时才要求填写，并须签署声明，确认内容真实，否则可能承担伪证责任；申领须经核实。最高 5,000 美元的记录损失需要支持材料；误工时间须作出声明，最多四小时，每小时 20 美元。",
        },
        "dairy-farmers-america-data-breach-2026": {
            "title": "Dairy Farmers of America 数据泄露和解",
            "totalAmount": "现金支付总额上限为 475,000 美元",
            "individualPayout": "预计 55 美元现金或最高 4,500 美元，另加监控服务",
        },
        "anixter-center-data-breach-2026": {
            "title": "Anixter Center 数据泄露和解",
            "totalAmount": "未公开披露",
            "individualPayout": "50 美元现金或最高 5,000 美元，另加监控服务",
            "eligibility": "收到通知、其私人信息在 Anixter Center 2023 年 7 月数据事件中遭到泄露的人员。",
            "eligibilityBullets": [
                "您的私人信息涉及 2023 年 7 月的数据事件",
                "Anixter Center 向您发送了通知",
                "在 2026 年 10 月 19 日之前提交有效索赔",
            ],
        },
        "washington-county-oregon-tax-foreclosure-2026": {
            "title": "华盛顿县税务止赎和解",
            "totalAmount": "1.5 百万美元",
            "individualPayout": "按房产计算的盈余支付",
            "eligibility": "个人或实体，以及符合条件的继承人、权利承继人、受让人或留置权人，在俄勒冈州华盛顿县经税务止赎取得的不动产中拥有所有权权益或有效留置权；赎回期在 2017 年 10 月 12 日至 2025 年 12 月 31 日期间届满；且该县出售房产获得盈余款项，或保留、捐赠或转让具有符合条件的盈余权益的房产。",
            "eligibilityBullets": [
                "持有符合条件的所有权权益或有效留置权，包括通过遗产、权利承继或转让取得",
                "华盛顿县通过税务止赎取得房产，且赎回期已经届满",
                "该县出售房产获得盈余款项，或保留、捐赠或转让具有符合条件的盈余权益的房产",
                "赎回期届满日期介于 2017 年 10 月 12 日至 2025 年 12 月 31 日",
            ],
        },
        "hwwc-medical-data-breach-2026": {
            "title": "HWWC 医疗数据泄露和解",
            "totalAmount": "未公开披露",
            "individualPayout": "监控服务及最高 2,500 美元记录损失补偿，另加合格误工补偿",
        },
        "mary-black-health-system-settlement-2026": {
            "title": "Mary Black Health System 和解",
            "totalAmount": "2.25 百万美元",
            "individualPayout": "根据获批集体成员损失按比例分配",
        },
        "bestway-above-ground-pool-settlement-2026": {
            "title": "Bestway 地上泳池和解",
            "totalAmount": "15 百万美元",
            "individualPayout": "40 美元或合格购买价格的 10%",
        },
        "kroger-prescription-savings-club-settlement-2026": {
            "title": "Kroger 处方药储蓄俱乐部和解",
            "totalAmount": "17 百万美元",
            "individualPayout": "根据合格处方支出按比例分配",
        },
    },
    "vi": {
        "advanced-recovery-equipment-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của Advanced Recovery Equipment & Supplies",
            "totalAmount": "Tổng tiền mặt giới hạn ở $325,000",
            "individualPayout": "Tối đa $4.250 cho tổn thất có chứng từ, tối đa $50 tiền mặt và dịch vụ giám sát",
        },
        "aidvantage-tcpa-settlement-2026": {
            "title": "Dàn xếp cuộc gọi ghi âm sẵn của Aidvantage",
            "totalAmount": "$3 triệu",
            "individualPayout": "Khoản tiền mặt chia theo tỷ lệ",
            "proofDetails": (
                "Người nhận bưu thiếp có thể nộp đơn bằng mẫu yêu cầu bồi thường được cá nhân hóa gửi "
                "kèm thông báo. Người không nhận được bưu thiếp phải gửi văn bản yêu cầu mẫu đơn và nộp "
                "bằng chứng cho thấy cuộc gọi hoặc tin nhắn bằng giọng nói nhân tạo hay ghi âm sẵn từ "
                "Aidvantage đã đến số điện thoại di động của họ trong thời gian của Nhóm."
            ),
        },
        "backchecked-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của BackChecked",
            "totalAmount": "$535,000",
            "individualPayout": "$50 tiền mặt hoặc tối đa $2.500, kèm dịch vụ giám sát",
        },
        "king-county-jail-booking-settlement-2026": {
            "title": "Dàn xếp về việc giam giữ tại nhà tù Quận King",
            "totalAmount": "$1.6 triệu",
            "individualPayout": "$150 hoặc ít nhất $1,500, tùy theo lệnh bắt giữ và thời gian giam giữ",
        },
        "zoll-heart-device-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu thiết bị tim ZOLL",
            "totalAmount": "$3.5 triệu",
            "individualPayout": "Tiền mặt chia theo tỷ lệ hoặc tối đa $5.000",
        },
        "vertical-hold-climbing-gender-settlement-2026": {
            "title": "Dàn xếp vé ngày leo núi Vertical Hold",
            "totalAmount": "Dàn xếp không bằng tiền mặt",
            "individualPayout": "Bốn vé ngày",
        },
        "sportsedtv-video-privacy-settlement-2026": {
            "title": "Dàn xếp quyền riêng tư video của SportsEdTV",
            "totalAmount": "$500,000",
            "individualPayout": "Tiền mặt chia theo tỷ lệ; yêu cầu tại California nhận hai phần",
        },
        "acmq-unsolicited-fax-settlement-2026": {
            "title": "Dàn xếp fax không được yêu cầu của ACMQ",
            "totalAmount": "Tối đa $175,000 cho các yêu cầu của nhóm",
            "individualPayout": "Tối đa $500 cho mỗi số fax đủ điều kiện",
            "summary": (
                "ACMQ và các bị đơn khác đã dàn xếp cáo buộc rằng quảng cáo hội nghị được gửi "
                "qua fax khi chưa được phép. Mỗi số fax đủ điều kiện đã được xác minh có thể nhận "
                "tối đa $500, tùy thuộc vào giới hạn bồi thường chung $175,000 và việc điều chỉnh "
                "theo tỷ lệ."
            ),
        },
        "naper-grove-vision-care-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của Naper Grove Vision Care",
            "totalAmount": "Quỹ tiền mặt thay thế $50,000",
            "individualPayout": "Tiền mặt chia theo tỷ lệ hoặc tối đa $1.000, kèm dịch vụ giám sát",
        },
        "moodswings-ticket-fee-settlement-2026": {
            "title": "Dàn xếp phí vé của Moodswings",
            "totalAmount": "Chưa công bố công khai",
            "individualPayout": "Tiền mặt cho mỗi vé hoặc mã giảm giá 25%",
            "proofDetails": (
                "Việc nộp trực tuyến yêu cầu ID Thành viên Nhóm trong thông báo dàn xếp. Khoản tiền mặt "
                "được tính theo các giao dịch mua vé đủ điều kiện có trong hồ sơ dàn xếp và chỉ được trả "
                "khi có yêu cầu bồi thường hợp lệ; nếu không làm gì, bạn chỉ nhận được mã giảm giá 25%."
            ),
        },
        "community-realty-management-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của Community Realty Management",
            "totalAmount": "Quyền lợi tiền mặt giới hạn ở $200,000",
            "individualPayout": "$20 tiền mặt hoặc tối đa $2.000, kèm dịch vụ giám sát",
            "eligibility": "Những người được Community Realty Management xác định là có thông tin cá nhân có thể bị xâm phạm do truy cập trái phép vào tài khoản email từ ngày 10 tháng 9 đến ngày 22 tháng 10 năm 2024, bao gồm tất cả những người đã được gửi thông báo về sự cố.",
        },
        "pierce-county-library-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của Pierce County Library",
            "totalAmount": "Quyền lợi tiền mặt giới hạn ở $385,000",
            "individualPayout": "Tiền mặt, bồi hoàn thời gian hoặc tối đa $4.000, kèm dịch vụ giám sát",
        },
        "chemocentryx-securities-settlement-2026": {
            "title": "Dàn xếp chứng khoán ChemoCentryx",
            "totalAmount": "$69 triệu",
            "individualPayout": "Khoản thanh toán chứng khoán chia theo tỷ lệ",
        },
        "credit-suisse-rmbs-restitution-2026": {
            "title": "Quỹ bồi hoàn RMBS của Credit Suisse",
            "totalAmount": "$300 triệu",
            "individualPayout": "Khoản bồi hoàn chia theo tỷ lệ",
        },
        "automotive-information-systems-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của AIS InfoSource",
            "totalAmount": "Chưa công bố công khai",
            "individualPayout": "Tối đa $5.000, kèm dịch vụ giám sát",
        },
        "dairy-farmers-america-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của Dairy Farmers of America",
            "totalAmount": "Tổng tiền mặt giới hạn ở $475,000",
            "individualPayout": "Ước tính $55 tiền mặt hoặc tối đa $4.500, kèm dịch vụ giám sát",
        },
        "anixter-center-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu của Anixter Center",
            "totalAmount": "Chưa công bố công khai",
            "individualPayout": "$50 tiền mặt hoặc tối đa $5.000, kèm dịch vụ giám sát",
        },
        "washington-county-oregon-tax-foreclosure-2026": {
            "title": "Dàn xếp tịch thu tài sản do nợ thuế tại Quận Washington",
            "totalAmount": "$1.5 triệu",
            "individualPayout": "Khoản tiền thặng dư theo từng bất động sản",
            "eligibility": "Cá nhân hoặc tổ chức, cùng những người thừa kế, người kế quyền, người được chuyển nhượng hoặc người có quyền lưu giữ đủ điều kiện, có quyền sở hữu hoặc quyền lưu giữ hợp lệ đối với bất động sản tại Quận Washington, Oregon bị thu hồi qua thủ tục tịch thu thuế; thời hạn chuộc lại hết hạn từ ngày 12 tháng 10 năm 2017 đến ngày 31 tháng 12 năm 2025; và Quận đã bán bất động sản để thu khoản tiền thặng dư hoặc giữ lại, tặng hay chuyển giao bất động sản có phần giá trị thặng dư đủ điều kiện.",
        },
        "hwwc-medical-data-breach-2026": {
            "title": "Dàn xếp vi phạm dữ liệu y tế HWWC",
            "totalAmount": "Chưa công bố công khai",
            "individualPayout": "Giám sát và tối đa $2.500 cho tổn thất có chứng từ, cộng bồi hoàn thời gian đủ điều kiện",
        },
        "mary-black-health-system-settlement-2026": {
            "title": "Dàn xếp Mary Black Health System",
            "totalAmount": "$2.25 triệu",
            "individualPayout": "Phần chia theo tỷ lệ dựa trên tổn thất đã được phê duyệt",
        },
        "bestway-above-ground-pool-settlement-2026": {
            "title": "Dàn xếp hồ bơi nổi Bestway",
            "totalAmount": "$15 triệu",
            "individualPayout": "$40 hoặc 10% giá mua đủ điều kiện",
        },
        "kroger-prescription-savings-club-settlement-2026": {
            "title": "Dàn xếp Câu lạc bộ Tiết kiệm Thuốc theo toa Kroger",
            "totalAmount": "$17 triệu",
            "individualPayout": "Phần chia theo tỷ lệ dựa trên chi tiêu thuốc theo toa đủ điều kiện",
        },
    },
    "fil": {
        "advanced-recovery-equipment-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng Advanced Recovery Equipment & Supplies",
            "totalAmount": "Limitado sa $325,000 ang mga cash payment",
            "individualPayout": "Hanggang $4,250 sa dokumentadong pagkalugi, hanggang $50 cash, at monitoring",
        },
        "aidvantage-tcpa-settlement-2026": {
            "title": "Settlement sa Prerecorded na Tawag ng Aidvantage",
            "totalAmount": "$3 milyon",
            "individualPayout": "Pro rata na cash payment",
            "proofDetails": (
                "Maaaring mag-file ang mga nakatanggap ng postcard gamit ang personalized na claim form "
                "na kasama sa kanilang notice. Ang hindi nakatanggap ng postcard ay dapat humiling ng claim "
                "form sa pamamagitan ng sulat at magsumite ng patunay na nakatanggap ang kanilang cellular "
                "phone ng artificial o prerecorded-voice na tawag o mensahe mula sa Aidvantage sa loob ng "
                "class period."
            ),
        },
        "backchecked-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng BackChecked",
            "totalAmount": "$535,000",
            "individualPayout": "$50 cash o hanggang $2,500, kasama ang monitoring",
        },
        "king-county-jail-booking-settlement-2026": {
            "title": "Settlement sa Detensyon sa King County Jail",
            "totalAmount": "$1.6 milyon",
            "individualPayout": "$150 o hindi bababa sa $1,500, depende sa mga warrant at detensyon",
            "summary": (
                "Sumang-ayon ang King County na ayusin ang mga claim na ang mga taong inaresto "
                "nang walang warrant ay ikinulong nang mahigit 48 oras nang walang agarang "
                "pagpapasiya ng probable cause. Ang mga miyembrong walang ibang warrant ay "
                "makatatanggap ng batayang $1,500 at $57.81 para sa bawat kwalipikadong oras ng "
                "detensyon; ang may isa o higit pang ibang warrant ay makatatanggap ng $150."
            ),
        },
        "zoll-heart-device-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng ZOLL Heart Device",
            "totalAmount": "$3.5 milyon",
            "individualPayout": "Pro rata na cash o hanggang $5,000",
            "eligibilityBullets": [
                "Isa kang buhay na residente ng United States",
                "Posibleng naapektuhan ang iyong impormasyon ng insidente noong Enero 2023",
                "Nagpadala sa iyo ang ZOLL ng abiso na naapektuhan ang ilang personal na impormasyon",
                "Ang mga miyembro ng Social Security number subclass ay makakatanggap ng dalawang bahagi ng pro rata payment",
            ],
        },
        "vertical-hold-climbing-gender-settlement-2026": {
            "title": "Settlement sa Day Pass ng Vertical Hold Climbing",
            "totalAmount": "Settlement na hindi cash",
            "individualPayout": "Apat na day pass",
        },
        "sportsedtv-video-privacy-settlement-2026": {
            "title": "Settlement sa Privacy ng Video ng SportsEdTV",
            "totalAmount": "$500,000",
            "individualPayout": "Pro rata na cash payment; dalawang bahagi para sa mga claim sa California",
        },
        "acmq-unsolicited-fax-settlement-2026": {
            "title": "Settlement sa Hindi Hiniling na Fax ng ACMQ",
            "totalAmount": "Hanggang $175,000 para sa mga claim ng klase",
            "individualPayout": "Hanggang $500 bawat kwalipikadong numero ng fax",
            "summary": (
                "Inayos ng ACMQ at iba pang nasasakdal ang mga alegasyong nagpadala sila ng mga "
                "advertisement ng conference sa fax nang walang pahintulot. Maaaring makatanggap "
                "ng hanggang $500 ang bawat beripikadong kwalipikadong numero ng fax, alinsunod "
                "sa $175,000 na kabuuang limitasyon at anumang pro rata na pagsasaayos."
            ),
        },
        "naper-grove-vision-care-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng Naper Grove Vision Care",
            "totalAmount": "$50,000 na alternatibong cash fund",
            "individualPayout": "Pro rata na cash o hanggang $1,000, kasama ang monitoring",
        },
        "moodswings-ticket-fee-settlement-2026": {
            "title": "Settlement sa Bayad sa Ticket ng Moodswings",
            "totalAmount": "Hindi isinapubliko",
            "individualPayout": "Cash bawat ticket o 25% discount code",
            "proofDetails": (
                "Kinakailangan sa online filing ang Class Member ID mula sa settlement notice. Kinakalkula "
                "ang cash batay sa mga kwalipikadong pagbili ng ticket na nasa settlement records at "
                "kinakailangan ang isang valid claim; kung walang gagawin, 25% discount code lamang ang "
                "matatanggap."
            ),
        },
        "community-realty-management-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng Community Realty Management",
            "totalAmount": "Limitado sa $200,000 ang mga cash benefit",
            "individualPayout": "$20 cash o hanggang $2,000, kasama ang monitoring",
            "eligibility": "Mga taong tinukoy ng Community Realty Management na maaaring nakompromiso ang pribadong impormasyon dahil sa hindi awtorisadong access sa mga email account mula Setyembre 10 hanggang Oktubre 22, 2024, kabilang ang lahat ng pinadalhan ng abiso tungkol sa insidente.",
        },
        "pierce-county-library-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng Pierce County Library",
            "totalAmount": "Limitado sa $385,000 ang mga cash benefit",
            "individualPayout": "Cash, bayad sa nawalang oras, o hanggang $4,000, kasama ang monitoring",
        },
        "chemocentryx-securities-settlement-2026": {
            "title": "ChemoCentryx Securities Settlement",
            "totalAmount": "$69 milyon",
            "individualPayout": "Pro rata na securities payment",
        },
        "credit-suisse-rmbs-restitution-2026": {
            "title": "Credit Suisse RMBS Restitution Fund",
            "totalAmount": "$300 milyon",
            "individualPayout": "Pro rata na restitution payment",
        },
        "automotive-information-systems-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng AIS InfoSource",
            "totalAmount": "Hindi isinapubliko",
            "individualPayout": "Hanggang $5,000, kasama ang monitoring",
        },
        "dairy-farmers-america-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng Dairy Farmers of America",
            "totalAmount": "Limitado sa $475,000 ang mga cash payment",
            "individualPayout": "Tinatayang $55 cash o hanggang $4,500, kasama ang monitoring",
        },
        "anixter-center-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Data ng Anixter Center",
            "totalAmount": "Hindi isinapubliko",
            "individualPayout": "$50 cash o hanggang $5,000, kasama ang monitoring",
            "eligibility": "Mga taong naabisuhan na nakompromiso ang kanilang pribadong impormasyon sa insidente ng data ng Anixter Center noong Hulyo 2023.",
        },
        "washington-county-oregon-tax-foreclosure-2026": {
            "title": "Settlement sa Tax Foreclosure ng Washington County",
            "totalAmount": "$1.5 milyon",
            "individualPayout": "Surplus payment batay sa partikular na ari-arian",
            "eligibility": "Mga tao o entidad, at mga kwalipikadong tagapagmana, kahalili, assignee, o lienholder, na may interes sa pagmamay-ari o balidong lien sa real property sa Washington County, Oregon na kinuha sa tax foreclosure; nag-expire ang redemption period mula Oktubre 12, 2017 hanggang Disyembre 31, 2025; at ibinenta ng County ang property para sa surplus proceeds o pinanatili, ibinigay, o inilipat ang property na may kwalipikadong surplus equity.",
        },
        "hwwc-medical-data-breach-2026": {
            "title": "Settlement sa Paglabag sa Medical Data ng HWWC",
            "totalAmount": "Hindi isinapubliko",
            "individualPayout": "Monitoring at hanggang $2,500 sa dokumentadong pagkalugi, kasama ang kwalipikadong nawalang oras",
        },
        "mary-black-health-system-settlement-2026": {
            "title": "Mary Black Health System Settlement",
            "totalAmount": "$2.25 milyon",
            "individualPayout": "Pro rata na bahagi batay sa aprubadong pagkawala ng miyembro ng klase",
        },
        "bestway-above-ground-pool-settlement-2026": {
            "title": "Settlement sa Above-Ground Pool ng Bestway",
            "totalAmount": "$15 milyon",
            "individualPayout": "$40 o 10% ng kwalipikadong presyo ng pagbili",
        },
        "kroger-prescription-savings-club-settlement-2026": {
            "title": "Settlement sa Kroger Prescription Savings Club",
            "totalAmount": "$17 milyon",
            "individualPayout": "Pro rata na bahagi batay sa kwalipikadong gastos sa reseta",
        },
    },
}

VERIFIED_FACT_TRANSLATION_OVERRIDES = {
    "es": {
        "playstation-psn-digital-games-2026": {
            "title": "Acuerdo antimonopolio sobre juegos digitales de PlayStation",
            "individualPayout": "Distribución automática a la cartera de PSN; cheque para cuentas desactivadas",
            "eligibility": (
                "Titulares de cuentas de PlayStation Network que, entre el 1 de abril de 2019 y el "
                "31 de diciembre de 2023, compraron al menos un juego digital elegible en PlayStation "
                "Store. El juego debe figurar en la lista oficial de juegos elegibles y cumplir los "
                "criterios del acuerdo sobre vales de juegos vendidos por minoristas y aumento de precio."
            ),
            "eligibilityBullets": [
                "Compró un juego en PlayStation Store entre el 1 de abril de 2019 y el 31 de diciembre de 2023",
                "El juego debe figurar en la lista oficial de juegos elegibles del acuerdo",
                "Las cuentas activas elegibles reciben automáticamente una distribución en su cartera de PSN",
                "Los titulares de cuentas desactivadas deben solicitar un cheque antes del 27 de agosto de 2026",
            ],
            "proofDetails": (
                "No se requiere una reclamación para una cuenta PSN activa elegible; si el acuerdo entra "
                "en vigor, su parte se distribuye automáticamente a la cartera de PSN. Un miembro elegible "
                "con una cuenta desactivada debe comunicarse con el administrador y proporcionar información "
                "sobre una compra elegible y una dirección postal actual antes del 27 de agosto de 2026 para "
                "solicitar un cheque."
            ),
            "summary": (
                "Sony Interactive Entertainment aceptó un acuerdo de $7.85 millones por presunta conducta "
                "anticompetitiva que afectó determinadas compras de juegos elegibles en PlayStation Store. "
                "Las cuentas activas elegibles reciben automáticamente una distribución en su cartera; la "
                "fecha límite del 27 de agosto de 2026 solo corresponde a titulares elegibles de cuentas "
                "desactivadas que soliciten un cheque."
            ),
        },
    },
    "zh-Hans": {
        "western-union-remission-phase3-2026": {
            "summary": (
                "根据司法部的返还计划，2004 年至 2020 年间因通过 Western Union 汇款而遭受诈骗的受害者，"
                "可申请返还经核实的汇款损失。2026 年 8 月 5 日，官方管理机构将 Phase 3 申请截止日期"
                "延长至 2026 年 12 月 31 日。"
            ),
        },
        "delta-dental-wyssta-privacy-2026": {
            "eligibilityBullets": [
                "在 my.deltadentalcoversme.com 持有账户",
                "时间为 1/23/2021 至 1/23/2025",
                "美国居民",
            ],
            "proofDetails": (
                "必须提供集体成员 ID。请填写电子邮件或明信片通知中的 ID；如果未收到通知，请在提交"
                "申请前致电和解管理机构 (833) 930-1183 获取 ID。表格还要求声明您在适用期间持有"
                "符合条件的账户。"
            ),
        },
        "ny-renaissance-faire-fees-2026": {
            "eligibilityBullets": [
                "通过官方网站购买了纽约文艺复兴博览会电子门票",
                "支付了服务费或预订费",
                "时间为 8/29/2022 至 4/4/2025",
            ],
            "proofDetails": (
                "在线提交需要电子邮件通知中的 Unique ID 和 PIN。如果您未收到或找不到通知，请致电"
                "和解管理机构 (877) 239-7771 寻求帮助，或者下载、签署并邮寄公开提供的索赔表。"
            ),
        },
        "playstation-psn-digital-games-2026": {
            "title": "PlayStation 数字游戏反垄断和解",
            "individualPayout": "自动发放至 PSN 钱包；已停用账户可申请支票",
            "eligibility": (
                "在 2019 年 4 月 1 日至 2023 年 12 月 31 日期间通过 PlayStation Store 购买至少一款"
                "符合条件的数字游戏的 PlayStation Network 账户持有人。该游戏必须列在官方合格游戏"
                "清单中，并符合和解协议关于零售商游戏专用代金券和价格上涨的条件。"
            ),
            "eligibilityBullets": [
                "在 2019 年 4 月 1 日至 2023 年 12 月 31 日期间通过 PlayStation Store 购买了游戏",
                "该游戏必须列在和解协议的官方合格游戏清单中",
                "有效的合格账户会自动收到 PSN 钱包款项",
                "已停用账户的持有人须在 2026 年 8 月 27 日前申请支票",
            ],
            "proofDetails": (
                "有效的合格 PSN 账户无需提交索赔；如果和解协议生效，其份额会自动发放至 PSN 钱包。"
                "合格但账户已停用的集体成员必须联系管理机构，并在 2026 年 8 月 27 日前提供合格购买"
                "信息及当前邮寄地址，以申请支票。"
            ),
            "summary": (
                "Sony Interactive Entertainment 同意支付 $7.85 百万，就涉嫌影响部分 PlayStation "
                "Store 合格游戏购买的反竞争行为达成和解。有效的合格账户会自动收到钱包款项；"
                "2026 年 8 月 27 日仅是合格的已停用账户持有人申请支票的截止日期。"
            ),
        },
        "marlboro-chesterfield-breach-2026": {
            "proofDetails": (
                "收到明信片通知的人可使用 Notice ID 和 PIN 在线提交。通过公告获知本案的人可下载并"
                "邮寄公开提供的索赔表，无需这些在线登录信息。申请有凭证的欺诈或身份盗窃损失必须"
                "提供证明材料；10 美元替代付款仅适用于社会安全号码在事件中受影响的集体成员。"
            ),
        },
        "bmw-shark-fin-antenna-2026": {
            "title": "BMW 鲨鱼鳍天线密封缺陷和解",
        },
    },
    "vi": {
        "western-union-remission-phase3-2026": {
            "title": "Chương trình hoàn trả gian lận Western Union - Giai đoạn 3",
            "proofDetails": (
                "Nộp Đơn xin Hoàn trả cùng mọi tài liệu hỗ trợ hiện có. Mỗi giao dịch được yêu cầu phải có "
                "Mã số Kiểm soát Chuyển tiền (MTCN) gồm 10 chữ số; nếu không thể xác minh MTCN, quản trị viên "
                "sẽ yêu cầu hồ sơ hỗ trợ, chẳng hạn như biên nhận của khách hàng. Số An sinh Xã hội chỉ bắt "
                "buộc đối với công dân Hoa Kỳ; người không phải công dân Hoa Kỳ và không có SSN hoặc ITIN có "
                "thể đánh dấu lựa chọn \"Tôi không phải là công dân Hoa Kỳ\" trên biểu mẫu."
            ),
            "summary": (
                "Theo chương trình hoàn trả của Bộ Tư pháp, những người bị lừa đảo qua giao dịch Western Union "
                "từ năm 2004 đến năm 2020 có thể yêu cầu hoàn trả khoản chuyển tiền bị mất đã được xác minh. Vào "
                "ngày 5 tháng 8 năm 2026, quản trị viên chính thức đã gia hạn hạn chót nộp đơn Giai đoạn 3 đến "
                "ngày 31 tháng 12 năm 2026."
            ),
        },
        "delta-dental-wyssta-privacy-2026": {
            "proofDetails": (
                "Bắt buộc phải có Mã Thành viên Nhóm. Nhập mã trong thông báo qua email hoặc bưu thiếp; nếu "
                "không nhận được thông báo, hãy gọi Quản trị viên Dàn xếp theo số (833) 930-1183 để lấy mã trước "
                "khi nộp. Biểu mẫu cũng yêu cầu bạn xác nhận đã có tài khoản đủ điều kiện."
            ),
        },
        "ny-renaissance-faire-fees-2026": {
            "proofDetails": (
                "Nộp trực tuyến cần Unique ID và PIN trong thông báo qua email. Nếu không nhận được hoặc không "
                "tìm thấy thông báo, hãy gọi Quản trị viên Dàn xếp theo số (877) 239-7771 để được hỗ trợ, hoặc "
                "tải xuống, ký và gửi qua đường bưu điện Mẫu Yêu cầu bồi thường được cung cấp công khai."
            ),
        },
        "playstation-psn-digital-games-2026": {
            "title": "Dàn xếp chống độc quyền trò chơi kỹ thuật số PlayStation",
            "individualPayout": "Tự động phân phối vào ví PSN; tài khoản đã vô hiệu hóa có thể yêu cầu séc",
            "eligibility": (
                "Chủ tài khoản PlayStation Network đã mua ít nhất một trò chơi kỹ thuật số đủ điều kiện trên "
                "PlayStation Store từ ngày 1 tháng 4 năm 2019 đến ngày 31 tháng 12 năm 2023. Trò chơi phải có "
                "trong danh sách trò chơi đủ điều kiện chính thức và đáp ứng các tiêu chí của thỏa thuận về "
                "phiếu trò chơi bán lẻ và mức tăng giá."
            ),
            "eligibilityBullets": [
                "Đã mua trò chơi trên PlayStation Store từ ngày 1 tháng 4 năm 2019 đến ngày 31 tháng 12 năm 2023",
                "Trò chơi phải có trong danh sách trò chơi đủ điều kiện chính thức của thỏa thuận",
                "Tài khoản đủ điều kiện đang hoạt động tự động nhận khoản phân phối vào ví PSN",
                "Chủ tài khoản đã vô hiệu hóa phải yêu cầu séc trước ngày 27 tháng 8 năm 2026",
            ],
            "proofDetails": (
                "Tài khoản PSN đủ điều kiện đang hoạt động không cần nộp yêu cầu; nếu thỏa thuận có hiệu lực, "
                "phần tiền sẽ tự động được phân phối vào ví PSN. Thành viên đủ điều kiện có tài khoản đã vô "
                "hiệu hóa phải liên hệ quản trị viên, cung cấp thông tin giao dịch mua đủ điều kiện và địa chỉ "
                "gửi thư hiện tại trước ngày 27 tháng 8 năm 2026 để yêu cầu séc."
            ),
            "summary": (
                "Sony Interactive Entertainment đồng ý dàn xếp với quỹ $7.85 triệu cho cáo buộc hành vi phản "
                "cạnh tranh ảnh hưởng đến một số giao dịch mua trò chơi đủ điều kiện trên PlayStation Store. "
                "Tài khoản đủ điều kiện đang hoạt động tự động nhận khoản phân phối vào ví; ngày 27 tháng 8 năm "
                "2026 chỉ là hạn chót để chủ tài khoản đủ điều kiện đã vô hiệu hóa yêu cầu séc."
            ),
        },
        "marlboro-chesterfield-breach-2026": {
            "proofDetails": (
                "Người nhận thông báo qua bưu thiếp có thể nộp trực tuyến bằng Notice ID và PIN. Người biết đến "
                "vụ việc qua Thông báo Công khai có thể tải xuống và gửi qua bưu điện Mẫu Yêu cầu bồi thường "
                "được cung cấp công khai mà không cần các thông tin đăng nhập trực tuyến đó. Khoản bồi hoàn gian "
                "lận hoặc trộm danh tính có chứng từ cần tài liệu hỗ trợ; khoản thay thế $10 chỉ dành cho thành "
                "viên có số An sinh Xã hội bị ảnh hưởng."
            ),
        },
    },
    "fil": {
        "western-union-remission-phase3-2026": {
            "proofDetails": (
                "Magsumite ng Petition for Remission at anumang makukuhang pansuportang dokumento. Kailangan "
                "ng 10-digit Money Transfer Control Number (MTCN) para sa bawat transfer na isinasama; kung "
                "hindi ma-verify ang MTCN, hihingi ang administrator ng mga pansuportang rekord gaya ng resibo. "
                "Ang Social Security number ay kailangan lamang para sa mga mamamayan ng U.S.; maaaring piliin "
                "ng hindi mamamayan ng U.S. na walang SSN o ITIN ang \"I am not a U.S. Citizen\" sa form."
            ),
        },
        "playstation-psn-digital-games-2026": {
            "title": "PlayStation Digital Games Antitrust Settlement",
            "individualPayout": "Awtomatikong pamamahagi sa PSN wallet; tseke para sa mga na-deactivate na account",
            "eligibility": (
                "Mga may hawak ng PlayStation Network account na bumili ng kahit isang kwalipikadong digital "
                "game sa PlayStation Store mula Abril 1, 2019 hanggang Disyembre 31, 2023. Dapat kasama ang game "
                "sa opisyal na listahan ng mga kwalipikadong game at matugunan ang mga pamantayan ng settlement "
                "para sa retail game-specific voucher at pagtaas ng presyo."
            ),
            "eligibilityBullets": [
                "Bumili ng game sa PlayStation Store mula Abril 1, 2019 hanggang Disyembre 31, 2023",
                "Dapat kasama ang game sa opisyal na listahan ng mga kwalipikadong game ng settlement",
                "Awtomatikong tumatanggap ang mga aktibong kwalipikadong account ng pamamahagi sa PSN wallet",
                "Dapat humiling ng tseke ang mga may na-deactivate na account bago Agosto 27, 2026",
            ],
            "proofDetails": (
                "Hindi kailangang mag-file ng claim para sa aktibong kwalipikadong PSN account; kung magiging "
                "epektibo ang settlement, awtomatikong ilalagay ang bahagi nito sa PSN wallet. Ang kwalipikadong "
                "miyembro na may na-deactivate na account ay kailangang makipag-ugnayan sa administrator at "
                "magbigay ng impormasyon sa kwalipikadong pagbili at kasalukuyang mailing address bago Agosto "
                "27, 2026 upang humiling ng tseke."
            ),
            "summary": (
                "Pumayag ang Sony Interactive Entertainment sa $7.85 milyon na settlement para sa diumano'y "
                "anti-competitive na gawain na nakaapekto sa ilang kwalipikadong pagbili ng game sa PlayStation "
                "Store. Awtomatikong tumatanggap ang mga aktibong kwalipikadong account ng pamamahagi sa wallet; "
                "ang Agosto 27, 2026 ay deadline lamang para sa mga kwalipikadong may na-deactivate na account "
                "na humihiling ng tseke."
            ),
        },
    },
}


DEAL_OVERRIDES = {
    "es": {
        "mrs-meyers-hand-soap-rainwater-2026": {
            "title": "MRS. MEYER'S CLEAN DAY Jabón de manos — Aroma Rain Water, 12.5 oz",
        },
    },
    "zh-Hans": {},
    "vi": {
        "mrs-meyers-hand-soap-rainwater-2026": {
            "title": "Nước rửa tay MRS. MEYER'S CLEAN DAY — Hương Rain Water, 12.5 oz",
        },
    },
    "fil": {
        "mrs-meyers-hand-soap-rainwater-2026": {
            "title": "MRS. MEYER'S CLEAN DAY Hand Soap — Rain Water Scent, 12.5 oz",
        },
    },
}


# Reviewed corrections for older records whose structured fallback vocabulary is
# broader than the generic token replacer can safely handle. Keep these explicit so
# rerunning the pipeline cannot reintroduce mixed-language display labels.
LEGACY_DISPLAY_FIXES = {
    "es": {
        "connectoncall-data-breach-2026": {
            "individualPayout": "Hasta $75 en efectivo alternativo o $5,000 por pérdidas documentadas",
        },
        "efs-aviben-data-breach-2026": {
            "totalAmount": "Límite total de $850,000",
            "individualPayout": "$50 en efectivo alternativo o hasta $2,500 más monitoreo",
        },
        "palomar-health-data-breach-2026": {
            "individualPayout": "Pago estimado de $60 o hasta $5,000 más monitoreo",
        },
        "vsl3-probiotic-2026": {
            "individualPayout": "$20 por unidad; hasta $800 con pruebas",
        },
        "release-card-fees-2026": {
            "individualPayout": "Mínimo de $15 más tres veces las comisiones elegibles",
        },
        "mg217-shampoo-2026": {
            "individualPayout": "Hasta $7 por compra; reembolso del precio o cupón de $25 con pruebas",
        },
    },
    "zh-Hans": {
        "connectoncall-data-breach-2026": {"totalAmount": "495 万美元"},
        "efs-aviben-data-breach-2026": {"totalAmount": "总额上限为 850,000 美元"},
        "palomar-health-data-breach-2026": {"totalAmount": "310 万美元"},
        "vsl3-probiotic-2026": {"totalAmount": "2,000 万美元"},
        "release-card-fees-2026": {"totalAmount": "420 万美元"},
        "mg217-shampoo-2026": {"totalAmount": "120 万美元"},
    },
    "vi": {
        "efs-aviben-data-breach-2026": {"totalAmount": "Giới hạn tổng cộng 850.000 USD"},
    },
    "fil": {
        "efs-aviben-data-breach-2026": {"totalAmount": "Limitado sa $850,000 ang kabuuang halaga"},
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--settlements-only",
        action="store_true",
        help="Do not modify localized deal feeds.",
    )
    args = parser.parse_args()

    english = json.loads((ROOT / "settlements.json").read_text())
    source_by_id = {record["id"]: record for record in english}
    for language, records in OVERRIDES.items():
        language_overrides = {
            **records,
            **NEW_SETTLEMENT_DISPLAY_OVERRIDES.get(language, {}),
            **VERIFIED_FACT_TRANSLATION_OVERRIDES.get(language, {}),
            **LEGACY_DISPLAY_FIXES.get(language, {}),
        }
        path = ROOT / f"settlements.{language}.json"
        feed = json.loads(path.read_text())
        by_id = {record["id"]: record for record in feed}
        for record_id, fields in language_overrides.items():
            by_id[record_id].update(fields)
        # Keep every non-translatable fact byte-for-byte aligned with English. This
        # also propagates deadline/status/source corrections whose translation hash
        # intentionally does not change.
        for record in feed:
            source_record = source_by_id[record["id"]]
            for field in PROTECTED_FIELDS:
                record[field] = source_record[field]
            record["totalAmount"] = localize_total_amount(
                source_record["totalAmount"], language
            )
            if language == "es" or record["individualPayout"] == source_record["individualPayout"]:
                record["individualPayout"] = localize_untranslated_payout(
                    source_record["individualPayout"], language
                )
            # Apply reviewed display text after structured defaults so explicit
            # translations are not overwritten by generic localization.
            record.update(language_overrides.get(record["id"], {}))
            for field in TRANSLATED_FIELDS:
                record[field] = repair_spacing(record.get(field), language)
        path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n")
        print(
            f"Applied {sum(map(len, language_overrides.values()))} "
            f"{language} quality overrides"
        )

        if args.settlements_only:
            continue

        deal_path = ROOT / f"deals.{language}.json"
        deals = json.loads(deal_path.read_text())
        for deal in deals:
            deal.update(DEAL_OVERRIDES.get(language, {}).get(deal["id"], {}))
            for field in ("title", "description", "features", "reviewSummary"):
                deal[field] = repair_spacing(deal.get(field), language)
                if language in {"es", "vi", "fil"}:
                    if isinstance(deal[field], str):
                        deal[field] = re.sub(r"(?<=\d[Kk])\s+\+", "+", deal[field])
                        deal[field] = deal[field].replace("8 -in- 1", "8-in-1").replace("8-in- 1", "8-in-1")
                    elif isinstance(deal[field], list):
                        deal[field] = [
                            re.sub(r"(?<=\d[Kk])\s+\+", "+", item)
                            .replace("8 -in- 1", "8-in-1")
                            .replace("8-in- 1", "8-in-1")
                            for item in deal[field]
                        ]
        deal_path.write_text(json.dumps(deals, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
