#!/usr/bin/env python
"""
Script pour configurer la base de données MySQL avec XAMPP.
"""
import pymysql
import sys

def test_mysql_connection():
    """Teste la connexion à MySQL et crée la base de données si nécessaire."""
    try:
        # Connexion à MySQL sans spécifier de base de données
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            port=3306,
            charset='utf8mb4'
        )
        print("✅ Connexion à MySQL réussie!")
        
        cursor = connection.cursor()
        
        # Vérifier si la base de données existe
        cursor.execute("SHOW DATABASES LIKE 'blogora'")
        result = cursor.fetchone()
        
        if result:
            print("✅ La base de données 'blogora' existe déjà.")
        else:
            # Créer la base de données
            cursor.execute("CREATE DATABASE blogora CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Base de données 'blogora' créée avec succès!")
        
        # Vérifier les permissions
        cursor.execute("SHOW GRANTS FOR CURRENT_USER()")
        grants = cursor.fetchall()
        print("✅ Permissions de l'utilisateur:")
        for grant in grants:
            print(f"   {grant[0]}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 Configuration MySQL terminée avec succès!")
        print("Vous pouvez maintenant lancer les migrations Django avec:")
        print("   python manage.py makemigrations")
        print("   python manage.py migrate")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion à MySQL: {e}")
        print("\n🔧 Solutions possibles:")
        print("1. Vérifiez que XAMPP est démarré (Apache + MySQL)")
        print("2. Vérifiez que MySQL écoute sur le port 3306")
        print("3. Vérifiez que l'utilisateur 'root' n'a pas de mot de passe")
        print("4. Vérifiez que le service MySQL n'est pas bloqué par un firewall")
        return False

if __name__ == "__main__":
    test_mysql_connection()
