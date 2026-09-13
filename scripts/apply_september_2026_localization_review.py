#!/usr/bin/env python3
"""Apply reviewed corrections for settlements added on 2026-09-13.

The baseline translator is useful for coverage, but legal eligibility and proof text
must not rely on sentence batching. This file records deliberate, repeatable fixes
for display labels and the five proof-sensitive settlements reviewed for this batch.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ("es", "zh-Hans", "vi", "fil")


TOTALS = {
    "es": {
        "Settlement amount not disclosed": "Monto del acuerdo no divulgado",
        "$7.75 million": "$7.75 millones",
        "$20 million": "$20 millones",
        "$9.9 million plus a $100,000 notice contribution": "$9.9 millones, más una contribución de $100,000 para notificaciones",
        "Cash claims capped at $500,000": "Reclamaciones en efectivo limitadas a $500,000",
        "$28 million": "$28 millones",
        "$9.375 million": "$9.375 millones",
        "Out-of-pocket claims capped at $175,000": "Reclamaciones por gastos de bolsillo limitadas a $175,000",
        "Up to $6.3 million in claimant payments": "Hasta $6.3 millones en pagos a reclamantes",
        "$17.05 million": "$17.05 millones",
        "$288,125 to $412,500": "$288,125 a $412,500",
        "Alternative cash payments capped at $300,000": "Pagos alternativos en efectivo limitados a $300,000",
        "$4.5 million": "$4.5 millones",
        "$500,000 benefit cap": "Límite de $500,000 para beneficios",
        "$12 million to $30 million": "$12 millones a $30 millones",
        "Up to $15 million in claimant benefits": "Hasta $15 millones en beneficios para reclamantes",
        "$300,000 benefit cap": "Límite de $300,000 para beneficios",
        "$500,000 cash-payment cap": "Límite de $500,000 para pagos en efectivo",
        "$925,000 benefit cap": "Límite de $925,000 para beneficios",
    },
    "zh-Hans": {
        "Settlement amount not disclosed": "和解金额未披露",
        "$7.75 million": "775 万美元",
        "$20 million": "2,000 万美元",
        "$9.9 million plus a $100,000 notice contribution": "990 万美元，另加 10 万美元通知费用",
        "Cash claims capped at $500,000": "现金索赔总额上限为 50 万美元",
        "$28 million": "2,800 万美元",
        "$9.375 million": "937.5 万美元",
        "Out-of-pocket claims capped at $175,000": "自付损失索赔总额上限为 17.5 万美元",
        "Up to $6.3 million in claimant payments": "索赔人付款总额最高 630 万美元",
        "$17.05 million": "1,705 万美元",
        "$288,125 to $412,500": "288,125 至 412,500 美元",
        "Alternative cash payments capped at $300,000": "替代现金付款总额上限为 30 万美元",
        "$4.5 million": "450 万美元",
        "$500,000 benefit cap": "福利总额上限为 50 万美元",
        "$12 million to $30 million": "1,200 万至 3,000 万美元",
        "Up to $15 million in claimant benefits": "索赔人福利总额最高 1,500 万美元",
        "$300,000 benefit cap": "福利总额上限为 30 万美元",
        "$500,000 cash-payment cap": "现金付款总额上限为 50 万美元",
        "$925,000 benefit cap": "福利总额上限为 92.5 万美元",
    },
    "vi": {
        "Settlement amount not disclosed": "Số tiền dàn xếp chưa được công bố",
        "$7.75 million": "7,75 triệu USD",
        "$20 million": "20 triệu USD",
        "$9.9 million plus a $100,000 notice contribution": "9,9 triệu USD, cộng thêm 100.000 USD cho chi phí thông báo",
        "Cash claims capped at $500,000": "Tổng yêu cầu thanh toán bằng tiền mặt giới hạn ở 500.000 USD",
        "$28 million": "28 triệu USD",
        "$9.375 million": "9,375 triệu USD",
        "Out-of-pocket claims capped at $175,000": "Tổng yêu cầu bồi hoàn chi phí tự trả giới hạn ở 175.000 USD",
        "Up to $6.3 million in claimant payments": "Tối đa 6,3 triệu USD để thanh toán cho người yêu cầu",
        "$17.05 million": "17,05 triệu USD",
        "$288,125 to $412,500": "288.125 đến 412.500 USD",
        "Alternative cash payments capped at $300,000": "Tổng khoản tiền mặt thay thế giới hạn ở 300.000 USD",
        "$4.5 million": "4,5 triệu USD",
        "$500,000 benefit cap": "Tổng quyền lợi giới hạn ở 500.000 USD",
        "$12 million to $30 million": "12 triệu đến 30 triệu USD",
        "Up to $15 million in claimant benefits": "Tối đa 15 triệu USD cho quyền lợi của người yêu cầu",
        "$300,000 benefit cap": "Tổng quyền lợi giới hạn ở 300.000 USD",
        "$500,000 cash-payment cap": "Tổng khoản thanh toán tiền mặt giới hạn ở 500.000 USD",
        "$925,000 benefit cap": "Tổng quyền lợi giới hạn ở 925.000 USD",
    },
    "fil": {
        "Settlement amount not disclosed": "Hindi isinapubliko ang halaga ng settlement",
        "$7.75 million": "$7.75 milyon",
        "$20 million": "$20 milyon",
        "$9.9 million plus a $100,000 notice contribution": "$9.9 milyon, at karagdagang $100,000 para sa mga notice",
        "Cash claims capped at $500,000": "Limitado sa $500,000 ang kabuuang cash claims",
        "$28 million": "$28 milyon",
        "$9.375 million": "$9.375 milyon",
        "Out-of-pocket claims capped at $175,000": "Limitado sa $175,000 ang kabuuang out-of-pocket claims",
        "Up to $6.3 million in claimant payments": "Hanggang $6.3 milyon para sa mga claimant",
        "$17.05 million": "$17.05 milyon",
        "$288,125 to $412,500": "$288,125 hanggang $412,500",
        "Alternative cash payments capped at $300,000": "Limitado sa $300,000 ang kabuuang alternatibong cash payments",
        "$4.5 million": "$4.5 milyon",
        "$500,000 benefit cap": "Limitado sa $500,000 ang kabuuang benepisyo",
        "$12 million to $30 million": "$12 milyon hanggang $30 milyon",
        "Up to $15 million in claimant benefits": "Hanggang $15 milyon sa mga benepisyo para sa mga claimant",
        "$300,000 benefit cap": "Limitado sa $300,000 ang kabuuang benepisyo",
        "$500,000 cash-payment cap": "Limitado sa $500,000 ang kabuuang cash payments",
        "$925,000 benefit cap": "Limitado sa $925,000 ang kabuuang benepisyo",
    },
}


PAYOUTS = {
    "es": {
        "Pro rata payment based on eligible direct purchases": "Pago prorrateado según las compras directas elegibles",
        "Up to $5,000 in documented losses plus medical monitoring": "Hasta $5,000 por pérdidas documentadas, más monitoreo de identidad médica",
        "Pro rata payment based on qualifying searches": "Pago prorrateado según la cantidad de registros elegibles",
        "$250 to $650 estimated": "Pago estimado de $250 a $650",
        "$50 cash or up to $2,500 in documented losses plus monitoring": "$50 en efectivo o hasta $2,500 por pérdidas documentadas, más monitoreo",
        "$45 or $95 cash, or up to $2,100 in losses and time, plus monitoring": "$45 o $95 en efectivo, o hasta $2,100 por pérdidas y tiempo, más monitoreo",
        "$70 cash or up to $2,500 in documented losses plus monitoring": "$70 en efectivo o hasta $2,500 por pérdidas documentadas, más monitoreo",
        "$45 cash or up to $5,000 in documented losses plus monitoring": "$45 en efectivo o hasta $5,000 por pérdidas documentadas, más monitoreo",
        "Pro rata cash or up to $3,500 in documented losses plus monitoring": "Pago prorrateado en efectivo o hasta $3,500 por pérdidas documentadas, más monitoreo",
        "$0.31 per eligible share estimated before deductions": "Estimado de $0.31 por acción elegible antes de deducciones",
        "$920.91 to $5,000 estimated": "Pago estimado de $920.91 a $5,000",
        "$25 estimated or up to $5,000 in documented losses plus monitoring": "$25 estimados o hasta $5,000 por pérdidas documentadas, más monitoreo",
        "$85 estimated cash or up to $5,000 in documented losses plus monitoring": "$85 estimados en efectivo o hasta $5,000 por pérdidas documentadas, más monitoreo",
        "Pro rata payment up to $10,000": "Pago prorrateado de hasta $10,000",
        "$50 cash or up to $4,000 in documented losses plus monitoring": "$50 en efectivo o hasta $4,000 por pérdidas documentadas, más monitoreo",
        "Pro rata payment based on qualifying virtual-coin purchases": "Pago prorrateado según las compras elegibles de monedas virtuales",
        "$110 to $222 estimated": "Pago estimado de $110 a $222",
        "$45 cash or up to $4,480 in losses and time plus monitoring": "$45 en efectivo o hasta $4,480 por pérdidas y tiempo, más monitoreo",
        "$75 cash or up to $5,600 in losses and time plus monitoring": "$75 en efectivo o hasta $5,600 por pérdidas y tiempo, más monitoreo",
        "Up to $550 residual cash or up to $6,550 in combined benefits plus monitoring": "Hasta $550 en efectivo residual o hasta $6,550 en beneficios combinados, más monitoreo",
        "$40 cash or up to $5,000 in documented losses plus monitoring": "$40 en efectivo o hasta $5,000 por pérdidas documentadas, más monitoreo",
        "$40 cash or up to $5,075 in losses and time plus monitoring": "$40 en efectivo o hasta $5,075 por pérdidas y tiempo, más monitoreo",
        "$75 cash or up to $4,600 in losses and time plus monitoring": "$75 en efectivo o hasta $4,600 por pérdidas y tiempo, más monitoreo",
        "Up to $45 for lost time and up to $2,500 in documented losses plus monitoring": "Hasta $45 por tiempo perdido y hasta $2,500 por pérdidas documentadas, más monitoreo",
        "Pro rata payment based on processing fees paid": "Pago prorrateado según los cargos de procesamiento pagados",
        "$45 cash or up to $2,000 in documented losses plus monitoring": "$45 en efectivo o hasta $2,000 por pérdidas documentadas, más monitoreo",
    },
    "zh-Hans": {
        "Pro rata payment based on eligible direct purchases": "按符合条件的直接采购额比例分配",
        "Up to $5,000 in documented losses plus medical monitoring": "最高 5,000 美元的有凭证损失补偿，另加医疗身份监测",
        "Pro rata payment based on qualifying searches": "按符合条件的搜查次数比例分配",
        "$250 to $650 estimated": "预计 250 至 650 美元",
        "$50 cash or up to $2,500 in documented losses plus monitoring": "50 美元现金，或最高 2,500 美元的有凭证损失补偿，另加监测服务",
        "$45 or $95 cash, or up to $2,100 in losses and time, plus monitoring": "45 或 95 美元现金，或最高 2,100 美元的损失及误工补偿，另加监测服务",
        "$70 cash or up to $2,500 in documented losses plus monitoring": "70 美元现金，或最高 2,500 美元的有凭证损失补偿，另加监测服务",
        "$45 cash or up to $5,000 in documented losses plus monitoring": "45 美元现金，或最高 5,000 美元的有凭证损失补偿，另加监测服务",
        "Pro rata cash or up to $3,500 in documented losses plus monitoring": "按比例分配的现金，或最高 3,500 美元的有凭证损失补偿，另加监测服务",
        "$0.31 per eligible share estimated before deductions": "扣除费用前，预计每股合格股票 0.31 美元",
        "$920.91 to $5,000 estimated": "预计 920.91 至 5,000 美元",
        "$25 estimated or up to $5,000 in documented losses plus monitoring": "预计 25 美元，或最高 5,000 美元的有凭证损失补偿，另加监测服务",
        "$85 estimated cash or up to $5,000 in documented losses plus monitoring": "预计 85 美元现金，或最高 5,000 美元的有凭证损失补偿，另加监测服务",
        "Pro rata payment up to $10,000": "按比例分配，每人最高 10,000 美元",
        "$50 cash or up to $4,000 in documented losses plus monitoring": "50 美元现金，或最高 4,000 美元的有凭证损失补偿，另加监测服务",
        "Pro rata payment based on qualifying virtual-coin purchases": "按符合条件的虚拟币购买额比例分配",
        "$110 to $222 estimated": "预计 110 至 222 美元",
        "$45 cash or up to $4,480 in losses and time plus monitoring": "45 美元现金，或最高 4,480 美元的损失及误工补偿，另加监测服务",
        "$75 cash or up to $5,600 in losses and time plus monitoring": "75 美元现金，或最高 5,600 美元的损失及误工补偿，另加监测服务",
        "Up to $550 residual cash or up to $6,550 in combined benefits plus monitoring": "最高 550 美元剩余现金，或最高 6,550 美元的综合福利，另加监测服务",
        "$40 cash or up to $5,000 in documented losses plus monitoring": "40 美元现金，或最高 5,000 美元的有凭证损失补偿，另加监测服务",
        "$40 cash or up to $5,075 in losses and time plus monitoring": "40 美元现金，或最高 5,075 美元的损失及误工补偿，另加监测服务",
        "$75 cash or up to $4,600 in losses and time plus monitoring": "75 美元现金，或最高 4,600 美元的损失及误工补偿，另加监测服务",
        "Up to $45 for lost time and up to $2,500 in documented losses plus monitoring": "误工补偿最高 45 美元，有凭证损失补偿最高 2,500 美元，另加监测服务",
        "Pro rata payment based on processing fees paid": "按已付手续费比例分配",
        "$45 cash or up to $2,000 in documented losses plus monitoring": "45 美元现金，或最高 2,000 美元的有凭证损失补偿，另加监测服务",
    },
    "vi": {},
    "fil": {},
}

# Vietnamese and Filipino use predictable, readable constructions for the same labels.
PAYOUTS["vi"] = {
    key: value for key, value in {
        "Pro rata payment based on eligible direct purchases": "Khoản thanh toán theo tỷ lệ dựa trên các giao dịch mua trực tiếp đủ điều kiện",
        "Up to $5,000 in documented losses plus medical monitoring": "Tối đa 5.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát danh tính y tế",
        "Pro rata payment based on qualifying searches": "Khoản thanh toán theo tỷ lệ dựa trên số lần khám xét đủ điều kiện",
        "$250 to $650 estimated": "Ước tính từ 250 đến 650 USD",
        "$50 cash or up to $2,500 in documented losses plus monitoring": "50 USD tiền mặt hoặc tối đa 2.500 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "$45 or $95 cash, or up to $2,100 in losses and time, plus monitoring": "45 hoặc 95 USD tiền mặt, hoặc tối đa 2.100 USD cho tổn thất và thời gian, kèm dịch vụ giám sát",
        "$70 cash or up to $2,500 in documented losses plus monitoring": "70 USD tiền mặt hoặc tối đa 2.500 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "$45 cash or up to $5,000 in documented losses plus monitoring": "45 USD tiền mặt hoặc tối đa 5.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "Pro rata cash or up to $3,500 in documented losses plus monitoring": "Tiền mặt theo tỷ lệ hoặc tối đa 3.500 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "$0.31 per eligible share estimated before deductions": "Ước tính 0,31 USD cho mỗi cổ phiếu đủ điều kiện trước khi khấu trừ",
        "$920.91 to $5,000 estimated": "Ước tính từ 920,91 đến 5.000 USD",
        "$25 estimated or up to $5,000 in documented losses plus monitoring": "Ước tính 25 USD hoặc tối đa 5.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "$85 estimated cash or up to $5,000 in documented losses plus monitoring": "Ước tính 85 USD tiền mặt hoặc tối đa 5.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "Pro rata payment up to $10,000": "Khoản thanh toán theo tỷ lệ, tối đa 10.000 USD",
        "$50 cash or up to $4,000 in documented losses plus monitoring": "50 USD tiền mặt hoặc tối đa 4.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "Pro rata payment based on qualifying virtual-coin purchases": "Khoản thanh toán theo tỷ lệ dựa trên giao dịch mua xu ảo đủ điều kiện",
        "$110 to $222 estimated": "Ước tính từ 110 đến 222 USD",
        "$45 cash or up to $4,480 in losses and time plus monitoring": "45 USD tiền mặt hoặc tối đa 4.480 USD cho tổn thất và thời gian, kèm dịch vụ giám sát",
        "$75 cash or up to $5,600 in losses and time plus monitoring": "75 USD tiền mặt hoặc tối đa 5.600 USD cho tổn thất và thời gian, kèm dịch vụ giám sát",
        "Up to $550 residual cash or up to $6,550 in combined benefits plus monitoring": "Tối đa 550 USD tiền mặt còn lại hoặc tối đa 6.550 USD tổng quyền lợi, kèm dịch vụ giám sát",
        "$40 cash or up to $5,000 in documented losses plus monitoring": "40 USD tiền mặt hoặc tối đa 5.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "$40 cash or up to $5,075 in losses and time plus monitoring": "40 USD tiền mặt hoặc tối đa 5.075 USD cho tổn thất và thời gian, kèm dịch vụ giám sát",
        "$75 cash or up to $4,600 in losses and time plus monitoring": "75 USD tiền mặt hoặc tối đa 4.600 USD cho tổn thất và thời gian, kèm dịch vụ giám sát",
        "Up to $45 for lost time and up to $2,500 in documented losses plus monitoring": "Tối đa 45 USD cho thời gian bị mất và 2.500 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
        "Pro rata payment based on processing fees paid": "Khoản thanh toán theo tỷ lệ dựa trên phí xử lý đã trả",
        "$45 cash or up to $2,000 in documented losses plus monitoring": "45 USD tiền mặt hoặc tối đa 2.000 USD cho tổn thất có chứng từ, kèm dịch vụ giám sát",
    }.items()
}
PAYOUTS["fil"] = {
    "Pro rata payment based on eligible direct purchases": "Pro rata na bayad batay sa mga kwalipikadong direktang pagbili",
    "Up to $5,000 in documented losses plus medical monitoring": "Hanggang $5,000 para sa dokumentadong pagkalugi, kasama ang medical identity monitoring",
    "Pro rata payment based on qualifying searches": "Pro rata na bayad batay sa bilang ng mga kwalipikadong search",
    "$250 to $650 estimated": "Tinatayang $250 hanggang $650",
    "$50 cash or up to $2,500 in documented losses plus monitoring": "$50 cash o hanggang $2,500 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "$45 or $95 cash, or up to $2,100 in losses and time, plus monitoring": "$45 o $95 cash, o hanggang $2,100 para sa pagkalugi at oras, kasama ang monitoring",
    "$70 cash or up to $2,500 in documented losses plus monitoring": "$70 cash o hanggang $2,500 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "$45 cash or up to $5,000 in documented losses plus monitoring": "$45 cash o hanggang $5,000 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "Pro rata cash or up to $3,500 in documented losses plus monitoring": "Pro rata na cash o hanggang $3,500 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "$0.31 per eligible share estimated before deductions": "Tinatayang $0.31 bawat kwalipikadong share bago ang mga bawas",
    "$920.91 to $5,000 estimated": "Tinatayang $920.91 hanggang $5,000",
    "$25 estimated or up to $5,000 in documented losses plus monitoring": "Tinatayang $25 o hanggang $5,000 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "$85 estimated cash or up to $5,000 in documented losses plus monitoring": "Tinatayang $85 cash o hanggang $5,000 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "Pro rata payment up to $10,000": "Pro rata na bayad na hanggang $10,000",
    "$50 cash or up to $4,000 in documented losses plus monitoring": "$50 cash o hanggang $4,000 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "Pro rata payment based on qualifying virtual-coin purchases": "Pro rata na bayad batay sa mga kwalipikadong pagbili ng virtual coin",
    "$110 to $222 estimated": "Tinatayang $110 hanggang $222",
    "$45 cash or up to $4,480 in losses and time plus monitoring": "$45 cash o hanggang $4,480 para sa pagkalugi at oras, kasama ang monitoring",
    "$75 cash or up to $5,600 in losses and time plus monitoring": "$75 cash o hanggang $5,600 para sa pagkalugi at oras, kasama ang monitoring",
    "Up to $550 residual cash or up to $6,550 in combined benefits plus monitoring": "Hanggang $550 na residual cash o hanggang $6,550 sa pinagsamang benepisyo, kasama ang monitoring",
    "$40 cash or up to $5,000 in documented losses plus monitoring": "$40 cash o hanggang $5,000 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "$40 cash or up to $5,075 in losses and time plus monitoring": "$40 cash o hanggang $5,075 para sa pagkalugi at oras, kasama ang monitoring",
    "$75 cash or up to $4,600 in losses and time plus monitoring": "$75 cash o hanggang $4,600 para sa pagkalugi at oras, kasama ang monitoring",
    "Up to $45 for lost time and up to $2,500 in documented losses plus monitoring": "Hanggang $45 para sa nawalang oras at $2,500 para sa dokumentadong pagkalugi, kasama ang monitoring",
    "Pro rata payment based on processing fees paid": "Pro rata na bayad batay sa processing fees na binayaran",
    "$45 cash or up to $2,000 in documented losses plus monitoring": "$45 cash o hanggang $2,000 para sa dokumentadong pagkalugi, kasama ang monitoring",
}


CRITICAL = {
    "es": {
        "nyc-doc-strip-search-2026": {
            "title": "Acuerdo por registros al desnudo del DOC de Nueva York",
            "eligibility": "Personas bajo custodia del Departamento de Corrección de la Ciudad de Nueva York que fueron sometidas a un segundo registro al desnudo elegible en la División de Tribunales de Manhattan: del 28 de marzo de 2020 al 29 de febrero de 2024 si tenían la clasificación de Seguridad Reforzada, o del 1 de octubre de 2022 al 29 de febrero de 2024 en los demás casos.",
            "eligibilityBullets": ["Estuvieron bajo custodia del DOC de Nueva York del 28 de marzo de 2020 al 29 de febrero de 2024 si tenían la clasificación de Seguridad Reforzada, o del 1 de octubre de 2022 al 29 de febrero de 2024 en los demás casos", "Fueron registrados en la División de Tribunales de Manhattan después de haber sido registrados antes de salir de Rikers Island", "Figuran en la lista oficial de miembros del grupo del acuerdo"],
            "proofDetails": "No se solicitan recibos ni un ID del aviso, pero la elegibilidad y el número de registros que cumplen los requisitos se verifican con los registros oficiales del DOC mediante los datos de identificación del reclamante.",
            "summary": "La Ciudad de Nueva York acordó resolver las reclamaciones de que personas bajo custodia del DOC fueron sometidas innecesariamente a un segundo registro al desnudo en la División de Tribunales de Manhattan. Los miembros aprobados compartirán un fondo de $28 millones según la cantidad de registros elegibles.",
        },
        "highland-health-systems-data-2026": {
            "title": "Acuerdo por la filtración de datos de Highland Health Systems",
            "eligibility": "Residentes de Estados Unidos cuya información privada quedó expuesta a terceros no autorizados en la filtración de datos de Highland Health Systems descubierta alrededor del 3 de julio de 2023.",
            "eligibilityBullets": ["Residen en Estados Unidos", "Su información privada quedó expuesta en la filtración de Highland Health", "La filtración se descubrió alrededor del 3 de julio de 2023"],
            "proofDetails": "El sitio oficial ofrece un formulario que puede presentarse sin ID de inicio de sesión ni PIN. La opción alternativa estimada de $85 en efectivo no exige documentos; solo la opción separada de hasta $5,000 por pérdidas exige comprobantes.",
            "summary": "Highland Health Systems aceptó un acuerdo de $650,000 por un ciberataque de 2023 que presuntamente expuso información personal y médica. Los miembros pueden elegir un pago estimado de $85 sin documentos o reclamar hasta $5,000 por pérdidas documentadas, además de monitoreo.",
        },
        "amn-healthcare-cipa-2026": {
            "title": "Acuerdo por grabaciones de interpretación de AMN Healthcare",
            "eligibility": "Personas que se encontraban físicamente en California y participaron en una conversación interpretada por AMN entre el 4 de diciembre de 2022 y el 7 de agosto de 2026, y cuya conversación presuntamente fue monitoreada, escuchada o grabada por AMN sin consentimiento previo.",
            "eligibilityBullets": ["Se encontraban físicamente en California", "Participaron en una conversación interpretada por AMN entre el 4 de diciembre de 2022 y el 7 de agosto de 2026", "La conversación presuntamente fue monitoreada, escuchada o grabada sin consentimiento previo"],
            "proofDetails": "Los reclamantes deben facilitar datos suficientes para identificar la sesión de interpretación y certificar que cumplen los requisitos. Se puede registrar una reclamación sin ID, pero se verificará con los registros de sesiones de AMN.",
            "summary": "AMN Healthcare acordó resolver las acusaciones de que determinadas sesiones de interpretación en California fueron monitoreadas o grabadas sin consentimiento previo. Los reclamantes aprobados compartirán el fondo neto de $4.5 millones de forma prorrateada, con un máximo de $10,000 por persona.",
        },
        "high5-games-washington-2026": {
            "title": "Acuerdo de High 5 Games por compras de monedas virtuales en Washington",
            "eligibility": "Personas que compraron monedas virtuales en High 5 Casino o High 5 Vegas, en Washington o vinculadas a Washington, entre el 9 de abril de 2014 y el 30 de septiembre de 2022.",
            "eligibilityBullets": ["Compraron monedas virtuales en High 5 Casino o High 5 Vegas", "La compra se realizó en Washington o estuvo vinculada a Washington", "La compra se realizó entre el 9 de abril de 2014 y el 30 de septiembre de 2022"],
            "proofDetails": "El ID único puede omitirse y no se piden recibos, pero la elegibilidad y el pago se determinan con la cuenta de High 5 del reclamante y sus registros de compras de monedas virtuales.",
            "summary": "High 5 Games acordó resolver reclamaciones por pérdidas de juego en Washington relacionadas con compras de monedas virtuales. Los reclamantes aprobados recibirán una parte del acuerdo, financiado durante varios años, según sus compras elegibles.",
        },
        "sugared-bronzed-tcpa-2026": {
            "title": "Acuerdo de Sugared + Bronzed por mensajes de texto",
            "eligibility": "Personas cuyo número móvil recibió, a través de Klaviyo, dos o más mensajes de telemercadeo de Sugared + Bronzed en un período de 12 meses después de solicitar la baja, entre el 14 de agosto de 2020 y el 17 de julio de 2026.",
            "eligibilityBullets": ["Recibieron dos o más mensajes de telemercadeo de Sugared + Bronzed en un período de 12 meses", "Los mensajes llegaron después de una solicitud de baja o de detención", "Los mensajes se enviaron entre el 14 de agosto de 2020 y el 17 de julio de 2026"],
            "proofDetails": "El sitio permite presentar la reclamación sin ID de inicio de sesión ni PIN, pero el número móvil indicado debe coincidir con los registros de Sugared + Bronzed y Klaviyo que demuestren los mensajes y la solicitud de detención elegibles.",
            "summary": "Sugared + Bronzed acordó resolver las acusaciones de que siguió enviando mensajes de telemercadeo después de que los destinatarios pidieran que cesaran. Los reclamantes aprobados compartirán el fondo neto de $750,000; se estiman pagos de $110 a $222.",
        },
    },
    "zh-Hans": {
        "nyc-doc-strip-search-2026": {"title": "纽约市惩教局重复脱衣搜查和解", "eligibility": "在纽约市惩教局羁押期间被重复脱衣搜查且符合以下时间条件的人员：如被列为“加强安保”级别，时间为 2020 年 3 月 28 日至 2024 年 2 月 29 日；其他人员则为 2022 年 10 月 1 日至 2024 年 2 月 29 日。搜查地点须为曼哈顿法院分部。", "eligibilityBullets": ["如被列为“加强安保”级别，在 2020 年 3 月 28 日至 2024 年 2 月 29 日期间受纽约市惩教局羁押；其他人员则须在 2022 年 10 月 1 日至 2024 年 2 月 29 日期间受羁押", "离开赖克斯岛前已接受搜查，之后又在曼哈顿法院分部接受搜查", "姓名列入官方和解集体名单"], "proofDetails": "无需提交收据或通知 ID，但管理方会根据索赔人的身份信息，对照惩教局的官方集体记录核实资格及符合条件的搜查次数。", "summary": "纽约市同意解决有关惩教局羁押人员在曼哈顿法院分部遭到不必要重复脱衣搜查的诉讼。获批集体成员将根据符合条件的搜查次数分配 2,800 万美元基金。"},
        "highland-health-systems-data-2026": {"title": "Highland Health Systems 数据泄露和解", "eligibility": "在 Highland Health Systems 于 2023 年 7 月 3 日前后发现的数据泄露事件中，私人信息被未获授权方获取的美国居民。", "eligibilityBullets": ["居住在美国", "私人信息在 Highland Health 数据泄露事件中被未获授权方获取", "该事件于 2023 年 7 月 3 日前后被发现"], "proofDetails": "官方网站提供无需登录 ID 或 PIN 即可提交的索赔表。预计 85 美元的替代现金选项无需证明文件；只有单独的最高 5,000 美元损失补偿选项需要提供记录。", "summary": "Highland Health Systems 同意支付 65 万美元，就 2023 年网络攻击涉嫌泄露个人及医疗信息一事达成和解。集体成员可选择无需文件的预计 85 美元现金，或申请最高 5,000 美元的有凭证损失补偿及监测服务。"},
        "amn-healthcare-cipa-2026": {"title": "AMN Healthcare 口译录音和解", "eligibility": "2022 年 12 月 4 日至 2026 年 8 月 7 日期间身处加利福尼亚州并参加 AMN 口译对话，且该对话据称被 AMN 在未经事先同意的情况下监控、监听或录音的人员。", "eligibilityBullets": ["当时身处加利福尼亚州", "在 2022 年 12 月 4 日至 2026 年 8 月 7 日期间参加 AMN 口译对话", "该对话据称在未经事先同意的情况下被监控、监听或录音"], "proofDetails": "索赔人必须提供足以识别口译会话的资料，并确认自己符合资格。虽然可以在没有 ID 的情况下登记，但管理方会对照 AMN 的会话记录核实索赔。", "summary": "AMN Healthcare 同意解决有关加州口译会话在未经事先同意的情况下被监控或录音的指控。获批索赔人将按比例分配 450 万美元净基金，每人最高 10,000 美元。"},
        "high5-games-washington-2026": {"title": "High 5 Games 华盛顿州虚拟币购买和解", "eligibility": "2014 年 4 月 9 日至 2022 年 9 月 30 日期间，在华盛顿州内或与华盛顿州有关联的情况下，于 High 5 Casino 或 High 5 Vegas 购买虚拟币的人员。", "eligibilityBullets": ["在 High 5 Casino 或 High 5 Vegas 购买过虚拟币", "购买发生在华盛顿州内或与华盛顿州有关联", "购买日期在 2014 年 4 月 9 日至 2022 年 9 月 30 日之间"], "proofDetails": "可不填写唯一 ID，也无需提交收据；但管理方会根据索赔人的 High 5 账户及虚拟币购买记录确定资格和赔付金额。", "summary": "High 5 Games 同意解决与华盛顿州虚拟币购买有关的赌博损失索赔。获批索赔人将根据符合条件的购买额，分配由多年付款组成的和解基金。"},
        "sugared-bronzed-tcpa-2026": {"title": "Sugared + Bronzed 营销短信和解", "eligibility": "2020 年 8 月 14 日至 2026 年 7 月 17 日期间，在提出退订要求后的 12 个月内，通过 Klaviyo 收到两条或以上 Sugared + Bronzed 营销短信的手机号码持有人。", "eligibilityBullets": ["在 12 个月内收到两条或以上 Sugared + Bronzed 营销短信", "短信是在提出退订或停止要求后收到的", "短信发送日期在 2020 年 8 月 14 日至 2026 年 7 月 17 日之间"], "proofDetails": "索赔网站允许在没有登录 ID 或 PIN 的情况下提交，但所填手机号码必须与 Sugared + Bronzed 及 Klaviyo 的记录相符，并能显示符合条件的短信和停止要求。", "summary": "Sugared + Bronzed 同意解决有关其在收件人要求停止后仍发送营销短信的指控。获批索赔人将分配 75 万美元净基金，预计每人可获 110 至 222 美元。"},
    },
    "vi": {
        "nyc-doc-strip-search-2026": {"title": "Thỏa thuận về việc khám xét khỏa thân lặp lại của Sở Cải huấn Thành phố New York", "eligibility": "Những người bị Sở Cải huấn Thành phố New York giam giữ và bị khám xét khỏa thân lặp lại tại Phân khu Tòa án Manhattan: từ ngày 28 tháng 3 năm 2020 đến ngày 29 tháng 2 năm 2024 nếu được xếp loại An ninh Tăng cường, hoặc từ ngày 1 tháng 10 năm 2022 đến ngày 29 tháng 2 năm 2024 đối với những người khác.", "eligibilityBullets": ["Bị Sở Cải huấn Thành phố New York giam giữ từ ngày 28 tháng 3 năm 2020 đến ngày 29 tháng 2 năm 2024 nếu được xếp loại An ninh Tăng cường, hoặc từ ngày 1 tháng 10 năm 2022 đến ngày 29 tháng 2 năm 2024 đối với những người khác", "Bị khám xét tại Phân khu Tòa án Manhattan sau khi đã bị khám xét trước khi rời Đảo Rikers", "Có tên trong danh sách tập thể chính thức của thỏa thuận"], "proofDetails": "Không cần biên lai hoặc ID trên thông báo, nhưng tư cách đủ điều kiện và số lần khám xét đủ điều kiện sẽ được đối chiếu với hồ sơ chính thức của DOC bằng thông tin nhận dạng của người yêu cầu.", "summary": "Thành phố New York đồng ý giải quyết các khiếu nại rằng người bị DOC giam giữ đã phải chịu những lần khám xét khỏa thân lặp lại không cần thiết tại Phân khu Tòa án Manhattan. Thành viên được chấp thuận sẽ chia quỹ 28 triệu USD theo số lần khám xét đủ điều kiện."},
        "highland-health-systems-data-2026": {"title": "Thỏa thuận về vụ rò rỉ dữ liệu của Highland Health Systems", "eligibility": "Cư dân Hoa Kỳ có thông tin riêng tư bị tiết lộ cho bên không được phép trong vụ rò rỉ dữ liệu của Highland Health Systems được phát hiện vào khoảng ngày 3 tháng 7 năm 2023.", "eligibilityBullets": ["Cư trú tại Hoa Kỳ", "Thông tin riêng tư bị tiết lộ trong vụ rò rỉ dữ liệu của Highland Health", "Vụ việc được phát hiện vào khoảng ngày 3 tháng 7 năm 2023"], "proofDetails": "Trang web chính thức cung cấp biểu mẫu có thể nộp mà không cần ID đăng nhập hoặc mã PIN. Khoản tiền mặt thay thế ước tính 85 USD không yêu cầu chứng từ; chỉ lựa chọn riêng về tổn thất tối đa 5.000 USD mới cần hồ sơ.", "summary": "Highland Health Systems đồng ý trả 650.000 USD để giải quyết các khiếu nại liên quan đến cuộc tấn công mạng năm 2023 bị cáo buộc làm lộ thông tin cá nhân và y tế. Thành viên có thể chọn khoản tiền mặt ước tính 85 USD không cần chứng từ, hoặc yêu cầu tối đa 5.000 USD cho tổn thất có chứng từ cùng dịch vụ giám sát."},
        "amn-healthcare-cipa-2026": {"title": "Thỏa thuận về việc ghi âm phiên dịch của AMN Healthcare", "eligibility": "Những người có mặt tại California và tham gia cuộc trò chuyện có phiên dịch của AMN từ ngày 4 tháng 12 năm 2022 đến ngày 7 tháng 8 năm 2026, trong đó AMN bị cáo buộc đã theo dõi, nghe hoặc ghi âm mà không có sự đồng ý trước.", "eligibilityBullets": ["Có mặt tại California", "Tham gia cuộc trò chuyện có phiên dịch của AMN từ ngày 4 tháng 12 năm 2022 đến ngày 7 tháng 8 năm 2026", "Cuộc trò chuyện bị cáo buộc đã bị theo dõi, nghe hoặc ghi âm mà không có sự đồng ý trước"], "proofDetails": "Người yêu cầu phải cung cấp đủ thông tin để xác định phiên phiên dịch và xác nhận mình đủ điều kiện. Có thể đăng ký mà không cần ID, nhưng yêu cầu sẽ được đối chiếu với hồ sơ phiên của AMN.", "summary": "AMN Healthcare đồng ý giải quyết các cáo buộc rằng một số phiên dịch tại California đã bị theo dõi hoặc ghi âm mà không có sự đồng ý trước. Người yêu cầu được chấp thuận sẽ chia quỹ ròng 4,5 triệu USD theo tỷ lệ, tối đa 10.000 USD mỗi người."},
        "high5-games-washington-2026": {"title": "Thỏa thuận High 5 Games về việc mua xu ảo tại Washington", "eligibility": "Những người đã mua xu ảo trong High 5 Casino hoặc High 5 Vegas tại Washington hoặc có liên quan đến Washington từ ngày 9 tháng 4 năm 2014 đến ngày 30 tháng 9 năm 2022.", "eligibilityBullets": ["Đã mua xu ảo trong High 5 Casino hoặc High 5 Vegas", "Giao dịch mua được thực hiện tại Washington hoặc có liên quan đến Washington", "Giao dịch mua diễn ra từ ngày 9 tháng 4 năm 2014 đến ngày 30 tháng 9 năm 2022"], "proofDetails": "Có thể bỏ qua ID duy nhất và không cần biên lai, nhưng tư cách đủ điều kiện và số tiền được nhận sẽ được xác định từ tài khoản High 5 và hồ sơ mua xu ảo của người yêu cầu.", "summary": "High 5 Games đồng ý giải quyết các khiếu nại về tổn thất cờ bạc tại Washington liên quan đến việc mua xu ảo. Người yêu cầu được chấp thuận sẽ nhận phần quỹ dàn xếp được tài trợ trong nhiều năm, phân bổ theo các giao dịch mua đủ điều kiện."},
        "sugared-bronzed-tcpa-2026": {"title": "Thỏa thuận Sugared + Bronzed về tin nhắn tiếp thị", "eligibility": "Những người có số điện thoại di động nhận từ hai tin nhắn tiếp thị trở lên của Sugared + Bronzed qua Klaviyo trong vòng 12 tháng sau khi yêu cầu hủy đăng ký, từ ngày 14 tháng 8 năm 2020 đến ngày 17 tháng 7 năm 2026.", "eligibilityBullets": ["Nhận từ hai tin nhắn tiếp thị trở lên của Sugared + Bronzed trong vòng 12 tháng", "Tin nhắn được gửi sau khi có yêu cầu hủy đăng ký hoặc dừng", "Tin nhắn được gửi từ ngày 14 tháng 8 năm 2020 đến ngày 17 tháng 7 năm 2026"], "proofDetails": "Trang yêu cầu cho phép nộp mà không cần ID đăng nhập hoặc mã PIN, nhưng số điện thoại di động phải khớp với hồ sơ của Sugared + Bronzed và Klaviyo về các tin nhắn đủ điều kiện và yêu cầu dừng.", "summary": "Sugared + Bronzed đồng ý giải quyết cáo buộc rằng công ty tiếp tục gửi tin nhắn tiếp thị sau khi người nhận yêu cầu dừng. Người yêu cầu được chấp thuận sẽ chia quỹ ròng 750.000 USD; khoản thanh toán ước tính từ 110 đến 222 USD."},
    },
    "fil": {
        "nyc-doc-strip-search-2026": {"title": "Kasunduan sa Paulit-ulit na Strip Search ng NYC DOC", "eligibility": "Mga taong nasa kustodiya ng New York City Department of Correction at sumailalim sa kwalipikadong paulit-ulit na strip search sa Manhattan Court Division: mula Marso 28, 2020 hanggang Pebrero 29, 2024 kung inuri bilang Enhanced Security, o mula Oktubre 1, 2022 hanggang Pebrero 29, 2024 para sa lahat ng iba pa.", "eligibilityBullets": ["Nasa kustodiya ng NYC DOC mula Marso 28, 2020 hanggang Pebrero 29, 2024 kung inuri bilang Enhanced Security, o mula Oktubre 1, 2022 hanggang Pebrero 29, 2024 para sa lahat ng iba pa", "Hinanap sa Manhattan Court Division matapos ang naunang search bago umalis sa Rikers Island", "Kasama sa opisyal na listahan ng settlement class"], "proofDetails": "Hindi kailangan ng resibo o notice ID, pero ibe-verify ang eligibility at bilang ng mga kwalipikadong search gamit ang pagkakakilanlan ng claimant at ang opisyal na records ng DOC.", "summary": "Sumang-ayon ang New York City na ayusin ang mga claim na ang mga nasa kustodiya ng DOC ay sumailalim sa hindi kinakailangang paulit-ulit na strip search sa Manhattan Court Division. Hahatiin ng mga aprubadong class member ang $28 milyon na pondo batay sa bilang ng mga kwalipikadong search."},
        "highland-health-systems-data-2026": {"title": "Kasunduan sa Data Breach ng Highland Health Systems", "eligibility": "Mga residente ng United States na nalantad sa mga hindi awtorisadong partido ang pribadong impormasyon dahil sa data breach ng Highland Health Systems na natuklasan noong o bandang Hulyo 3, 2023.", "eligibilityBullets": ["Nakatira sa United States", "Nalantad ang pribadong impormasyon sa data breach ng Highland Health", "Natuklasan ang breach noong o bandang Hulyo 3, 2023"], "proofDetails": "May claim form sa opisyal na site na maaaring isumite nang walang Login ID o PIN. Hindi kailangan ng dokumento para sa tinatayang $85 na alternatibong cash; ang hiwalay na opsyon na hanggang $5,000 para sa pagkalugi lamang ang nangangailangan ng records.", "summary": "Sumang-ayon ang Highland Health Systems sa $650,000 na settlement matapos ang isang cyberattack noong 2023 na sinasabing naglantad ng personal at medikal na impormasyon. Maaaring piliin ng mga class member ang tinatayang $85 cash na walang kailangang dokumento, o humiling ng hanggang $5,000 para sa dokumentadong pagkalugi at monitoring."},
        "amn-healthcare-cipa-2026": {"title": "Kasunduan sa Pag-record ng Interpretation ng AMN Healthcare", "eligibility": "Mga taong pisikal na nasa California at lumahok sa usapang may AMN interpreter mula Disyembre 4, 2022 hanggang Agosto 7, 2026, na sinasabing minonitor, pinakinggan, o ni-record ng AMN nang walang paunang pahintulot.", "eligibilityBullets": ["Pisikal na nasa California", "Lumahok sa usapang may AMN interpreter mula Disyembre 4, 2022 hanggang Agosto 7, 2026", "Sinasabing minonitor, pinakinggan, o ni-record ang usapan nang walang paunang pahintulot"], "proofDetails": "Kailangang magbigay ang claimant ng sapat na detalye para matukoy ang interpretation session at patunayang kwalipikado siya. Maaaring mag-register nang walang ID, pero ibe-verify ang claim gamit ang session records ng AMN.", "summary": "Sumang-ayon ang AMN Healthcare na ayusin ang mga alegasyong minonitor o ni-record nang walang paunang pahintulot ang ilang interpretation session sa California. Hahatiin nang pro rata ng mga aprubadong claimant ang netong $4.5 milyon na pondo, hanggang $10,000 bawat isa."},
        "high5-games-washington-2026": {"title": "Kasunduan ng High 5 Games sa Pagbili ng Virtual Coin sa Washington", "eligibility": "Mga taong bumili ng virtual coin sa High 5 Casino o High 5 Vegas sa Washington o kaugnay ng Washington mula Abril 9, 2014 hanggang Setyembre 30, 2022.", "eligibilityBullets": ["Bumili ng virtual coin sa High 5 Casino o High 5 Vegas", "Ginawa ang pagbili sa Washington o kaugnay ng Washington", "Ginawa ang pagbili mula Abril 9, 2014 hanggang Setyembre 30, 2022"], "proofDetails": "Maaaring laktawan ang Unique ID at hindi hinihingi ang resibo, pero tutukuyin ang eligibility at award mula sa High 5 account at virtual-coin purchase records ng claimant.", "summary": "Sumang-ayon ang High 5 Games na ayusin ang mga claim sa pagkalugi sa pagsusugal sa Washington na may kaugnayan sa pagbili ng virtual coin. Makakatanggap ang mga aprubadong claimant ng bahagi ng settlement na popondohan sa loob ng ilang taon at hahatiin ayon sa mga kwalipikadong pagbili."},
        "sugared-bronzed-tcpa-2026": {"title": "Kasunduan ng Sugared + Bronzed sa mga Marketing Text", "eligibility": "Mga taong nakatanggap sa kanilang mobile number ng dalawa o higit pang marketing text mula sa Sugared + Bronzed sa pamamagitan ng Klaviyo sa loob ng 12 buwan matapos humiling na mag-opt out, mula Agosto 14, 2020 hanggang Hulyo 17, 2026.", "eligibilityBullets": ["Nakatanggap ng dalawa o higit pang marketing text mula sa Sugared + Bronzed sa loob ng 12 buwan", "Dumating ang mga text matapos ang opt-out o stop request", "Ipinadala ang mga text mula Agosto 14, 2020 hanggang Hulyo 17, 2026"], "proofDetails": "Maaaring magsumite sa claim site nang walang Login ID o PIN, pero kailangang tumugma ang mobile number sa records ng Sugared + Bronzed at Klaviyo na nagpapakita ng mga kwalipikadong mensahe at stop request.", "summary": "Sumang-ayon ang Sugared + Bronzed na ayusin ang alegasyong nagpadala ito ng marketing text kahit humiling nang tumigil ang mga recipient. Hahatiin ng mga aprubadong claimant ang netong $750,000 na pondo; tinatayang $110 hanggang $222 ang bawat bayad."},
    },
}


# Precise repairs for fields where the baseline changed a numeric fact.
FACT_REPAIRS = {
    "es": {
        "mdi-tdi-dow-huntsman-antitrust-2026": {"eligibilityBullets": ["Compraron directamente productos MDI o TDI elegibles", "Compraron a Dow, Huntsman u otro fabricante incluido en el grupo del acuerdo", "La compra se realizó en Estados Unidos, sus territorios o el Distrito de Columbia entre el 1 de enero de 2016 y el 29 de julio de 2026"]},
        "mdi-tdi-basf-covestro-antitrust-2026": {"eligibilityBullets": ["Compraron directamente productos MDI o TDI elegibles", "Compraron a BASF, Covestro u otro fabricante incluido en el grupo del acuerdo", "La compra se realizó en Estados Unidos, sus territorios o el Distrito de Columbia entre el 1 de enero de 2016 y el 29 de julio de 2026"]},
    },
    "zh-Hans": {},
    "vi": {
        "mdi-tdi-dow-huntsman-antitrust-2026": {"eligibilityBullets": ["Đã mua trực tiếp sản phẩm MDI hoặc TDI đủ điều kiện", "Mua từ Dow, Huntsman hoặc nhà sản xuất khác thuộc tập thể dàn xếp", "Giao dịch mua diễn ra tại Hoa Kỳ, các vùng lãnh thổ của Hoa Kỳ hoặc Đặc khu Columbia từ ngày 1 tháng 1 năm 2016 đến ngày 29 tháng 7 năm 2026"]},
        "mdi-tdi-basf-covestro-antitrust-2026": {"eligibilityBullets": ["Đã mua trực tiếp sản phẩm MDI hoặc TDI đủ điều kiện", "Mua từ BASF, Covestro hoặc nhà sản xuất khác thuộc tập thể dàn xếp", "Giao dịch mua diễn ra tại Hoa Kỳ, các vùng lãnh thổ của Hoa Kỳ hoặc Đặc khu Columbia từ ngày 1 tháng 1 năm 2016 đến ngày 29 tháng 7 năm 2026"]},
    },
    "fil": {
        "mdi-tdi-wanhua-antitrust-2026": {"eligibility": "Mga indibidwal at entity na direktang bumili ng kwalipikadong MDI o TDI product sa United States, mga teritoryo nito, o District of Columbia mula Enero 1, 2016 hanggang Hulyo 29, 2026.", "eligibilityBullets": ["Direktang bumili ng kwalipikadong MDI o TDI product", "Bumili mula sa Wanhua o ibang manufacturer na saklaw ng settlement class", "Ginawa ang pagbili sa United States, mga teritoryo nito, o District of Columbia mula Enero 1, 2016 hanggang Hulyo 29, 2026"]},
        "mdi-tdi-dow-huntsman-antitrust-2026": {"eligibility": "Mga indibidwal at entity na direktang bumili ng kwalipikadong MDI o TDI product sa United States, mga teritoryo nito, o District of Columbia mula Enero 1, 2016 hanggang Hulyo 29, 2026.", "eligibilityBullets": ["Direktang bumili ng kwalipikadong MDI o TDI product", "Bumili mula sa Dow, Huntsman, o ibang manufacturer na saklaw ng settlement class", "Ginawa ang pagbili sa United States, mga teritoryo nito, o District of Columbia mula Enero 1, 2016 hanggang Hulyo 29, 2026"], "proofDetails": "Kailangan ang Class Member ID mula sa settlement notice para magsumite ng claim. Maaari ring hingin ang purchase records para magdagdag o magwasto ng mga pagbili sa records ng administrator."},
        "mdi-tdi-basf-covestro-antitrust-2026": {"eligibility": "Mga indibidwal at entity na direktang bumili ng kwalipikadong MDI o TDI product sa United States, mga teritoryo nito, o District of Columbia mula Enero 1, 2016 hanggang Hulyo 29, 2026.", "eligibilityBullets": ["Direktang bumili ng kwalipikadong MDI o TDI product", "Bumili mula sa BASF, Covestro, o ibang manufacturer na saklaw ng settlement class", "Ginawa ang pagbili sa United States, mga teritoryo nito, o District of Columbia mula Enero 1, 2016 hanggang Hulyo 29, 2026"], "proofDetails": "Kailangan ang Class Member ID mula sa settlement notice para magsumite ng claim. Maaari ring hingin ang purchase records para magdagdag o magwasto ng mga pagbili sa records ng administrator."},
        "schnucks-rewards-tax-2026": {"eligibility": "Kasalukuyan o dating miyembro ng Schnucks Rewards na gumamit ng points sa mga kwalipikadong personal, pampamilya, o pambahay na pagbili sa Missouri Schnucks stores mula Mayo 2, 2020 hanggang Agosto 7, 2026.", "eligibilityBullets": ["Kasalukuyan o dating miyembro ng Schnucks Rewards", "Gumamit ng points sa mga personal, pampamilya, o pambahay na pagbiling may sales tax", "Ginawa ang pagbili sa isang Missouri Schnucks store mula Mayo 2, 2020 hanggang Agosto 7, 2026"]},
        "vasindas-data-2026": {"eligibility": "Mga residente ng United States na posibleng naapektuhan ang personal na impormasyon ng insidente sa Around the Clock Care mula Enero 30 hanggang Hunyo 18, 2024."},
        "covenant-transport-job-posting-2026": {"eligibility": "Mga taong nag-apply online para sa team-driver position ng Covenant Transport na matatagpuan sa Washington mula Enero 1, 2023 hanggang Hunyo 17, 2024.", "eligibilityBullets": ["Nag-apply online sa Covenant Transport", "Nag-apply para sa team-driver position na matatagpuan sa Washington", "Nag-apply mula Enero 1, 2023 hanggang Hunyo 17, 2024"]},
        "wayne-memorial-hospital-data-2026": {"eligibility": "Mga taong posibleng nakompromiso ang personal na impormasyon sa data incident ng Wayne Memorial Hospital na nangyari mula Mayo 30 hanggang Hunyo 3, 2024."},
        "peco-foods-data-2026": {"eligibility": "Mga residente ng United States na nakatanggap ng nakasulat na notice na maaaring nakompromiso ang kanilang personal na impormasyon sa data incident ng Peco Foods noong o bandang Disyembre 4, 2023."},
        "raging-waters-fee-2026": {"eligibilityBullets": ["Nakatira sa United States", "Bumili ng admission ticket mula sa RagingWaters.com", "Nagbayad ng processing fee mula Hunyo 1, 2020 hanggang Hunyo 22, 2026"]},
    },
}


FILIPINO_TITLES = {
    "mdi-tdi-wanhua-antitrust-2026": "Kasunduan sa Antitrust ng Wanhua MDI at TDI",
    "mdi-tdi-dow-huntsman-antitrust-2026": "Mga Kasunduan sa Antitrust ng Dow at Huntsman MDI at TDI",
    "mdi-tdi-basf-covestro-antitrust-2026": "Mga Kasunduan sa Antitrust ng BASF at Covestro MDI at TDI",
    "cpap-medical-data-incident-2026": "Kasunduan sa Data Incident ng CPAP Medical Supplies",
    "concora-credit-tcpa-2026": "Kasunduan sa mga Prerecorded Call ng Concora Credit",
    "fujifilm-diosynth-data-2026": "Kasunduan sa Data Incident ng Fujifilm Diosynth",
    "la-jolla-group-data-2026": "Kasunduan sa Employee Data ng La Jolla Group",
    "schnucks-rewards-tax-2026": "Kasunduan sa Sales Tax ng Schnucks Rewards",
    "vasindas-data-2026": "Kasunduan sa Data ng Vasindas' Around the Clock Care",
    "autobell-data-2026": "Kasunduan sa Data Incident ng Autobell Car Wash",
    "carter-credit-union-data-2026": "Kasunduan sa Data Incident ng Carter Credit Union",
    "southern-graphics-data-2026": "Kasunduan sa Data Incident ng Southern Graphics",
    "twist-bioscience-securities-2026": "Kasunduan sa Securities ng Twist Bioscience",
    "covenant-transport-job-posting-2026": "Kasunduan para sa mga Job Applicant ng Covenant Transport sa Washington",
    "wayne-memorial-hospital-data-2026": "Kasunduan sa Data Incident ng Wayne Memorial Hospital",
    "international-shoppes-data-2026": "Kasunduan sa Data Incident ng International Shoppes",
    "levoit-air-purifier-2026": "Kasunduan sa Marketing ng Levoit Air Purifier",
    "wpm-salina-data-2026": "Kasunduan sa Data ng WPM Pathology at Salina Regional",
    "onetouchpoint-data-2026": "Kasunduan sa Data Incident ng OneTouchPoint",
    "peco-foods-data-2026": "Kasunduan sa Data Incident ng Peco Foods",
    "regional-urology-data-2026": "Kasunduan sa Data ng Regional Urology at Ochsner LSU",
    "mental-health-association-data-2026": "Kasunduan sa Data Breach ng Mental Health Association",
    "california-casualty-data-2026": "Kasunduan sa Data Incident ng California Casualty",
    "furniture-mart-usa-data-2026": "Kasunduan sa Data Breach ng Furniture Mart USA",
    "summit-medical-data-2026": "Kasunduan sa Data Incident ng Summit Medical Group",
    "raging-waters-fee-2026": "Kasunduan sa Processing Fee ng Raging Waters",
    "mortgage-investors-group-data-2026": "Kasunduan sa Data Incident ng Mortgage Investors Group",
}


FILIPINO_DETAILS = {
    "cpap-medical-data-incident-2026": {
        "eligibility": "Mga residente ng United States na nakatanggap ng notice na maaaring naapektuhan ng data incident ng CPAP Medical noong Disyembre 2024 ang kanilang pribadong impormasyon.",
        "proofDetails": "Para sa cash reimbursement, kailangan ng mga record gaya ng resibo, bank statement, o ibang dokumento ng pagkaluging maiuugnay sa insidente. Kailangan din sa online filing ang Login ID at PIN mula sa settlement notice.",
    },
    "concora-credit-tcpa-2026": {
        "eligibility": "Mga tao sa United States na nakatanggap sa cellphone ng artificial o prerecorded-voice call mula sa Concora Credit mula Mayo 2, 2021 hanggang Mayo 31, 2026, kung ang numero ay hindi nakatalaga sa isang Concora accountholder.",
        "proofDetails": "Kailangang gamitin ng mga nakatanggap ng notice ang kanilang personalized claim credentials. Kung walang notice, kailangang humiling ng form at magbigay ng ebidensyang nakatanggap ang cellphone ng kwalipikadong prerecorded call.",
    },
    "fujifilm-diosynth-data-2026": {
        "eligibility": "Mga taong nakatanggap ng notice na maaaring naapektuhan ng data incident ng Fujifilm Diosynth noong 2025 ang kanilang pribadong impormasyon.",
        "proofDetails": "Kailangan sa karaniwang online claim ang Login ID at PIN mula sa settlement notice. Kailangan din ng makatwirang dokumento para sa opsyong hanggang $2,500; hindi kailangan ng proof of loss para sa alternatibong $50.",
    },
    "la-jolla-group-data-2026": {
        "eligibility": "Kasalukuyan at dating empleyado ng La Jolla Group sa United States na naapektuhan ng cybersecurity incident noong Nobyembre 2023 ang personal na impormasyon.",
        "proofDetails": "Kailangan sa opisyal na claim form ang Class Member ID at PIN mula sa settlement notice. Kailangan din ng third-party records para sa documented-loss claim; $95 ang alternatibong cash para sa mga residente ng California at $45 para sa ibang class member.",
    },
    "schnucks-rewards-tax-2026": {
        "proofDetails": "Kailangan sa online filing ang Access Code at PIN mula sa postcard notice. May paper option kung walang postcard, pero kailangang magbigay ng account information at ibe-verify ang eligibility sa Schnucks Rewards records.",
    },
    "vasindas-data-2026": {
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng supporting records para sa opsyong hanggang $2,500; hindi kailangan ng proof of loss para sa alternatibong $70 cash.",
    },
    "autobell-data-2026": {
        "eligibility": "Mga residente ng United States na nakatanggap ng notice na naapektuhan ng data incident ng Autobell noong Abril 2024 ang kanilang personal na impormasyon.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Unique ID at PIN mula sa notice. Kailangan ng supporting records para sa loss claim; hindi kailangan ng proof of loss para sa alternatibong $45 cash.",
    },
    "carter-credit-union-data-2026": {
        "eligibility": "Mga taong nakompromiso ang personally identifiable information sa data incident ng Carter Credit Union na nagsimula noong o bandang Hunyo 25, 2025.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng supporting records para sa opsyong hanggang $2,500; hindi kailangan ng proof of loss para sa alternatibong $50 cash.",
    },
    "southern-graphics-data-2026": {
        "eligibility": "Mga taong nakatanggap ng notice na maaaring nakompromiso ng data incident ng Southern Graphics noong Disyembre 2024 ang kanilang pribadong impormasyon.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng supporting records para sa documented-loss claim; hindi kailangan ng proof of loss para sa alternatibong pro rata cash.",
    },
    "twist-bioscience-securities-2026": {
        "eligibility": "Mga tao at entity na kumuha ng common stock ng Twist Bioscience sa offering noong Disyembre 2020 o mula Disyembre 20, 2018 hanggang Nobyembre 15, 2022 at nagkaroon ng kinikilalang pagkalugi.",
        "proofDetails": "Kailangang magbigay ng broker confirmation, account statement, o ibang record na nagpapakita ng pagbili, pagbenta, at paghawak ng Twist stock.",
    },
    "covenant-transport-job-posting-2026": {
        "proofDetails": "Ibe-verify ang eligibility gamit ang job-application records ng Covenant. Maaaring gumamit ang online filing ng personalized CPT credentials; kailangan sa paper form ang pagkakakilanlan at detalye ng application.",
    },
    "wayne-memorial-hospital-data-2026": {
        "proofDetails": "Kailangan ang Unique ID mula sa settlement notice para sa bawat cash claim, at kailangan din ng notice passcode para sa online filing. Kailangan ng supporting documents para sa opsyong hanggang $5,000.",
    },
    "international-shoppes-data-2026": {
        "eligibility": "Mga taong nakompromiso ang personal na impormasyon sa data incident noong Nobyembre 2023 na kinasangkutan ng International Shoppes o Diplomatic Duty Free Shops of New York.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng dokumento para sa opsyong hanggang $4,000; hindi kailangan ng proof of loss para sa alternatibong $50 cash.",
    },
    "levoit-air-purifier-2026": {
        "eligibility": "Mga taong bumili sa United States ng kwalipikadong Levoit Core o EverestAir air purifier o replacement filter na may True HEPA, HEPA, o H13 marketing mula Agosto 29, 2019 hanggang Agosto 4, 2023.",
        "proofDetails": "Kailangan ng patunay ng petsa ng orihinal na kwalipikadong pagbili. Makakatanggap ng $10 digital payment ang mga aprubadong claim.",
    },
    "wpm-salina-data-2026": {
        "eligibility": "Mga taong nakompromiso ang pribadong impormasyon sa data incident noong Nobyembre 2024 na kinasangkutan ng WPM Pathology Laboratory o Salina Regional Health Center, kabilang ang mga direktang inabisuhan ng mga defendant.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Notice ID at PIN. Kailangan ng supporting documents para sa loss claim at paliwanag para sa lost-time claim; hindi kailangan ng proof of loss para sa alternatibong $45 cash.",
    },
    "onetouchpoint-data-2026": {
        "eligibility": "Mga tao sa United States na natukoy sa imbestigasyon ng OneTouchPoint na naapektuhan ng data incident noong Abril 2022 ang kanilang pribadong impormasyon.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Claim Number at PIN mula sa notice. Kailangan ng dokumento para sa loss claim at paliwanag para sa lost-time claim; hindi kailangan ng proof of loss para sa alternatibong $75 cash.",
    },
    "peco-foods-data-2026": {
        "proofDetails": "Kailangan sa karaniwang online filing ang Claim ID mula sa settlement notice. Kailangan ng dokumento para sa ordinary at extraordinary loss, at paliwanag para sa lost time; hindi kailangan ng proof of loss para sa residual cash.",
    },
    "regional-urology-data-2026": {
        "eligibility": "Mga residente ng United States na maaaring nakompromiso ang pribadong impormasyon sa data incident noong Oktubre 2025 na kinasangkutan ng Regional Urology at Ochsner LSU Health.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng supporting documents para sa opsyong hanggang $5,000; hindi kailangan ng proof of loss para sa alternatibong $40 cash.",
    },
    "mental-health-association-data-2026": {
        "eligibility": "Mga taong naa-access ang pribadong impormasyon sa cyberattack sa Mental Health Association noong Nobyembre 2024, kabilang ang mga natukoy na taong nakatanggap ng notice.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng records para sa documented loss at paliwanag para sa lost time; hindi kailangan ng proof of loss para sa alternatibong $40 cash.",
    },
    "california-casualty-data-2026": {
        "eligibility": "Mga residente ng United States na naapektuhan ang personally identifiable information sa data incident ng California Casualty na natuklasan noong Setyembre 2025.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa settlement notice. Kailangan ng supporting documents para sa opsyong hanggang $4,000; hindi kailangan ng proof of loss para sa alternatibong $50 cash.",
    },
    "furniture-mart-usa-data-2026": {
        "eligibility": "Mga residente ng United States na maaaring nakompromiso ang personal na impormasyon sa data breach ng Furniture Mart USA noong Nobyembre 2024.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng supporting records para sa loss claim at paliwanag para sa lost time; hindi kailangan ng proof of loss para sa alternatibong $75 cash.",
    },
    "summit-medical-data-2026": {
        "eligibility": "Mga nabubuhay na residente ng United States na maaaring nakompromiso ang pribadong impormasyon sa cyberattack sa Summit Medical Group noong Setyembre 2024.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa notice. Kailangan ng dokumento para sa opsyong hanggang $2,500; kailangan ng certification at paliwanag para sa hiwalay na lost-time option na limitado sa $45.",
    },
    "raging-waters-fee-2026": {
        "eligibility": "Mga residente ng United States na bumili ng admission ticket sa RagingWaters.com mula Hunyo 1, 2020 hanggang Hunyo 22, 2026 at nagbayad ng processing fee.",
        "proofDetails": "Kailangan sa karaniwang online filing ang ID at confirmation code mula sa settlement notice. Kailangang patunayan ng claimant na gumawa siya ng kwalipikadong pagbili at nagbayad ng processing fee; ibe-verify ang bayad gamit ang available transaction records.",
    },
    "mortgage-investors-group-data-2026": {
        "eligibility": "Mga taong maaaring nalantad ang sensitibong impormasyon sa data incident ng Mortgage Investors Group noong Disyembre 2024.",
        "proofDetails": "Kailangan sa karaniwang online filing ang Login ID at PIN mula sa settlement notice. Kailangan ng supporting documents para sa opsyong hanggang $2,000; hindi kailangan ng proof of loss para sa alternatibong $45 cash.",
    },
}


def clean_spacing(value):
    if isinstance(value, list):
        return [clean_spacing(item) for item in value]
    if not isinstance(value, str):
        return value
    value = re.sub(r"\.(?=[A-ZÁÉÍÓÚÜÑĐA-Z])", ". ", value)
    value = re.sub(r";(?=\S)", "; ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def main() -> int:
    source = json.loads((ROOT / "settlements.json").read_text())
    english = {record["id"]: record for record in source}
    for language in LANGUAGES:
        path = ROOT / f"settlements.{language}.json"
        records = json.loads(path.read_text())
        by_id = {record["id"]: record for record in records}
        for record_id, record in by_id.items():
            if record.get("dateAdded") != "2026-09-13":
                continue
            original = english[record_id]
            record["totalAmount"] = TOTALS[language].get(
                original.get("totalAmount"), record.get("totalAmount")
            )
            record["individualPayout"] = PAYOUTS[language].get(
                original.get("individualPayout"), record.get("individualPayout")
            )
            for field in ("title", "eligibility", "eligibilityBullets", "proofDetails", "summary"):
                record[field] = clean_spacing(record.get(field))
                if language == "zh-Hans":
                    if isinstance(record[field], list):
                        record[field] = [item.replace("结算", "和解").replace("定居", "和解") for item in record[field]]
                    elif isinstance(record[field], str):
                        record[field] = record[field].replace("结算", "和解").replace("定居", "和解")
        for record_id, fields in FACT_REPAIRS[language].items():
            by_id[record_id].update(fields)
        for record_id, fields in CRITICAL[language].items():
            by_id[record_id].update(fields)
        if language == "fil":
            for record_id, title in FILIPINO_TITLES.items():
                by_id[record_id]["title"] = title
            for record_id, fields in FILIPINO_DETAILS.items():
                by_id[record_id].update(fields)
        if language == "es":
            by_id["vasindas-data-2026"]["title"] = (
                "Acuerdo por datos de Vasindas' Around the Clock Care"
            )
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
        print(f"Applied September 2026 review overrides to {language}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
