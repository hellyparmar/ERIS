#!/bin/bash
#========================================
# PHASE 0 BACKUP PROCEDURES
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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SQLITE_DB="petpooja_retail_db.sqlite3"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="SecurePassword123"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5433"
POSTGRES_DB="enterprise_retail"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

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

# ===== BACKUP FUNCTIONS =====

backup_sqlite() {
    log_info "Starting SQLite backup..."
    
    if [ ! -f "${SQLITE_DB}" ]; then
        log_error "SQLite database not found: ${SQLITE_DB}"
        return 1
    fi
    
    local backup_file="${BACKUP_DIR}/sqlite_backup_${TIMESTAMP}.sqlite3"
    cp "${SQLITE_DB}" "${backup_file}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ -f "${backup_file}" ]; then
        local size=$(du -h "${backup_file}" | cut -f1)
        log_success "SQLite backup created: ${backup_file} (${size})"
        echo "${backup_file}"
        return 0
    else
        log_error "Failed to create SQLite backup"
        return 1
    fi
}

backup_postgresql() {
    log_info "Starting PostgreSQL backup..."
    
    local backup_file="${BACKUP_DIR}/postgresql_backup_${TIMESTAMP}.sql"
    local backup_compressed="${backup_file}.gz"
    
    # Full database dump
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    pg_dump -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
        -d "${POSTGRES_DB}" --verbose > "${backup_file}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ $? -ne 0 ]; then
        log_error "PostgreSQL dump failed"
        return 1
    fi
    
    # Verify backup size
    if [ ! -f "${backup_file}" ] || [ ! -s "${backup_file}" ]; then
        log_error "PostgreSQL backup file is empty or missing"
        return 1
    fi
    
    # Compress backup
    log_info "Compressing PostgreSQL backup..."
    gzip -v "${backup_file}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ -f "${backup_compressed}" ]; then
        local uncompressed_size=$(du -h "${backup_file}" 2>/dev/null | cut -f1 || echo "unknown")
        local compressed_size=$(du -h "${backup_compressed}" | cut -f1)
        log_success "PostgreSQL backup created: ${backup_compressed} (compressed to ${compressed_size})"
        echo "${backup_compressed}"
        return 0
    else
        log_warning "Compression failed, backup file exists uncompressed: ${backup_file}"
        echo "${backup_file}"
        return 0
    fi
}

backup_environment_files() {
    log_info "Backing up environment configuration files..."
    
    local env_backup_dir="${BACKUP_DIR}/env_backup_${TIMESTAMP}"
    mkdir -p "${env_backup_dir}"
    
    # Backup environment files
    if [ -f "backend/.env" ]; then
        cp backend/.env "${env_backup_dir}/backend.env"
        log_success "Backed up backend/.env"
    fi
    
    if [ -f "frontend/.env.local" ]; then
        cp frontend/.env.local "${env_backup_dir}/frontend.env.local"
        log_success "Backed up frontend/.env.local"
    fi
    
    if [ -f "PHASE_0_IMPLEMENTATION/scripts/.env" ]; then
        cp PHASE_0_IMPLEMENTATION/scripts/.env "${env_backup_dir}/scripts.env"
        log_success "Backed up scripts/.env"
    fi
    
    echo "${env_backup_dir}"
}

backup_schema() {
    log_info "Backing up database schema definition..."
    
    local schema_backup="${BACKUP_DIR}/schema_backup_${TIMESTAMP}.sql"
    
    export PGPASSWORD="${POSTGRES_PASSWORD}"
    pg_dump -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -p "${POSTGRES_PORT}" \
        -d "${POSTGRES_DB}" --schema-only > "${schema_backup}" 2>&1 | tee -a "${LOG_FILE}"
    
    if [ -f "${schema_backup}" ] && [ -s "${schema_backup}" ]; then
        local size=$(du -h "${schema_backup}" | cut -f1)
        log_success "Schema backup created: ${schema_backup} (${size})"
        echo "${schema_backup}"
        return 0
    else
        log_error "Schema backup failed or is empty"
        return 1
    fi
}

# ===== VERIFICATION FUNCTIONS =====

verify_sqlite_backup() {
    log_info "Verifying SQLite backup integrity..."
    
    local backup_file=$1
    
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    # Check if it's a valid SQLite database
    local header=$(file "${backup_file}")
    if [[ "${header}" == *"SQLite"* ]]; then
        log_success "SQLite backup is valid (SQLite format confirmed)"
        
        # Try to count tables
        local table_count=$(sqlite3 "${backup_file}" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "unknown")
        log_info "Tables in backup: ${table_count}"
        
        return 0
    else
        log_error "SQLite backup is NOT valid (file header: ${header})"
        return 1
    fi
}

verify_postgresql_backup() {
    log_info "Verifying PostgreSQL backup integrity..."
    
    local backup_file=$1
    
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    # Decompress if needed
    local temp_file="${backup_file}"
    if [[ "${backup_file}" == *.gz ]]; then
        temp_file=$(mktemp)
        gunzip -c "${backup_file}" > "${temp_file}"
    fi
    
    # Verify it contains SQL
    if head -20 "${temp_file}" | grep -q "PostgreSQL"; then
        log_success "PostgreSQL backup header is valid"
        
        # Count SQL statements
        local statement_count=$(grep -c "^--" "${temp_file}" || echo "unknown")
        log_info "SQL statements in backup: ${statement_count}"
        
        # Clean up temp file
        if [[ "${backup_file}" == *.gz ]]; then
            rm "${temp_file}"
        fi
        
        return 0
    else
        log_error "PostgreSQL backup is NOT valid (missing PostgreSQL header)"
        return 1
    fi
}

# ===== MAIN BACKUP EXECUTION =====

main() {
    log_info "=========================================="
    log_info "Phase 0 Backup Procedures Started"
    log_info "=========================================="
    log_info "Backup directory: ${BACKUP_DIR}"
    log_info "Timestamp: ${TIMESTAMP}"
    log_info ""
    
    # Create backups
    SQLITE_BACKUP=$(backup_sqlite)
    POSTGRES_BACKUP=$(backup_postgresql)
    ENV_BACKUP=$(backup_environment_files)
    SCHEMA_BACKUP=$(backup_schema)
    
    log_info ""
    log_info "Verifying backups..."
    log_info ""
    
    # Verify backups
    if [ -n "${SQLITE_BACKUP}" ]; then
        verify_sqlite_backup "${SQLITE_BACKUP}"
    fi
    
    if [ -n "${POSTGRES_BACKUP}" ]; then
        verify_postgresql_backup "${POSTGRES_BACKUP}"
    fi
    
    log_info ""
    log_info "=========================================="
    log_success "Backup procedures completed successfully!"
    log_info "=========================================="
    log_info ""
    log_info "Backup Summary:"
    log_info "  SQLite:       ${SQLITE_BACKUP}"
    log_info "  PostgreSQL:   ${POSTGRES_BACKUP}"
    log_info "  Environment:  ${ENV_BACKUP}"
    log_info "  Schema:       ${SCHEMA_BACKUP}"
    log_info "  Log file:     ${LOG_FILE}"
    log_info ""
}

# Run main if executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
