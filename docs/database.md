# Database Documentation

## Schema Overview

The Kronic application uses PostgreSQL with SQLAlchemy ORM and Alembic migrations.

### Tables

#### `users`
- `id` (UUID) - Primary key
- `email` (VARCHAR 255) - Unique email address
- `password_hash` (VARCHAR 255) - Hashed password
- `created_at` (TIMESTAMP) - Creation timestamp
- `updated_at` (TIMESTAMP) - Last update timestamp
- `is_active` (BOOLEAN) - Account active status
- `is_verified` (BOOLEAN) - Email verification status
- `last_login` (TIMESTAMP) - Last login timestamp

#### `roles`
- `id` (INTEGER) - Primary key
- `name` (VARCHAR 50) - Unique role name
- `permissions` (JSON) - Role permissions object

#### `user_roles`
- `user_id` (UUID) - Foreign key to users.id
- `role_id` (INTEGER) - Foreign key to roles.id
- Composite primary key and unique constraint

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KRONIC_DATABASE_URL` | - | Full database URL (overrides other DB settings) |
| `KRONIC_DATABASE_HOST` | localhost | Database host |
| `KRONIC_DATABASE_PORT` | 5432 | Database port |
| `KRONIC_DATABASE_NAME` | kronic | Database name |
| `KRONIC_DATABASE_USER` | kronic | Database user |
| `KRONIC_DATABASE_PASSWORD` | - | Database password |
| `KRONIC_DATABASE_POOL_SIZE` | 20 | Connection pool size |
| `KRONIC_DATABASE_MAX_OVERFLOW` | 0 | Max overflow connections |
| `KRONIC_DATABASE_POOL_TIMEOUT` | 30 | Pool timeout in seconds |

### Example Configuration

```bash
# Database connection
export KRONIC_DATABASE_HOST=postgres.example.com
export KRONIC_DATABASE_PORT=5432
export KRONIC_DATABASE_NAME=kronic_prod
export KRONIC_DATABASE_USER=kronic_user
export KRONIC_DATABASE_PASSWORD=secure_password

# Or use a single URL
export KRONIC_DATABASE_URL=postgresql://kronic_user:secure_password@postgres.example.com:5432/kronic_prod

# Admin user for seeding
export KRONIC_ADMIN_EMAIL=admin@example.com
export KRONIC_ADMIN_PASSWORD=admin_password
```

## Setup Instructions

1. **Install PostgreSQL 15+**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql-15 postgresql-client-15
   
   # macOS
   brew install postgresql@15
   
   # Docker
   docker run -d --name kronic-postgres \
     -e POSTGRES_DB=kronic \
     -e POSTGRES_USER=kronic \
     -e POSTGRES_PASSWORD=kronic123 \
     -p 5432:5432 \
     postgres:15
   ```

2. **Create Database and User**
   ```sql
   CREATE DATABASE kronic;
   CREATE USER kronic WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE kronic TO kronic;
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**
   ```bash
   # Run migrations to create tables
   alembic upgrade head
   ```

5. **Seed Database**
   ```bash
   # Create initial roles and admin user
   python scripts/seed_database.py
   ```

## Migrations

### Running Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

## Backup and Restore

### Daily Backup Script

```bash
#!/bin/bash
# backup-kronic-db.sh

DB_HOST="${KRONIC_DATABASE_HOST:-localhost}"
DB_PORT="${KRONIC_DATABASE_PORT:-5432}"
DB_NAME="${KRONIC_DATABASE_NAME:-kronic}"
DB_USER="${KRONIC_DATABASE_USER:-kronic}"
BACKUP_DIR="/var/backups/kronic"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
  --verbose --clean --no-owner --no-privileges \
  --file=$BACKUP_DIR/kronic_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/kronic_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "kronic_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: kronic_backup_$DATE.sql.gz"
```

### Restore from Backup

```bash
# Restore from compressed backup
gunzip -c /var/backups/kronic/kronic_backup_20231201_120000.sql.gz | \
  psql -h localhost -p 5432 -U kronic -d kronic

# Restore from uncompressed backup
psql -h localhost -p 5432 -U kronic -d kronic < backup_file.sql
```

### Automated Backup with Cron

```bash
# Add to crontab for daily backups at 2 AM
0 2 * * * /usr/local/bin/backup-kronic-db.sh >> /var/log/kronic-backup.log 2>&1
```

## Monitoring

### Health Checks

The application provides database health checks at `/healthz`:

```json
{
  "status": "ok",
  "components": {
    "database": {
      "status": "healthy",
      "database_url": "localhost:5432/kronic",
      "pool": {
        "size": 20,
        "checked_in": 18,
        "checked_out": 2,
        "overflow": 0,
        "invalid": 0
      }
    }
  }
}
```

### Connection Pool Monitoring

Monitor connection pool metrics:
- `size`: Total pool size
- `checked_in`: Available connections
- `checked_out`: Active connections
- `overflow`: Overflow connections
- `invalid`: Invalid connections

### Log Monitoring

Monitor application logs for database issues:
```bash
# Monitor for database errors
tail -f /var/log/kronic/app.log | grep -i "database\|sql\|connection"
```

## Security

### Best Practices

1. **Use Strong Passwords**: Ensure database passwords are strong and unique
2. **Limit Connections**: Configure firewall to limit database access
3. **SSL/TLS**: Enable SSL for database connections in production
4. **Regular Updates**: Keep PostgreSQL updated
5. **Backup Encryption**: Encrypt database backups
6. **Access Logging**: Enable PostgreSQL query logging for auditing

### SSL Configuration

For production, configure SSL in the database URL:
```bash
export KRONIC_DATABASE_URL="postgresql://user:pass@host:port/db?sslmode=require"
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if PostgreSQL is running
   - Verify host/port configuration
   - Check firewall settings

2. **Authentication Failed**
   - Verify username/password
   - Check `pg_hba.conf` configuration
   - Ensure user has proper permissions

3. **Migration Failures**
   - Check database connectivity
   - Verify migration file syntax
   - Review Alembic logs

4. **Pool Exhaustion**
   - Monitor connection usage
   - Increase pool size if needed
   - Check for connection leaks

### Debug Mode

Enable SQL logging for debugging:
```python
# In database.py, set echo=True
engine = create_engine(database_url, echo=True)
```