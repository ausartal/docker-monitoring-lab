# Gunakan base image nginx versi stabil
FROM nginx:1.26-alpine

# Metadata
LABEL maintainer="admin@pens.ac.id"
LABEL description="Custom Nginx untuk praktikum Docker PENS"
LABEL version="1.0"

# Hapus halaman default dan ganti dengan halaman custom
RUN rm -rf /usr/share/nginx/html/*
COPY index.html /usr/share/nginx/html/index.html

# Expose port 80
EXPOSE 80

# Command default
CMD ["nginx", "-g", "daemon off;"]
