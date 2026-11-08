# Projet EauSolidaire – Plateforme de Suivi des Points d'Eau au Mali

Plateforme web de suivi des infrastructures hydrauliques (forages, puits, bornes-fontaines), des équipements, des pannes, des stocks de pièces détachées et des interventions de maintenance au Mali.

L'interface Frontend d'origine est intégralement préservée à 100 % et connectée à une architecture Backend **Django 6.1** modulaire reliée à **MySQL (WampServer / phpMyAdmin)**.

---

## 1. Architecture du Projet Django

- [`config/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/config) : Configuration centrale du projet (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- [`utilisateurs/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/utilisateurs) : Modèle utilisateur personnalisé (`Utilisateur` basé sur `AbstractUser` avec connexion par e-mail unique), gestion des 4 rôles (`Administrateur`, `Responsable`, `Technicien`, `Agent local`), notifications et messages de contact.
- [`localisation/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/localisation) : Hiérarchie géographique complète du Mali (`Region` → `Cercle` → `Commune` → `Village`).
- [`points_eau/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/points_eau) : Gestion des points d'eau (`PointEau`) et journal de suivi des états (`HistoriqueEtatPointEau`).
- [`equipements/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/equipements) : Gestion des équipements installés sur les points d'eau (`Equipement`).
- [`pannes/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/pannes) : Déclaration et suivi des pannes (`Panne`).
- [`interventions/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/interventions) : Gestion des interventions (`Intervention`) et des pièces consommées (`PieceUtiliseeIntervention`).
- [`techniciens/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/techniciens) : Profils professionnels, compétences et disponibilité des techniciens (`Technicien`).
- [`stock/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/stock) : Gestion des pièces détachées (`PieceDetachee`) et historique des entrées/sorties (`MouvementStock`).
- [`rapports/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/rapports) : Statistiques temps réel, rapports d'activité (`RapportActivite`) et export CSV.
- [`suivi/`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/suivi) : Application centrale servant l'interface existante intacte ([`acceuil.html`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/suivi/templates/suivi/acceuil.html)) et le connecteur AJAX/CSRF ([`backend.js`](file:///c:/wamp64/www/ProgramDjango/EauSolidaire/suivi/static/suivi/js/backend.js)).

---

## 2. Préparation de MySQL avec WampServer et phpMyAdmin

1. Démarrez **WampServer** et vérifiez que l'icône est verte (service MySQL démarré sur le port `3306`).
2. Ouvrez **phpMyAdmin** (`http://localhost/phpmyadmin`) ou utilisez la console MySQL de WampServer :
   ```sql
   CREATE DATABASE IF NOT EXISTS eausolidaire_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Vérifiez le fichier `.env` à la racine du projet (copié depuis `.env.example`) :
   ```env
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=eausolidaire_db
   DB_USER=root
   DB_PASSWORD=
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```

---

## 3. Installation et Lancement du Projet

Ouvrez un terminal PowerShell ou CMD à la racine du projet (`c:\wamp64\www\ProgramDjango\EauSolidaire`) :

### Étape 1 : Activer l'environnement virtuel et installer les dépendances
```powershell
.\env\Scripts\activate
pip install -r requirements.txt
```

### Étape 2 : Appliquer les migrations Django vers MySQL
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Étape 3 : Initialiser les données de base dans MySQL (optionnel, aussi exécuté automatiquement au premier chargement)
```powershell
python manage.py initialiser_donnees
```

### Étape 4 : Créer le compte Administrateur initial de manière sécurisée
Pour créer votre compte administrateur (`diabymadoussou528@gmail.com`) avec le mot de passe sécurisé de votre choix (saisi au clavier sans jamais apparaître en clair dans le code) :
```powershell
python manage.py creer_admin_initial
```
*(Ou via la commande native Django : `python manage.py createsuperuser --email diabymadoussou528@gmail.com --username diabymadoussou528@gmail.com`)*

### Étape 5 : Lancer le serveur de développement
```powershell
python manage.py runserver
```

- **Plateforme EauSolidaire** : `http://127.0.0.1:8000/`
- **Administration native Django** : `http://127.0.0.1:8000/admin/`
- **Administration MySQL (phpMyAdmin)** : `http://localhost/phpmyadmin/` (base `eausolidaire_db`)

---

## 4. Réinitialisation de mot de passe par e-mail SMTP & Gestion des Équipements

### Réinitialisation de mot de passe (SMTP)
- Le lien **« Mot de passe oublié ? »** sur la page de connexion ouvre une modale permettant d'envoyer un lien et un code de réinitialisation sécurisés (`uid` + `token` Django) via `/api/auth/password-reset/` et de définir un nouveau mot de passe via `/api/auth/password-reset/confirm/`.
- Pour activer l'envoi réel d'e-mails SMTP (ex. Gmail), renseignez dans `.env` :
  ```env
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST=smtp.gmail.com
  EMAIL_PORT=587
  EMAIL_USE_TLS=True
  EMAIL_HOST_USER=diabymadoussou528@gmail.com
  EMAIL_HOST_PASSWORD=votre_mot_de_passe_application_google
  DEFAULT_FROM_EMAIL=EauSolidaire Mali <diabymadoussou528@gmail.com>
  ```
- Si `EMAIL_HOST_PASSWORD` est vide en développement local, Django bascule automatiquement sur le backend console afin d'afficher l'e-mail (avec l'UID et le Token) dans le terminal sans générer d'erreur.

### Gestion des Équipements dans le Frontend
- Dans l'espace Administrateur (**Points d'eau**), la section **« Équipements installés sur les points d'eau »** permet de rechercher, ajouter (`Ajouter un équipement`), modifier l'état de fonctionnement et supprimer des équipements en temps réel dans MySQL, en réutilisant strictement les composants visuels existants (`table()`, `modal()`, `badge()`).
- Les équipements d'un point d'eau sont également affichés dans la fiche détail de la **Cartographie** et peuvent être sélectionnés lors de la **Déclaration d'une panne**.
