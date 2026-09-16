-- Execute como usuário postgres: psql -U postgres -f create_database.sql
-- Troque a senha abaixo e repita o mesmo valor em server/.env.
CREATE USER media_app WITH PASSWORD 'troque_esta_senha';
CREATE DATABASE media_processor OWNER media_app ENCODING 'UTF8';
