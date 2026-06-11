FROM httpd:2.4-alpine

RUN sed -i \
    -e 's/#LoadModule vhost_alias_module/LoadModule vhost_alias_module/' \
    -e 's/#LoadModule rewrite_module/LoadModule rewrite_module/' \
    /usr/local/apache2/conf/httpd.conf

RUN echo "Include conf/extra/vhosts.conf" >> /usr/local/apache2/conf/httpd.conf
RUN mkdir -p /var/log/apache2

COPY sites/vhosts.conf /usr/local/apache2/conf/extra/vhosts.conf
COPY html-site1/ /usr/local/apache2/htdocs/site1/
COPY html-site2/ /usr/local/apache2/htdocs/site2/

EXPOSE 80
