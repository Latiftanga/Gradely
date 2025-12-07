"""
Bulk import utilities for Student model.
Supports CSV and XLSX file formats.
"""
import io
import csv
import uuid
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
import pandas as pd

from accounts.models import User
from .models import Student


# Expected columns in the import file
REQUIRED_COLUMNS = ['student_id', 'first_name', 'last_name', 'gender', 'date_of_birth']
OPTIONAL_COLUMNS = [
    'email',  # Now optional - placeholder will be generated if not provided
    'middle_name', 'index_number', 'admission_number', 'ghana_card_number',
    'admission_date', 'previous_school', 'hometown', 'region', 'nationality',
    'residential_status', 'house', 'residential_address',
    'medical_conditions', 'allergies', 'blood_group'
]
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def get_template_columns():
    """Return all columns for the template file."""
    return ALL_COLUMNS


def generate_placeholder_email(student_id):
    """Generate a placeholder email for students without email provided."""
    # Use student_id as base, add random suffix for uniqueness
    clean_id = student_id.lower().replace(' ', '_').replace('-', '_')
    return f"{clean_id}.{uuid.uuid4().hex[:6]}@student.placeholder"


def generate_template_csv():
    """Generate a CSV template file for bulk import."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(ALL_COLUMNS)
    # Add example rows
    writer.writerow([
        'STU001', 'John', 'Doe', 'M', '2010-05-15',
        'john.doe@example.com',  # With email
        'Middle', 'IDX001', 'ADM001', 'GHA-123456789-0',
        '2024-09-01', 'Previous School Name', 'Accra', 'Greater Accra', 'Ghanaian',
        'day', '', '123 Main Street',
        '', '', 'O+'
    ])
    writer.writerow([
        'STU002', 'Jane', 'Smith', 'F', '2011-03-20',
        '',  # Without email - placeholder will be generated
        '', '', '', '',
        '', '', 'Kumasi', 'Ashanti', 'Ghanaian',
        'boarder', 'Blue House', '',
        '', '', ''
    ])
    output.seek(0)
    return output.getvalue()


def generate_template_xlsx():
    """Generate an XLSX template file for bulk import."""
    df = pd.DataFrame(columns=ALL_COLUMNS)
    # Add example rows
    example_data = [
        {
            'student_id': 'STU001',
            'first_name': 'John',
            'last_name': 'Doe',
            'gender': 'M',
            'date_of_birth': '2010-05-15',
            'email': 'john.doe@example.com',  # With email
            'middle_name': 'Middle',
            'index_number': 'IDX001',
            'admission_number': 'ADM001',
            'ghana_card_number': 'GHA-123456789-0',
            'admission_date': '2024-09-01',
            'previous_school': 'Previous School Name',
            'hometown': 'Accra',
            'region': 'Greater Accra',
            'nationality': 'Ghanaian',
            'residential_status': 'day',
            'house': '',
            'residential_address': '123 Main Street',
            'medical_conditions': '',
            'allergies': '',
            'blood_group': 'O+',
        },
        {
            'student_id': 'STU002',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'gender': 'F',
            'date_of_birth': '2011-03-20',
            'email': '',  # Without email - placeholder will be generated
            'middle_name': '',
            'index_number': '',
            'admission_number': '',
            'ghana_card_number': '',
            'admission_date': '',
            'previous_school': '',
            'hometown': 'Kumasi',
            'region': 'Ashanti',
            'nationality': 'Ghanaian',
            'residential_status': 'boarder',
            'house': 'Blue House',
            'residential_address': '',
            'medical_conditions': '',
            'allergies': '',
            'blood_group': '',
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


def validate_row(row, row_num, existing_emails, existing_student_ids):
    """Validate a single row of data."""
    errors = []

    # Check required fields
    for col in REQUIRED_COLUMNS:
        value = row.get(col, '')
        if pd.isna(value) or str(value).strip() == '':
            errors.append(f"Row {row_num}: Missing required field '{col}'")

    if errors:
        return errors

    # Validate email if provided
    email = row.get('email', '')
    if not pd.isna(email) and str(email).strip():
        email = str(email).strip().lower()
        if '@' not in email:
            errors.append(f"Row {row_num}: Invalid email format '{email}'")
        elif email in existing_emails:
            errors.append(f"Row {row_num}: Email '{email}' already exists")

    # Validate student_id uniqueness
    student_id = str(row.get('student_id', '')).strip()
    if student_id in existing_student_ids:
        errors.append(f"Row {row_num}: Student ID '{student_id}' already exists")

    # Validate gender
    gender = str(row.get('gender', '')).strip().upper()
    if gender not in ['M', 'F']:
        errors.append(f"Row {row_num}: Gender must be 'M' or 'F', got '{gender}'")

    # Validate date_of_birth
    try:
        parse_date(row.get('date_of_birth'))
    except ValueError as e:
        errors.append(f"Row {row_num}: {e}")

    # Validate admission_date if provided
    admission_date = row.get('admission_date')
    if not pd.isna(admission_date) and str(admission_date).strip():
        try:
            parse_date(admission_date)
        except ValueError as e:
            errors.append(f"Row {row_num}: {e}")

    # Validate residential_status if provided
    residential_status = str(row.get('residential_status', '')).strip().lower()
    if residential_status and residential_status not in ['day', 'boarder', '']:
        errors.append(f"Row {row_num}: Residential status must be 'day' or 'boarder', got '{residential_status}'")

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

    # Get existing emails and student IDs for uniqueness check
    existing_emails = set(User.objects.values_list('email', flat=True))
    existing_student_ids = set(Student.objects.values_list('student_id', flat=True))

    # Track duplicates within file
    file_emails = set()
    file_student_ids = set()

    errors = []
    valid_rows = []
    with_email_count = 0
    without_email_count = 0

    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row number (1-indexed + header)
        row_dict = row.to_dict()

        # Check for duplicates within file
        student_id = str(row_dict.get('student_id', '')).strip()

        if student_id in file_student_ids:
            errors.append(f"Row {row_num}: Duplicate student ID '{student_id}' within file")
        else:
            file_student_ids.add(student_id)

        # Check email duplicates only if email is provided
        email = row_dict.get('email', '')
        if not pd.isna(email) and str(email).strip():
            email = str(email).strip().lower()
            if email in file_emails:
                errors.append(f"Row {row_num}: Duplicate email '{email}' within file")
            else:
                file_emails.add(email)
            with_email_count += 1
        else:
            without_email_count += 1

        # Validate row
        row_errors = validate_row(row_dict, row_num, existing_emails, existing_student_ids)
        if row_errors:
            errors.extend(row_errors)
        else:
            valid_rows.append(row_dict)

    # Prepare preview data (first 5 rows)
    preview_data = df.head(5).to_dict('records')

    stats = {
        'total': len(df),
        'with_email': with_email_count,
        'without_email': without_email_count,
    }

    return len(errors) == 0, errors, preview_data, len(df), stats


@transaction.atomic
def process_import_file(file, default_password='changeme123', create_accounts=True):
    """
    Process the import file and create students.

    Args:
        file: The uploaded file
        default_password: Default password for new accounts
        create_accounts: If True, create user accounts. If False, generate placeholder emails.

    Returns: (success_count, error_count, errors, stats)
    """
    try:
        df = read_import_file(file)
    except Exception as e:
        return 0, 0, [f"Error reading file: {str(e)}"], {}

    success_count = 0
    error_count = 0
    errors = []
    accounts_created = 0
    placeholders_created = 0

    for idx, row in df.iterrows():
        row_num = idx + 2
        row_dict = row.to_dict()

        try:
            # Extract and clean data
            student_id = str(row_dict.get('student_id', '')).strip()
            first_name = str(row_dict.get('first_name', '')).strip()
            last_name = str(row_dict.get('last_name', '')).strip()
            middle_name = str(row_dict.get('middle_name', '')).strip() if not pd.isna(row_dict.get('middle_name')) else ''
            gender = str(row_dict.get('gender', '')).strip().upper()
            date_of_birth = parse_date(row_dict.get('date_of_birth'))

            # Handle email - use provided or generate placeholder
            email_value = row_dict.get('email', '')
            has_real_email = not pd.isna(email_value) and str(email_value).strip() and '@' in str(email_value)

            if has_real_email:
                email = str(email_value).strip().lower()
            else:
                # Generate placeholder email
                email = generate_placeholder_email(student_id)

            # Check if user/student already exists
            if User.objects.filter(email=email).exists():
                if has_real_email:
                    errors.append(f"Row {row_num}: Email '{email}' already exists, skipped")
                    error_count += 1
                    continue
                else:
                    # Regenerate placeholder with new random suffix
                    email = generate_placeholder_email(student_id)

            if Student.objects.filter(student_id=student_id).exists():
                errors.append(f"Row {row_num}: Student ID '{student_id}' already exists, skipped")
                error_count += 1
                continue

            # Create user
            if has_real_email and create_accounts:
                user = User.objects.create_studentuser(email=email, password=default_password)
                accounts_created += 1
            else:
                # Create user with placeholder email but inactive/unusable password
                user = User.objects.create_studentuser(email=email, password=None)
                user.set_unusable_password()
                user.save()
                placeholders_created += 1

            # Prepare optional fields
            optional_data = {}

            # Index number
            index_number = row_dict.get('index_number')
            if not pd.isna(index_number) and str(index_number).strip():
                optional_data['index_number'] = str(index_number).strip()

            # Admission number
            admission_number = row_dict.get('admission_number')
            if not pd.isna(admission_number) and str(admission_number).strip():
                optional_data['admission_number'] = str(admission_number).strip()

            # Ghana card
            ghana_card = row_dict.get('ghana_card_number')
            if not pd.isna(ghana_card) and str(ghana_card).strip():
                optional_data['ghana_card_number'] = str(ghana_card).strip()

            # Admission date
            admission_date = row_dict.get('admission_date')
            if not pd.isna(admission_date) and str(admission_date).strip():
                optional_data['admission_date'] = parse_date(admission_date)

            # Previous school
            previous_school = row_dict.get('previous_school')
            if not pd.isna(previous_school) and str(previous_school).strip():
                optional_data['previous_school'] = str(previous_school).strip()

            # Location fields
            for field in ['hometown', 'region', 'nationality']:
                value = row_dict.get(field)
                if not pd.isna(value) and str(value).strip():
                    optional_data[field] = str(value).strip()

            # Residential status
            residential_status = row_dict.get('residential_status')
            if not pd.isna(residential_status) and str(residential_status).strip():
                status = str(residential_status).strip().lower()
                if status in ['day', 'boarder']:
                    optional_data['residential_status'] = status

            # House
            house = row_dict.get('house')
            if not pd.isna(house) and str(house).strip():
                optional_data['house'] = str(house).strip()

            # Address
            address = row_dict.get('residential_address')
            if not pd.isna(address) and str(address).strip():
                optional_data['residential_address'] = str(address).strip()

            # Health fields
            for field in ['medical_conditions', 'allergies', 'blood_group']:
                value = row_dict.get(field)
                if not pd.isna(value) and str(value).strip():
                    optional_data[field] = str(value).strip()

            # Create student
            Student.objects.create(
                user=user,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                gender=gender,
                date_of_birth=date_of_birth,
                **optional_data
            )

            success_count += 1

        except Exception as e:
            errors.append(f"Row {row_num}: Error - {str(e)}")
            error_count += 1

    stats = {
        'accounts_created': accounts_created,
        'placeholders_created': placeholders_created,
    }

    return success_count, error_count, errors, stats
