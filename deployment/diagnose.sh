#!/bin/bash

echo "--- DIAGNOSTIC START ---"
echo "Checking usage of Port 5000..."
sudo lsof -i :5000 || echo "Nothing listening on port 5000"

echo -e "\nChecking what process is listening (full detail)..."
sudo netstat -tulpn | grep :5000

echo -e "\nChecking Firewall (UFW) Status..."
sudo ufw status | grep 5000

echo -e "\nChecking Supervisor Status..."
sudo supervisorctl status

echo -e "\nChecking Local Connectivity..."
curl -v http://127.0.0.1:5000 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "SUCCESS: Local curl working."
else
    echo "FAILURE: Local curl failed."
fi

echo -e "\nChecking Public Bind..."
# Check if listening on 0.0.0.0 (all interfaces) or 127.0.0.1 (local only)
if sudo netstat -tulpn | grep :5000 | grep -q "0.0.0.0"; then
    echo "OK: Listening on 0.0.0.0 (Publicly accessible)"
elif sudo netstat -tulpn | grep :5000 | grep -q "::"; then
    echo "OK: Listening on :: (IPv6 + IPv4 usually)"
else
    echo "WARNING: Only listening on localhost (127.0.0.1)? Check netstat output above."
fi

echo "--- DIAGNOSTIC END ---"
