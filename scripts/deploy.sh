#!/bin/bash
# Deployment script for RAGTrace Lite

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE=${1:-docker-compose.prod.yml}
BACKUP_DIR="./backups"

echo -e "${GREEN}Deploying RAGTrace Lite...${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed!${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed!${NC}"
    exit 1
fi

# Check environment variables
if [ ! -f .env ]; then
    echo -e "${RED}.env file not found!${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p data reports logs ${BACKUP_DIR} ssl

# Backup existing data
if [ -f "data/ragtrace_lite.db" ]; then
    echo -e "\n${YELLOW}Backing up existing data...${NC}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    tar -czf "${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz" data/ reports/
    echo -e "${GREEN}Backup created: ${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz${NC}"
fi

# Pull latest images
echo -e "\n${YELLOW}Pulling latest images...${NC}"
docker-compose -f ${COMPOSE_FILE} pull

# Stop existing containers
echo -e "\n${YELLOW}Stopping existing containers...${NC}"
docker-compose -f ${COMPOSE_FILE} down

# Start services
echo -e "\n${YELLOW}Starting services...${NC}"
docker-compose -f ${COMPOSE_FILE} up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo -e "\n${YELLOW}Checking service status...${NC}"
docker-compose -f ${COMPOSE_FILE} ps

# Show logs
echo -e "\n${YELLOW}Recent logs:${NC}"
docker-compose -f ${COMPOSE_FILE} logs --tail=20

echo -e "\n${GREEN}Deployment complete!${NC}"
echo -e "Access reports at: http://localhost/reports/"
echo -e "Prometheus metrics at: http://localhost:9090/"
echo -e "Kibana dashboard at: http://localhost:5601/"