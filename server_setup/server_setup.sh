PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && cd ../src && pwd )"
THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

sed -i "s|#PROJECT_ROOT|$PROJECT_ROOT|g" "$THIS_DIR/sinsloveandrainbows.eu"
sed -i "s|#PROJECT_ROOT|$PROJECT_ROOT|g" "$THIS_DIR/sinsloveandrainbows.service"
sed -i "s|#USER|$USER|g" "$THIS_DIR/sinsloveandrainbows.service"

sudo cp "$THIS_DIR/sinsloveandrainbows.socket" /etc/systemd/system/sinsloveandrainbows.socket
sudo cp "$THIS_DIR/sinsloveandrainbows.service" /etc/systemd/system/sinsloveandrainbows.service
sudo systemctl start sinsloveandrainbows.socket
sudo systemctl enable sinsloveandrainbows.socket
sudo cp "$THIS_DIR/sinsloveandrainbows.eu" /etc/nginx/sites-available/sinsloveandrainbows.eu
sudo ln -s /etc/nginx/sites-available/sinsloveandrainbows.eu /etc/nginx/sites-enabled/sinsloveandrainbows.eu
#sudo certbot --nginx -d sinsloveandrainbows.eu -d www.sinsloveandrainbows.eu