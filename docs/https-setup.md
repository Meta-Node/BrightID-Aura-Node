# Setting up HTTPS for a BrightID node

There are various ways to set up an SSL reverse proxy in front of a BrightID node. One way is to use nginx and certbot.

1. Get a domain name (sub-domains work). (This example uses `aura-node.brightid.org`.)
    1. Configure the DNS to point the domain or sub-domain to your node's IP address.
2. Change the port BrightID node's docker-managed nginx uses to 8080 (so your reverse proxy can use port 80 as certbot expects).
    1. Edit `web/brightid-nginx.conf` (relative to your node checkout) to replace the existing `listen 80;` directive with:
    ```
        listen 127.0.0.1:8080;
    ```
    2. From your node checkout directory, run `docker-compose restart web` to pick up the changes.
    3. `docker ps -a` to ensure that `nginx` restarted successfully.
3. Install `nginx`, `certbot`, and `python3-certbot-nginx`:
```
sudo apt-get install nginx certbot python3-certbot-nginx
```
4. Configure your reverse proxy. Here is an example nginx server configuration. (You could install it in `/etc/nginx/sites-enabled/brightid-node`.)
```
server {
        server_name aura-node.brightid.org;
        location / {
                proxy_pass http://127.0.0.1:8080/;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto https;
                proxy_ignore_headers    X-Accel-Expires Expires Cache-Control;
                proxy_hide_header       Access-Control-Allow-Origin;
                add_header Access-Control-Allow-Origin * always;
        }
}
```
  * Then restart nginx (e.g. `systemctl restart nginx`).

5. Run certbot:
```
sudo certbot --nginx -d aura-node.brightid.org
```

6. Edit your nginx server configuration to use 308 instead of 301 redirects (to preserve HTTP POST verbs).

Certbot will add a second `server` section to the bottom of your file, similar to this one.

Edit the file to replace `301` with `308` and remove the first `# managed by Certbot` comment.

```
server {
    # Redirect domain to HTTPS
    if ($host = aura-node.brightid.org) {
        return 308 https://$host$request_uri;
    }

    server_name aura-node.brightid.org
    listen 80;
    return 404; # managed by Certbot
}
```

See also [this guide from nginx and certbot](https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/).
