# Changing password for MariaDB 

```bash
sudo mysql
# mysql -h 166.78.144.191 -u username -ppassword database_name
SELECT User FROM mysql.user;
SET PASSWORD FOR 'user' = PASSWORD('xxxxxx');
Query OK, 0 rows affected (0.003 sec)
```