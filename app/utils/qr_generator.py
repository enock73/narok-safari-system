import qrcode
import os
from flask import current_app, url_for


def generate_clearance_qr(clearance):
    """Generate QR code for a gate clearance token."""
    qr_folder = current_app.config['QR_FOLDER']
    filename = f'qr_{clearance.token}.png'
    filepath = os.path.join(qr_folder, filename)

    # Encode token + basic info
    data = (
        f"MARA-CLEARANCE\n"
        f"Token: {clearance.token}\n"
        f"Gate: {clearance.gate}\n"
        f"Date: {clearance.entry_date}\n"
        f"Vehicle: {clearance.vehicle.plate_number}\n"
        f"Guide: {clearance.guide.full_name}\n"
        f"Status: {clearance.status.upper()}\n"
        f"Verify: /api/v1/clearance/{clearance.token}/status"
    )

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1a3c2e', back_color='white')
    img.save(filepath)

    return filename
