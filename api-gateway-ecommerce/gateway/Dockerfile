FROM nginx:1.27-alpine

# Replaces the stock configuration wholesale rather than dropping a file into
# conf.d, because the upstream blocks and the proxy defaults live in the http
# block and there is nothing in the default file worth keeping.
COPY nginx.conf /etc/nginx/nginx.conf

# The storefront. Serving it from the gateway is what puts the page and the API
# on one origin.
COPY html/ /usr/share/nginx/html/

# There is deliberately no `RUN nginx -t` here, which was not the first plan.
# `nginx -t` resolves every name in an upstream block, and during a build there
# is no network and no products-service to resolve, so the check fails on a
# configuration file that is perfectly valid:
#
#   [emerg] host not found in upstream "products-service:8000"
#
# The same resolution happens when the container starts, which is why
# docker-compose.yml declares depends_on. The configuration is verified instead
# by run.sh, from inside the running container where the names resolve.

EXPOSE 8091
