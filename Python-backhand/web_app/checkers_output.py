from datetime import date, datetime

from flask import Blueprint, jsonify, render_template, request, url_for

from web_app.auth import login_required
from web_app.data_utils import (
    get_all_po_defect_counts,
    get_po_defect_counts,
    show_checker_output_dashboard,
)

bp = Blueprint("checkers_output", __name__, url_prefix="/checkers-output")


def get_dashboard_filter():
    if request.args.get("view") == "all":
        return None, True

    selected_date = request.args.get("date", "").strip()

    if not selected_date:
        return None, True

    try:
        datetime.strptime(selected_date, "%Y-%m-%d")
    except ValueError:
        return None, True

    return selected_date, False


def get_filter_query_args(selected_date, show_all):
    if show_all:
        return {"view": "all"}
    return {"date": selected_date}


def as_count(value):
    return int(value or 0)


def calculate_total_processed(pass_count, reject_count, alter_count):
    return as_count(pass_count) + as_count(reject_count) + as_count(alter_count)


def calculate_defect_percentage(alter_count, total_processed):
    if not total_processed:
        return 0

    return round((as_count(alter_count) / total_processed) * 100, 2)


def filter_incomplete_po_rows(rows, show_all):
    if not show_all:
        return rows

    return [
        row
        for row in rows
        if as_count(row[3]) < as_count(row[2])
    ]


def build_defect_details_url(po_number, filter_query_args, line_no=None):
    url_kwargs = {"po_number": po_number, **filter_query_args}
    if line_no is not None:
        url_kwargs["line"] = line_no
    return url_for("checkers_output.defect_details", **url_kwargs)


def serialize_dashboard_rows(rows):
    selected_date, show_all = get_dashboard_filter()
    filter_query_args = get_filter_query_args(selected_date, show_all)

    serialized_rows = []
    for (
        po_number,
        product_name,
        target,
        line_or_produced,
        pass_count,
        reject_count,
        alter_count,
    ) in rows:
        row = {
            "po_number": po_number,
            "product_name": product_name,
            "target": target,
            "total_processed": calculate_total_processed(
                pass_count,
                reject_count,
                alter_count,
            ),
            "pass_count": pass_count,
            "reject_count": reject_count,
            "alter_count": alter_count,
        }
        line_no = None
        if not show_all:
            line_no = line_or_produced
            row["line_no"] = line_no
        row["defect_details_url"] = build_defect_details_url(
            po_number,
            filter_query_args,
            line_no,
        )
        serialized_rows.append(row)

    return serialized_rows


def calculate_status_totals(rows):
    pass_count = sum(as_count(row[4]) for row in rows)
    reject_count = sum(as_count(row[5]) for row in rows)
    alter_count = sum(as_count(row[6]) for row in rows)
    total_processed = calculate_total_processed(
        pass_count,
        reject_count,
        alter_count,
    )

    return {
        "total_processed": total_processed,
        "defect_percentage": calculate_defect_percentage(
            alter_count,
            total_processed,
        ),
        "pass_count": pass_count,
        "reject_count": reject_count,
        "alter_count": alter_count,
    }


def prepare_top_defects_chart(rows):
    top_defects = sorted(rows, key=lambda item: item[1], reverse=True)[:3]

    return {
        "chart_labels": [defect_name for defect_name, _ in top_defects],
        "chart_counts": [int(defect_count or 0) for _, defect_count in top_defects],
    }


def prepare_line_defect_chart(rows):
    line_totals = {}

    for (
        _po_number,
        _product_name,
        _target,
        line_no,
        pass_count,
        reject_count,
        alter_count,
    ) in rows:
        totals = line_totals.setdefault(
            line_no,
            {"alter_count": 0, "total_processed": 0},
        )
        totals["alter_count"] += as_count(alter_count)
        totals["total_processed"] += calculate_total_processed(
            pass_count,
            reject_count,
            alter_count,
        )

    sorted_lines = sorted(line_totals.items())

    return {
        "line_chart_labels": [f"Line {line_no}" for line_no, _ in sorted_lines],
        "line_chart_percentages": [
            calculate_defect_percentage(totals["alter_count"], totals["total_processed"])
            for _, totals in sorted_lines
        ],
    }


def empty_line_defect_chart():
    return {
        "line_chart_labels": [],
        "line_chart_percentages": [],
    }


def prepare_defect_dashboard(rows, show_line=False, dashboard_rows=None):
    defect_names = []
    defect_name_set = set()
    table_rows_by_po = {}
    chart_counts = {}
    dashboard_totals = {}

    for (
        row_po_number,
        product_name,
        _target,
        line_or_produced,
        pass_count,
        reject_count,
        alter_count,
    ) in dashboard_rows or []:
        if show_line:
            key = (product_name, row_po_number, line_or_produced)
        else:
            key = (product_name, row_po_number)

        dashboard_totals[key] = {
            "alter_count": as_count(alter_count),
            "total_processed": calculate_total_processed(
                pass_count,
                reject_count,
                alter_count,
            ),
        }

    if show_line:
        for product_name, po_number, line_no, defect_name, defect_count in rows:
            key = (product_name, po_number, line_no)

            if defect_name not in defect_name_set:
                defect_name_set.add(defect_name)
                defect_names.append(defect_name)

            if key not in table_rows_by_po:
                table_rows_by_po[key] = {
                    "product_name": product_name,
                    "po_number": po_number,
                    "line_no": line_no,
                    "defects": {},
                }

            table_rows_by_po[key]["defects"][defect_name] = defect_count
            chart_counts[defect_name] = chart_counts.get(defect_name, 0) + defect_count
    else:
        for product_name, po_number, defect_name, defect_count in rows:
            key = (product_name, po_number)

            if defect_name not in defect_name_set:
                defect_name_set.add(defect_name)
                defect_names.append(defect_name)

            if key not in table_rows_by_po:
                table_rows_by_po[key] = {
                    "product_name": product_name,
                    "po_number": po_number,
                    "defects": {},
                }

            table_rows_by_po[key]["defects"][defect_name] = defect_count
            chart_counts[defect_name] = chart_counts.get(defect_name, 0) + defect_count

    top_defects = sorted(chart_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    table_rows = list(table_rows_by_po.values())

    if dashboard_rows is not None:
        for row in table_rows:
            if show_line:
                key = (row["product_name"], row["po_number"], row["line_no"])
            else:
                key = (row["product_name"], row["po_number"])

            row_totals = dashboard_totals.get(
                key,
                {"alter_count": 0, "total_processed": 0},
            )
            row["defect_percentage"] = calculate_defect_percentage(
                row_totals["alter_count"],
                row_totals["total_processed"],
            )

    return {
        "defect_names": defect_names,
        "table_rows": table_rows,
        "chart_labels": [defect_name for defect_name, _ in top_defects],
        "chart_counts": [defect_count for _, defect_count in top_defects],
    }


@bp.route("/")
@login_required
def dashboard():
    selected_date, show_all = get_dashboard_filter()
    rows = filter_incomplete_po_rows(
        show_checker_output_dashboard(selected_date),
        show_all,
    )
    defect_chart = prepare_top_defects_chart(get_all_po_defect_counts(selected_date))
    line_chart = (
        empty_line_defect_chart()
        if show_all
        else prepare_line_defect_chart(rows)
    )

    return render_template(
        "checkers_output/show_checkers_output.html",
        rows=rows,
        status_totals=calculate_status_totals(rows),
        selected_date=selected_date or "",
        show_all=show_all,
        today_date=date.today().isoformat(),
        **defect_chart,
        **line_chart,
    )


@bp.route("/defects/<path:po_number>")
@login_required
def defect_details(po_number):
    selected_date, show_all = get_dashboard_filter()
    selected_line = request.args.get("line", type=int)
    show_line = not show_all
    dashboard_rows = [
        row
        for row in show_checker_output_dashboard(selected_date)
        if row[0] == po_number
        and (not show_line or selected_line is None or row[3] == selected_line)
    ]
    defect_data = prepare_defect_dashboard(
        get_po_defect_counts(po_number, selected_date, selected_line),
        show_line=show_line,
        dashboard_rows=dashboard_rows,
    )

    return render_template(
        "checkers_output/defect_details.html",
        po_number=po_number,
        selected_date=selected_date or "",
        show_all=show_all,
        selected_line=selected_line,
        dashboard_url=url_for(
            "checkers_output.dashboard",
            **get_filter_query_args(selected_date, show_all),
        ),
        **defect_data,
    )


@bp.route("/data")
@login_required
def dashboard_data():
    selected_date, show_all = get_dashboard_filter()
    rows = filter_incomplete_po_rows(
        show_checker_output_dashboard(selected_date),
        show_all,
    )
    defect_chart = prepare_top_defects_chart(get_all_po_defect_counts(selected_date))
    line_chart = (
        empty_line_defect_chart()
        if show_all
        else prepare_line_defect_chart(rows)
    )

    return jsonify(
        {
            "rows": serialize_dashboard_rows(rows),
            "status_totals": calculate_status_totals(rows),
            "selected_date": selected_date,
            "show_all": show_all,
            **defect_chart,
            **line_chart,
        }
    )