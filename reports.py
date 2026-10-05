"""Date-filtered transaction summaries and CSV export."""

import csv
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from database import DEFAULT_DATABASE_PATH, connect, initialize_database


def _validate_dates(start_date: str, end_date: str) -> None:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except (TypeError, ValueError):
        raise ValueError("Dates must use YYYY-MM-DD format.") from None
    if end < start:
        raise ValueError("End date must be on or after start date.")


def get_report(
    business_id: int,
    start_date: str,
    end_date: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict:
    _validate_dates(start_date, end_date)
    # Report dates follow the machine's local calendar, while storage stays UTC.
    start_utc = datetime.combine(date.fromisoformat(start_date), time.min).astimezone(timezone.utc)
    end_utc = datetime.combine(
        date.fromisoformat(end_date) + timedelta(days=1), time.min
    ).astimezone(timezone.utc)
    start_bound = start_utc.isoformat(timespec="seconds")
    end_bound = end_utc.isoformat(timespec="seconds")
    initialize_database(database_path)
    with connect(database_path) as connection:
        totals = connection.execute(
            """SELECT COUNT(*) AS transaction_count,
                      COALESCE(SUM(amount_minor), 0) AS revenue_minor,
                      COALESCE(SUM(CASE WHEN payment_type = 'Cash' THEN amount_minor ELSE 0 END), 0)
                          AS cash_minor,
                      COALESCE(SUM(CASE WHEN payment_type = 'Online' THEN amount_minor ELSE 0 END), 0)
                          AS online_minor
               FROM transactions
               WHERE business_id = ? AND created_at >= ? AND created_at < ?""",
            (business_id, start_bound, end_bound),
        ).fetchone()
        service_rows = connection.execute(
            """SELECT service_name, COUNT(*) AS transaction_count,
                      COALESCE(SUM(amount_minor), 0) AS revenue_minor
               FROM transactions
               WHERE business_id = ? AND created_at >= ? AND created_at < ?
               GROUP BY service_name COLLATE NOCASE
               ORDER BY revenue_minor DESC, service_name COLLATE NOCASE""",
            (business_id, start_bound, end_bound),
        ).fetchall()
    return {
        "start_date": start_date,
        "end_date": end_date,
        **dict(totals),
        "services": [dict(row) for row in service_rows],
    }


def export_report_csv(
    report: dict, output_path: str | Path
) -> Path:
    """Write a compact report summary and service-wise breakdown to CSV."""
    path = Path(output_path)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Business Manager Report"])
        writer.writerow(["Start date", report["start_date"]])
        writer.writerow(["End date", report["end_date"]])
        writer.writerow([])
        writer.writerow(["Summary", "Value"])
        writer.writerow(["Total transactions", report["transaction_count"]])
        writer.writerow(["Total revenue", f"{Decimal(report['revenue_minor']) / 100:.2f}"])
        writer.writerow(["Cash revenue", f"{Decimal(report['cash_minor']) / 100:.2f}"])
        writer.writerow(["Online revenue", f"{Decimal(report['online_minor']) / 100:.2f}"])
        writer.writerow([])
        writer.writerow(["Service", "Transactions", "Revenue"])
        for service in report["services"]:
            writer.writerow([
                service["service_name"], service["transaction_count"],
                f"{Decimal(service['revenue_minor']) / 100:.2f}",
            ])
    return path


def export_report_xlsx(report: dict, output_path: str | Path) -> Path:
    """Create a formatted Excel workbook using only Python's standard library."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    pkg_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    content_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    ET.register_namespace("", main_ns)
    ET.register_namespace("r", rel_ns)

    def tag(namespace: str, local: str) -> str:
        return f"{{{namespace}}}{local}"

    def cell(row, reference: str, value, style: int = 0, numeric: bool = False):
        attrs = {"r": reference}
        if style:
            attrs["s"] = str(style)
        item = ET.SubElement(row, tag(main_ns, "c"), attrs)
        if numeric:
            item.set("t", "n")
            ET.SubElement(item, tag(main_ns, "v")).text = str(value)
        else:
            item.set("t", "inlineStr")
            inline = ET.SubElement(item, tag(main_ns, "is"))
            ET.SubElement(inline, tag(main_ns, "t")).text = str(value)
        return item

    sheet = ET.Element(tag(main_ns, "worksheet"))
    ET.SubElement(sheet, tag(main_ns, "dimension"), {"ref": f"A1:C{12 + len(report['services'])}"})
    views = ET.SubElement(sheet, tag(main_ns, "sheetViews"))
    view = ET.SubElement(views, tag(main_ns, "sheetView"), {"workbookViewId": "0", "showGridLines": "0"})
    ET.SubElement(view, tag(main_ns, "pane"), {
        "ySplit": "12", "topLeftCell": "A13", "activePane": "bottomLeft", "state": "frozen"
    })
    ET.SubElement(view, tag(main_ns, "selection"), {"pane": "bottomLeft", "activeCell": "A13", "sqref": "A13"})
    cols = ET.SubElement(sheet, tag(main_ns, "cols"))
    for index, width in ((1, 38), (2, 21), (3, 22)):
        ET.SubElement(cols, tag(main_ns, "col"), {"min": str(index), "max": str(index), "width": str(width), "customWidth": "1"})
    data = ET.SubElement(sheet, tag(main_ns, "sheetData"))

    row = ET.SubElement(data, tag(main_ns, "row"), {"r": "1", "ht": "34", "customHeight": "1"})
    cell(row, "A1", "Business Manager  |  Report", 1)
    row = ET.SubElement(data, tag(main_ns, "row"), {"r": "2", "ht": "25", "customHeight": "1"})
    cell(row, "A2", "Reporting period", 5)
    cell(row, "B2", f"{report['start_date']}  to  {report['end_date']}", 2)
    row = ET.SubElement(data, tag(main_ns, "row"), {"r": "4", "ht": "24", "customHeight": "1"})
    cell(row, "A4", "SUMMARY", 3)
    row = ET.SubElement(data, tag(main_ns, "row"), {"r": "5", "ht": "22", "customHeight": "1"})
    cell(row, "A5", "Metric", 4)
    cell(row, "B5", "Value", 4)
    summary = (
        (6, "Total transactions", report["transaction_count"], 7),
        (7, "Total revenue", Decimal(report["revenue_minor"]) / 100, 6),
        (8, "Cash revenue", Decimal(report["cash_minor"]) / 100, 6),
        (9, "Online revenue", Decimal(report["online_minor"]) / 100, 6),
    )
    for row_number, label, value, style_id in summary:
        row = ET.SubElement(data, tag(main_ns, "row"), {"r": str(row_number), "ht": "22", "customHeight": "1"})
        cell(row, f"A{row_number}", label, 5)
        cell(row, f"B{row_number}", value, style_id, numeric=True)
    row = ET.SubElement(data, tag(main_ns, "row"), {"r": "11", "ht": "24", "customHeight": "1"})
    cell(row, "A11", "SERVICE BREAKDOWN", 3)
    row = ET.SubElement(data, tag(main_ns, "row"), {"r": "12", "ht": "24", "customHeight": "1"})
    for reference, heading in (("A12", "Service"), ("B12", "Transactions"), ("C12", "Revenue")):
        cell(row, reference, heading, 4)
    for offset, service in enumerate(report["services"], start=13):
        row = ET.SubElement(data, tag(main_ns, "row"), {"r": str(offset), "ht": "22", "customHeight": "1"})
        cell(row, f"A{offset}", service["service_name"], 5)
        cell(row, f"B{offset}", service["transaction_count"], 7, numeric=True)
        cell(row, f"C{offset}", Decimal(service["revenue_minor"]) / 100, 6, numeric=True)
    auto_filter_end = max(12, 12 + len(report["services"]))
    ET.SubElement(sheet, tag(main_ns, "autoFilter"), {"ref": f"A12:C{auto_filter_end}"})
    merges = ET.SubElement(sheet, tag(main_ns, "mergeCells"), {"count": "3"})
    for cell_range in ("A1:C1", "A4:C4", "A11:C11"):
        ET.SubElement(merges, tag(main_ns, "mergeCell"), {"ref": cell_range})
    ET.SubElement(sheet, tag(main_ns, "pageMargins"), {
        "left": "0.35", "right": "0.35", "top": "0.55", "bottom": "0.55", "header": "0.25", "footer": "0.25"
    })

    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <styleSheet xmlns="{main_ns}">
      <numFmts count="1"><numFmt numFmtId="164" formatCode="&quot;₹&quot;#,##0.00"/></numFmts>
      <fonts count="4">
        <font><sz val="10"/><name val="Aptos"/><color rgb="FF172B4D"/></font>
        <font><b/><sz val="16"/><name val="Aptos Display"/><color rgb="FFFFFFFF"/></font>
        <font><b/><sz val="10"/><name val="Aptos"/><color rgb="FFFFFFFF"/></font>
        <font><b/><sz val="10"/><name val="Aptos"/><color rgb="FF172B4D"/></font>
      </fonts>
      <fills count="4">
        <fill><patternFill patternType="none"/></fill>
        <fill><patternFill patternType="gray125"/></fill>
        <fill><patternFill patternType="solid"><fgColor rgb="FF172B4D"/><bgColor indexed="64"/></patternFill></fill>
        <fill><patternFill patternType="solid"><fgColor rgb="FFE8EEFF"/><bgColor indexed="64"/></patternFill></fill>
      </fills>
      <borders count="2">
        <border><left/><right/><top/><bottom/><diagonal/></border>
        <border><left/><right/><top/><bottom style="thin"><color rgb="FFDCE3EE"/></bottom><diagonal/></border>
      </borders>
      <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
      <cellXfs count="8">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
        <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" indent="1"/></xf>
        <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
        <xf numFmtId="0" fontId="2" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" indent="1"/></xf>
        <xf numFmtId="0" fontId="3" fillId="3" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
        <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
        <xf numFmtId="164" fontId="3" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
        <xf numFmtId="3" fontId="3" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment horizontal="right" vertical="center"/></xf>
      </cellXfs>
      <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
    </styleSheet>'''

    workbook = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <workbook xmlns="{main_ns}" xmlns:r="{rel_ns}">
      <bookViews><workbookView/></bookViews>
      <sheets><sheet name="Business Report" sheetId="1" r:id="rId1"/></sheets>
      <calcPr calcId="191029"/>
    </workbook>'''
    content_types = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="{content_ns}">
      <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
      <Default Extension="xml" ContentType="application/xml"/>
      <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
      <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
      <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
    </Types>'''
    root_rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="{pkg_rel_ns}">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
    </Relationships>'''
    workbook_rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="{pkg_rel_ns}">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
      <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
    </Relationships>'''

    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", styles)
        archive.writestr("xl/worksheets/sheet1.xml", ET.tostring(sheet, encoding="utf-8", xml_declaration=True))
    return path
