#!/bin/bash
#========================================
# PHASE 0 ROLLBACK/RECOVERY PROCEDURES
# Enterprise Retail Intelligence System
# Created: $(date)
#========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./PHASE_0_IMPLEMENTATION/backups"
SQLITE_DB="petpooja_retail_db.sqlite3"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="SecurePassword123"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5433"
POSTGRES_DB="enterprise_retail"
LOG_FILE="./PHASE_0_IMPLEMENTATION/recovery_${$(date +%Y%m%d_%H%M%S)}.log"

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "${LOG_FILE}"
}

# ===== RECOVERY FUNCTIONS =====

list_available_backups() {
    log_info "Available backups:"
    log_info ""
    
    echo -e "${BLUE}SQLite Backups:${NC}"
    ls -lh "${BACKUP_DIR}"/sqlite_backup_*.sqlite3 2>/dev/null || log_warning "No SQLite backups found"
    
    echo -e ""
    echo -e "${BLUE}PostgreSQL Backups:${NC}"
    ls -lh "${BACKUP_DIR}"/postgresql_backup_*.sql* 2>/dev/null || log_warning "No PostgreSQL backups found"
    
    echo -e ""
    echo -e "${BLUE}Environment Backups:${NC}"
    ls -lhd "${BACKUP_DIR}"/env_backup_* 2>/dev/null || log_warning "No environment backups found"
    
    echo -e ""
    echo -e "${BLUE}Schema Backups:${NC}"
    ls -lh "${BACKUP_DIR}"/schema_backup_*.sql 2>/dev/null || log_warning "No schema backups found"
}

restore_sqlite_from_backup() {
    local backup_file=$1
    
    if [ -z "${backup_file}" ]; then
        log_error "Backup file not specified"
        return 1
    fi
    
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    log_warning "This will overwrite: ${SQLITE_DB}"
    read -p "Continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Recovery cancelled"
        return 1
    fi
    
    log_info "Restoring SQLite database from backup..."
    
    # Create a backup of current state
    local timestamp=$(date +%Y%m%d_%H%M%S)
    cp "${SQLITE_DB}" "${SQLITE_DB}.backup_before_recovery_${timestamp}" 2>&1 | tee -a "${LOG_FILE}"
    log_success "Current database backed up to: ${SQLITE_DB}.backup_before_recovery_${timestamp}"
    
    # Restore
    cp "${backup_file}" "${SQLITE_DB}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ -f "${SQLITE_DB}" ]; then
        log_success "SQLite database restored successfully"
        return 0
    else
        log_error "Failed to restore SQLite database"
        return 1
    fi
}

restore_postgresql_from_backup() {
    local backup_file=$1
    
    if [ -z "${backup_file}" ]; then
        log_error "Backup file not specified"
        return 1
    fi
    
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    log_warning "This will overwrite PostgreSQL database: ${POSTGRES_DB}"
    read -p "Continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Recovery cancelled"
        return 1
    fi
    
    log_info "Restoring PostgreSQL database from backup..."
    
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    
    # Drop existing database
    log_info "Dropping existing database..."
    psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
        -tc "DROP DATABASE IF EXISTS ${POSTGRES_DB};" 2>&1 | tee -a "${LOG_FILE}"
    
    # Create new database
    log_info "Creating new database..."
    psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
        -tc "CREATE DATABASE ${POSTGRES_DB};" 2>&1 | tee -a "${LOG_FILE}"
    
    # Restore from backup
    log_info "Restoring data from backup..."
    
    if [[ "${backup_file}" == *.gz ]]; then
        gunzip -c "${backup_file}" | psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" \
            -p "${POSTGRES_PORT}" -d "${POSTGRES_DB}" 2>&1 | tee -a "${LOG_FILE}"
    else
        psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
            -d "${POSTGRES_DB}" < "${backup_file}" 2>&1 | tee -a "${LOG_FILE}"
    fi
    
    if [ $? -eq 0 ]; then
        log_success "PostgreSQL database restored successfully"
        return 0
    else
        log_error "Failed to restore PostgreSQL database"
        return 1
    fi
}

restore_environment_files() {
    local env_backup_dir=$1
    
    if [ -z "${env_backup_dir}" ] || [ ! -d "${env_backup_dir}" ]; then
        log_error "Environment backup directory not found or not specified"
        return 1
    fi
    
    log_info "Restoring environment files from: ${env_backup_dir}"
    
    if [ -f "${env_backup_dir}/backend.env" ]; then
        cp "${env_backup_dir}/backend.env" backend/.env
        log_success "Restored backend/.env"
    fi
    
    if [ -f "${env_backup_dir}/frontend.env.local" ]; then
        cp "${env_backup_dir}/frontend.env.local" frontend/.env.local
        log_success "Restored frontend/.env.local"
    fi
    
    if [ -f "${env_backup_dir}/scripts.env" ]; then
        cp "${env_backup_dir}/scripts.env" PHASE_0_IMPLEMENTATION/scripts/.env
        log_success "Restored scripts/.env"
    fi
    
    return 0
}

# ===== RECOVERY SCENARIOS =====

scenario_complete_postgresql_reset() {
    log_warning "This will completely reset PostgreSQL database to initial state"
    log_warning "This action CANNOT be undone without another backup"
    
    read -p "I understand the consequences. Continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Operation cancelled"
        return 1
    fi
    
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    
    log_info "Dropping database ${POSTGRES_DB}..."
    psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
        -tc "DROP DATABASE IF EXISTS ${POSTGRES_DB};" 2>&1 | tee -a "${LOG_FILE}"
    
    log_info "Creating fresh database ${POSTGRES_DB}..."
    psql -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
        -tc "CREATE DATABASE ${POSTGRES_DB};" 2>&1 | tee -a "${LOG_FILE}"
    
    log_success "PostgreSQL database reset to clean state"
    log_info "Next step: Run migration script (01_create_schema.sh)"
}

# ===== INTERACTIVE MENU =====

show_menu() {
    echo -e ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}PHASE 0 ROLLBACK/RECOVERY PROCEDURES${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "1. List available backups"
    echo "2. Restore SQLite from backup"
    echo "3. Restore PostgreSQL from backup"
    echo "4. Restore environment files"
    echo "5. Complete PostgreSQL reset (DANGEROUS)"
    echo "6. Exit"
    echo ""
    read -p "Select option (1-6): " choice
}

main() {
    while true; do
        show_menu
        
        case $choice in
            1)
                list_available_backups
                ;;
            2)
                echo ""
                echo "Enter SQLite backup file path:"
                read -r backup_file
                restore_sqlite_from_backup "${backup_file}"
                ;;
            3)
                echo ""
                echo "Enter PostgreSQL backup file path (can be .sql or .sql.gz):"
                read -r backup_file
                restore_postgresql_from_backup "${backup_file}"
                ;;
            4)
                echo ""
                echo "Enter environment backup directory path:"
                read -r env_dir
                restore_environment_files "${env_dir}"
                ;;
            5)
                scenario_complete_postgresql_reset
                ;;
            6)
                log_info "Exiting recovery procedures"
                exit 0
                ;;
            *)
                log_error "Invalid option"
                ;;
        esac
    done
}

# Run if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
