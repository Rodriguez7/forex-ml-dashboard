#!/bin/bash
# Quick start script for Flask dashboard

echo "=========================================="
echo "Starting Forex ML Signal Dashboard"
echo "=========================================="
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

cd "$(dirname "$0")"
python app.py
