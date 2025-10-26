# 📜 Scripts Directory

Utility scripts organized by purpose.

## 📁 Directory Structure

```
scripts/
├── deployment/      # Deployment and health check scripts
├── database/        # Database backup and restore
├── development/     # Development utilities
└── maintenance/     # Maintenance tasks
```

---

## 🚀 Deployment Scripts

### `deployment/health_check.sh`
Check if all services are running and healthy.

**Usage:**
```bash
./scripts/deployment/health_check.sh
```

**What it checks:**
- Backend API health
- Frontend accessibility
- Database connectivity
- Redis connectivity

---

## 💾 Database Scripts

### `database/backup_database.sh`
Create a backup of the PostgreSQL database.

**Usage:**
```bash
./scripts/database/backup_database.sh
```

**Output:**
- Creates `backup_YYYYMMDD_HHMMSS.sql.gz` in `backups/` directory

### `database/restore_database.sh`
Restore database from a backup file.

**Usage:**
```bash
./scripts/database/restore_database.sh <backup_file>
```

**Example:**
```bash
./scripts/database/restore_database.sh backups/backup_20251026_100000.sql.gz
```

---

## 🛠️ Development Scripts

Directory for development utilities:
- Test data generation
- Database seeding
- Development environment reset
- etc.

---

## 🔧 Maintenance Scripts

Directory for maintenance tasks:
- Log rotation
- Old backup cleanup
- Cache clearing
- etc.

---

## 📝 Adding New Scripts

### Guidelines:

1. **Choose the right directory:**
   - Deployment → deployment/
   - Database → database/
   - Development → development/
   - Maintenance → maintenance/

2. **Make it executable:**
   ```bash
   chmod +x scripts/category/your_script.sh
   ```

3. **Add shebang:**
   ```bash
   #!/bin/bash
   set -e  # Exit on error
   ```

4. **Document it:**
   - Add usage instructions
   - Document parameters
   - Add examples

5. **Update this README:**
   - Add script description
   - Include usage example

---

## 🔐 Security Notes

- Scripts should NOT contain sensitive data (passwords, tokens, etc.)
- Use environment variables for sensitive data
- Never commit `.env` files
- Use `.env.example` for templates

---

## ✅ Best Practices

1. **Error Handling:**
   ```bash
   set -e  # Exit on error
   set -u  # Exit on undefined variable
   ```

2. **Logging:**
   ```bash
   echo "$(date): Starting backup..."
   ```

3. **Confirmation Prompts:**
   ```bash
   read -p "Are you sure? (y/n) " -n 1 -r
   echo
   if [[ ! $REPLY =~ ^[Yy]$ ]]; then
       exit 1
   fi
   ```

4. **Help Messages:**
   ```bash
   if [ "$#" -ne 1 ]; then
       echo "Usage: $0 <backup_file>"
       exit 1
   fi
   ```

---

**Maintained by:** Development Team  
**Last Updated:** October 26, 2025

