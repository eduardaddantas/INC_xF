#!/bin/bash

# ----------------------------
# Configurações
# ----------------------------
CONTAINER_NAME="postgres_db"     
DB_USER="postgres"                # usuário do banco
DB_NAME="postgres"                # nome do banco a ser feito backup
BACKUP_DIR="C:/Users/MFORNELOSD/OneDrive - Econocom" # pasta onde os backups serão salvos
MAX_BACKUPS=7                     # número máximo de backups a manter


# ----------------------------

# Cria a pasta de backup, se não existir
mkdir -p "$BACKUP_DIR"

# Gera o nome do arquivo com a data
DATA=$(date +%F_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_$DATA.sql"

# Executa o backup
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"

# Remove backups antigos (mantém apenas os últimos $MAX_BACKUPS)
ls -1t "$BACKUP_DIR"/backup_*.sql | tail -n +$((MAX_BACKUPS+1)) | xargs rm -f

echo "Backup criado em: $BACKUP_FILE"
