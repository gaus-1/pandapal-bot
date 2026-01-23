# SQL Scripts

SQL scripts for database structure and migrations.

## Files

### Schema Creation
- `01_drop_all_tables.sql` - Drop all tables (use with caution)
- `02_create_tables.sql` - Create all tables

### Feature Migrations
- `03_add_premium_subscriptions.sql` - Add premium subscriptions
- `04_add_payment_method_fields.sql` - Add payment method fields
- `05_check_payment_method_migration.sql` - Verify payment migration
- `05_create_payments_table.sql` - Create payments table
- `06_add_saved_payment_method_id.sql` - Add saved payment method
- `06_create_daily_request_counts.sql` - Add daily request counters

### Data
- `subscriptions.csv` - Subscription plans data

## Usage

These scripts are for initial database setup. In production, use Alembic migrations instead.

```bash
# Apply script
psql $DATABASE_URL -f sql/02_create_tables.sql

# Check migration
psql $DATABASE_URL -f sql/05_check_payment_method_migration.sql
```

## Important

- Always backup before applying
- Test on staging database first
- Don't modify scripts after production deployment
- Prefer Alembic migrations for schema changes
