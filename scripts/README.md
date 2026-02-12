# Scripts Directory

Utility scripts for development, testing, and maintenance.

## Categories

### Database Scripts
Scripts for database management and migrations:
- `check_database.py` - Check database connection and schema
- `check_db.py` - Quick database health check
- `check_all_tables.py` - Verify all tables exist
- `check_railway_db.py` - Check Railway PostgreSQL connection
- `init_db_simple.py` - Simple database initialization
- `reset_alembic.py` - Reset Alembic migrations
- `view_database.py` - Interactive database viewer
- `README_VIEW_DB.md` - Database viewer documentation

### Testing Scripts
Scripts for testing and quality assurance:
- `test_ab_testing.py` - A/B testing experiments
- `test_imports.py` - Test import structure
- `load_testing.py` - Load testing
- `jmeter_load_test.py` - JMeter load tests
- `analyze_subjects_tests.py` - Analyze subject test coverage
- `analyze_text_handler.py` - Analyze text handler performance

### Security Scripts
Scripts for security checks and audits:
- `security_check.py` - Run security audit
- `check_vulnerabilities.py` - Check for known vulnerabilities
- `check_circular_imports.py` - Detect circular dependencies
- `check_dead_code.py` - Find unused code

### Dependency Management
Scripts for managing dependencies:
- `check_dependencies.py` - Check dependency health
- `check_package_versions.py` - Verify package versions
- `update_dependencies.py` - Update dependencies
- `update_requirements_txt.py` - Regenerate requirements.txt

### Payment Scripts
Scripts for payment system management:
- `activate_premium_manual.py` - Manually activate premium
- `activate_premium.sql` - SQL for premium activation
- `check_payment_method.py` - Check payment methods
- `check_payment_migration.py` - Verify payment migrations
- `setup_yookassa_webhook.py` - Setup YooKassa webhooks

### Analytics Scripts
Scripts for analytics and metrics:
- `analytics_dashboard.py` - Generate analytics dashboard
- `export_metrics.py` - Export metrics data
- `view_analytics_metrics.py` - View analytics
- `detailed_persistence_report.py` - Data persistence report
- `verify_data_persistence.py` - Verify data persistence

### Code Generation
Scripts for code generation and refactoring:
- `split_api_ts.py` - Split large TypeScript API files
- `split_game_engines.py` - Split game engine code
- `split_games_service.py` - Split games service
- `split_models.py` - Split database models
- `split_telegram_ts.py` - Split Telegram TypeScript code
- `split_yandex_service.py` - Split Yandex service

### Data Management
Scripts for data operations:
- `add_test_data.py` - Add test data to database
- `update_knowledge_base.py` - Update knowledge base
- `fix_encoding.py` - Fix file encoding issues

### Environment
Scripts for environment setup:
- `check_env.py` - Verify environment variables
- `check_yandexgpt_models.py` - Check YandexGPT models

### Documentation
Scripts for generating documentation:
- `generate_pdf.py` - Generate PDF documentation
- `generate_resume_html.py` - Generate HTML resume
- `generate_resume_pdf.py` - Generate PDF resume

## Usage

Most scripts can be run directly:

```bash
python scripts/check_database.py
python scripts/security_check.py
python scripts/load_testing.py
```

Some scripts require environment variables to be set (see `.env` file).

## Adding New Scripts

When adding new scripts:
1. Place in appropriate category above
2. Add brief description
3. Follow naming convention: `verb_noun.py`
4. Include docstring with usage example
5. Handle errors gracefully
