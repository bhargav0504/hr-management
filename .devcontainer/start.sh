#!/bin/bash
nohup gunicorn run:app --bind 0.0.0.0:5000 --workers 2 > /tmp/app.log 2>&1 &
echo "HR Management app started on port 5000 (PID $!)"
