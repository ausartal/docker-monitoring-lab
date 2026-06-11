FROM httpd:2.4-alpine
RUN sed -i \
    -e 's/#LoadModule vhost_alias_module/LoadModule vhost_alias_module/' \
    -e 's/#LoadModule rewrite_module/LoadModule rewrite_module/' \
    -e 's/#Include conf\/extra\/httpd-vhosts.conf/Include conf\/extra\/httpd-vhosts.conf/' \
    /usr/local/apache2/conf/httpd.conf
COPY vhosts.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf
COPY html/ /usr/local/apache2/htdocs/
EXPOSE 80
