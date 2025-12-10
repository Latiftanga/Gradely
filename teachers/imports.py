"""
Bulk import utilities for Teacher model.
Supports CSV and XLSX file formats.
"""
import io
import csv
import uuid
import secrets
import string
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
import pandas as pd

from accounts.models import User
from .models import Teacher


def generate_random_password(length=12):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_credentials_email(email, password, first_name, last_name):
    """Send login credentials to the teacher's email."""
    subject = 'Your Teacher Account Has Been Created'
    message = f"""
Hello {first_name} {last_name},

Your teacher account has been created. Here are your login credentials:

Email: {email}
Password: {password}

Please log in and change your password immediately for security purposes.

Best regards,
School Administration
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


# Expected columns in the import file
REQUIRED_COLUMNS = ['staff_id', 'first_name', 'last_name', 'email', 'date_employed']
OPTIONAL_COLUMNS = [
    'middle_name', 'gender', 'date_of_birth', 'ghana_card_number', 'ssnit_number',
    'employment_status', 'qualification', 'specialization',
    'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
    'residential_address'
]
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def get_template_columns():
    """Return all columns for the template file."""
    return ALL_COLUMNS


def generate_template_csv():
    """Generate a CSV template file for bulk import."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(ALL_COLUMNS)
    # Add example rows
    writer.writerow([
        'TCH001', 'John', 'Doe', 'john.doe@school.com', '2020-01-15',
        'Middle', 'M', '1985-05-15', 'GHA-123456789-0', 'SSN12345',
        'full_time', 'bachelors', 'Mathematics',
        '0201234567', 'Jane Doe', '0209876543',
        '123 Main Street, Accra'
    ])
    writer.writerow([
        'TCH002', 'Jane', 'Smith', 'jane.smith@school.com', '2021-09-01',
        '', 'F', '1990-03-20', '', '',
        'part_time', 'masters', 'English Language',
        '0551234567', '', '',
        ''
    ])
    output.seek(0)
    return output.getvalue()


def generate_template_xlsx():
    """Generate an XLSX template file for bulk import."""
    df = pd.DataFrame(columns=ALL_COLUMNS)
    # Add example rows
    example_data = [
        {
            'staff_id': 'TCH001',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@school.com',
            'date_employed': '2020-01-15',
            'middle_name': 'Middle',
            'gender': 'M',
            'date_of_birth': '1985-05-15',
            'ghana_card_number': 'GHA-123456789-0',
            'ssnit_number': 'SSN12345',
            'employment_status': 'full_time',
            'qualification': 'bachelors',
            'specialization': 'Mathematics',
            'phone_number': '0201234567',
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '0209876543',
            'residential_address': '123 Main Street, Accra',
        },
        {
            'staff_id': 'TCH002',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@school.com',
            'date_employed': '2021-09-01',
            'middle_name': '',
            'gender': 'F',
            'date_of_birth': '1990-03-20',
            'ghana_card_number': '',
            'ssnit_number': '',
            'employment_status': 'part_time',
            'qualification': 'masters',
            'specialization': 'English Language',
            'phone_number': '0551234567',
            'emergency_contact_name': '',
            'emergency_contact_phone': '',
            'residential_address': '',
        }
    ]
    df = pd.concat([df, pd.DataFrame(example_data)], ignore_index=True)

    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)
    return output.getvalue()


def parse_date(value):
    """Parse a date value from various formats."""
    if pd.isna(value) or value == '' or value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, pd.Timestamp):
        return value.date()

    # Try common date formats
    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    for fmt in date_formats:
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Cannot parse date: {value}")


def validate_row(row, row_num, existing_emails, existing_staff_ids):
    """Validate a single row of data."""
    errors = []

    # Check required fields
    for col in REQUIRED_COLUMNS:
        value = row.get(col, '')
        if pd.isna(value) or str(value).strip() == '':
            errors.append(f"Row {row_num}: Missing required field '{col}'")

    if errors:
        return errors

    # Validate email
    email = str(row.get('email', '')).strip().lower()
    if '@' not in email:
        errors.append(f"Row {row_num}: Invalid email format '{email}'")
    elif email in existing_emails:
        errors.append(f"Row {row_num}: Email '{email}' already exists")

    # Validate staff_id uniqueness
    staff_id = str(row.get('staff_id', '')).strip()
    if staff_id in existing_staff_ids:
        errors.append(f"Row {row_num}: Staff ID '{staff_id}' already exists")

    # Validate gender if provided
    gender = str(row.get('gender', '')).strip().upper()
    if gender and gender not in ['M', 'F', '']:
        errors.append(f"Row {row_num}: Gender must be 'M' or 'F', got '{gender}'")

    # Validate date_employed
    try:
        date_employed = parse_date(row.get('date_employed'))
        if date_employed is None:
            errors.append(f"Row {row_num}: date_employed is required")
    except ValueError as e:
        errors.append(f"Row {row_num}: {e}")

    # Validate date_of_birth if provided
    dob = row.get('date_of_birth')
    if not pd.isna(dob) and str(dob).strip():
        try:
            parse_date(dob)
        except ValueError as e:
            errors.append(f"Row {row_num}: {e}")

    # Validate employment_status if provided
    employment_status = str(row.get('employment_status', '')).strip().lower()
    valid_statuses = ['full_time', 'part_time', 'contract', 'volunteer', '']
    if employment_status and employment_status not in valid_statuses:
        errors.append(f"Row {row_num}: Employment status must be one of {valid_statuses[:-1]}, got '{employment_status}'")

    # Validate qualification if provided
    qualification = str(row.get('qualification', '')).strip().lower()
    valid_qualifications = ['diploma', 'bachelors', 'masters', 'phd', 'other', '']
    if qualification and qualification not in valid_qualifications:
        errors.append(f"Row {row_num}: Qualification must be one of {valid_qualifications[:-1]}, got '{qualification}'")

    return errors


def read_import_file(file):
    """Read and parse the import file (CSV or XLSX)."""
    filename = file.name.lower()

    if filename.endswith('.csv'):
        # Read CSV
        try:
            content = file.read().decode('utf-8-sig')  # Handle BOM
            df = pd.read_csv(io.StringIO(content))
        except UnicodeDecodeError:
            file.seek(0)
            content = file.read().decode('latin-1')
            df = pd.read_csv(io.StringIO(content))
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        # Read Excel
        df = pd.read_excel(file, engine='openpyxl')
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or XLSX file.")

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    return df


def validate_import_file(file):
    """
    Validate the import file and return validation results.
    Returns: (is_valid, errors, preview_data, total_rows, stats)
    """
    try:
        df = read_import_file(file)
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"], [], 0, {}

    if df.empty:
        return False, ["The file is empty"], [], 0, {}

    # Check for required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        return False, [f"Missing required columns: {', '.join(missing_columns)}"], [], 0, {}

    # Get existing emails and staff IDs for uniqueness check
    existing_emails = set(User.objects.values_list('email', flat=True))
    existing_staff_ids = set(Teacher.objects.values_list('staff_id', flat=True))

    # Track duplicates within file
    file_emails = set()
    file_staff_ids = set()

    errors = []
    valid_rows = []

    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row number (1-indexed + header)
        row_dict = row.to_dict()

        # Check for duplicates within file
        staff_id = str(row_dict.get('staff_id', '')).strip()
        email = str(row_dict.get('email', '')).strip().lower()

        if staff_id in file_staff_ids:
            errors.append(f"Row {row_num}: Duplicate staff ID '{staff_id}' within file")
        else:
            file_staff_ids.add(staff_id)

        if email in file_emails:
            errors.append(f"Row {row_num}: Duplicate email '{email}' within file")
        else:
            file_emails.add(email)

        # Validate row
        row_errors = validate_row(row_dict, row_num, existing_emails, existing_staff_ids)
        if row_errors:
            errors.extend(row_errors)
        else:
            valid_rows.append(row_dict)

    # Prepare preview data (first 5 rows)
    preview_data = df.head(5).to_dict('records')

    stats = {
        'total': len(df),
        'valid': len(valid_rows),
    }

    return len(errors) == 0, errors, preview_data, len(df), stats


@transaction.atomic
def process_import_file(file, send_emails=True):
    """
    Process the import file and create teachers.

    Args:
        file: The uploaded file
        send_emails: If True, send login credentials via email.

    Returns: (success_count, error_count, errors, stats)
    """
    try:
        df = read_import_file(file)
    except Exception as e:
        return 0, 0, [f"Error reading file: {str(e)}"], {}

    success_count = 0
    error_count = 0
    errors = []
    emails_sent = 0

    for idx, row in df.iterrows():
        row_num = idx + 2
        row_dict = row.to_dict()

        try:
            # Extract and clean data
            staff_id = str(row_dict.get('staff_id', '')).strip()
            first_name = str(row_dict.get('first_name', '')).strip()
            last_name = str(row_dict.get('last_name', '')).strip()
            middle_name = str(row_dict.get('middle_name', '')).strip() if not pd.isna(row_dict.get('middle_name')) else ''
            email = str(row_dict.get('email', '')).strip().lower()
            date_employed = parse_date(row_dict.get('date_employed'))

            # Check if user/teacher already exists
            if User.objects.filter(email=email).exists():
                errors.append(f"Row {row_num}: Email '{email}' already exists, skipped")
                error_count += 1
                continue

            if Teacher.objects.filter(staff_id=staff_id).exists():
                errors.append(f"Row {row_num}: Staff ID '{staff_id}' already exists, skipped")
                error_count += 1
                continue

            # Generate random password
            password = generate_random_password()

            # Create user with teacher role
            user = User.objects.create_teacheruser(email=email, password=password)
            user.force_password_change = True
            user.save()

            # Send credentials email
            if send_emails:
                try:
                    send_credentials_email(email, password, first_name, last_name)
                    emails_sent += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: Account created but email failed - {str(e)}")

            # Prepare optional fields
            optional_data = {}

            # Gender
            gender = row_dict.get('gender')
            if not pd.isna(gender) and str(gender).strip():
                optional_data['gender'] = str(gender).strip().upper()

            # Date of birth
            dob = row_dict.get('date_of_birth')
            if not pd.isna(dob) and str(dob).strip():
                optional_data['date_of_birth'] = parse_date(dob)

            # Ghana card
            ghana_card = row_dict.get('ghana_card_number')
            if not pd.isna(ghana_card) and str(ghana_card).strip():
                optional_data['ghana_card_number'] = str(ghana_card).strip()

            # SSNIT number
            ssnit = row_dict.get('ssnit_number')
            if not pd.isna(ssnit) and str(ssnit).strip():
                optional_data['ssnit_number'] = str(ssnit).strip()

            # Employment status
            employment_status = row_dict.get('employment_status')
            if not pd.isna(employment_status) and str(employment_status).strip():
                status = str(employment_status).strip().lower()
                if status in ['full_time', 'part_time', 'contract', 'volunteer']:
                    optional_data['employment_status'] = status

            # Qualification
            qualification = row_dict.get('qualification')
            if not pd.isna(qualification) and str(qualification).strip():
                qual = str(qualification).strip().lower()
                if qual in ['diploma', 'bachelors', 'masters', 'phd', 'other']:
                    optional_data['qualification'] = qual

            # Specialization
            specialization = row_dict.get('specialization')
            if not pd.isna(specialization) and str(specialization).strip():
                optional_data['specialization'] = str(specialization).strip()

            # Phone number
            phone = row_dict.get('phone_number')
            if not pd.isna(phone) and str(phone).strip():
                optional_data['phone_number'] = str(phone).strip()

            # Emergency contact
            ec_name = row_dict.get('emergency_contact_name')
            if not pd.isna(ec_name) and str(ec_name).strip():
                optional_data['emergency_contact_name'] = str(ec_name).strip()

            ec_phone = row_dict.get('emergency_contact_phone')
            if not pd.isna(ec_phone) and str(ec_phone).strip():
                optional_data['emergency_contact_phone'] = str(ec_phone).strip()

            # Address
            address = row_dict.get('residential_address')
            if not pd.isna(address) and str(address).strip():
                optional_data['residential_address'] = str(address).strip()

            # Create teacher
            Teacher.objects.create(
                user=user,
                staff_id=staff_id,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                date_employed=date_employed,
                **optional_data
            )

            success_count += 1

        except Exception as e:
            errors.append(f"Row {row_num}: Error - {str(e)}")
            error_count += 1

    stats = {
        'accounts_created': success_count,
        'emails_sent': emails_sent,
    }

    return success_count, error_count, errors, stats
