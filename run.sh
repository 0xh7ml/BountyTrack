#!/bin/bash

# Function to display usage instructions
show_usage() {
    echo "Usage: ./run.sh [command]"
    echo "Commands:"
    echo "  start   - Build and start the containers"
    echo "  stop    - Stop the containers"
    echo "  restart - Restart the containers"
    echo "  logs    - Show container logs"
    echo "  build   - Rebuild the containers"
    echo "  shell   - Open a shell in the web container"
    echo "  clean   - Stop containers and remove volumes"
}

case "$1" in
    "start")
        echo "Building and starting containers..."
        docker-compose up --build -d
        echo "Containers are running!"
        ;;
    "stop")
        echo "Stopping containers..."
        docker-compose down
        ;;
    "restart")
        echo "Restarting containers..."
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "build")
        echo "Rebuilding containers..."
        docker-compose build --no-cache
        ;;
    "shell")
        echo "Opening shell in web container..."
        docker-compose exec web sh
        ;;
    "clean")
        echo "Stopping containers and removing volumes..."
        docker-compose down -v
        ;;
    *)
        show_usage
        ;;
esac 
