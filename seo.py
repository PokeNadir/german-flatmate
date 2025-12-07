import streamlit as st
import pathlib
import os

# --- CONFIGURATION ---
GA_ID = "G-F3PX9QD8EL"  # Votre ID est déjà là

def patch_index_html():
    """
    Ce script va chercher le fichier index.html original de Streamlit
    et insérer les balises SEO AVANT le démarrage du serveur.
    """
    print("🚀 Démarrage du patch SEO...")
    
    # 1. Localiser le fichier index.html dans les dossiers d'installation
    # On utilise st.__file__ pour trouver où Streamlit est installé
    streamlit_path = pathlib.Path(st.__file__).parent
    index_path = streamlit_path / "static" / "index.html"
    
    print(f"📂 Fichier trouvé ici : {index_path}")

    if not index_path.exists():
        print("❌ ERREUR : index.html introuvable !")
        return

    # 2. Lire le contenu
    try:
        html_content = index_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Erreur de lecture : {e}")
        return

    # 3. Vérifier si déjà patché
    if "" in html_content:
        print("✅ Le fichier est déjà patché. Rien à faire.")
        return

    # 4. Le Code à injecter
    injection_code = f"""
    <meta name="description" content="Generate your professional German rental application (Bewerbungsmappe) in minutes. Perfect for expats without German skills or SCHUFA. Get your german flat!">
    <meta name="keywords" content="German rental application, Bewerbungsmappe generator, Schufa help, expat berlin, flat hunting germany">
    
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_ID}');
    </script>
    """
    
    # 5. Insérer dans le HEAD
    if "</head>" in html_content:
        new_html = html_content.replace("</head>", f"{injection_code}\n</head>")
        
        try:
            index_path.write_text(new_html, encoding='utf-8')
            print("✨ SUCCÈS : Balises SEO injectées avec succès !")
        except Exception as e:
            print(f"❌ Erreur d'écriture : {e}")
    else:
        print("❌ Balise </head> non trouvée dans le fichier.")

if __name__ == "__main__":
    patch_index_html()
