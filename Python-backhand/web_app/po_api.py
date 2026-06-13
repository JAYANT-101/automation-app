from flask import Blueprint, jsonify, request

from web_app.data_utils import get_all_product_names, get_po_numbers_by_product


bp = Blueprint("po_api", __name__, url_prefix="/api/po")


@bp.route("/product-types", methods=("GET",))
def product_types():
    """Return product types for the frontend product select."""
    try:
        return jsonify({
            "product_types": get_all_product_names(),
        })
    except Exception as e:
        return jsonify({
            "errors": [str(e)],
        }), 500


@bp.route("/po-numbers", methods=("GET",))
def po_numbers():
    """Return PO numbers and targets for the selected product type."""
    product_type = request.args.get("product_type", "").strip()

    if not product_type:
        return jsonify({
            "errors": ["product_type is required"],
        }), 400

    try:
        po_rows = get_po_numbers_by_product(product_type)
    except Exception as e:
        return jsonify({
            "errors": [str(e)],
        }), 500

    return jsonify({
        "product_type": product_type,
        "po_numbers": [
            {
                "po_id": po_id,
                "po_number": po_number,
                "target": target,
            }
            for po_id, po_number, target in po_rows
        ],
    })
